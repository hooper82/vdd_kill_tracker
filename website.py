import os
from flask import Flask
from flask import render_template
from RedisService import RedisService
import datetime

REDIS_HOSTNAME = os.environ['REDIS_HOSTNAME']
REDIS_PORT = os.environ['REDIS_PORT']

STATIC_FILE_PATH = '/static'

app = Flask(__name__, static_url_path=STATIC_FILE_PATH)
redis_service = RedisService(REDIS_HOSTNAME, REDIS_PORT)

@app.route('/')
def index():
    last_update_datetime = redis_service.get_update_datetime()

    characters = redis_service.get_killers()
    characters = sorted(characters, key=lambda c : c['kill_count'], reverse=True)

    # characters = [
    #     {
    #         'name'             : 'Luskan Telamon',
    #         'id'               : 413104079,
    #         'kill_count'       : 5,
    #         'kill_value'       : 5000,
    #         'total_kill_count' : 5,
    #     }
    #     {
    #         'name'             : 'Test',
    #         'id'               : 413104079,
    #         'kill_count'       : 10,
    #         'kill_value'       : 5000,
    #         'total_kill_count' : 5,
    #     }
    # ]

    return render_template('index.html', characters=characters, last_update_datetime=last_update_datetime.strftime("%Y-%m-%d %H:%M:%S"))


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0')
