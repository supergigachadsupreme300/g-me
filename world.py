from ursina import Entity, Sky, DirectionalLight, color, Vec3
import config
from player import create_player
import random

GROUND_SIZE = 150
GROUND_HALF = GROUND_SIZE / 2

ground = None
player = None
player_model = None
sun = None
bed = None

trees = []
rocks = []


def create_world():
    global ground, player, player_model, sun

    ground = Entity(
        model='plane',
        scale=(GROUND_SIZE, 0.1, GROUND_SIZE),
        collider='box',
        name='ground'
    )
    if config.is_texture(config.GRASS_TEXTURE):
        ground.texture = config.GRASS_TEXTURE
        ground.color = color.white
        ground.texture_scale = (GROUND_SIZE / 2, GROUND_SIZE / 2)
    else:
        ground.color = config.GRASS_TEXTURE

    player, player_model = create_player()

    Sky()
    sun = DirectionalLight()
    sun.color = color.rgb(255/255, 250/255, 235/255)
    sun.look_at(Vec3(1, -1, -1))
    spawn_trees()
    spawn_rocks()
    build_house()


def spawn_trees(num_trees=10):
    for i in range(num_trees):
        while True:
            x = random.randint(-int(GROUND_HALF) + 5, int(GROUND_HALF) - 5)
            z = random.randint(-int(GROUND_HALF) + 5, int(GROUND_HALF) - 5)
            if abs(x) > 8 or abs(z) > 8:
                break
        trunk = Entity(model='cube', color=color.brown, scale=(1, 4, 1), position=(x, 2, z), collider='box')
        leaves = Entity(model='sphere', color=color.green, scale=3, position=(x, 5, z))
        bar = Entity(model='cube', color=color.red, scale=(2, 0.2, 0.1), position=(x, 4.5, z))
        trees.append({"trunk": trunk, "leaves": leaves, "hp": 10, "bar": bar})


def spawn_rocks(num_rocks=8):
    for i in range(num_rocks):
        while True:
            x = random.randint(-int(GROUND_HALF) + 5, int(GROUND_HALF) - 5)
            z = random.randint(-int(GROUND_HALF) + 5, int(GROUND_HALF) - 5)
            if abs(x) > 8 or abs(z) > 8:
                break
        rock = Entity(model='cube', color=color.gray, scale=(2, 2, 2), position=(x, 1, z), collider='box')
        bar = Entity(model='cube', color=color.red, scale=(2, 0.2, 0.1), position=(x, 2.5, z))
        rocks.append({"rock": rock, "hp": 15, "bar": bar})


def build_house():
    # Simple 3 walls house
    if config.is_texture(config.WOOD_TEXTURE):  # It's a texture
        Entity(model='cube', texture=config.WOOD_TEXTURE, scale=(10, 5, 0.5), position=(0, 2.5, -5), texture_scale=(1, 1))
        Entity(model='cube', texture=config.WOOD_TEXTURE, scale=(10, 5, 0.5), position=(0, 2.5, 5), texture_scale=(1, 1))
        Entity(model='cube', texture=config.WOOD_TEXTURE, scale=(0.5, 5, 10), position=(-5, 2.5, 0), texture_scale=(1, 1))
        Entity(model='cube', texture=config.WOOD_TEXTURE, scale=(10, 0.5, 10), position=(0, 0, 0), texture_scale=(1, 1))
        Entity(model='cube', texture=config.WOOD_TEXTURE, scale=(11, 1, 11), position=(0, 5.5, 0), texture_scale=(1, 1))
    else:  # It's a color
        Entity(model='cube', color=config.WOOD_TEXTURE, scale=(10, 5, 0.5), position=(0, 2.5, -5))
        Entity(model='cube', color=config.WOOD_TEXTURE, scale=(10, 5, 0.5), position=(0, 2.5, 5))
        Entity(model='cube', color=config.WOOD_TEXTURE, scale=(0.5, 5, 10), position=(-5, 2.5, 0))
        Entity(model='cube', color=config.WOOD_TEXTURE, scale=(10, 0.5, 10), position=(0, 0, 0))
        Entity(model='cube', color=config.WOOD_TEXTURE, scale=(11, 1, 11), position=(0, 5.5, 0))

    # Add a simple bed inside the house
    global bed
    bed = Entity(model='cube', color=color.azure, scale=(2.8, 0.25, 1.8), position=(1.2, 0.4, -1.8), collider='box')
    bed.is_bed = True
    Entity(model='cube', color=color.white, scale=(0.8, 0.15, 1.0), position=(1.8, 0.225, -1.8), parent=bed)
