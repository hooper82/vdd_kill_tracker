import os
import argparse
import logging

from CCPAdaptor import CCPAdaptor
from ZKBAdaptor import ZKBAdaptor
from RedisService import RedisService
from Tracker import Tracker

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('--redis_host', default=os.environ['REDIS_HOSTNAME'])
    parser.add_argument('--redis_port', default=os.environ['REDIS_PORT'])

    parser.add_argument('--corp_id', type=int, default=os.environ['CORPORATION_ID'])
    parser.add_argument('--region_id', type=int, default=os.environ['REGION_ID'])
    parser.add_argument('--month_id', type=int, default=os.environ['MONTH'])

    args = parser.parse_args()

    redis_service = RedisService(args.redis_host, args.redis_port)
    ccp_adaptor = CCPAdaptor()
    zkb_adaptor = ZKBAdaptor()

    tracker = Tracker(redis_service, ccp_adaptor, zkb_adaptor, args.corp_id, args.region_id, args.month_id)

    while True:
        tracker.run(120)