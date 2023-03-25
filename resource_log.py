import logging
import psutil
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from kafka import KafkaProducer
from json import dumps

class ResourceLogger():
    def __init__(self, kafka_bootstrap_servers):
        # Configure logger
        self.logger = logging.getLogger("flask-kafka")
        logging.basicConfig(filename='app.log', level=logging.DEBUG)

        # Configure Kafka producer
        self.producer = KafkaProducer(
            bootstrap_servers=kafka_bootstrap_servers,
            value_serializer=lambda x: dumps(x).encode('utf-8')
        )

    def log_system_metrics(self):
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        current_time = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')

        self.logger.info(f"CPU Usage: {cpu_percent}%")
        self.logger.info(f"Memory Usage: {memory_percent}%")

        log_message = {
            '@timestamp': current_time,
            'cpu_percent': cpu_percent,
            'mem_percent': memory_percent
        }

        self.producer.send('system-metrics', value=log_message)
        self.producer.flush()


    def start_scheduler(self):
        scheduler = BackgroundScheduler()
        scheduler.start()
        scheduler.add_job(
            func=self.log_system_metrics,
            trigger=IntervalTrigger(seconds=60),
            id="log_system_metrics",
            name="Log system metrics every 60 seconds",
            replace_existing=True,
        )