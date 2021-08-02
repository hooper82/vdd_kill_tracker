import redis

KILLERS_KEY = 'killers'

class RedisService:
    def __init__(self, hostname, port):
        self._redis = redis.StrictRedis(host=hostname, port=port, charset="utf-8", decode_responses=True)

    def update_killers(self, killers):
        assert isinstance(killers, dict)

        self._redis.set(KILLERS_KEY, killers)

    def get_killers(self):
        return self._redis.get(KILLERS_KEY)
