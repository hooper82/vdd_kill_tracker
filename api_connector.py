import os
import argparse

from KillmailFetcher import KillmailFetcher
from CharacterTracker import CharacterTracker
from RedisService import RedisService

VDD_CORP_ID = 1282059165
REGION_ID = 10000060

if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('--redis_host', default=os.environ['REDIS_HOSTNAME'])
    parser.add_argument('--redis_port', default=os.environ['REDIS_PORT'])

    parser.add_argument('--corp_id', type=int, default=os.environ['CORPORATION_ID'])
    parser.add_argument('--region_id', type=int, default=os.environ['REGION_ID'])
    parser.add_argument('--month', type=int, default=os.environ['MONTH'])

    args = parser.parse_args()

    redis_service = RedisService(args.redis_host, args.redis_port)
    killmail_fetcher = KillmailFetcher(args.corp_id, args.region_id, args.month)

    character_tracker = CharacterTracker(killmail_fetcher, redis_service, args.corp_id, True, True)

    while True:
        character_tracker.run(60)

