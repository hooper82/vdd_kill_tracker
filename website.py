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
    characters = redis_service.get_killers()
    characters = {k: v for k, v in sorted(characters.items(), key=lambda item: item[1], reverse=True)}

    return render_template('index.html', character_names=characters.keys(), characters=characters)


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0')