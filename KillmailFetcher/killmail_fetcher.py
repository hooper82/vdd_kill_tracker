import requests
import logging
from time import sleep
from collections import namedtuple
import datetime
from pprint import pprint

URL_ZKILLBOARD_CORP_KILLS = "https://zkillboard.com/api/corporationID/{}/regionID/{}/month/{}/page/{}/"
URL_CCP_KILLMAIL = "https://esi.evetech.net/latest/killmails/{}/{}/?datasource=tranquility"
API_WAIT_SECONDS = 5

KillIdentifier = namedtuple("KillIdentifier", ['id', 'hash'])


class KillmailFetcher:
    def __init__(self, corporation_id, region_id, month_int):
        assert isinstance(corporation_id, int)
        assert isinstance(month_int, int)

        self.corporation_id = corporation_id
        self.region_id = region_id
        self.month = month_int

        self.kills = {}

    def kill_exists(self, killmail_id):
        assert isinstance(killmail_id, KillIdentifier)
        return killmail_id in self.kills.keys()

    def add_kill(self, killmail_id, killmail=None):
        assert isinstance(killmail_id, KillIdentifier)
        self.kills[killmail_id] = killmail

    @property
    def kill_count(self):
        return len(self.kills.keys())

    @classmethod
    def _get_corp_killmails(cls, corporation_id, region_id, month, page):
        assert isinstance(page, int)
        assert page > 0

        _resp = requests.get(url=URL_ZKILLBOARD_CORP_KILLS.format(corporation_id, region_id, month, page))
        if _resp.status_code != 200:
            logging.warning(f'ZKillboard Request Failed (Code {_resp.status_code}), waiting {API_WAIT_SECONDS} seconds and retrying.')
            sleep(API_WAIT_SECONDS)
            results = cls._get_corp_killmails(corporation_id, region_id, month, page)
        else:
            results = _resp.json()
        return results

    def get_all_corp_killmail_hashes_and_ids(self):
        _kill_count_before_starting = self.kill_count
        for page in range(1, 1000):
            results = self._get_corp_killmails(self.corporation_id, self.region_id, self.month, page)

            if len(results) == 0:
                break   # ZKillboard has no more kills for us.

            for killmail in results:
                kill_id = killmail['killmail_id']
                kill_hash = killmail['zkb']['hash']

                kill = KillIdentifier(kill_id, kill_hash)
                if not self.kill_exists(kill):
                    self.add_kill(kill)

        added_kill_count = self.kill_count - _kill_count_before_starting
        logging.info(f'Added {added_kill_count} new kills')

    @classmethod
    def _get_killmail(cls, kill_id, kill_hash):
        _resp = requests.get(url=URL_CCP_KILLMAIL.format(kill_id, kill_hash))
        if _resp.status_code != 200:
            logging.warning(f'CCP ESI Request Failed (Code {_resp.status_code}), waiting {API_WAIT_SECONDS} seconds and retrying.')
            sleep(API_WAIT_SECONDS)
            results = cls._get_killmail(kill_id, kill_hash)
        else:
            results = _resp.json()
        return results

    def get_killmail(self, kill_id, kill_hash):
        logging.info(f'Getting Killmail ID {kill_id} from CCP ESI API.')
        return self._get_killmail(kill_id, kill_hash)

    def update_all_killmails(self):
        for killmail_id, killmail in self.kills.items():
            if killmail is None:
                killmail = self.get_killmail(killmail_id.id, killmail_id.hash)
                self.add_kill(killmail_id, killmail)

    def run(self):
        self.get_all_corp_killmail_hashes_and_ids()
        self.update_all_killmails()