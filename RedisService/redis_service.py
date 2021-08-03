import redis
import json
import datetime

KILLERS_KEY = 'killers'
UPDATE_KEY = 'update_datetime'
UPDATE_FORMAT = "%Y-%m-%d %H:%M:%S"

class RedisService:
    def __init__(self, hostname, port):
        self._redis = redis.StrictRedis(host=hostname, port=port, charset="utf-8", decode_responses=True)

    def update_killers(self, killers):
        assert isinstance(killers, list)

        self._redis.set(KILLERS_KEY, json.dumps(killers))

    def get_killers(self):
        return json.loads(self._redis.get(KILLERS_KEY))

    def update_update_datetime(self):
        self._redis.set(UPDATE_KEY, datetime.datetime.now().strftime(UPDATE_FORMAT))
    
    def get_update_datetime(self):
        return datetime.datetime.strptime(self._redis.get(UPDATE_KEY, UPDATE_FORMAT))
