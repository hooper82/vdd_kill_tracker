import datetime
from .redis_service import RedisService

class MockRedisService(RedisService):
    def __init__(self, hostname, port):
        self._redis = None

    def get_killers(self):
        return  [
            {
                'name'             : 'Luskan Telamon',
                'id'               : 413104079,
                'kill_count'       : 5,
                'kill_value'       : 5000,
                'total_kill_count' : 5,
            },
            {
                'name'             : 'Malakai Asamov',
                'id'               : 1454312349,
                'kill_count'       : 10,
                'kill_value'       : 5000,
                'total_kill_count' : 5,
            }
        ]

    def get_update_datetime(self):
        return datetime.datetime.now()
