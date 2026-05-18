from ursina import Entity, color
from ursina.prefabs.first_person_controller import FirstPersonController


def create_player():
    player = FirstPersonController()
    player.cursor.visible = False
    player.hp = 100
    player.max_hp = 100
    player.stamina = 100
    player.max_stamina = 100
    player.base_speed = 5.0
    player.sprint_speed_multiplier = 2.0
    player.stamina_regen_rate = 25.0
    player.stamina_sprint_cost = 35.0
    player.is_sprinting = False
    player.money = 0
    player_model = Entity(model='cube', color=color.azure, scale=(1, 2, 1), parent=player, position=(0, -1, 0))
    return player, player_model
