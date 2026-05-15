from ursina import Entity, color
from ursina.prefabs.first_person_controller import FirstPersonController


def create_player():
    player = FirstPersonController()
    player.cursor.visible = False
    player_model = Entity(model='cube', color=color.azure, scale=(1, 2, 1), parent=player, position=(0, -1, 0))
    return player, player_model
