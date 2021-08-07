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


class Character:
    def __init__(self, character_id, character_name, region_id, exclude_pod_kills, exclude_corvettes):
        assert isinstance(character_id, int)
        assert isinstance(character_name, str)
        assert isinstance(region_id, int)

        self.id = character_id
        self.name = character_name
        self.region_id = region_id
        self.exclude_pod_kills = exclude_pod_kills
        self.exclude_corvettes = exclude_corvettes

        self.kills = {}
        self.kill_ids = set()

    def _get_attacker_blob(self, ccp_blob):
        for attacker_blob in ccp_blob["attackers"]:
            if 'character_id' not in attacker_blob.keys():
                continue    # Probably an NPC v0v
            
            if self.id == attacker_blob['character_id']:
                return attacker_blob

        raise Exception("Could not find character in attacker blob!")

    def is_new_kill_id(self, kill_id):
        return kill_id not in self.kills.keys()

    def is_in_kill_blob(self, ccp_blob):
        for attacker_blob in ccp_blob["attackers"]:
            if 'character_id' not in attacker_blob.keys():
                continue    # Probably an NPC v0v
            
            if self.id == attacker_blob['character_id']:
                return True
        return False

    def add_kill(self, kill_id, ccp_blob, zkb_blob, ccp_adaptor):
        if not self.is_new_kill_id(kill_id):
            return

        if not self.is_in_kill_blob(ccp_blob):
            return

        kill_timestamp = ccp_blob['killmail_time']
        kill_solarsystem_id = ccp_blob['solar_system_id']
        kill_region_id = ccp_adaptor.get_region(kill_solarsystem_id)
        kill_value = zkb_blob['zkb']['totalValue']
        attacker_blob = self._get_attacker_blob(ccp_blob)
        victim_blob = ccp_blob['victim']
        kill_victim_type_id = victim_blob['ship_type_id']

        self.kills[kill_id] = {
            'id'                  : kill_id,
            'timestamp'           : kill_timestamp,
            'solarsystem_id'      : kill_solarsystem_id,
            'region_id'           : kill_region_id,
            'value'               : kill_value,
            'attacker_blob'       : attacker_blob,
            'victim_ship_type_id' : kill_victim_type_id,
            'victim_blob'         : victim_blob,
        }

    def _is_valid_kill(self, kill):
        if kill['region_id'] != self.region_id:
            return False
        if (self.exclude_pod_kills) and (kill['victim_ship_type_id'] in CAPSUAL_TYPE_IDS):
            return False
        if (self.exclude_corvettes) and (kill['victim_ship_type_id'] in CORVETTE_TYPE_IDS):
            return False
        return True

    @property
    def kill_count(self):
        _count = 0
        for kill in self.kills.values():
            if self._is_valid_kill(kill):
                _count += 1
        return _count

    @property
    def kill_value(self):
        _value = 0
        for kill in self.kills.values():
            if self._is_valid_kill(kill):
                _value += kill['value']

        _value = round(_value, 0)
        return f'{_value:,}'

    @property
    def total_kill_count(self):
        return len(self.kills)

    @property
    def get_row(self):
        return {
            'name'             : self.name,
            'id'               : self.id,
            'kill_count'       : self.kill_count,
            'kill_value'       : self.kill_value,
            'total_kill_count' : self.total_kill_count,
        }
