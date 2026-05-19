from ursina import *
import math
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
    spawn_trees()
    spawn_rocks()
    build_house()
    build_shop()
    spawn_buffalo()
    spawn_vendor_cart()


def spawn_trees(num_trees=10):
    for _ in range(num_trees):
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
    # Shop center at (25, 0, 0) — 20 units in front of the house entrance
    sx, sz = 25, 0
    sw, sh, sd = 10, 4, 10   # width (X), height, depth (Z)
    hw, hd = sw / 2, sd / 2
    cy = sh / 2               # wall center Y

    def detail(scale, pos, col):
        return Entity(model='cube', color=col, scale=scale, position=pos)

    # Color palette (lighter/greener to contrast with the house)
    plaster_c  = color.rgb(242/255, 228/255, 198/255)
    roof_c     = color.rgb(55/255, 108/255, 50/255)
    ridge_c    = color.rgb(30/255, 65/255, 28/255)
    eave_c     = color.rgb(145/255, 88/255, 40/255)
    stone_c    = color.rgb(112/255, 102/255, 92/255)
    frame_c    = color.rgb(42/255, 24/255, 8/255)
    win_c      = color.rgb(140/255, 200/255, 220/255)
    floor_c    = color.rgb(158/255, 128/255, 88/255)
    counter_c  = color.rgb(110/255, 65/255, 25/255)
    countertop_c = color.rgb(135/255, 90/255, 38/255)
    shelf_c    = color.rgb(120/255, 75/255, 30/255)
    sign_c     = color.rgb(188/255, 138/255, 62/255)
    awning_c   = color.rgb(188/255, 68/255, 40/255)

    # ── Walls + floor ───────────────────────────────────────────────────
    detail((0.5, sh, sd),   (sx+hw, cy, sz), plaster_c)        # back  (x=+5)
    detail((sw+0.5, sh, 0.5), (sx, cy, sz-hd), plaster_c)      # left  (z=-5)
    detail((sw+0.5, sh, 0.5), (sx, cy, sz+hd), plaster_c)      # right (z=+5)
    detail((sw, 0.5, sd),   (sx, 0, sz), floor_c)               # floor

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

    # Gable end fill (left z=-5 and right z=+5 faces)
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

    # ── Entrance (-X face, facing house) ─────────────────────────────────
    ent_x = sx - hw  # = 20
    # Corner posts
    detail((0.4, sh+0.2, 0.4), (ent_x, cy, sz-hd+0.25), frame_c)
    detail((0.4, sh+0.2, 0.4), (ent_x, cy, sz+hd-0.25), frame_c)
    # Header beam
    detail((0.4, 0.4, sd-0.1), (ent_x, sh+0.2, sz), frame_c)
    # Awning
    detail((1.8, 0.22, sd*0.75), (ent_x-0.9, sh-0.55, sz), awning_c)
    # Awning support posts
    for az in (-hd*0.55, hd*0.55):
        detail((0.14, sh-0.55, 0.14), (ent_x-1.8, (sh-0.55)/2, sz+az), frame_c)

    # ── Sign board (faces player approaching from house) ─────────────────
    detail((0.18, 1.4, 4.8), (ent_x-0.12, sh+rise*0.38, sz), sign_c)
    detail((0.12, 1.65, 5.1), (ent_x-0.14, sh+rise*0.38, sz), frame_c)
    # Decorative text lines on sign
    for dz in (-1.0, 0.0, 1.0):
        detail((0.22, 0.18, 2.6), (ent_x-0.18, sh+rise*0.38+0.22, sz+dz), frame_c)
        detail((0.22, 0.18, 2.6), (ent_x-0.18, sh+rise*0.38-0.22, sz+dz), frame_c)

    # ── Windows on side walls ─────────────────────────────────────────────
    for wx in (-sw/4, sw/4):
        # Left wall (z = sz-hd, facing outward = -Z)
        detail((1.3, 1.3, 0.14), (sx+wx, cy+0.2, sz-hd-0.03), win_c)
        detail((0.1, 1.3, 0.16), (sx+wx, cy+0.2, sz-hd-0.03), frame_c)
        detail((1.3, 0.1, 0.16), (sx+wx, cy+0.2, sz-hd-0.03), frame_c)
        # Right wall (z = sz+hd, facing outward = +Z)
        detail((1.3, 1.3, 0.14), (sx+wx, cy+0.2, sz+hd+0.03), win_c)
        detail((0.1, 1.3, 0.16), (sx+wx, cy+0.2, sz+hd+0.03), frame_c)
        detail((1.3, 0.1, 0.16), (sx+wx, cy+0.2, sz+hd+0.03), frame_c)
    # Back wall window
    detail((0.14, 1.3, 1.3), (sx+hw+0.03, cy+0.2, sz), win_c)
    detail((0.16, 0.1, 1.3), (sx+hw+0.03, cy+0.2, sz), frame_c)
    detail((0.16, 1.3, 0.1), (sx+hw+0.03, cy+0.2, sz), frame_c)

    # ── Counter (buffalo stands behind this) ──────────────────────────────
    counter_x = sx + hw/2   # = 27.5, halfway between center and back wall
    detail((0.9, 1.2, sd-1.0), (counter_x, 0.6, sz), counter_c)
    detail((1.15, 0.15, sd-0.8), (counter_x, 1.27, sz), countertop_c)

    # ── Shelves on back wall ──────────────────────────────────────────────
    item_colors = [
        color.rgb(165/255, 80/255, 40/255),
        color.rgb(90/255, 135/255, 60/255),
        color.rgb(185/255, 155/255, 50/255),
        color.rgb(125/255, 80/255, 165/255),
        color.rgb(50/255, 130/255, 150/255),
    ]
    for shelf_y in (1.0, 1.9, 2.8):
        detail((0.5, 0.12, sd-1.4), (sx+hw-0.3, shelf_y, sz), shelf_c)
    for si, shelf_y in enumerate((1.12, 2.02, 2.92)):
        for j, dz in enumerate((-3.5, -2.2, -0.9, 0.4, 1.7, 3.0)):
            if abs(dz) < hd - 0.8:
                detail((0.3, 0.38, 0.3), (sx+hw-0.25, shelf_y, sz+dz),
                       item_colors[(si + j) % len(item_colors)])


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
        position=(29, 0, 0),
        scale=1.5,
        collider='box',
        double_sided=True,
        unlit=True,
    )
    if texture is not None:
        buffalo.texture = texture
    buffalo.is_buffalo = True


def spawn_vendor_cart():
    vendor_root = Entity(position=(-GROUND_HALF + 8, 0.5, -GROUND_HALF + 8))
    # cart body
    Entity(parent=vendor_root, model='cube', color=color.rgb(200, 120, 60), scale=(4, 1.4, 2), position=(0, 0.9, 0), collider='box')
    Entity(parent=vendor_root, model='cube', color=color.rgb(180, 80, 40), scale=(4.2, 0.4, 2.2), position=(0, 1.6, 0))
    Entity(parent=vendor_root, model='cube', color=color.gray, scale=(0.2, 0.8, 0.2), position=(1.9, 1.1, -0.8))
    Entity(parent=vendor_root, model='cube', color=color.white, scale=(2, 0.2, 1), position=(0, 2.1, 0.9))

    # wheels
    wheel_positions = [(-1.4, 0.35, -0.8), (1.4, 0.35, -0.8), (-1.4, 0.35, 0.8), (1.4, 0.35, 0.8)]
    for pos in wheel_positions:
        Entity(parent=vendor_root, model='cylinder', color=color.black, scale=(0.3, 0.3, 0.3), position=pos, rotation=(90, 0, 0))

    # vendor character
    vendor = Entity(parent=vendor_root, position=(0, 0, 1.8))
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
