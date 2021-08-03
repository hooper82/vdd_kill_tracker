class Character:
    def __init__(self, character_id, character_name):
        assert isinstance(character_id, int)
        assert isinstance(character_name, str)

        self.id = character_id
        self.name = character_name
        self.kill_ids = set()

    def add_kill_id(self, kill_id):
        self.kill_ids.add(kill_id)

    @property
    def kill_count(self):
        return len(self.kill_ids)

    @property
    def get_row(self):
        return {
            'name'             : self.name,
            'id'               : self.id,
            'kill_count'       : self.kill_count,
            'kill_value'       : '???',
            'total_kill_count' : '???',
        }
