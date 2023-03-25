import unittest
from unittest.mock import patch
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from resource_log import ResourceLogger

class TestLoggingFunctionality(unittest.TestCase):
    def set_up(self):
        self.test_logger = ResourceLogger(kafka_bootstrap_servers=['localhost:9092'])

    def test_log_system_metrics(self):
        with patch('resource_log.ResourceLogger.producer') as mock_producer:
            with patch('resource_log.ResourceLogger.logger', new=self.test_logger.logger):
                self.test_logger.log_system_metrics()

                self.assertEqual(self.test_logger.logger.info.call_count, 2)
                self.test_logger.logger.info.assert_any_call('CPU Usage: 10%')
                self.test_logger.logger.info.assert_any_call('Memory Usage: 20%')

                self.assertEqual(mock_producer.send.call_count, 1)
                mock_producer.send.assert_called_with('system-metrics', value={'@timestamp': '2023-01-01T00:00:00.000000Z', 'cpu_percent': 10, 'mem_percent': 20})

    def tear_down(self):
        log_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.log')
        if os.path.exists(log_file_path):
            os.remove(log_file_path)

if __name__ == '__main__':
    unittest.main()