class Quest:
    def __init__(self, name: str, objective: dict, reward: dict):
        self.name = name
        self.objective = objective
        self.reward = reward
        self.progress = 0
        self.completed = False

    @property
    def goal(self) -> int:
        return int(self.objective.get('count', 0))

    @property
    def objective_description(self) -> str:
        return self.objective.get('description', '')

    def add_progress(self, amount: int = 1) -> bool:
        if self.completed:
            return False
        self.progress += amount
        if self.progress >= self.goal:
            self.progress = self.goal
            self.completed = True
            return True
        return False

    def claim_reward(self) -> dict:
        return self.reward


def create_harvest_wheat_quest() -> Quest:
    return Quest(
        name='Harvest wheat',
        objective={'description': 'Harvest 100 wheat', 'target': 'wheat', 'count': 100},
        reward={'money': 250}
    )


active_quest: Quest | None = None


def set_active_quest(quest: Quest) -> None:
    global active_quest
    active_quest = quest


def add_progress(amount: int = 1) -> bool:
    if active_quest is None:
        return False
    return active_quest.add_progress(amount)


def get_quest_status() -> tuple[str, int, int]:
    if active_quest is None:
        return 'No active quest', 0, 0
    return active_quest.name, active_quest.progress, active_quest.goal


def get_active_quest() -> Quest | None:
    return active_quest


def claim_reward() -> dict | None:
    if active_quest is None or not active_quest.completed:
        return None
    return active_quest.claim_reward()
