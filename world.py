from ursina import Entity, Sky, DirectionalLight, color, Vec3, destroy, load_model, load_texture
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
buffalo = None

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
    spawn_trees(22)
    spawn_rocks(14)
    spawn_bushes(12)
    build_house()
    spawn_buffalo()


def _random_pos(min_dist=15):
    while True:
        x = random.randint(-int(GROUND_HALF) + 5, int(GROUND_HALF) - 5)
        z = random.randint(-int(GROUND_HALF) + 5, int(GROUND_HALF) - 5)
        if abs(x) > min_dist or abs(z) > min_dist:
            return x, z


# ── Trees ──────────────────────────────────────────────────────────────────────

def _tex(texture, fallback_color):
    """Return texture= or color= kwargs depending on what loaded."""
    if config.is_texture(texture):
        return {"texture": texture, "color": color.white}
    return {"color": fallback_color}


def _spawn_pine_tree(x, z):
    s = random.uniform(0.9, 1.4)
    trunk = Entity(
        model='cube',
        scale=(0.5*s, 4*s, 0.5*s),
        position=(x, 2*s, z),
        collider='box',
        **_tex(config.BARK_TEXTURE, color.rgb(90/255, 60/255, 28/255)),
    )
    c1 = Entity(model='cone', scale=(3.2*s, 2.6*s, 3.2*s), position=(x, 4.2*s, z),
                **_tex(config.LEAVES_TEXTURE, color.rgb(28/255, 88/255, 28/255)))
    c2 = Entity(model='cone', scale=(2.4*s, 2.2*s, 2.4*s), position=(x, 5.8*s, z),
                **_tex(config.LEAVES_TEXTURE, color.rgb(38/255, 108/255, 38/255)))
    c3 = Entity(model='cone', scale=(1.5*s, 1.8*s, 1.5*s), position=(x, 7.2*s, z),
                **_tex(config.LEAVES_TEXTURE, color.rgb(50/255, 125/255, 50/255)))
    bar = Entity(model='cube', color=color.red, scale=(2, 0.2, 0.1),
                 position=(x, 9.5*s, z))
    trees.append({"trunk": trunk, "leaves": c1, "hp": 10, "bar": bar,
                  "extra": [c2, c3]})


def _spawn_oak_tree(x, z):
    s = random.uniform(0.9, 1.3)
    trunk = Entity(
        model='cube',
        scale=(0.65*s, 4*s, 0.65*s),
        position=(x, 2*s, z),
        collider='box',
        **_tex(config.BARK_TEXTURE, color.rgb(90/255, 58/255, 25/255)),
    )
    l1 = Entity(model='sphere', scale=3.6*s, position=(x, 5.8*s, z),
                **_tex(config.LEAVES_TEXTURE, color.rgb(32/255, 108/255, 32/255)))
    l2 = Entity(model='sphere', scale=2.6*s, position=(x + 1.3*s, 5.2*s, z + 0.6*s),
                **_tex(config.LEAVES_TEXTURE, color.rgb(42/255, 125/255, 42/255)))
    l3 = Entity(model='sphere', scale=2.0*s, position=(x - 1.0*s, 5.5*s, z - 0.8*s),
                **_tex(config.LEAVES_TEXTURE, color.rgb(25/255, 95/255, 25/255)))
    bar = Entity(model='cube', color=color.red, scale=(2, 0.2, 0.1),
                 position=(x, 8.8*s, z))
    trees.append({"trunk": trunk, "leaves": l1, "hp": 10, "bar": bar,
                  "extra": [l2, l3]})


def spawn_trees(num_trees=22):
    for _ in range(num_trees):
        x, z = _random_pos(15)
        if random.random() < 0.5:
            _spawn_pine_tree(x, z)
        else:
            _spawn_oak_tree(x, z)


def remove_tree(tree):
    destroy(tree["trunk"])
    destroy(tree["leaves"])
    destroy(tree["bar"])
    for e in tree.get("extra", []):
        destroy(e)
    trees.remove(tree)


# ── Rocks ──────────────────────────────────────────────────────────────────────

def _spawn_rock_cluster(x, z):
    s = random.uniform(0.8, 1.5)
    main = Entity(
        model='sphere',
        scale=(2.2*s, 1.4*s, 1.8*s),
        position=(x, 0.7*s, z),
        collider='box',
        **_tex(config.ROCK_TEXTURE, color.rgb(118/255, 112/255, 107/255)),
    )
    r2 = Entity(model='sphere', scale=(1.3*s, 1.0*s, 1.2*s),
                position=(x + 1.1*s, 0.5*s, z + 0.5*s),
                **_tex(config.ROCK_TEXTURE, color.rgb(100/255, 96/255, 90/255)))
    r3 = Entity(model='sphere', scale=(0.9*s, 0.7*s, 0.8*s),
                position=(x - 0.7*s, 0.35*s, z - 0.5*s),
                **_tex(config.ROCK_TEXTURE, color.rgb(128/255, 122/255, 118/255)))
    bar = Entity(model='cube', color=color.red, scale=(2, 0.2, 0.1),
                 position=(x, 2.5*s, z))
    rocks.append({"rock": main, "hp": 15, "bar": bar, "extra": [r2, r3]})


def spawn_rocks(num_rocks=14):
    for _ in range(num_rocks):
        x, z = _random_pos(12)
        _spawn_rock_cluster(x, z)


def remove_rock(rock):
    destroy(rock["rock"])
    destroy(rock["bar"])
    for e in rock.get("extra", []):
        destroy(e)
    rocks.remove(rock)


# ── Bushes (decorative) ────────────────────────────────────────────────────────

def spawn_bushes(num_bushes=12):
    for _ in range(num_bushes):
        x, z = _random_pos(10)
        s = random.uniform(0.5, 1.0)
        Entity(model='sphere', color=color.rgb(40/255, 112/255, 40/255),
               scale=(1.6*s, 1.0*s, 1.6*s), position=(x, 0.5*s, z))
        if random.random() < 0.6:
            Entity(model='sphere', color=color.rgb(35/255, 95/255, 35/255),
                   scale=(1.1*s, 0.8*s, 1.1*s),
                   position=(x + 0.7*s, 0.4*s, z + 0.5*s))


# ── House ──────────────────────────────────────────────────────────────────────

def build_house():
    wood = config.WOOD_TEXTURE
    use_tex = config.is_texture(wood)

    def wall(scale, pos, **kw):
        if use_tex:
            return Entity(model='cube', texture=wood, scale=scale, position=pos,
                          texture_scale=(1, 1), **kw)
        return Entity(model='cube', color=wood, scale=scale, position=pos, **kw)

    # Walls (3 sides + open front at x=+5)
    wall((10, 5, 0.5), (0, 2.5, -5))
    wall((10, 5, 0.5), (0, 2.5, 5))
    wall((0.5, 5, 10), (-5, 2.5, 0))
    # Floor
    wall((10, 0.5, 10), (0, 0, 0))
    # Flat roof with overhang
    wall((11.5, 0.6, 11.5), (0, 5.5, 0))
    # Roof ridge / parapet color accent
    Entity(model='cube', color=color.rgb(120/255, 55/255, 25/255),
           scale=(11.8, 0.4, 11.8), position=(0, 5.8, 0))

    # Bed
    global bed
    bed = Entity(model='cube', color=color.rgb(180/255, 50/255, 50/255),
                 scale=(2.8, 0.4, 1.8), position=(1.2, 0.7, -1.8), collider='box')
    bed.is_bed = True
    # Pillow
    Entity(model='cube', color=color.white, scale=(2.4, 0.2, 0.5),
           position=(0, 0.31, -0.65), parent=bed)
    # Blanket
    Entity(model='cube', color=color.rgb(80/255, 80/255, 200/255),
           scale=(2.4, 0.12, 1.0), position=(0, 0.28, 0.15), parent=bed)


def spawn_buffalo():
    global buffalo
    try:
        model = load_model('model/buffalo/source/buffalo 2024final.glb')
    except Exception as e:
        print(f"Failed to load buffalo model: {e}")
        model = 'cube'
    try:
        texture = load_texture('model/buffalo/textures/diffuse6_4.jpg')
    except Exception as e:
        print(f"Failed to load buffalo texture: {e}")
        texture = None

    buffalo_kwargs = {
        'model': model,
        'position': (5, 0, 5),
        'scale': 1.5,
        'collider': 'box',
        'double_sided': True,
    }
    if texture is not None:
        buffalo_kwargs['texture'] = texture

    buffalo = Entity(**buffalo_kwargs)
    buffalo.is_buffalo = True
