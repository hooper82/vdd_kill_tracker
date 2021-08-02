import datetime
import requests
import logging
from time import sleep

from pprint import pprint

from .character import Character

CAPSUAL_TYPE_IDS = [
    33328,    # Capsule - Genolution 'Auroral' 197-variant
    670,      # Capsule
]
CORVETTE_TYPE_IDS = [
    33079, # Hematos
    33083, # Violator
    1233,  # Polaris Enigma Frigate
    9860,  # Polaris Legatus Frigate
    33081, # Taipan
    588,   # Reaper
    601,   # Ibis
    615,   # Immolator
    617,   # Echo
    9854,  # Polaris Inspector Frigate
    9858,  # Polaris Centurion TEST
    596,   # Impairor
    606,   # Velator
    9862,  # Polaris Centurion Frigate
]

URL_ESI_CHARACTER = "https://esi.evetech.net/latest/characters/{}/?datasource=tranquility"
API_WAIT_SECONDS = 5

class CharacterTracker:
    def __init__(self, killmail_fetcher, corporation_id, exclude_pod_kills, exclude_corvettes):
        assert isinstance(corporation_id, int)
        assert isinstance(exclude_pod_kills, bool)
        assert isinstance(exclude_corvettes, bool)

        self.killmail_fetcher = killmail_fetcher
        self.corporation_id = corporation_id
        
        self.exclude_pod_kills = exclude_pod_kills
        self.exclude_corvettes = exclude_corvettes

        self.characters = {}

    def character_exists(self, character_id):
        assert isinstance(character_id, int)
        return character_id in self.characters.keys()

    def add_character(self, character_id):
        assert not self.character_exists(character_id)

        character_name = self.get_character_name(character_id)
        character = Character(character_id, character_name)
        self.characters[character_id] = character

    def get_character(self, character_id):
        return self.characters[character_id]

    def add_kill_to_character(self, character_id, kill_id):
        assert self.character_exists(character_id)

        character = self.get_character(character_id)
        character.add_kill_id(kill_id)

    @classmethod
    def get_character_name(cls, character_id):
        assert isinstance(character_id, int)

        logging.info(f'Getting Character ID {character_id} from CCP ESI API.')
        _resp = requests.get(url=URL_ESI_CHARACTER.format(character_id))
        if _resp.status_code != 200:
            logging.warning(f'CCP ESI API Character call failed (Code {_resp.status_code}), waiting {API_WAIT_SECONDS} seconds and retrying.')
            sleep(API_WAIT_SECONDS)
            name = cls.get_character_name(character_id)
        else:
            name = _resp.json()['name']
        return name

    def run(self, cycle_seconds):
        _start_time = datetime.datetime.now()

        self.killmail_fetcher.run()

        for killmail in self.killmail_fetcher.kills.values():
            if killmail is None:
                continue

            victim_type_id = killmail["victim"]["ship_type_id"]
            if (self.exclude_pod_kills is True) and (victim_type_id in CAPSUAL_TYPE_IDS):
                continue
            if (self.exclude_corvettes is True) and (victim_type_id in CORVETTE_TYPE_IDS):
                continue

            killmail_id = killmail["killmail_id"]

            for attackers in killmail["attackers"]:
                if 'character_id' not in attackers.keys():
                    continue    # Probably an NPC
                character_id = attackers['character_id']
                corporation_id = attackers['corporation_id']

                # Not in correct corporation
                if corporation_id != self.corporation_id:
                    continue

                if not self.character_exists(character_id):
                    self.add_character(character_id)
                self.add_kill_to_character(character_id, killmail_id)

        _seconds_taken = (datetime.datetime.now() - _start_time).total_seconds()
        if _seconds_taken < cycle_seconds:
            sleep_seconds = (cycle_seconds - _seconds_taken)
            logging.info(f'Sleeping for {sleep_seconds} seconds')
            sleep(sleep_seconds)

        character_kill_count = []
        for character in self.characters.values():
            character_kill_count.append( (character.name, character.kill_count) )

        pprint(sorted(character_kill_count, key=lambda t:t[1]))
