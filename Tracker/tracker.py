import datetime
import logging
from time import sleep
from Character import Character


class Tracker:
    def __init__(self, redis_adaptor, ccp_adaptor, zkb_adaptor, corp_id, region_id, month_id):
        self.redis_adaptor = redis_adaptor
        self.ccp_adaptor = ccp_adaptor
        self.zkb_adaptor = zkb_adaptor

        self.corp_id = corp_id
        self.region_id = region_id
        self.month_id = month_id

        self.characters = {}
            # character_id : Character
        self.kills = {}
            # killmail_id : {
            #    'killmail_id'   : int
            #    'killmail_hash' : str,
            #    'zkb_blob'      : dict,
            #    'ccp_blob'      : dict or none,
            # }

    def run(self, min_runtime_seconds=120):
        _start_datetime = datetime.datetime.now()

        self.get_all_corp_killmails()
        self.get_all_ccp_killblobs()
        self.add_characters_to_redis()

        _seconds_taken = (datetime.datetime.now() - _start_datetime).total_seconds()
        if _seconds_taken < min_runtime_seconds:
            sleep_seconds = (min_runtime_seconds - _seconds_taken)
            logging.info(f'Run Cycle finished, sleeping for {sleep_seconds} seconds')
            sleep(sleep_seconds)

    def add_characters_to_redis(self):
        killers = []

        for character in self.characters.values():
            killers.append(character.get_row)

        logging.info(f'Writing {len(killers)} characters to redis.')
        self.redis_adaptor.update_killers(killers)
        self.redis_adaptor.update_update_datetime()

    def get_all_corp_killmails(self):
        all_corp_killmails = self.zkb_adaptor.get_all_corp_kill_ids(self.corp_id, self.month_id)

        _old_count = self.killmail_count
        for killmail_blob in all_corp_killmails:
            killmail_id = killmail_blob['killmail_id']

            if self.known_killmail(killmail_id):
                continue
            else:
                self.add_new_killmail(killmail_id, killmail_blob)
        logging.info(f'{self.__class__.__name__} : Added {self.killmail_count - _old_count} Killmails.')

    @property
    def killmail_count(self):
        return len(self.kills)

    def known_killmail(self, killmail_id):
        return killmail_id in self.kills.keys()

    def add_new_killmail(self, killmail_id, killmail_blob):
        self.kills[killmail_id] = {
            'killmail_id'   : killmail_id,
            'killmail_hash' : killmail_blob['zkb']['hash'],
            'zkb_blob'      : killmail_blob,
            'ccp_blob'      : None,
        }

    def get_all_ccp_killblobs(self):
        kills_to_query = []
        for killmail_id, kill_blob in self.kills.items():
            if kill_blob['ccp_blob'] is None:
                kills_to_query.append( (killmail_id, kill_blob['killmail_hash']) )

        if len(kills_to_query) == 0:
            return

        ccp_killmails = self.ccp_adaptor.get_killmails(kills_to_query)
        for killmail_id, ccp_blob in ccp_killmails.items():
            self.kills[killmail_id]['ccp_blob'] = ccp_blob
        logging.info(f'{self.__class__.__name__} : Got {len(ccp_killmails)} CCP Killmail Blobs.')

    def populate_all_characters(self):
        all_character_ids = self.get_all_character_ids_from_killmails()
        

    def get_all_character_ids_from_killmails(self):
        character_ids = set()
        for killmail in self.kills.values():
            if killmail['ccp_blob'] is None:
                continue
        
            for attacker_blob in killmail['ccp_blob']['attackers']:
                if 'character_id' not in attacker_blob.keys():
                    continue    # Probably an NPC v0v
                if 'corporation_id' not in attacker_blob.keys():
                    continue
                if attacker_blob['corporation_id'] != self.corp_id:
                    continue

                character_ids.add(attacker_blob['character_id'])

        return character_ids
