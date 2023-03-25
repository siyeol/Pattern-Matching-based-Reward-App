import unittest
from json import dumps, loads
from kafka import KafkaProducer, KafkaConsumer
import time

class TestKafkaFunctionality(unittest.TestCase):
    def set_up(self):
        self.producer = KafkaProducer(
            bootstrap_servers=["localhost:9092"],
            value_serializer=lambda x: dumps(x).encode("utf-8"),
        )

        self.consumer = KafkaConsumer(
            "opencv",
            bootstrap_servers=["localhost:9092"],
            auto_offset_reset="earliest",
            enable_auto_commit=True,
            group_id="test-group",
            value_deserializer=lambda x: loads(x.decode("utf-8")),
        )

    def test_kafka_producer_consumer(self):
        test_message = {
            "success": True,
            "location": {"latitude": 37.421999, "longitude": -122.084057},
            "name": "test_adv",
        }

        self.producer.send("opencv", value=test_message)
        self.producer.flush()

        time.sleep(5)

        received_message = None
        for message in self.consumer:
            received_message = message.value
            break

        self.assertIsNotNone(received_message, "No message received from the 'opencv' topic")
        self.assertEqual(test_message, received_message, "Sent and received messages do not match")

    def tear_down(self):
        self.producer.close()
        self.consumer.close()

if __name__ == "__main__":
    unittest.main()
