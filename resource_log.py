import logging
from logging.handlers import SocketHandler
import psutil
import json
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from pythonjsonlogger import jsonlogger

from elasticsearch import Elasticsearch

class ResourceLogger():
    def __init__(self, elasticsearch_host):
        # Configure logger
        self.logger = logging.getLogger("flask-elk")
        logging.basicConfig(filename='app.log', level=logging.DEBUG)

        socket_handler = SocketHandler("localhost", 5001)
        formatter = jsonlogger.JsonFormatter("%(asctime)s - %(levelname)s - %(message)s")
        socket_handler.setFormatter(formatter)
        self.logger.addHandler(socket_handler)

        self.es = Elasticsearch(hosts=[elasticsearch_host])

    def log_system_metrics(self):
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        current_time = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')

        self.logger.info(f"CPU Usage: {cpu_percent}%")
        self.logger.info(f"Memory Usage: {memory_percent}%")

        self.es.index(index='system-metrics', body={
            'cpu_percent': cpu_percent,
            'mem_percent': memory_percent,
            '@timestamp': current_time
        })

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