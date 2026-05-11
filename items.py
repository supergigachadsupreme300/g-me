from ursina import Entity, color, Vec3
from config import DIRT_TEXTURE, WOOD_TEXTURE


def spawn_ground_item(item_type, position):
    root = Entity(position=position, collider='box')
    root.item_type = item_type

    if item_type == "axe":
        Entity(model='cube', color=color.brown, scale=(0.2, 0.8, 0.2), parent=root, position=(0, 0, 0))
        Entity(model='cube', color=color.gray, scale=(0.2, 0.3, 0.75), parent=root, position=(0, 0.5, 0.25))
    elif item_type == "pickaxe":
        Entity(model='cube', color=color.brown, scale=(0.2, 0.8, 0.2), parent=root, position=(0, 0, 0))
        Entity(model='cube', color=color.gray, scale=(0.2, 0.2, 0.8), parent=root, position=(0, 0.5, 0))
        Entity(model='cube', color=color.gray, scale=(0.25, 0.125, 0.25), parent=root, position=(0, 0.4, 0.35))
        Entity(model='cube', color=color.gray, scale=(0.25, 0.125, 0.25), parent=root, position=(0, 0.4, -0.35))
    elif item_type == "hoe":
        Entity(model='cube', color=color.brown, scale=(0.18, 0.8, 0.18), parent=root, position=(0, 0, 0))
        Entity(model='cube', color=color.gray, scale=(0.5, 0.15, 0.3), parent=root, position=(0, 0.45, 0))
    elif item_type == "hammer":
        Entity(model='cube', color=color.gray, scale=(0.2, 0.8, 0.2), parent=root, position=(0, 0, 0))
        Entity(model='cube', color=color.black, scale=(0.3, 0.1, 0.4), parent=root, position=(0, 0.5, 0))
    elif item_type == "wood":
        Entity(model='cube', color=WOOD_TEXTURE, scale=(0.6, 0.2, 0.2), parent=root, position=(0, 0.3, 0))
    elif item_type == "stone":
        Entity(model='cube', color=color.gray, scale=(0.6, 0.6, 0.6), parent=root, position=(0, 0.5, 0))
    elif item_type == "seed":
        Entity(model='cube', color=color.green, scale=(0.3, 0.3, 0.1), parent=root, position=(0, 0.2, 0))
    elif item_type == "field":
        # Use texture if loaded, else color
        if hasattr(DIRT_TEXTURE, 'width'):  # It's a texture
            Entity(model='cube', texture=DIRT_TEXTURE, scale=(1, 0.2, 1), parent=root, position=(0, 0.1, 0), texture_scale=(1, 1))
        else:  # It's a color
            Entity(model='cube', color=DIRT_TEXTURE, scale=(1, 0.2, 1), parent=root, position=(0, 0.1, 0))
    else:
        Entity(model='cube', color=color.white, scale=(0.3, 0.3, 0.3), parent=root, position=(0, 0.3, 0))

    return root


def find_ground_item_root(entity):
    e = entity
    while e is not None:
        if hasattr(e, "item_type"):
            return e
        e = e.parent
    return None
