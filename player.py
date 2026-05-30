from ursina import Entity, color, load_model
from ursina.prefabs.first_person_controller import FirstPersonController


def create_player():
    player = FirstPersonController()
    player.cursor.visible = False
    player.hp = 100
    player.max_hp = 100
    player.stamina = 1000
    player.max_stamina = 1000
    player.base_speed = 5.0
    player.sprint_speed_multiplier = 3.0
    player.stamina_regen_rate = 25.0
    player.stamina_sprint_cost = 35.0
    player.is_sprinting = False
    player.money = 1000
    try:
        model_asset = load_model('model/player/source/roblox_noob_r6.fbx')
        if model_asset is None:
            raise Exception('player model returned None')
        player_model = Entity(model=model_asset, parent=player, position=(0, -1, 0), scale=(1, 2, 1))
    except Exception as e:
        print(f'Failed to load player model: {e}')
        player_model = Entity(model='cube', color=color.azure, scale=(1, 2, 1), parent=player, position=(0, -1, 0))
    return player, player_model
