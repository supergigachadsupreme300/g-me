from ursina import Entity, color, invoke, curve, load_texture

arm = None
axe = None
pickaxe = None
hoe = None
hammer = None
sword = None
gun = None
scythe = None
fertilizer = None
seed = None
peashooter_seed = None
mi_hao_hao = None
wheat = None
damaged_wheat = None
corn_seed = None
potato_seed = None
corn = None
potato = None
damaged_corn = None
damaged_potato = None


def setup_tools():
    global arm, axe, pickaxe, hoe, hammer, sword, gun, scythe, fertilizer, seed, peashooter_seed, mi_hao_hao, wheat, damaged_wheat
    global corn_seed, potato_seed, corn, potato, damaged_corn, damaged_potato
    arm = Entity(model='cube', color=color.brown, scale=(0.3, 1, 0.3),
                 position=(0.7, -0.6, 1.5), rotation=(20, -30, 0), parent=None, enabled=True)
    axe = Entity(position=(0.7, -0.6, 1.5), rotation=(0, 0, 0), parent=None, enabled=False)
    _make_axe_on_parent(axe)
    pickaxe = Entity(position=(0.7, -0.6, 1.5), rotation=(0, 0, 0), parent=None, enabled=False)
    _make_pick_on_parent(pickaxe)
    hoe = Entity(position=(0.7, -0.6, 1.5), rotation=(0, 0, 0), parent=None, enabled=False)
    _make_hoe_on_parent(hoe)
    hammer = Entity(position=(0.7, -0.6, 1.5), rotation=(0, 0, 0), parent=None, enabled=False)
    _make_hammer_on_parent(hammer)
    sword = Entity(position=(0.7, -0.6, 1.5), rotation=(0, 0, 0), parent=None, enabled=False)
    _make_sword_on_parent(sword)
    gun = Entity(position=(0.7, -0.6, 1.5), rotation=(0, 0, 0), parent=None, enabled=False)
    _make_gun_on_parent(gun)
    scythe = Entity(position=(0.7, -0.6, 1.5), rotation=(0, 0, 0), parent=None, enabled=False)
    _make_scythe_on_parent(scythe)
    fertilizer = Entity(position=(0.7, -0.6, 1.5), rotation=(0, 0, 0), parent=None, enabled=False)
    _make_fertilizer_on_parent(fertilizer)
    seed = Entity(position=(0.7, -0.6, 1.5), rotation=(0, 0, 0), parent=None, enabled=False)
    _make_seed_on_parent(seed)
    peashooter_seed = Entity(position=(0.7, -0.6, 1.5), rotation=(0, 0, 0), parent=None, enabled=False)
    _make_peashooter_seed_on_parent(peashooter_seed)
    mi_hao_hao = Entity(position=(0.7, -0.6, 1.5), rotation=(0, 0, 0), parent=None, enabled=False)
    _make_mi_hao_hao_on_parent(mi_hao_hao)
    wheat = Entity(position=(0.7, -0.6, 1.5), rotation=(0, 0, 0), parent=None, enabled=False)
    _make_wheat_on_parent(wheat)
    damaged_wheat = Entity(position=(0.7, -0.6, 1.5), rotation=(0, 0, 0), parent=None, enabled=False)
    _make_damaged_wheat_on_parent(damaged_wheat)
    corn_seed = Entity(position=(0.7, -0.6, 1.5), rotation=(0, 0, 0), parent=None, enabled=False)
    _make_seed_with_texture_on_parent(corn_seed, color.rgb(255 / 255, 220 / 255, 60 / 255))
    corn = Entity(position=(0.7, -0.6, 1.5), rotation=(0, 0, 0), parent=None, enabled=False)
    _make_corn_on_parent(corn)
    potato = Entity(position=(0.7, -0.6, 1.5), rotation=(0, 0, 0), parent=None, enabled=False)
    _make_potato_on_parent(potato)
    damaged_corn = Entity(position=(0.7, -0.6, 1.5), rotation=(0, 0, 0), parent=None, enabled=False)
    _make_crop_on_parent(damaged_corn, color.brown)
    damaged_potato = Entity(position=(0.7, -0.6, 1.5), rotation=(0, 0, 0), parent=None, enabled=False)
    _make_crop_on_parent(damaged_potato, color.brown)


def _make_axe_on_parent(parent_entity):
    Entity(model='cube', color=color.brown, scale=(0.15, 0.8, 0.15), parent=parent_entity, position=(0, 0, 0))
    Entity(model='cube', color=color.gray, scale=(0.2, 0.3, 0.7), parent=parent_entity, position=(0, 0.5, 0.25))
    Entity(model='cube', color=color.gray, scale=(0.2, 0.5, 0.2), parent=parent_entity, position=(0, 0.5, 0.5))


def _make_pick_on_parent(parent_entity):
    Entity(model='cube', color=color.brown, scale=(0.15, 0.8, 0.15), parent=parent_entity, position=(0, 0, 0))
    Entity(model='cube', color=color.gray, scale=(0.2, 0.2, 0.8), parent=parent_entity, position=(0, 0.5, 0))
    Entity(model='cube', color=color.gray, scale=(0.25, 0.125, 0.25), parent=parent_entity, position=(0, 0.4, 0.35))
    Entity(model='cube', color=color.gray, scale=(0.25, 0.125, 0.25), parent=parent_entity, position=(0, 0.4, -0.35))


def _make_hoe_on_parent(parent_entity):
    Entity(model='cube', color=color.brown, scale=(0.18, 0.8, 0.18), parent=parent_entity, position=(0, 0, 0))
    Entity(model='cube', color=color.gray, scale=(0.3, 0.15, 0.7), parent=parent_entity, position=(0, 0.4, 0.3))


def _make_hammer_on_parent(parent_entity):
    Entity(model='cube', color=color.gray, scale=(0.15, 0.8, 0.15), parent=parent_entity, position=(0, 0, 0))
    Entity(model='cube', color=color.black, scale=(0.3, 0.2, 0.4), parent=parent_entity, position=(0, 0.5, 0))


def _make_sword_on_parent(parent_entity):
    Entity(model='cube', color=color.gray, scale=(0.1, 0.4, 0.1), parent=parent_entity, position=(0, 0, 0))
    Entity(model='cube', color=color.gold, scale=(0.2, 0.05, 0.2), parent=parent_entity, position=(0, 0.25, 0))
    Entity(model='cube', color=color.white, scale=(0.05, 1, 0.3), parent=parent_entity, position=(0, 0.7, 0))
    Entity(model='cube', color=color.white, scale=(0.05, 0.3, 0.3), parent=parent_entity, position=(0, 1.15, 0), rotation=(45,0,0))


def _make_gun_on_parent(parent_entity):
    Entity(model='cube', color=color.black, scale=(0.15, 0.5, 0.15), parent=parent_entity, position=(0, 0, 0), rotation=(45,0,0))
    Entity(model='cube', color=color.gray, scale=(0.2, 0.2, 1), parent=parent_entity, position=(0, 0.2, 0.4))


def _make_fertilizer_on_parent(parent_entity):
    try:
        tex = load_texture('texture/fertilize')
        if hasattr(tex, 'width'):
            Entity(model='cube', texture=tex, scale=(0.3, 0.3, 0.3), parent=parent_entity, position=(0, 0, 0))
        else:
            Entity(model='cube', color=color.green, scale=(0.3, 0.3, 0.3), parent=parent_entity, position=(0, 0, 0))
    except Exception as e:
        print(f"Failed to load fertilizer texture: {e}")
        Entity(model='cube', color=color.green, scale=(0.3, 0.3, 0.3), parent=parent_entity, position=(0, 0, 0))


def _make_seed_on_parent(parent_entity):
    try:
        from ursina import load_texture
        tex = load_texture('texture/seed.png')
        if hasattr(tex, 'width'):
            Entity(model='cube', texture=tex, color=color.rgb(180/255, 120/255, 60/255), scale=(0.25, 0.25, 0.1), parent=parent_entity, position=(0, 0.2, 0), texture_scale=(1, 1))
            return
    except Exception:
        pass
    Entity(model='cube', color=color.rgb(180/255, 120/255, 60/255), scale=(0.25, 0.25, 0.1), parent=parent_entity, position=(0, 0.2, 0))


def _make_peashooter_seed_on_parent(parent_entity):
    try:
        from ursina import load_texture
        tex = load_texture('texture/peashooter_seed.png')
        if hasattr(tex, 'width'):
            Entity(model='cube', texture=tex, color=color.rgb(255/255, 220/255, 80/255), scale=(0.25, 0.25, 0.1), parent=parent_entity, position=(0, 0.2, 0), texture_scale=(1, 1))
            return
    except Exception:
        pass
    Entity(model='cube', color=color.rgb(255/255, 220/255, 80/255), scale=(0.25, 0.25, 0.1), parent=parent_entity, position=(0, 0.2, 0))


def _make_mi_hao_hao_on_parent(parent_entity):
    try:
        from ursina import load_model
        noodle_model = load_model('model/haohao/source/Mitomhaohao.glb')
        if noodle_model:
            parent_entity.model = noodle_model
            parent_entity.scale = (0.4, 0.4, 0.4)
            parent_entity.position = (0, -0.1, 0)
            parent_entity.rotation = (0, 180, 0)
            return
    except Exception:
        pass
    Entity(model='cube', color=color.red, scale=(0.3, 0.1, 0.3), parent=parent_entity, position=(0, 0.1, 0))


def _make_wheat_on_parent(parent_entity):
    # try to use wheat sack model if available, otherwise fallback to a yellow cube
    try:
        from ursina import load_model, load_texture
        sack_model = load_model('model/wheat_sack/source/WheatSack.fbx')
        sack_tex = None
        try:
            sack_tex = load_texture('model/wheat_sack/textures/WheatSack_albedo.jpg')
        except Exception:
            sack_tex = None
        if sack_model:
            # scale to ~1/100 of original hand size
            if sack_tex:
                Entity(model=sack_model, texture=sack_tex, parent=parent_entity, scale=(0.0035, 0.0035, 0.0035), position=(0, -0.1, 0), rotation=(0, 180, 0))
            else:
                Entity(model=sack_model, parent=parent_entity, scale=(0.0035, 0.0035, 0.0035), position=(0, -0.1, 0), rotation=(0, 180, 0))
            return
    except Exception:
        pass
    Entity(model='cube', color=color.yellow, scale=(0.25, 0.25, 0.25), parent=parent_entity, position=(0, 0.15, 0))


def _make_colored_seed_on_parent(parent_entity, seed_color):
    Entity(model='cube', color=seed_color, scale=(0.25, 0.25, 0.1), parent=parent_entity, position=(0, 0.2, 0))


def _make_seed_with_texture_on_parent(parent_entity, seed_color):
    """Try to use the generic seed texture; fall back to colored cube."""
    try:
        from ursina import load_texture
        tex = load_texture('texture/seed.png')
        if hasattr(tex, 'width'):
            Entity(model='cube', texture=tex, color=seed_color, scale=(0.25, 0.25, 0.1), parent=parent_entity, position=(0, 0.2, 0), texture_scale=(1, 1))
            return
    except Exception:
        pass
    Entity(model='cube', color=seed_color, scale=(0.25, 0.25, 0.1), parent=parent_entity, position=(0, 0.2, 0))


def _make_corn_on_parent(parent_entity):
    """Build a corn fruit made of 5 co-located rectangles with evenly spaced rotations.
    No rotation animation; all rectangles share the same origin but have different Y rotations.
    """
    ear_color = color.rgb(255/255, 210/255, 60/255)
    # rectangle dimensions (same for all 5 pieces) - scale up 1.5x per user request
    rect_thickness = 0.05 * 1.5
    rect_height = 0.18 * 1.5
    rect_depth = 0.10 * 1.5
    # place all rectangles at the same coordinate (slightly raised)
    pos = (0, 0.08 * 1.5, 0)
    count = 5
    for i in range(count):
        angle = i * (360.0 / float(count))
        Entity(model='cube', color=ear_color, parent=parent_entity,
               position=pos, scale=(rect_thickness, rect_height, rect_depth), rotation=(0, angle, 0))


def _make_potato_on_parent(parent_entity):
    """Build a simple potato model: a couple of rounded lumps (spheres)"""
    try:
        # prefer spheres for a rounder look
        Entity(model='sphere', color=color.rgb(160/255, 110/255, 60/255), scale=(0.18, 0.12, 0.12), parent=parent_entity, position=(-0.04, 0.02, 0))
        Entity(model='sphere', color=color.rgb(150/255, 100/255, 55/255), scale=(0.14, 0.1, 0.12), parent=parent_entity, position=(0.06, 0.0, 0))
    except Exception:
        # fallback to cubes if sphere model is not available
        Entity(model='cube', color=color.rgb(160/255, 110/255, 60/255), scale=(0.25, 0.18, 0.18), parent=parent_entity, position=(0, 0.05, 0))


def _make_crop_on_parent(parent_entity, crop_color):
    Entity(model='cube', color=crop_color, scale=(0.25, 0.25, 0.25), parent=parent_entity, position=(0, 0.15, 0))


def _make_damaged_wheat_on_parent(parent_entity):
    Entity(model='cube', color=color.brown, scale=(0.25, 0.25, 0.25), parent=parent_entity, position=(0, 0.15, 0))


def _make_scythe_on_parent(parent_entity):
    Entity(model='cube', color=color.brown, scale=(0.1, 0.8, 0.1), parent=parent_entity, position=(0, 0, 0))
    Entity(model='cube', color=color.gray, scale=(0.05, 0.35, 0.05), parent=parent_entity, position=(0.1, 0.5, 0), rotation=(0, 0, 45))
    Entity(model='cube', color=color.gray, scale=(0.05, 0.2, 0.05), parent=parent_entity, position=(0.2, 0.7, 0), rotation=(0, 0, 0))
    Entity(model='cube', color=color.gray, scale=(0.05, 0.35, 0.05), parent=parent_entity, position=(0.1, 0.9, 0), rotation=(0, 0, -45))


def set_active_item(item_type):
    arm.enabled = (item_type is None)
    axe.enabled = (item_type == "axe")
    pickaxe.enabled = (item_type == "pickaxe")
    hoe.enabled = (item_type == "hoe")
    hammer.enabled = (item_type == "hammer")
    sword.enabled = (item_type == "sword")
    gun.enabled = (item_type == "gun")
    scythe.enabled = (item_type == "scythe")
    fertilizer.enabled = (item_type == "fertilizer")
    seed.enabled = (item_type == "seed")
    peashooter_seed.enabled = (item_type == "peashooter seed")
    mi_hao_hao.enabled = (item_type == "mì hảo hảo")
    wheat.enabled = (item_type == "wheat")
    damaged_wheat.enabled = (item_type == "damaged wheat")
    corn_seed.enabled = (item_type == "corn seed")
    # no potato seed item anymore; potato item is used for planting
    corn.enabled = (item_type == "corn")
    potato.enabled = (item_type == "potato")
    damaged_corn.enabled = (item_type == "damaged corn")
    damaged_potato.enabled = (item_type == "damaged potato")


def swing_item(item_entity):
    if item_entity is None:
        return
    item_entity.animate_rotation((120, 0, 0), duration=0.15, curve=curve.linear)
    from ursina import invoke
    invoke(lambda: item_entity.animate_rotation((0, 0, 0), duration=0.15), delay=0.15)
