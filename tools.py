from ursina import Entity, color, invoke, curve, load_texture

arm = None
axe = None
pickaxe = None
hoe = None
hammer = None
sword = None
gun = None
fertilizer = None


def setup_tools():
    global arm, axe, pickaxe, hoe, hammer, sword, gun, fertilizer
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
    fertilizer = Entity(position=(0.7, -0.6, 1.5), rotation=(0, 0, 0), parent=None, enabled=False)
    _make_fertilizer_on_parent(fertilizer)


def _make_axe_on_parent(parent_entity):
    Entity(model='cube', color=color.brown, scale=(0.2, 0.8, 0.2), parent=parent_entity, position=(0, 0, 0))
    Entity(model='cube', color=color.gray, scale=(0.2, 0.3, 0.75), parent=parent_entity, position=(0, 0.5, 0.25))


def _make_pick_on_parent(parent_entity):
    Entity(model='cube', color=color.brown, scale=(0.2, 0.8, 0.2), parent=parent_entity, position=(0, 0, 0))
    Entity(model='cube', color=color.gray, scale=(0.2, 0.2, 0.8), parent=parent_entity, position=(0, 0.5, 0))
    Entity(model='cube', color=color.gray, scale=(0.25, 0.125, 0.25), parent=parent_entity, position=(0, 0.4, 0.35))
    Entity(model='cube', color=color.gray, scale=(0.25, 0.125, 0.25), parent=parent_entity, position=(0, 0.4, -0.35))


def _make_hoe_on_parent(parent_entity):
    Entity(model='cube', color=color.brown, scale=(0.18, 0.8, 0.18), parent=parent_entity, position=(0, 0, 0))
    Entity(model='cube', color=color.gray, scale=(0.5, 0.15, 0.3), parent=parent_entity, position=(0, 0.45, 0))


def _make_hammer_on_parent(parent_entity):
    Entity(model='cube', color=color.gray, scale=(0.2, 0.8, 0.2), parent=parent_entity, position=(0, 0, 0))
    Entity(model='cube', color=color.black, scale=(0.3, 0.1, 0.4), parent=parent_entity, position=(0, 0.5, 0))


def _make_sword_on_parent(parent_entity):
    Entity(model='cube', color=color.gray, scale=(0.1, 0.4, 0.1), parent=parent_entity, position=(0, 0, 0))
    Entity(model='cube', color=color.white, scale=(0.05, 1, 0.3), parent=parent_entity, position=(0, 0.7, 0))
    Entity(model='cube', color=color.gold, scale=(0.2, 0.05, 0.2), parent=parent_entity, position=(0, 0.25, 0))


def _make_gun_on_parent(parent_entity):
    Entity(model='cube', color=color.black, scale=(0.15, 0.5, 0.15), parent=parent_entity, position=(0, 0, 0))
    Entity(model='cube', color=color.gray, scale=(0.4, 0.15, 0.15), parent=parent_entity, position=(0, 0.2, 0.4))
    Entity(model='cube', color=color.gray, scale=(0.2, 0.15, 0.15), parent=parent_entity, position=(0, 0.15, 0.65))


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


def set_active_item(item_type):
    arm.enabled = (item_type is None)
    axe.enabled = (item_type == "axe")
    pickaxe.enabled = (item_type == "pickaxe")
    hoe.enabled = (item_type == "hoe")
    hammer.enabled = (item_type == "hammer")
    sword.enabled = (item_type == "sword")
    gun.enabled = (item_type == "gun")
    fertilizer.enabled = (item_type == "fertilizer")


def swing_item(item_entity):
    if item_entity is None:
        return
    item_entity.animate_rotation((120, 0, 0), duration=0.15, curve=curve.linear)
    from ursina import invoke
    invoke(lambda: item_entity.animate_rotation((0, 0, 0), duration=0.15), delay=0.15)
