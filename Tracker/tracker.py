import datetime
import logging
from time import sleep
from Character import Character


class Tracker:
    def __init__(self, redis_adaptor, ccp_adaptor, zkb_adaptor, corp_id, region_id, month_id, exclude_pod_kills, exclude_corvettes):
        self.redis_adaptor = redis_adaptor
        self.ccp_adaptor = ccp_adaptor
        self.zkb_adaptor = zkb_adaptor

        self.corp_id = corp_id
        self.region_id = region_id
        self.month_id = month_id

        self.exclude_pod_kills = exclude_pod_kills
        self.exclude_corvettes = exclude_corvettes

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
        self.populate_all_characters()
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

        for character_id, character_name in self.get_new_character_names(all_character_ids).items():
            new_character = Character(character_id, character_name, self.region_id, self.exclude_pod_kills, self.exclude_corvettes)
            self.characters[character_id] = new_character
        
        for kill in self.kills.values():
            kill_id = kill['killmail_id']
            zkb_blob = kill['zkb_blob']
            ccp_blob = kill['ccp_blob']

            if ccp_blob is None:
                continue

            for character in self.characters.values():
                character.add_kill(kill_id, ccp_blob, zkb_blob, self.ccp_adaptor)

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

    def get_new_character_names(self, all_character_ids):
        new_character_ids = [c for c in all_character_ids if not self.character_exists(c)]

        character_ids_and_names = {}
        for character_id, character_blob in self.ccp_adaptor.get_characters(new_character_ids).items():
            character_ids_and_names[character_id] = character_blob['name']
        return character_ids_and_names

    def character_exists(self, character_id):
        return character_id in self.characters.keys()