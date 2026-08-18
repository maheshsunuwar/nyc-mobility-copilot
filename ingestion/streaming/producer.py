import json
import time
import requests
from kafka import KafkaProducer


GBFS_URL = "https://gbfs.citibikenyc.com/gbfs/en/station_status.json"
KAFKA_BROKER = "localhost:9092"
TOPIC = "station-status"
POLL_INTERVAL_SECONDS = 30 # pull every 30 seconds

producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER,
    key_serializer=lambda k: k.encode("utf-8"),
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

def poll_and_produce():
    response = requests.get(GBFS_URL, timeout=10)
    response.raise_for_status()
    stations = response.json()['data']['stations']

    fetched_at = int(time.time())
    count = 0

    for station in stations:
        station['fetched_at'] = fetched_at
        producer.send(TOPIC, key=station['station_id'], value=station)
        count+=1

    producer.flush()
    print(f"Produced {count} station events at {fetched_at}")

if __name__ == '__main__':
    print("run the kafka producer")
    while True:
        poll_and_produce()
        time.sleep(POLL_INTERVAL_SECONDS)
