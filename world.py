from ursina import *
import math
from ursina import time as ursina_time
import config
from player import create_player
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

new_house_door_pivot = None
new_house_door_open  = False

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
    spawn_trees()
    spawn_rocks()
    build_house()
    create_vendor_spawn_button()
    build_shop()
    build_road()
    build_two_storey_house()
    spawn_buffalo()


def spawn_trees(num_trees=60):
    TREE_PATH = 'model/tree/source/minecraft_tree.glb'
    SCALE     = 5
    Y_OFFSET  = -0.429 * SCALE  # GLB model bottom offset to ground the tree

    for _ in range(num_trees):
        while True:
            x = random.randint(-int(GROUND_HALF) + 5, int(GROUND_HALF) - 5)
            z = random.randint(-int(GROUND_HALF) + 5, int(GROUND_HALF) - 5)
            near_house = abs(x) <= 9 and abs(z) <= 9
            near_shop     = abs(x) <= 9 and 51 <= z <= 69
            near_road     = 10 <= x <= 18
            near_new_house = 21 <= x <= 42 and abs(z) <= 10
            if not near_house and not near_shop and not near_road and not near_new_house:
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


def spawn_rocks(num_rocks=8):
    for _ in range(num_rocks):
        while True:
            x = random.randint(-int(GROUND_HALF) + 5, int(GROUND_HALF) - 5)
            z = random.randint(-int(GROUND_HALF) + 5, int(GROUND_HALF) - 5)
            if abs(x) > 8 or abs(z) > 8:
                break
        rock = Entity(model='cube', color=color.gray, scale=(2, 2, 2), position=(x, 1, z), collider='box')
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
                 scale=(2.8, 0.5, 1.8), position=(1.2, 0.72, -1.8), collider='box')
    bed.is_bed = True
    Entity(model='cube', color=color.white, scale=(0.2, 0.5, 0.4),
           position=(-0.4, 0.7, 0), parent=bed)
    # Headboard
    detail((2.85, 1.2, 0.22), (1.2, 1.1, -2.65), color.rgb(88/255, 50/255, 18/255))
    # Legs
    for lx, lz in [(-1.3, -2.65), (1.3, -2.65), (-1.3, -0.95), (1.3, -0.95)]:
        detail((0.16, 0.45, 0.16), (lx, 0.22, lz), color.rgb(78/255, 44/255, 14/255))


def build_shop():
    # Shop center at (0, 0, 28) — north of house, entrance faces +X (toward road)
    sx, sz = 0, 60
    sw, sh, sd = 10, 4, 10
    hw, hd = sw / 2, sd / 2
    cy = sh / 2

    def detail(scale, pos, col):
        return Entity(model='cube', color=col, scale=scale, position=pos)

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

    Entity(model='cube', color=roof_c,
           scale=(panel_len, 0.55, sd + overhang * 2),
           position=(sx+hw/2, sh+rise/2, sz),
           rotation=(0, 0, tilt))
    Entity(model='cube', color=roof_c,
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


def build_two_storey_house():
    global new_house_door_pivot, new_house_door_open

    cx, cz  = 33, 0
    hw, hd  = 7, 7
    h1, h2  = 6, 5
    total_h = h1 + h2   # 11
    ent_x   = cx - hw   # 26
    door_w  = 3.0
    door_h  = 4.0
    wing_w  = (hd * 2 - door_w) / 2   # 5.5

    # ── Load textures ─────────────────────────────────────────────────
    T = 'model/house/texture/'
    def _tex(name):
        try:    return load_texture(T + name)
        except: return None

    t_wall  = _tex('wall_plaster.png')
    t_floor = _tex('wood_floor.png')
    t_roof  = _tex('roof_tiles.png')
    t_stone = _tex('stone_wall.png')

    # ── Color fallbacks (used as tint when texture loads, or standalone) ─
    wall_c  = color.white if t_wall  else color.rgb(235, 220, 195)
    floor_c = color.white if t_floor else color.rgb(158, 118,  72)
    roof_c  = color.white if t_roof  else color.rgb(112,  46,  26)
    stone_c = color.white if t_stone else color.rgb(110, 102,  92)

    ridge_c = color.rgb(68,  24, 10)
    eave_c  = color.rgb(86,  50, 22)
    frame_c = color.rgb(50,  28,  8)
    win_c   = color.rgb(145, 205, 228)
    shutt_c = color.rgb(50,  86, 38)
    door_c  = color.rgb(82,  48, 14)
    yard_c  = color.rgb(82,  128, 55)

    def blk(scale, pos, col, coll=False, tex=None, ts=None):
        e = Entity(model='cube', color=col, scale=scale, position=pos)
        if tex:
            e.texture = tex
            if ts: e.texture_scale = ts
        if coll: e.collider = 'box'
        return e

    def wall(scale, pos, ts=(3, 4)):
        return blk(scale, pos, wall_c, coll=True, tex=t_wall, ts=ts)

    def floor_slab(scale, pos, ts=(4, 4)):
        return blk(scale, pos, floor_c, coll=True, tex=t_floor, ts=ts)

    def stone(scale, pos, ts=(2, 2), coll=False):
        return blk(scale, pos, stone_c, coll=coll, tex=t_stone, ts=ts)

    # ── Foundation ───────────────────────────────────────────────────
    stone((hw*2+2.2, 0.75, hd*2+2.2), (cx, -0.38, cz), ts=(5, 5), coll=True)

    # ── Outer walls ───────────────────────────────────────────────────
    wall((0.5,     total_h, hd*2),   (cx+hw, total_h/2, cz),                      ts=(4, 4))
    wall((hw*2,    total_h, 0.5),    (cx,    total_h/2, cz-hd),                   ts=(5, 4))
    wall((hw*2,    total_h, 0.5),    (cx,    total_h/2, cz+hd),                   ts=(5, 4))
    wall((0.5,     total_h, wing_w), (ent_x, total_h/2, cz - door_w/2 - wing_w/2), ts=(2, 4))
    wall((0.5,     total_h, wing_w), (ent_x, total_h/2, cz + door_w/2 + wing_w/2), ts=(2, 4))
    wall((0.5, total_h-door_h, door_w), (ent_x, door_h+(total_h-door_h)/2, cz),   ts=(1, 2))

    # ── Floors ───────────────────────────────────────────────────────
    floor_slab((hw*2-0.5, 0.3, hd*2-0.5), (cx, 0.15,    cz), ts=(5, 5))
    floor_slab((hw*2-0.5, 0.3, hd*2-0.5), (cx, h1+0.15, cz), ts=(5, 5))

    # ── Interior dividing wall ────────────────────────────────────────
    wall((0.4, h2*0.6, hd*2-1.0), (cx, h1+h2*0.3, cz), ts=(4, 2))

    # ── Interior staircase ────────────────────────────────────────────
    steps = 10
    run   = (hw*2 - 2.0) / steps
    rise  = h1 / steps
    for i in range(steps):
        sx = (cx + hw - 1.2) - (i + 0.5) * run
        sy = rise * i + rise / 2
        stone((run+0.06, rise, 3.2), (sx, sy, cz+hd-2.2), ts=(1, 1), coll=True)

    # ── Gabled roof ──────────────────────────────────────────────────
    r_rise   = 3.5
    pan_len  = math.sqrt(hw**2 + r_rise**2)
    tilt     = math.degrees(math.atan2(r_rise, hw))
    overhang = 1.8
    pan_z    = hd*2 + overhang*2

    for side, ang in ((+1, tilt), (-1, -tilt)):
        rp = Entity(model='cube', color=roof_c,
                    scale=(pan_len, 0.72, pan_z),
                    position=(cx + side*hw/2, total_h+r_rise/2, cz),
                    rotation=(0, 0, ang))
        if t_roof:
            rp.texture       = t_roof
            rp.texture_scale = (3, 10)

    blk((0.78, 0.42, pan_z+0.2), (cx, total_h+r_rise+0.1, cz), ridge_c)
    blk((0.62, 0.36, pan_z+0.2), (cx+hw, total_h+0.05, cz), eave_c)
    blk((0.62, 0.36, pan_z+0.2), (cx-hw, total_h+0.05, cz), eave_c)

    # Gable end fill (wall texture)
    for gz in (cz-hd, cz+hd):
        gf = gz + (-0.05 if gz < cz else 0.05)
        for i in range(7):
            t  = (i+0.5)/7
            sw = hw*2*(1-t)+0.2
            sy = total_h + (i+0.5)*r_rise/7
            sh = r_rise/7 + 0.18
            wall((sw, sh, 0.55), (cx, sy, gf), ts=(int(sw/2)+1, 1))

    # ── Chimney ──────────────────────────────────────────────────────
    chx = cx + hw - 2.5
    chz = cz - hd + 2.5
    cb  = total_h - 1.8
    ct  = total_h + r_rise + 1.1
    stone((1.6, ct-cb, 1.6), (chx, (cb+ct)/2, chz), ts=(1, 2))
    blk((2.0, 0.55, 2.0), (chx, ct+0.27, chz), color.rgb(68, 58, 50))

    # ── Windows ──────────────────────────────────────────────────────
    for gy in (3.0, h1+3.0):
        ws = 1.55 if gy < h1 else 1.4
        for gz_s, go in ((cz-hd, -0.05), (cz+hd, 0.05)):
            for wx in (cx-hw/2, cx+hw/2):
                blk((ws, ws, 0.16),     (wx, gy, gz_s+go), win_c)
                blk((0.12, ws, 0.2),    (wx, gy, gz_s+go), frame_c)
                blk((ws, 0.12, 0.2),    (wx, gy, gz_s+go), frame_c)
                if gy < h1:
                    blk((0.28, ws, 0.14), (wx-0.95, gy, gz_s+go), shutt_c)
                    blk((0.28, ws, 0.14), (wx+0.95, gy, gz_s+go), shutt_c)
        blk((0.16, ws, ws),    (cx+hw+0.05, gy, cz), win_c)
        blk((0.2, 0.12, ws),   (cx+hw+0.05, gy, cz), frame_c)
        blk((0.2, ws, 0.12),   (cx+hw+0.05, gy, cz), frame_c)
    for wz in (cz-door_w/2-wing_w/2, cz+door_w/2+wing_w/2):
        blk((0.16, 1.4, 1.4), (ent_x-0.05, h1+3.0, wz), win_c)
        blk((0.2, 0.12, 1.4), (ent_x-0.05, h1+3.0, wz), frame_c)
        blk((0.2, 1.4, 0.12), (ent_x-0.05, h1+3.0, wz), frame_c)

    # ── Door frame ───────────────────────────────────────────────────
    blk((0.38, door_h, 0.38),      (ent_x, door_h/2, cz-door_w/2+0.2),  frame_c)
    blk((0.38, door_h, 0.38),      (ent_x, door_h/2, cz+door_w/2-0.2),  frame_c)
    blk((0.38, 0.45, door_w+0.22), (ent_x, door_h+0.22, cz),             frame_c)

    # ── Interactive door ──────────────────────────────────────────────
    hinge_z = cz - door_w/2 + 0.2
    new_house_door_pivot = Entity(position=(ent_x, 0, hinge_z))
    dp = Entity(parent=new_house_door_pivot, model='cube', color=door_c,
                scale=(0.14, door_h-0.3, door_w-0.4),
                position=(0, (door_h-0.3)/2, (door_w-0.4)/2),
                collider='box')
    dp.name = 'new_house_door'
    blk((0.2, 0.2, 0.2),
        (ent_x-0.1, door_h*0.45, hinge_z+(door_w-0.4)*0.8), color.rgb(200, 162, 48))
    for dy in (door_h*0.28, door_h*0.68):
        blk((0.16, door_h*0.36, 0.1),
            (ent_x-0.09, dy, hinge_z+(door_w-0.4)*0.5), color.rgb(65, 36, 10))

    # ── Entrance steps ────────────────────────────────────────────────
    step_h = 0.28
    step_d = 1.0
    for i in range(3):
        h   = (i+1) * step_h
        xc  = ent_x - (2.5-i) * step_d
        zw  = door_w + 2.4 - i*0.5
        stone((step_d, h, zw), (xc, h/2, cz), ts=(1, 1), coll=True)

    # ── Front yard ───────────────────────────────────────────────────
    blk((8.0, 0.06, hd*2+4), (ent_x-4.0, 0.03, cz), yard_c)
    for dz in (-hd-2, hd+2):
        stone((8.0, 0.22, 0.35), (ent_x-4.0, 0.11, cz+dz), ts=(3, 1))
    stone((0.35, 0.22, hd*2+4), (ent_x-8.0, 0.11, cz), ts=(1, 4))

    # ── Upstairs bed ─────────────────────────────────────────────────
    blk((3.0, 0.55, 1.8),  (cx+hw-2.0, h1+0.57, cz-hd+1.6), color.rgb(138, 48, 48))
    blk((3.1, 1.25, 0.26), (cx+hw-2.0, h1+1.3,  cz-hd+0.58), color.rgb(72, 40, 14))



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
    Entity(parent=new_root, model='cube', color=color.gray, scale=(0.2, 0.8, 0.2), position=(1.9, 1.1, -0.8))
    Entity(parent=new_root, model='cube', color=color.white, scale=(2, 0.2, 1), position=(0, 2.1, 0.9))

    # wheels (keep references for rotation animation)
    wheel_positions = [(-1.4, -0.35, -1), (1.4, -0.35, -1), (-1.4, -0.35, 1), (1.4, -0.35, 1)]
    wheels = []
    for pos in wheel_positions:
        w = Entity(parent=new_root, model='cube', color=color.black,
                   scale=(0.5, 0.5, 0.2), position=pos, rotation=(0, 0, 0))
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
        vendor = Entity(parent=new_root, model=vm, position=(0, 0, 1.8), scale=0.4, collider='box', double_sided=True)
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
    global new_house_door_open
    from ursina import mouse

    # 'E' — interact with the two-storey house door
    if key == 'e' and new_house_door_pivot is not None and player is not None:
        door_pos   = Vec3(new_house_door_pivot.x, 0, new_house_door_pivot.z)
        player_pos = Vec3(player.x, 0, player.z)
        if (player_pos - door_pos).length() < 5:
            new_house_door_open = not new_house_door_open
            target = -90 if new_house_door_open else 0
            new_house_door_pivot.animate('rotation_y', target, duration=0.4)

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
