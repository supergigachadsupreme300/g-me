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
        objective={'description': 'Kill 30 enemies', 'target': 'enemies', 'count': 30},
        reward={'money': 500}
    )


def create_earn_money_quest() -> Quest:
    return Quest(
        name='Earn coins',
        objective={'description': 'Earn 100000 coins', 'target': 'money_earned', 'count': 100000},
        reward={'money': 1000}
    )


quest_list: list[Quest] = []
active_quest: Quest | None = None
focused_quest_index: int = 0


def initialize_quests() -> None:
    global quest_list, active_quest, focused_quest_index
    if quest_list:
        return
    quest_list = [
        create_harvest_wheat_quest(),
        create_earn_money_quest(),
        create_kill_enemies_quest(),
    ]
    focused_quest_index = 0
    active_quest = quest_list[0] if quest_list else None


def get_quests() -> list[Quest]:
    initialize_quests()
    return quest_list


def get_focused_index() -> int:
    initialize_quests()
    return max(0, min(focused_quest_index, len(quest_list) - 1))


def get_active_quest() -> Quest | None:
    initialize_quests()
    if active_quest is not None:
        return active_quest
    return quest_list[0] if quest_list else None


def set_active_quest(quest: Quest) -> None:
    global active_quest, focused_quest_index
    initialize_quests()
    if quest not in quest_list:
        quest_list.append(quest)
    focused_quest_index = quest_list.index(quest)
    active_quest = quest


def set_focused_quest(index: int) -> None:
    global active_quest, focused_quest_index
    initialize_quests()
    if not quest_list:
        return
    focused_quest_index = max(0, min(index, len(quest_list) - 1))
    active_quest = quest_list[focused_quest_index]


def add_progress(amount: int = 1, target: str | None = None) -> bool:
    initialize_quests()
    try:
        import stats as stats_mod
        summary = stats_mod.get_summary()
        enemies_map = summary.get('enemies_killed', {})
        total_enemies = sum(enemies_map.values()) if isinstance(enemies_map, dict) else 0
    except Exception:
        summary = {}
        total_enemies = 0

    result = False
    active = get_active_quest()
    for quest in quest_list:
        if quest.completed:
            continue
        target_key = quest.objective.get('target', '')
        if target_key == 'wheat':
            quest.progress = summary.get('harvested_wheat', 0)
        elif target_key == 'enemies':
            quest.progress = total_enemies
        elif target_key == 'money_earned':
            quest.progress = summary.get('money_earned', 0)
        elif target_key == 'money_stolen':
            quest.progress = summary.get('money_stolen', 0)
        elif target is not None and target_key == target:
            quest.progress += amount
        elif quest == active:
            quest.progress += amount

        quest.progress = min(quest.progress, quest.goal)
        if quest.progress >= quest.goal:
            quest.completed = True
        if quest == active:
            result = quest.completed

    try:
        if active is not None:
            print(f"Quest progress: {active.name} {active.progress}/{active.goal}")
    except Exception:
        pass
    try:
        from rendering import update_quest_text
        if active is not None:
            update_quest_text(active.name, active.progress, active.goal)
    except Exception:
        pass
    if result:
        try_trigger_happy_ending()
    return result


def get_quest_status() -> tuple[str, int, int]:
    quest = get_active_quest()
    if quest is None:
        return 'No active quest', 0, 0
    return quest.name, quest.progress, quest.goal


def claim_reward() -> dict | None:
    quest = get_active_quest()
    if quest is None or not quest.completed:
        return None
    return quest.claim_reward()


def all_quests_completed() -> bool:
    initialize_quests()
    return len(quest_list) > 0 and all(quest.completed for quest in quest_list)


def try_trigger_happy_ending() -> None:
    if not all_quests_completed():
        return
    try:
        import cutscene_manager
        cutscene_manager.request_happy_ending()
    except Exception as e:
        print(f'Happy ending trigger failed: {e}')
