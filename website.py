import os
from flask import Flask
from flask import render_template
from RedisService import RedisService


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

    return render_template('index.html', characters=characters, last_update_datetime=last_update_datetime.strftime("%Y-%m-%d %H:%M:%S"))


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0')
