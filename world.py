from ursina import *
import math
from ursina import time as ursina_time
import config
from player import create_player, create_player_display
import cutscene_manager as cutscene
import random
import sound_manager

GROUND_SIZE = 150
GROUND_HALF = GROUND_SIZE / 2

# Road bounds (set by build_road)
ROAD_CX = None
ROAD_HW = None
ROAD_Z_START = None
ROAD_Z_END = None

def is_on_road(pos):
    """Return True if world position `pos` lies on the road surface."""
    try:
        if ROAD_CX is None or ROAD_HW is None or ROAD_Z_START is None or ROAD_Z_END is None:
            return False
        return (abs(pos.x - ROAD_CX) <= (ROAD_HW + 0.5)) and (ROAD_Z_START <= pos.z <= ROAD_Z_END)
    except Exception:
        return False

ground = None
player = None
player_model = None
sun = None
sky = None
bed = None
buffalo = None
vendor_root = None
vendor_entity = None
vendor_spawn_button = None
vendors = []

shop_root = None

wife_door_pivot = None
wife_door_open  = False
wife_entity     = None
wife_married    = False

wife_root = None

trees = []
rocks = []

def create_world():
    global ground, player, player_model, sun, sky

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

    sky = Sky()
    sun = DirectionalLight()
    sun.color = color.rgb(255/255, 250/255, 235/255)
    sun.look_at(Vec3(1, -1, -1))
    # build road first so spawn logic can avoid road area
    build_road()
    spawn_trees()
    spawn_rocks()
    build_house()
    create_vendor_spawn_button()
    build_shop()
    build_wife_house()
    spawn_buffalo()


def spawn_trees(num_trees=200):
    TREE_PATH = 'model/tree/source/minecraft_tree.glb'
    SCALE     = 5
    Y_OFFSET  = -0.429 * SCALE  # GLB model bottom offset to ground the tree

    for _ in range(num_trees):
        while True:
            x = random.randint(-int(GROUND_HALF) + 5, int(GROUND_HALF) - 5)
            z = random.randint(-int(GROUND_HALF) + 5, int(GROUND_HALF) - 5)
            near_house      = abs(x) <= 9 and abs(z) <= 9
            near_shop       = abs(x) <= 9 and 51 <= z <= 69
            near_road       = 10 <= x <= 18
            near_wife_house = 20 <= x <= 42 and abs(z) <= 10
            if not near_house and not near_shop and not near_road and not near_wife_house:
                break
        trunk = Entity(
            model=TREE_PATH,
            position=(x, Y_OFFSET, z),
            scale=SCALE,
            collider='box',
            double_sided=True,
            color=color.white,
            unlit=True,
            rotation_y=random.randint(0, 359),
        )
        bar = Entity(model='cube', color=color.red, scale=(2, 0.2, 0.1),
                     position=(x, 6, z))
        trees.append({"trunk": trunk, "hp": 10, "bar": bar})


def remove_tree(tree):
    try:
        sound_manager.play('tree')
    except Exception:
        pass
    destroy(tree["trunk"])
    destroy(tree["bar"])
    if tree in trees:
        trees.remove(tree)


def remove_rock(rock):
    try:
        sound_manager.play('pickaxe')
    except Exception:
        pass
    destroy(rock["rock"])
    destroy(rock["bar"])
    if rock in rocks:
        rocks.remove(rock)


def spawn_rocks(num_rocks=100):
    for _ in range(num_rocks):
        while True:
            x = random.randint(-int(GROUND_HALF) + 5, int(GROUND_HALF) - 5)
            z = random.randint(-int(GROUND_HALF) + 5, int(GROUND_HALF) - 5)
            # avoid player house area and road
            near_house      = abs(x) <= 9 and abs(z) <= 9
            near_shop       = abs(x) <= 9 and 51 <= z <= 69
            near_road       = 10 <= x <= 18
            near_wife_house = 20 <= x <= 42 and abs(z) <= 10
            if not near_house and not near_shop and not near_road and not near_wife_house:
                break
        rock = Entity(model='cube', color=color.gray, scale=(2, 2, 2), position=(x, 1, z), collider='box')
        try:
            rock.is_rock = True
        except Exception:
            pass
        bar = Entity(model='cube', color=color.red, scale=(2, 0.2, 0.1), position=(x, 2.5, z))
        rocks.append({"rock": rock, "hp": 15, "bar": bar})


def build_house():
    is_tex = config.is_texture(config.WOOD_TEXTURE)

    def wood(scale, pos, tex_s=(1, 1)):
        if is_tex:
            return Entity(model='cube', texture=config.WOOD_TEXTURE,
                          scale=scale, position=pos, texture_scale=tex_s)
        return Entity(model='cube', color=config.WOOD_TEXTURE, scale=scale, position=pos)

    def detail(scale, pos, col):
        return Entity(model='cube', color=col, scale=scale, position=pos)

    # Color palette
    roof_c    = color.rgb(162/255, 62/255, 38/255)
    ridge_c   = color.rgb(88/255, 28/255, 10/255)
    eave_c    = color.rgb(145/255, 88/255, 40/255)
    stone_c   = color.rgb(112/255, 102/255, 92/255)
    chimney_c = color.rgb(98/255, 85/255, 74/255)
    win_c     = color.rgb(140/255, 200/255, 220/255)
    frame_c   = color.rgb(42/255, 24/255, 8/255)
    shutt_c   = color.rgb(58/255, 96/255, 44/255)
    porch_c   = color.rgb(148/255, 92/255, 42/255)

    # ── Walls + floor ───────────────────────────────────────────────────
    wood((10, 5, 0.5), (0, 2.5, -5), (5, 2.5))   # front (z=-5)
    wood((10, 5, 0.5), (0, 2.5,  5), (5, 2.5))   # back  (z=+5)
    wood((0.5, 5, 10), (-5, 2.5, 0), (5, 2.5))   # left  (x=-5)
    wood((10, 0.5, 10), (0, 0, 0),   (5, 5))     # floor
    # Right wall with doorway opening (3-unit wide gap centered at z=0)
    wood((0.5, 5, 3.5), (5, 2.5, -3.25), (2, 2.5))   # right-wall left wing
    wood((0.5, 5, 3.5), (5, 2.5,  3.25), (2, 2.5))   # right-wall right wing
    wood((0.5, 1.0, 3.0), (5, 4.5, 0),   (1.5, 0.5)) # transom above doorway

    # ── Gabled roof ─────────────────────────────────────────────────────
    rise      = 3.0
    half_w    = 5.0
    panel_len = math.sqrt(half_w**2 + rise**2)          # ≈ 5.83
    tilt      = math.degrees(math.atan2(rise, half_w))  # ≈ 31°
    overhang  = 1.6

    Entity(model='cube', color=roof_c,
           scale=(panel_len, 0.65, 10 + overhang * 2),
           position=( half_w / 2, 5 + rise / 2, 0),
           rotation=(0, 0, tilt))
    Entity(model='cube', color=roof_c,
           scale=(panel_len, 0.65, 10 + overhang * 2),
           position=(-half_w / 2, 5 + rise / 2, 0),
           rotation=(0, 0, -tilt))
    # Ridge beam
    detail((0.68, 0.38, 10 + overhang * 2 + 0.2), (0, 5 + rise + 0.1, 0), ridge_c)
    # Eave boards along both side edges
    detail((0.55, 0.32, 10 + overhang * 2 + 0.2), ( half_w, 5.05, 0), eave_c)
    detail((0.55, 0.32, 10 + overhang * 2 + 0.2), (-half_w, 5.05, 0), eave_c)

    # ── Gable end triangular fill (stacked decreasing-width slabs) ───────
    for gz in (-5, 5):
        gz_face = gz + (1 if gz > 0 else -1) * 0.04
        for i in range(6):
            t  = (i + 0.5) / 6
            sw = 10 * (1.0 - t) + 0.2
            sy = 5 + (i + 0.5) * rise / 6
            sh = rise / 6 + 0.15
            wood((sw, sh, 0.55), (0, sy, gz_face), (1, 1))

    # ── Stone foundation ─────────────────────────────────────────────────
    detail((11.5, 0.5, 11.5), (0, -0.27, 0), stone_c)
    detail((10.8, 0.22, 10.8), (0, -0.52, 0), stone_c)

    # ── Chimney ──────────────────────────────────────────────────────────
    ch_x, ch_z  = 2.8, 2.0
    ch_bot = 5 - 0.8
    ch_top = 5 + rise + 1.2
    ch_h   = ch_top - ch_bot
    detail((1.3, ch_h, 1.3), (ch_x, (ch_bot + ch_top) / 2, ch_z), chimney_c)
    detail((1.65, 0.44, 1.65), (ch_x, ch_top + 0.22, ch_z),
           color.rgb(66/255, 54/255, 46/255))

    # ── Front wall windows (z=-5 face) ───────────────────────────────────
    for wx in (-3.0, 3.0):
        detail((1.4, 1.4, 0.14), (wx, 2.8, -5.03), win_c)
        detail((0.1, 1.4, 0.16), (wx, 2.8, -5.03), frame_c)
        detail((1.4, 0.1, 0.16), (wx, 2.8, -5.03), frame_c)
        detail((0.22, 1.4, 0.12), (wx - 0.88, 2.8, -5.03), shutt_c)
        detail((0.22, 1.4, 0.12), (wx + 0.88, 2.8, -5.03), shutt_c)

    # ── Back wall window (z=+5 face) ─────────────────────────────────────
    detail((1.4, 1.4, 0.14), (0, 2.8, 5.03), win_c)
    detail((0.1, 1.4, 0.16), (0, 2.8, 5.03), frame_c)
    detail((1.4, 0.1, 0.16), (0, 2.8, 5.03), frame_c)

    # ── Left wall window (x=-5 face) ─────────────────────────────────────
    detail((0.14, 1.4, 1.4), (-5.03, 2.8, 0), win_c)
    detail((0.16, 0.1, 1.4), (-5.03, 2.8, 0), frame_c)
    detail((0.16, 1.4, 0.1), (-5.03, 2.8, 0), frame_c)

    # ── Right side entrance: door frame + porch ───────────────────────────
    # Door frame posts and lintel
    detail((0.32, 4.2, 0.32), (5.03, 2.1, -1.55), frame_c)
    detail((0.32, 4.2, 0.32), (5.03, 2.1,  1.55), frame_c)
    detail((0.32, 0.35, 3.42), (5.03, 4.35, 0), frame_c)
    # Porch overhang
    detail((1.2, 0.3, 4.2), (5.62, 4.05, 0), porch_c)
    # Porch columns
    detail((0.24, 4.05, 0.24), (6.12, 2.0, -1.8), frame_c)
    detail((0.24, 4.05, 0.24), (6.12, 2.0,  1.8), frame_c)

    # ── Bed ──────────────────────────────────────────────────────────────
    global bed
    bed = Entity(model='cube', color=color.rgb(155/255, 55/255, 55/255),
                 scale=(2.8, 0.5, 1.8), position=(1.2, 0.5, -1.8), collider='box')
    bed.is_bed = True
    Entity(model='cube', color=color.white, scale=(0.2, 0.5, 0.4), position=(-0.4, 0.7, 0), parent=bed)
    # Headboard
    Entity(model='cube', color=color.rgb(88/255, 50/255, 18/255), scale=(0.1, 2.2, 1), position=(-0.55, 0.5, 0), parent=bed)

    # Block player mannequin — face the entrance (door on +X wall)
    create_player_display(world_position=(-2.0, 1, 1.5), rotation_y=90)


def build_shop():
    global shop_root
    # create a root entity for the whole shop so all parts can be parented
    shop_root = Entity(name='shop_root')
    # Shop center at (0, 0, 28) — north of house, entrance faces +X (toward road)
    sx, sz = 0, 60
    sw, sh, sd = 10, 4, 10
    hw, hd = sw / 2, sd / 2
    cy = sh / 2

    def detail(scale, pos, col):
        return Entity(parent=shop_root, model='cube', color=col, scale=scale, position=pos)

    plaster_c    = color.rgb(242/255, 228/255, 198/255)
    roof_c       = color.rgb(55/255, 108/255, 50/255)
    ridge_c      = color.rgb(30/255, 65/255, 28/255)
    eave_c       = color.rgb(145/255, 88/255, 40/255)
    stone_c      = color.rgb(112/255, 102/255, 92/255)
    frame_c      = color.rgb(42/255, 24/255, 8/255)
    win_c        = color.rgb(140/255, 200/255, 220/255)
    floor_c      = color.rgb(158/255, 128/255, 88/255)
    counter_c    = color.rgb(110/255, 65/255, 25/255)
    countertop_c = color.rgb(135/255, 90/255, 38/255)
    shelf_c      = color.rgb(120/255, 75/255, 30/255)
    sign_c       = color.rgb(188/255, 138/255, 62/255)
    awning_c     = color.rgb(188/255, 68/255, 40/255)

    # ── Walls + floor ───────────────────────────────────────────────────
    detail((0.5, sh, sd),     (sx-hw, cy, sz), plaster_c)        # back  (x=-5)
    detail((sw+0.5, sh, 0.5), (sx, cy, sz-hd), plaster_c)        # left  (z=23)
    detail((sw+0.5, sh, 0.5), (sx, cy, sz+hd), plaster_c)        # right (z=33)
    detail((sw, 0.5, sd),     (sx, 0, sz), floor_c)               # floor

    # ── Gabled roof ─────────────────────────────────────────────────────
    rise      = 2.2
    panel_len = math.sqrt(hw**2 + rise**2)
    tilt      = math.degrees(math.atan2(rise, hw))
    overhang  = 1.3

    Entity(parent=shop_root, model='cube', color=roof_c,
            scale=(panel_len, 0.55, sd + overhang * 2),
            position=(sx+hw/2, sh+rise/2, sz),
            rotation=(0, 0, tilt))
    Entity(parent=shop_root, model='cube', color=roof_c,
            scale=(panel_len, 0.55, sd + overhang * 2),
            position=(sx-hw/2, sh+rise/2, sz),
            rotation=(0, 0, -tilt))
    detail((0.62, 0.32, sd+overhang*2+0.2), (sx, sh+rise+0.08, sz), ridge_c)
    detail((0.5, 0.28, sd+overhang*2+0.2), (sx+hw, sh+0.05, sz), eave_c)
    detail((0.5, 0.28, sd+overhang*2+0.2), (sx-hw, sh+0.05, sz), eave_c)

    # Gable end fill (z=23 and z=33 faces)
    for gz in (sz-hd, sz+hd):
        gz_face = gz + (-0.04 if gz < sz else 0.04)
        for i in range(5):
            t      = (i + 0.5) / 5
            slab_w = sw * (1.0 - t) + 0.15
            slab_y = sh + (i + 0.5) * rise / 5
            slab_h = rise / 5 + 0.15
            detail((slab_w, slab_h, 0.5), (sx, slab_y, gz_face), plaster_c)

    # ── Stone foundation ─────────────────────────────────────────────────
    detail((sw+1.2, 0.5, sd+1.2), (sx, -0.27, sz), stone_c)

    # ── Entrance (+X face, facing road) ──────────────────────────────────
    ent_x = sx + hw  # = 5
    # Corner posts
    detail((0.4, sh+0.2, 0.4), (ent_x, cy, sz-hd+0.25), frame_c)
    detail((0.4, sh+0.2, 0.4), (ent_x, cy, sz+hd-0.25), frame_c)
    # Header beam
    detail((0.4, 0.4, sd-0.1), (ent_x, sh+0.2, sz), frame_c)
    # Awning (extends outward in +X direction)
    detail((1.8, 0.22, sd*0.75), (ent_x+0.9, sh-0.55, sz), awning_c)
    # Awning support posts
    for az in (-hd*0.55, hd*0.55):
        detail((0.14, sh-0.55, 0.14), (ent_x+1.8, (sh-0.55)/2, sz+az), frame_c)

    # ── Sign board (faces +X / road side) ───────────────────────────────
    detail((0.18, 1.4, 4.8), (ent_x+0.12, sh+rise*0.38, sz), sign_c)
    detail((0.12, 1.65, 5.1), (ent_x+0.14, sh+rise*0.38, sz), frame_c)
    for dz in (-1.0, 0.0, 1.0):
        detail((0.22, 0.18, 2.6), (ent_x+0.18, sh+rise*0.38+0.22, sz+dz), frame_c)
        detail((0.22, 0.18, 2.6), (ent_x+0.18, sh+rise*0.38-0.22, sz+dz), frame_c)

    # ── Windows on side walls ─────────────────────────────────────────────
    for wx in (-sw/4, sw/4):
        detail((1.3, 1.3, 0.14), (sx+wx, cy+0.2, sz-hd-0.03), win_c)
        detail((0.1, 1.3, 0.16), (sx+wx, cy+0.2, sz-hd-0.03), frame_c)
        detail((1.3, 0.1, 0.16), (sx+wx, cy+0.2, sz-hd-0.03), frame_c)
        detail((1.3, 1.3, 0.14), (sx+wx, cy+0.2, sz+hd+0.03), win_c)
        detail((0.1, 1.3, 0.16), (sx+wx, cy+0.2, sz+hd+0.03), frame_c)
        detail((1.3, 0.1, 0.16), (sx+wx, cy+0.2, sz+hd+0.03), frame_c)
    # Back wall window (-X face)
    detail((0.14, 1.3, 1.3), (sx-hw-0.03, cy+0.2, sz), win_c)
    detail((0.16, 0.1, 1.3), (sx-hw-0.03, cy+0.2, sz), frame_c)
    detail((0.16, 1.3, 0.1), (sx-hw-0.03, cy+0.2, sz), frame_c)

    # ── Counter (buffalo stands behind this, near back wall) ──────────────
    counter_x = sx - hw/2   # = -2.5, near back (-X) wall
    detail((0.9, 1.2, sd-1.0), (counter_x, 0.6, sz), counter_c)
    detail((1.15, 0.15, sd-0.8), (counter_x, 1.27, sz), countertop_c)

    # ── Shelves on back wall (-X face) ────────────────────────────────────
    item_colors = [
        color.rgb(165/255, 80/255, 40/255),
        color.rgb(90/255, 135/255, 60/255),
        color.rgb(185/255, 155/255, 50/255),
        color.rgb(125/255, 80/255, 165/255),
        color.rgb(50/255, 130/255, 150/255),
    ]
    for shelf_y in (1.0, 1.9, 2.8):
        detail((0.5, 0.12, sd-1.4), (sx-hw+0.3, shelf_y, sz), shelf_c)
    for si, shelf_y in enumerate((1.12, 2.02, 2.92)):
        for j, dz in enumerate((-3.5, -2.2, -0.9, 0.4, 1.7, 3.0)):
            if abs(dz) < hd - 0.8:
                detail((0.3, 0.38, 0.3), (sx-hw+0.25, shelf_y, sz+dz),
                       item_colors[(si + j) % len(item_colors)])

    # mark shop_root for easy lookup
    try:
        shop_root.is_shop = True
    except Exception:
        pass


def create_vendor_spawn_button():
    global vendor_spawn_button
    # simplified single-entity spawn button in front of the house
    vendor_spawn_button = Entity(
        model='cube',
        color=color.rgb(80, 180, 255),
        scale=(2, 0.4, 2),
        position=(0, 0.2, -9),
        collider='box'
    )
    vendor_spawn_button.is_vendor_spawn = True


def build_wife_house():
    global wife_door_pivot, wife_door_open, wife_root

    # root entity for the wife house so all parts are grouped
    wife_root = Entity(name='wife_house_root')

    cx, cz   = 33, 0
    hw, hd   = 7, 7
    h1, h2   = 5, 4
    total_h  = h1 + h2      # 9
    ent_x    = cx - hw      # 26  (entrance on -X, faces road)
    door_w   = 2.4
    door_h   = 3.4
    wing_w   = (hd * 2 - door_w) / 2   # 5.8

    # ── textures ──────────────────────────────────────────────────────
    T = 'model/house/texture/'
    def _tex(name):
        try:    return load_texture(T + name)
        except: return None

    t_wall  = _tex('wall_plaster.png')
    t_floor = _tex('wood_floor.png')
    t_roof  = _tex('roof_tiles.png')
    t_stone = _tex('stone_wall.png')
    t_door  = _tex('door.png')
    t_wood  = config.WOOD_TEXTURE  if config.is_texture(config.WOOD_TEXTURE)  else None
    t_grass = _tex('stone_wall.png')

    # color.rgb() in this Ursina version does NOT divide by 255.
    # All integer 0-255 values must be divided manually before passing.
    def _rgb(r, g, b): return color.rgb(r/255, g/255, b/255)

    wall_c  = color.white if t_wall  else _rgb(235, 220, 195)
    floor_c = color.white if t_floor else _rgb(158, 118,  72)
    roof_c  = color.white if t_roof  else _rgb(112,  46,  26)
    stone_c = color.white if t_stone else _rgb(110, 102,  92)
    wood_c  = color.white if t_wood  else _rgb(110,  72,  30)
    grass_c = color.white if t_grass else _rgb( 75, 120,  50)

    ridge_c  = _rgb( 55,  20,   8)
    eave_c   = _rgb( 80,  48,  20)
    frame_c  = _rgb( 60,  32,  10)
    win_c    = _rgb(160, 215, 235)
    shutt_c  = _rgb( 55,  90,  42)
    door_c   = _rgb( 95,  55,  18)
    yard_c   = _rgb( 75, 120,  50)
    rail_c   = _rgb(220, 200, 170)

    def blk(scale, pos, col, coll=False, tex=None, ts=None):
        e = Entity(parent=wife_root, model='cube', color=col, scale=scale, position=pos, unlit=True)
        if tex:
            e.texture = tex
            if ts: e.texture_scale = ts
        if coll: e.collider = 'box'
        return e

    def wall(scale, pos, ts=(3, 4)):
        return blk(scale, pos, wall_c, coll=True, tex=t_wall, ts=ts)

    def fl(scale, pos, ts=(4, 4)):
        return blk(scale, pos, floor_c, coll=True, tex=t_floor, ts=ts)

    def stone(scale, pos, ts=(2, 2), coll=False):
        return blk(scale, pos, stone_c, coll=coll, tex=t_stone, ts=ts)

    # ── foundation ────────────────────────────────────────────────────
    stone((hw*2+2.2, 0.6, hd*2+2.2), (cx, -0.3, cz), ts=(5, 5), coll=True)

    # ── ground-floor walls ────────────────────────────────────────────
    wall((0.5, h1, hd*2),   (cx+hw,  h1/2,  cz),                       ts=(4, 3))
    wall((hw*2, h1, 0.5),   (cx,     h1/2,  cz-hd),                    ts=(5, 3))
    wall((hw*2, h1, 0.5),   (cx,     h1/2,  cz+hd),                    ts=(5, 3))
    wall((0.5, h1, wing_w), (ent_x,  h1/2,  cz - door_w/2 - wing_w/2), ts=(2, 3))
    wall((0.5, h1, wing_w), (ent_x,  h1/2,  cz + door_w/2 + wing_w/2), ts=(2, 3))
    wall((0.5, h1-door_h, door_w), (ent_x, door_h+(h1-door_h)/2, cz),  ts=(1, 1))

    # ── ground floor slab ─────────────────────────────────────────────
    fl((hw*2.1-0.6, 0.25, hd*2-0.6), (cx, 0.25, cz), ts=(6, 6))

    # ── kitchen partition (partial wall, back half, ground floor) ─────
    wall((hw - 2.2, h1*0.75, 0.4), (cx+hw/2+1.1, h1*0.375, cz+2.5), ts=(2, 2))

    # ── inter-floor slab with stair opening on north side ─────────────
    fl((hw*2-0.4, 0.3, hd*2-2.9), (cx, h1+0.15, cz-1.5), ts=(5, 4))

    # ── staircase along north interior (+Z side) ──────────────────────
    n_steps   = 9
    stair_run = (hw*2 - 2.5) / n_steps
    stair_rise = h1 / n_steps
    for i in range(n_steps):
        sx = (cx - hw + 1.2) + (i + 0.5) * stair_run
        sy = stair_rise * i + stair_rise / 2
        stone((stair_run+0.05, stair_rise, 2.6), (sx, sy, cz+hd-1.7), ts=(1, 1), coll=True)

    # ── 2F walls ──────────────────────────────────────────────────────
    wall((0.5, h2, hd*2),   (cx+hw, h1+h2/2, cz),    ts=(4, 3))
    wall((hw*2, h2, 0.5),   (cx,    h1+h2/2, cz-hd), ts=(5, 3))
    wall((hw*2, h2, 0.5),   (cx,    h1+h2/2, cz+hd), ts=(5, 3))
    # front (-X) 2F wall with balcony door gap (width=1.8, centred on z=0)
    bal_door_w = 1.8;  bal_door_h = 2.6
    bf_wing    = (hd*2 - bal_door_w) / 2   # 6.1
    wall((0.5, h2, bf_wing), (ent_x, h1+h2/2, cz - bal_door_w/2 - bf_wing/2), ts=(2, 3))
    wall((0.5, h2, bf_wing), (ent_x, h1+h2/2, cz + bal_door_w/2 + bf_wing/2), ts=(2, 3))
    wall((0.5, h2-bal_door_h, bal_door_w), (ent_x, h1+bal_door_h+(h2-bal_door_h)/2, cz), ts=(1, 1))

    # ── balcony floor + railings ───────────────────────────────────────
    bal_d = 4.0
    stone((bal_door_w+2.2, 0.22, bal_d), (ent_x-bal_d/2, h1+0.11, cz), ts=(2, 1), coll=True)
    for bz in (-(bal_door_w/2+0.7), (bal_door_w/2+0.7)):
        blk((0.16, 1.0, 0.16), (ent_x-bal_d/2, h1+0.62, cz+bz), rail_c, coll=True)
        blk((0.16, 1.0, 0.16), (ent_x-bal_d+0.1, h1+0.62, cz+bz), rail_c, coll=True)
    blk((0.14, 0.12, bal_door_w+1.4), (ent_x-bal_d+0.1, h1+1.1, cz), rail_c)
    blk((bal_d+0.1, 0.12, 0.14), (ent_x-bal_d/2, h1+1.1, cz-(bal_door_w/2+0.7)), rail_c)
    blk((bal_d+0.1, 0.12, 0.14), (ent_x-bal_d/2, h1+1.1, cz+(bal_door_w/2+0.7)), rail_c)

    # ── gabled roof ───────────────────────────────────────────────────
    r_rise  = 3.2
    pan_len = math.sqrt(hw**2 + r_rise**2)
    tilt    = math.degrees(math.atan2(r_rise, hw))
    overhang = 1.6
    pan_z   = hd*2 + overhang*2

    for side, ang in ((+1, tilt), (-1, -tilt)):
        rp = Entity(parent=wife_root, model='cube', color=roof_c,
                    scale=(pan_len, 0.68, pan_z),
                    position=(cx+side*hw/2, total_h+r_rise/2, cz),
                    rotation=(0, 0, ang), unlit=True)
        if t_roof:
            rp.texture       = t_roof
            rp.texture_scale = (3, 8)

    blk((0.75, 0.4,  pan_z+0.2), (cx,     total_h+r_rise+0.08, cz), ridge_c)
    blk((0.60, 0.34, pan_z+0.2), (cx+hw,  total_h+0.04, cz), eave_c)
    blk((0.60, 0.34, pan_z+0.2), (cx-hw,  total_h+0.04, cz), eave_c)

    for gz in (cz-hd, cz+hd):
        gf = gz + (-0.05 if gz < cz else 0.05)
        for i in range(6):
            t  = (i+0.5)/6
            sw = hw*2*(1-t)+0.2
            sy = total_h + (i+0.5)*r_rise/6
            sh = r_rise/6 + 0.15
            wall((sw, sh, 0.5), (cx, sy, gf), ts=(int(sw/2)+1, 1))

    # ── chimney ───────────────────────────────────────────────────────
    chx = cx+hw-2.2;  chz = cz-hd+2.2
    cb  = total_h-1.5;  ct = total_h+r_rise+0.9
    stone((1.5, ct-cb, 1.5), (chx, (cb+ct)/2, chz), ts=(1, 2))
    blk((1.9, 0.5, 1.9), (chx, ct+0.25, chz), _rgb(60, 50, 42))

    # ── windows (south + north, both floors) ──────────────────────────
    for floor_y, ws in ((2.4, 1.5), (h1+2.2, 1.4)):
        for wx in (cx-hw/2, cx+hw/2):
            for gz_s, go in ((cz-hd, -0.05), (cz+hd, 0.05)):
                blk((ws,   ws,   0.15), (wx, floor_y, gz_s+go), win_c)
                blk((0.10, ws,   0.18), (wx, floor_y, gz_s+go), frame_c)
                blk((ws,   0.10, 0.18), (wx, floor_y, gz_s+go), frame_c)
                if floor_y < h1:
                    blk((0.26, ws, 0.13), (wx-0.9, floor_y, gz_s+go), shutt_c)
                    blk((0.26, ws, 0.13), (wx+0.9, floor_y, gz_s+go), shutt_c)
        # +X side window
        blk((0.15, ws,   ws),   (cx+hw+0.05, floor_y, cz), win_c)
        blk((0.18, 0.10, ws),   (cx+hw+0.05, floor_y, cz), frame_c)
        blk((0.18, ws,   0.10), (cx+hw+0.05, floor_y, cz), frame_c)

    # ── door frame (placed on outer face of entrance wall) ────────────
    fx = ent_x - 0.26   # outer face of the 0.5-thick entrance wall
    blk((0.38, door_h, 0.38), (fx, door_h/2, cz-door_w/2), wood_c,
        tex=t_wood, ts=(1, 3))
    blk((0.38, door_h, 0.38), (fx, door_h/2, cz+door_w/2), wood_c,
        tex=t_wood, ts=(1, 3))
    blk((0.38, 0.44, door_w+0.22), (fx, door_h+0.22, cz), wood_c,
        tex=t_wood, ts=(2, 1))

    # ── interactive door (cube + door.png texture) ────────────────────
    hinge_z = cz - door_w/2 + 0.19
    wife_door_pivot = Entity(parent=wife_root, position=(ent_x, 0, hinge_z))
    _dp = Entity(parent=wife_door_pivot, model='cube',
                 color=color.white if t_door else door_c,
                 scale=(0.13, door_h-0.01, door_w-0.4),
                 position=(0, (door_h-0.01)/2, (door_w-0.4)/2),
                 collider='box', unlit=True)
    if t_door:
        _dp.texture       = t_door
        _dp.texture_scale = (1, 1)
    _dp.name = 'wife_house_door'
    # door knob
    blk((0.18, 0.18, 0.18), (fx-0.08, door_h*0.46, hinge_z+(door_w-0.4)*0.82),
        _rgb(210, 172, 50))
    for dy in (door_h*0.26, door_h*0.65):
        blk((0.15, door_h*0.30, 0.08),
            (fx-0.06, dy, hinge_z+(door_w-0.4)*0.5), _rgb(75, 42, 12))

    # ── front yard ────────────────────────────────────────────────────
    blk((8.0, 0.06, hd*2+4.0), (ent_x-4.0, 0.03, cz), grass_c,
        tex=t_grass if t_grass else None, ts=(4, 6))
    stone((0.3, 0.22, hd*2+4.0), (ent_x-8.0, 0.11, cz), ts=(1, 4))
    for dz in (-hd-2.0, hd+2.0):
        stone((8.0, 0.22, 0.3), (ent_x-4.0, 0.11, cz+dz), ts=(3, 1))

    # ── ground-floor furniture ────────────────────────────────────────
    # main sofa (centre of living room)
    blk((3.2, 0.58, 1.2),  (cx-1.5, 0.59, cz+0.4), _rgb(180, 140, 100), coll=True)
    blk((3.2, 0.85, 0.22), (cx-1.5, 0.82, cz+1.0), _rgb(160, 120,  85), coll=True)
    # left-side sofa against -Z wall (wife sits here)
    blk((2.6, 0.55, 1.1),  (cx-1.0, 0.57, cz-hd+0.8),  _rgb(160, 125,  90), coll=True)
    blk((2.6, 0.80, 0.22), (cx-1.0, 0.80, cz-hd+0.18), _rgb(140, 105,  75), coll=True)
    # coffee table
    blk((1.5, 0.08, 0.85), (cx-1.5, 0.68, cz-0.65), _rgb(120, 80, 40))
    for tx, tz in ((-2.2,-0.95),(-0.8,-0.95),(-2.2,-0.35),(-0.8,-0.35)):
        blk((0.10, 0.62, 0.10), (cx+tx, 0.31, cz+tz), _rgb(100, 65, 30))
    # kitchen counter along +X wall
    blk((0.7, 1.0, hd-1.8), (cx+hw-0.4, 0.5, cz+hd/2+0.9),  _rgb( 95,  72,  50), coll=True)
    blk((0.9, 0.08, hd-1.6),(cx+hw-0.4, 1.05, cz+hd/2+0.9), _rgb(220, 210, 195), coll=True)
    blk((0.65, 0.12, 0.65), (cx+hw-0.42, 1.07, cz+hd-1.8),   _rgb(190, 200, 210))
    # dining table
    blk((1.8, 0.08, 1.0), (cx+1.5, 0.78, cz+2.8), _rgb(130, 90, 45))
    for tx, tz in ((-0.7,-0.4),(0.7,-0.4),(-0.7,0.4),(0.7,0.4)):
        blk((0.08, 0.75, 0.08), (cx+1.5+tx, 0.37, cz+2.8+tz), _rgb(110, 75, 35))
    for dz2 in (-0.85, 0.85):
        blk((0.8, 0.36, 0.8), (cx+1.5, 0.36, cz+2.8+dz2), _rgb(160, 120, 80), coll=True)

    # ── 2F bedroom furniture ──────────────────────────────────────────
    bed_x = cx+hw-2.2;  bed_z = cz-hd+2.0
    blk((3.2, 0.50, 2.0), (bed_x, h1+0.50, bed_z), _rgb(120,  85,  50), coll=True)
    blk((3.0, 0.22, 1.8), (bed_x, h1+0.82, bed_z), _rgb(240, 230, 215))
    blk((0.7, 0.18, 0.55),(bed_x-0.95, h1+1.04, bed_z-0.56), _rgb(255, 245, 235))
    blk((0.7, 0.18, 0.55),(bed_x+0.95, h1+1.04, bed_z-0.56), _rgb(255, 245, 235))
    blk((3.3, 1.10, 0.22),(bed_x, h1+1.05, bed_z-0.92), _rgb(95, 62, 28))
    # wardrobe
    blk((1.8, 2.2, 0.6),  (cx-hw+1.0, h1+1.1,  cz-hd+1.2),  _rgb(110,  78, 42), coll=True)
    blk((1.85,2.25,0.08), (cx-hw+1.0, h1+1.12, cz-hd+0.88), _rgb(140, 100, 58))
    # bedside lamp
    blk((0.7,  0.65, 0.6),  (cx+hw-0.6, h1+0.62, cz-hd+2.0), _rgb(125,  88,  48), coll=True)
    blk((0.14, 0.48, 0.14), (cx+hw-0.6, h1+1.1,  cz-hd+2.0), _rgb(185, 155, 100))
    blk((0.44, 0.34, 0.44), (cx+hw-0.6, h1+1.45, cz-hd+2.0), _rgb(255, 240, 200))

    # ── wife character — seated on left-side sofa ─────────────────────
    # Left sofa seat top ≈ y 0.57+0.275 = 0.845; place wife just above it.
    _wx = cx - 1.0
    _wy = 0.85           # on sofa seat
    _wz = cz - hd + 0.7  # near -Z wall
    _ws = 0.75           # adjust if still too large/small

    try:
        # Use Teto model instead of the old wife model
        _wife_model_obj = load_model(cutscene.TETO_MODEL_PATH)

        wife = Entity(
            parent=wife_root,
            model=_wife_model_obj,
            position=(_wx, _wy, _wz),
            rotation_y=0,
            scale=cutscene.TETO_SCALE,
            double_sided=True,
            unlit=True,
        )

        wife.color = color.white

        # Apply Teto texture if available using the helper from cutscene
        try:
            cutscene._apply_texture_to_model(wife, _wife_model_obj, cutscene.TETO_TEXTURE_PATH)
        except Exception:
            pass

        global wife_entity
        wife_entity = wife
        print('[wife-as-teto] loaded OK')

    except Exception as e:
        print(f'[Wife->Teto] load error: {e}')
        blk((0.4, 1.4, 0.25), (_wx, _wy + 0.7, _wz), _rgb(220, 180, 140))


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

    # unlit=True: bypass Ursina's lighting so GLB/PBR textures render correctly
    buffalo = Entity(
        model=model,
        position=(-3.8, 0, 60),
        rotation_y=90,
        scale=1.5,
        collider='box',
        double_sided=True,
        unlit=True,
    )
    if texture is not None:
        buffalo.texture = texture
    buffalo.is_buffalo = True
    # parent buffalo to shop_root if it exists so shop+buffalo form a single group
    try:
        global shop_root
        if shop_root is not None:
            buffalo.parent = shop_root
    except Exception:
        pass


def build_road():
    # Road runs north-south (along Z) at x=14, covering z=-50 to z=70
    road_cx  = 14.0
    road_hw  = 3.8
    road_len = 150.0
    road_zc  = 17.0

    curb_c   = color.rgb(118, 115, 108)
    white_c  = color.white
    yellow_c = color.rgb(235, 205, 45)

    road_tex = None
    try:
        road_tex = load_texture('texture/Road006_1K_Color.jpeg')
    except Exception as e:
        print(f"Road texture: {e}")

    # ── Asphalt surface ───────────────────────────────────────────────
    road_surf = Entity(
        model='cube',
        scale=(road_hw * 2, 0.06, road_len),
        position=(road_cx, 0.03, road_zc),
        color=color.rgb(60, 62, 70),
        unlit=True,
    )
    if road_tex:
        road_surf.texture       = road_tex
        road_surf.color         = color.white
        road_surf.texture_scale = (1, road_len / 6)

    # ── Raised kerbs ──────────────────────────────────────────────────
    for side in (-1, 1):
        kerb = Entity(
            model='cube',
            scale=(0.55, 0.22, road_len),
            position=(road_cx + side * (road_hw + 0.27), 0.11, road_zc),
            color=curb_c,
            unlit=True,
        )
        if road_tex:
            kerb.texture       = road_tex
            kerb.texture_scale = (0.3, road_len / 2)

    # ── White edge lines ──────────────────────────────────────────────
    for side in (-1, 1):
        Entity(model='cube', color=white_c, unlit=True,
               scale=(0.18, 0.03, road_len),
               position=(road_cx + side * (road_hw - 0.22), 0.03, road_zc))

    # ── Yellow dashed centre line ─────────────────────────────────────
    dash_len  = 2.8
    dash_gap  = 2.2
    dash_step = dash_len + dash_gap
    z_start   = road_zc - road_len / 2 + dash_len / 2
    num_dashes = int(road_len / dash_step)
    for i in range(num_dashes):
        Entity(model='cube', color=yellow_c, unlit=True,
               scale=(0.18, 0.03, dash_len),
               position=(road_cx, 0.03, z_start + i * dash_step))

    # Publish road bounds for placement checks
    global ROAD_CX, ROAD_HW, ROAD_Z_START, ROAD_Z_END
    ROAD_CX = road_cx
    ROAD_HW = road_hw
    ROAD_Z_START = road_zc - road_len / 2
    ROAD_Z_END = road_zc + road_len / 2


def spawn_vendor_cart():
    global vendor_root, vendor_entity, vendors
    # define entry and exit positions
    arrival_pos = Vec3(15, 0.5, -8)
    offscreen_in = Vec3(15, 0.5, -30)
    offscreen_out = Vec3(15, 0.5, 30)
    # mark existing vendors to exit (they will run away)
    for v in list(vendors):
        try:
            v._vendor_exiting = True
            v._vendor_exit_target = offscreen_out + Vec3(random.uniform(-2,2), 0, random.uniform(-2,2))
            v._vendor_moving = False
        except Exception:
            pass
    # choose a random cart color so clicks are visibly distinguishable
    cart_color = color.rgb(random.randint(80, 255), random.randint(50, 220), random.randint(50, 220))
    # create new vendor root offscreen and register it
    new_root = Entity(position=offscreen_in)
    # rotate cart 90 degrees so it faces sideways by default
    try:
        new_root.rotation_y = -90
    except Exception:
        pass
    # cart body
    Entity(parent=new_root, model='cube', color=cart_color, scale=(4, 1.4, 2), position=(0, 0.9, 0), collider='box')
    Entity(parent=new_root, model='cube', color=color.rgb(max(0, cart_color.r-20), max(0, cart_color.g-40), max(0, cart_color.b-20)), scale=(4.2, 0.4, 2.2), position=(0, 1.6, 0))
    Entity(parent=new_root, model='cube', color=color.gray, scale=(0.2, 0.5, 1.8), position=(2, 1.1, 0))
    Entity(parent=new_root, model='cube', color=color.white, scale=(0.5, 0.7, 2), position=(2, 0.5, 0))

    # wheels (keep references for rotation animation)
    wheel_positions = [(-1.4, -0.35, -1), (1.4, -0.35, -1), (-1.4, -0.35, 1), (1.4, -0.35, 1)]
    wheels = []
    for pos in wheel_positions:
        w = Entity(parent=new_root, model='cube', color=color.black,
                   scale=(0.8, 0.8, 0.2), position=pos)
        # subtle rim color to match cart
        Entity(parent=w, model='cube', color=cart_color, scale=(0.4, 0.4, 0.06), position=(0, 0, 0.08))
        wheels.append(w)

    # vendor character: try to use mrkrab model if available
    try:
        vm = load_model('model/mrkrab/source/db_balloon_mr_krabs.obj')
    except Exception as e:
        print(f"Failed to load mrkrab model: {e}")
        vm = None
    try:
        vt = load_texture('model/mrkrab/textures/krabs.png')
    except Exception:
        vt = None

    if vm:
        # reduce model size to half
        vendor = Entity(parent=new_root, model=vm, position=(0, 0, 1.8), scale=0.2, collider='box', double_sided=True)
        if vt is not None and hasattr(vt, 'width'):
            vendor.texture = vt
    else:
        # fallback to simple blocky vendor
        vendor = Entity(parent=new_root, position=(0, 0, 1.8), collider='box')
        Entity(parent=vendor, model='cube', color=color.azure, scale=(0.5, 1.0, 0.4), position=(0, 1.0, 0))
        head = Entity(parent=vendor, model='cube', color=color.white, scale=(0.45, 0.45, 0.45), position=(0, 1.9, 0))
        try:
            face_texture = load_texture('texture/seed.png')
            if hasattr(face_texture, 'width'):
                Entity(parent=head, model='quad', texture=face_texture, scale=(0.35, 0.35), position=(0, 0, 0.26))
        except Exception:
            pass
        Entity(parent=vendor, model='cube', color=color.azure, scale=(0.15, 0.6, 0.15), position=(-0.35, 1.2, 0))
        Entity(parent=vendor, model='cube', color=color.azure, scale=(0.15, 0.6, 0.15), position=(0.35, 1.2, 0))
        Entity(parent=vendor, model='cube', color=color.blue, scale=(0.18, 0.7, 0.18), position=(-0.15, 0.35, 0))
        Entity(parent=vendor, model='cube', color=color.blue, scale=(0.18, 0.7, 0.18), position=(0.15, 0.35, 0))

    new_root.is_vendor = True
    vendor.is_vendor = True
    # vendor movement/animation properties (per-vendor)
    new_root._vendor_wheels = wheels
    new_root._vendor_arrival = arrival_pos
    new_root._vendor_speed = 6.0
    new_root._vendor_moving = True
    new_root._vendor_exiting = False
    new_root._vendor_exit_target = None
    new_root._vendor_model = vendor
    new_root._vendor_model_base_y = getattr(vendor, 'y', 0)
    # register vendor and update global refs to newest
    vendors.append(new_root)
    vendor_root = new_root
    vendor_entity = vendor
    try:
        sound_manager.play('mexican_truck')
    except Exception:
        pass


def input(key):
    global wife_door_open
    from ursina import mouse

    if key == 'e' and wife_door_pivot is not None and player is not None:
        dp   = Vec3(wife_door_pivot.x, 0, wife_door_pivot.z)
        pp   = Vec3(player.x,          0, player.z)
        if (pp - dp).length() < 5:
            wife_door_open = not wife_door_open
            wife_door_pivot.animate('rotation_y', -90 if wife_door_open else 0, duration=0.35)

    if key == 'left mouse down':
        hovered = getattr(mouse, 'hovered_entity', None)
        # walk up parents to find an ancestor marked as vendor or spawn button
        h = hovered
        while h is not None and not (getattr(h, 'is_vendor', False) or getattr(h, 'is_vendor_spawn', False)):
            h = getattr(h, 'parent', None)
        if h is not None:
            if getattr(h, 'is_vendor_spawn', False):
                # always spawn a new vendor and keep the button active
                spawn_vendor_cart()
            elif getattr(h, 'is_vendor', False):
                try:
                    import shop
                    shop.open_shop()
                except Exception as e:
                    print('Failed to open shop:', e)


def is_vendor_spawn_entity(entity):
    """Return the ancestor entity marked as vendor spawn button, or None."""
    current = entity
    while current is not None:
        if getattr(current, 'is_vendor_spawn', False):
            return current
        current = getattr(current, 'parent', None)
    return None


def update():
    # handle vendor cart movement, wheel rotation, and simple bobbing animation for all active vendors
    global vendor_root, vendor_entity, vendors
    if not vendors:
        return

    to_remove = []
    for v in list(vendors):
        # handle exiting vendors first
        if getattr(v, '_vendor_exiting', False):
            target = getattr(v, '_vendor_exit_target', None)
            speed = getattr(v, '_vendor_speed', 6.0)
            if target is not None:
                dir_vec = (target - v.position)
                dist = dir_vec.length()
                if dist < 0.5:
                    try:
                        destroy(v)
                    except Exception:
                        pass
                    to_remove.append(v)
                    # if the removed vendor was the global vendor_root, clear refs
                    if v is vendor_root:
                        vendor_root = None
                        vendor_entity = None
                    continue
                else:
                    step = dir_vec.normalized() * speed * ursina_time.dt
                    v.position = v.position + step
        # handle incoming movement
        elif getattr(v, '_vendor_moving', False):
            target = getattr(v, '_vendor_arrival', None)
            speed = getattr(v, '_vendor_speed', 6.0)
            if target is not None:
                dir_vec = (target - v.position)
                dist = dir_vec.length()
                if dist < 0.1:
                    v.position = target
                    v._vendor_moving = False
                else:
                    step = dir_vec.normalized() * speed * ursina_time.dt
                    v.position = v.position + step
        # rotate wheels if present
        wheels = getattr(v, '_vendor_wheels', None)
        if wheels:
            for w in wheels:
                w.rotation_z += 360 * ursina_time.dt
        # bob vendor model if present
        m = getattr(v, '_vendor_model', None)
        if m is not None:
            base_y = getattr(v, '_vendor_model_base_y', 0)
            bob = math.sin(ursina_time.time() * 2.0) * 0.05
            try:
                m.y = base_y + bob
            except Exception:
                pass

    # cleanup removed vendors from list
    for r in to_remove:
        if r in vendors:
            vendors.remove(r)
