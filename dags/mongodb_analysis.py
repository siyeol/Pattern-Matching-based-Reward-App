from datetime import datetime, timedelta, timezone

from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from pymongo import MongoClient, GEOSPHERE, UpdateOne


def calculate_success_rate(success_counts, failure_counts):
    success_rate = {}
    for key in set(success_counts.keys()).union(failure_counts.keys()):
        success_count = success_counts.get(key, 0)
        failure_count = failure_counts.get(key, 0)
        success_rate[key] = success_count / (success_count + failure_count)
    return success_rate


def advanced_analyze_mongodb_data():
    client = MongoClient('localhost:27017')
    collection = client.cash_hunter.match_log

    # Filter to consider only the past week
    one_week_ago = datetime.now(timezone.utc) - timedelta(days=6)

    base_pipeline = [
        {'$match': {'timestamp': {'$gte': one_week_ago}}}
    ]

    # Calculate success rate per advertisement
    adv_success_counts = collection.aggregate(base_pipeline + [
        {'$match': {'success': True}},
        {'$group': {'_id': '$name', 'count': {'$sum': 1}}}
    ])
    adv_failure_counts = collection.aggregate(base_pipeline + [
        {'$match': {'success': False}},
        {'$group': {'_id': '$name', 'count': {'$sum': 1}}}
    ])

    adv_success_counts = {doc['_id']: doc['count'] for doc in adv_success_counts}
    adv_failure_counts = {doc['_id']: doc['count'] for doc in adv_failure_counts}

    success_rate = calculate_success_rate(adv_success_counts, adv_failure_counts)

    # Calculate average success rate per location
    max_distance = 500  # in meters

    # Calculate average success rate per location
    location_success_counts = list(collection.aggregate([
        {'$match': {'success': True}},
        {'$group': {'_id': '$location', 'count': {'$sum': 1}}}
    ]))

    location_failure_counts = list(collection.aggregate([
        {'$match': {'success': False}},
        {'$group': {'_id': '$location', 'count': {'$sum': 1}}}
    ]))

    # Group by adjacent locations
    grouped_success_counts = {}
    grouped_failure_counts = {}

    def find_and_merge_adjacent_location(grouped_counts, new_location, count):
        for loc_str, loc_data in grouped_counts.items():
            loc = loc_data['location']
            dist = collection.aggregate([
                {
                    '$geoNear': {
                        'near': new_location,
                        'distanceField': 'dist.calculated',
                        'maxDistance': max_distance,
                        'includeLocs': 'dist.location',
                        'uniqueDocs': False,
                        'spherical': True
                    }
                }
            ]).next()

            if dist['dist']['calculated'] <= max_distance:
                grouped_counts[loc_str]['count'] += count
                return True

        return False

    for doc in location_success_counts:
        loc = doc['_id']
        count = doc['count']
        if not find_and_merge_adjacent_location(grouped_success_counts, loc, count):
            grouped_success_counts[str(loc)] = {'location': loc, 'count': count}

    for doc in location_failure_counts:
        loc = doc['_id']
        count = doc['count']
        if not find_and_merge_adjacent_location(grouped_failure_counts, loc, count):
            grouped_failure_counts[str(loc)] = {'location': loc, 'count': count}

    location_success_counts = {k: v['count'] for k, v in grouped_success_counts.items()}
    location_failure_counts = {k: v['count'] for k, v in grouped_failure_counts.items()}

    location_success_rate = calculate_success_rate(location_success_counts, location_failure_counts)

    # Calculate the number of matches per day
    matches_per_day = collection.aggregate([
        {'$project': {'day': {'$dateToString': {'format': '%Y-%m-%d', 'date': '$timestamp'}}}},
        {'$group': {'_id': '$day', 'count': {'$sum': 1}}},
        {'$sort': {'_id': 1}}
    ])

    matches_per_day = {doc['_id']: doc['count'] for doc in matches_per_day}

    return {
        'success_rate_per_adv': success_rate,
        'average_success_rate_per_location': location_success_rate,
        'matches_per_day': matches_per_day
    }

def save_analysis_results_to_mongodb(results):
    client = MongoClient('localhost:27017')
    db = client.analysis_data

    # Save success_rate_per_adv
    success_rate_per_adv_bulk = [
        UpdateOne({'adv_name': adv_name}, {'$set': {'rate': rate}}, upsert=True)
        for adv_name, rate in results['success_rate_per_adv'].items()
    ]
    db.success_rate_per_adv.bulk_write(success_rate_per_adv_bulk)

    # Save average_success_rate_per_location
    avg_success_rate_per_location_bulk = [
        UpdateOne({'location': location}, {'$set': {'rate': rate}}, upsert=True)
        for location, rate in results['average_success_rate_per_location'].items()
    ]
    db.avg_success_rate_per_location.bulk_write(avg_success_rate_per_location_bulk)

    # Save matches_per_day
    matches_per_day_bulk = [
        UpdateOne({'day': day}, {'$set': {'count': count}}, upsert=True)
        for day, count in results['matches_per_day'].items()
    ]
    db.matches_per_day.bulk_write(matches_per_day_bulk)


# Airflow DAG configuration
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2023, 3, 26),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5)
}

dag = DAG(
    'mongodb_analysis',
    default_args=default_args,
    description='MongoDB analysis DAG',
    schedule_interval=timedelta(weeks=1),
    catchup=False
)

analyze_mongodb_data_task = PythonOperator(
    task_id='advanced_analyze_mongodb_data',
    python_callable=advanced_analyze_mongodb_data,
    provide_context=True,
    dag=dag
)

save_analysis_results_to_mongodb_task = PythonOperator(
    task_id='save_analysis_results_to_mongodb',
    python_callable=save_analysis_results_to_mongodb,
    op_args=['{{ ti.xcom_pull(task_ids="advanced_analyze_mongodb_data") }}'],
    dag=dag
)

analyze_mongodb_data_task >> save_analysis_results_to_mongodb_task