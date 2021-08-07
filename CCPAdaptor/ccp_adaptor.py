import logging
import requests
import json
import concurrent.futures
from time import sleep

SOLARSYSTEMS_FILENAME = 'solarsystems.json'
RETRY_SECONDS = 5
RETRY_MAX_ATTEMPTS = 5
URL_KILLMAIL = "https://esi.evetech.net/latest/killmails/{}/{}/?datasource=tranquility"
URL_CHARACTER = "https://esi.evetech.net/latest/characters/{}/?datasource=tranquility"


def query_api(url, args):
    response = requests.get(url=url.format(*args))
    if response.status_code != 200:
        return False, None
    return True, response.json()


class CCPAdaptor:
    def __init__(self) -> None:
        self._solarsystems = self._load_solarsystems_from_disk()

    def _load_solarsystems_from_disk(self):
        with open(SOLARSYSTEMS_FILENAME, 'r') as f:
            solarsystems = json.load(f)
        logging.info(f'{self.__class__.__name__} : Loaded solarsystems from disk, found {len(solarsystems)}.')

        return {int(k):v for k, v in solarsystems.items()}

    def get_region(self, solarsystem_id):
        assert solarsystem_id in self._solarsystems.keys()
        return self._solarsystems[solarsystem_id]['region_id']

    @classmethod
    def get_killmail(cls, killmail_id, killmail_hash):
        for query_attempts in range(RETRY_MAX_ATTEMPTS):
            logging.info(f'{cls.__name__} : Querying Kill ({killmail_id}).')
            query_success, query_result = query_api(URL_KILLMAIL, (killmail_id, killmail_hash) )

            if query_success:
                return killmail_id, query_success, query_result
            else:
                logging.warning(f'{cls.__name__} : Kill Query Failed. Waiting {RETRY_SECONDS}')
                sleep(RETRY_SECONDS)

        return killmail_id, False, None

    @classmethod
    def get_killmails(cls, killmail_identifiers, workers=20):
        results = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            future_results = [executor.submit(cls.get_killmail, killmail_id, killmail_hash) for (killmail_id, killmail_hash) in killmail_identifiers]

        for future in concurrent.futures.as_completed(future_results):
            killmail_id, success, killmail_blob = future.result()
            if success:
                results[killmail_id] = killmail_blob

        return results

    @classmethod
    def get_character(cls, character_id):
        for query_attempts in range(RETRY_MAX_ATTEMPTS):
            logging.info(f'{cls.__name__} : Querying Character ({character_id}).')
            query_success, query_result = query_api(URL_CHARACTER, (character_id, ) )

            if query_success:
                return character_id, query_success, query_result
            else:
                logging.warning(f'{cls.__name__} : Character Query Failed. Waiting {RETRY_SECONDS}')
                sleep(RETRY_SECONDS)

        return character_id, False, None

    @classmethod
    def get_characters(cls, character_ids, workers=20):
        results = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            future_results = [executor.submit(cls.get_character, character_id) for character_id in character_ids]

        for future in concurrent.futures.as_completed(future_results):
            character_id, success, character_blob = future.result()
            if success:
                results[character_id] = character_blob

        return results