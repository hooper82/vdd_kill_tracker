import logging
from os import kill
import requests
import concurrent.futures
from time import sleep


RETRY_SECONDS = 5
RETRY_MAX_ATTEMPTS = 5
URL_CORPORATION_KILLS = "https://zkillboard.com/api/corporationID/{}/month/{}/page/{}/"


def query_api(url, args):
    response = requests.get(url=url.format(*args))
    if response.status_code != 200:
        return False, None
    return True, response.json()


def query_corporation_kills(corporation_id, month_id, page):
    success, results = query_api(URL_CORPORATION_KILLS, (corporation_id, month_id, page) )
    return page, success, results


class ZKBAdaptor:
    @classmethod
    def get_all_corp_kill_ids(cls, corporation_id, month_id, concurrent_page_count=5):
        results = []

        queried_fails = 0
        all_page_candidates = list(range(1, 10_000))
        query_not_finished = True

        while query_not_finished:
            batch_queried_fails = list()
            pages_to_query = all_page_candidates[0:concurrent_page_count]

            logging.info(f"{cls.__name__} : Querying Corpporation Kills (pages {','.join([str(p) for p in pages_to_query])}).")

            with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_page_count) as executor:
                future_results = [executor.submit(query_corporation_kills, corporation_id, month_id, page_id) for page_id in pages_to_query]

            for future in concurrent.futures.as_completed(future_results):
                page_id, success, kills_blob = future.result()
                if success:
                    all_page_candidates.pop(page_id)
                    if len(kills_blob) == 0:
                        query_not_finished = False
                        logging.info(f"{cls.__name__} : Corporation Kills Page {page_id} found 0 killmails.")
                    else:
                        results += kills_blob
                else:
                    queried_fails += 1
                    batch_queried_fails.append(page_id)

            if queried_fails > RETRY_MAX_ATTEMPTS:
                logging.warning(f'{cls.__name__} : Corporation Kills Query Failed. Failed {queried_fails} times. Stopping')
                break
            if len(batch_queried_fails) > 0:
                logging.warning(f"{cls.__name__} : Corporation Kills Query(s) Failed (pages {','.join([str(p) for p in batch_queried_fails])}). Waiting {RETRY_SECONDS}")
                sleep(RETRY_SECONDS)

        logging.info(f'{cls.__name__} : Found {len(results)} Corporation Kill IDs.')
        return results
