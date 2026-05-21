class Stats:
    def __init__(self):
        self.reset()

    def reset(self):
        self.harvested_wheat = 0
        self.enemies_killed = {}
        self.money_earned = 0
        self.money_stolen = 0

    def record_harvest(self, amount=1):
        self.harvested_wheat += amount

    def record_enemy_kill(self, enemy_type: str, amount=1):
        self.enemies_killed[enemy_type] = self.enemies_killed.get(enemy_type, 0) + amount

    def record_money_earned(self, amount: int):
        self.money_earned += amount

    def record_money_stolen(self, amount: int):
        self.money_stolen += amount

    def summary(self):
        return {
            'harvested_wheat': self.harvested_wheat,
            'enemies_killed': dict(self.enemies_killed),
            'money_earned': self.money_earned,
            'money_stolen': self.money_stolen,
        }


stats = Stats()

def record_harvest(n=1):
    stats.record_harvest(n)

def record_enemy_kill(enemy_type, n=1):
    stats.record_enemy_kill(enemy_type, n)

def record_money_earned(amount):
    stats.record_money_earned(amount)

def record_money_stolen(amount):
    stats.record_money_stolen(amount)

def get_summary():
    return stats.summary()
