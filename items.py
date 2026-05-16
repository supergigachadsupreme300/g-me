from ursina import Entity, color, Vec3, load_texture
import config


def spawn_ground_item(item_type, position):
    root = Entity(position=position, collider='box')
    root.item_type = item_type

    if item_type == "axe":
        Entity(model='cube', color=color.brown, scale=(0.15, 0.8, 0.15), parent=root, position=(0, 0, 0))
        Entity(model='cube', color=color.gray, scale=(0.2, 0.3, 0.7), parent=root, position=(0, 0.5, 0.25))
        Entity(model='cube', color=color.gray, scale=(0.2, 0.5, 0.2), parent=root, position=(0, 0.5, 0.5))
    elif item_type == "pickaxe":
        Entity(model='cube', color=color.brown, scale=(0.15, 0.8, 0.15), parent=root, position=(0, 0, 0))
        Entity(model='cube', color=color.gray, scale=(0.2, 0.2, 0.8), parent=root, position=(0, 0.5, 0))
        Entity(model='cube', color=color.gray, scale=(0.25, 0.125, 0.25), parent=root, position=(0, 0.4, 0.35))
        Entity(model='cube', color=color.gray, scale=(0.25, 0.125, 0.25), parent=root, position=(0, 0.4, -0.35))
    elif item_type == "hoe":
        Entity(model='cube', color=color.brown, scale=(0.18, 0.8, 0.18), parent=root, position=(0, 0, 0))
        Entity(model='cube', color=color.gray, scale=(0.3, 0.15, 0.7), parent=root, position=(0, 0.4, 0.3))
    elif item_type == "hammer":
        Entity(model='cube', color=color.gray, scale=(0.15, 0.8, 0.15), parent=root, position=(0, 0, 0))
        Entity(model='cube', color=color.black, scale=(0.3, 0.2, 0.4), parent=root, position=(0, 0.5, 0))
    elif item_type == "sword":
        Entity(model='cube', color=color.gray, scale=(0.1, 0.4, 0.1), parent=root, position=(0, 0, 0))
        Entity(model='cube', color=color.gold, scale=(0.2, 0.05, 0.2), parent=root, position=(0, 0.25, 0))
        Entity(model='cube', color=color.white, scale=(0.05, 1, 0.3), parent=root, position=(0, 0.7, 0))
        Entity(model='cube', color=color.white, scale=(0.05, 0.3, 0.3), parent=root, position=(0, 1.15, 0), rotation=(45,0,0))
    elif item_type == "gun":
        Entity(model='cube', color=color.black, scale=(0.15, 0.5, 0.15), parent=root, position=(0, 0, 0), rotation=(45,0,0))
        Entity(model='cube', color=color.gray, scale=(0.2, 0.2, 1), parent=root, position=(0, 0.2, 0.4))
    elif item_type == "ammo":
        Entity(model='cube', color=color.light_gray, scale=(0.4, 0.2, 0.15), parent=root, position=(0, 0.2, 0))
        Entity(model='cube', color=color.dark_gray, scale=(0.35, 0.1, 0.1), parent=root, position=(0, 0.3, 0))
    elif item_type == "wood":
        if config.is_texture(config.WOOD_TEXTURE):
            Entity(model='cube', texture=config.WOOD_TEXTURE, scale=(0.6, 0.2, 0.2), parent=root, position=(0, 0.3, 0), texture_scale=(1, 1))
        else:
            Entity(model='cube', color=config.WOOD_TEXTURE, scale=(0.6, 0.2, 0.2), parent=root, position=(0, 0.3, 0))
    elif item_type == "stone":
        Entity(model='cube', color=color.gray, scale=(0.6, 0.6, 0.6), parent=root, position=(0, 0.5, 0))
    elif item_type == "seed":
        Entity(model='cube', color=color.green, scale=(0.3, 0.3, 0.1), parent=root, position=(0, 0.2, 0))
    elif item_type == "fertilizer":
        try:
            tex = load_texture('texture/fertilize')
            if hasattr(tex, 'width'):
                Entity(model='cube', texture=tex, scale=(0.3, 0.3, 0.3), parent=root, position=(0, 0.2, 0))
            else:
                Entity(model='cube', color=color.green, scale=(0.3, 0.3, 0.3), parent=root, position=(0, 0.2, 0))
        except Exception as e:
            print(f"Failed to load fertilizer texture: {e}")
            Entity(model='cube', color=color.green, scale=(0.3, 0.3, 0.3), parent=root, position=(0, 0.2, 0))
    elif item_type == "field":
        # Use texture if loaded, else color
        if config.is_texture(config.DIRT_TEXTURE):  # It's a texture
            Entity(model='cube', texture=config.DIRT_TEXTURE, scale=(1, 0.2, 1), parent=root, position=(0, 0.1, 0), texture_scale=(1, 1))
        else:  # It's a color
            Entity(model='cube', color=config.DIRT_TEXTURE, scale=(1, 0.2, 1), parent=root, position=(0, 0.1, 0))
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
