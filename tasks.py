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


def create_kill_enemies_quest() -> Quest:
    return Quest(
        name='Slay monsters',
        objective={'description': 'Kill 100 enemies', 'target': 'enemies', 'count': 100},
        reward={'item': 'gun', 'count': 1}
    )


active_quest: Quest | None = None


def set_active_quest(quest: Quest) -> None:
    global active_quest
    active_quest = quest


def add_progress(amount: int = 1) -> bool:
    if active_quest is None:
        return False
    # Update progress directly from stats for known objective targets
    try:
        import stats as stats_mod
        summary = stats_mod.get_summary()
        target = active_quest.objective.get('target', '')
        if target == 'wheat':
            active_quest.progress = summary.get('harvested_wheat', 0)
        elif target == 'enemies':
            enemies_map = summary.get('enemies_killed', {})
            total = sum(enemies_map.values()) if isinstance(enemies_map, dict) else 0
            active_quest.progress = total
        else:
            active_quest.progress += amount
    except Exception:
        active_quest.progress += amount
    
    prev = active_quest.progress
    result = active_quest.progress >= active_quest.goal
    if result and not active_quest.completed:
        active_quest.completed = True
    
    try:
        print(f"Quest progress: {active_quest.name} {active_quest.progress}/{active_quest.goal}")
    except Exception:
        pass
    try:
        from rendering import update_quest_text
        if active_quest is not None:
            update_quest_text(active_quest.name, active_quest.progress, active_quest.goal)
    except Exception:
        pass
    return result
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
