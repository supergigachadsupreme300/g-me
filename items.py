from ursina import Entity, color, Vec3, load_texture, load_model
import config
from ursina import time as ursina_time, destroy

# list of active thrown item entities (projectiles)
thrown_items = []
GRAVITY = 9.81


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
    elif item_type == "scythe":
        Entity(model='cube', color=color.brown, scale=(0.1, 0.8, 0.1), parent=root, position=(0, 0, 0))
        Entity(model='cube', color=color.gray, scale=(0.05, 0.35, 0.05), parent=root, position=(0.1, 0.5, 0), rotation=(0, 0, 45))
        Entity(model='cube', color=color.gray, scale=(0.05, 0.2, 0.05), parent=root, position=(0.2, 0.7, 0), rotation=(0, 0, 0))
        Entity(model='cube', color=color.gray, scale=(0.05, 0.35, 0.05), parent=root, position=(0.1, 0.9, 0), rotation=(0, 0, -45))
    elif item_type == "mobspawner":
        Entity(model='cube', color=color.dark_gray, scale=(0.4, 0.4, 0.4), parent=root, position=(0, 0.2, 0))
        Entity(model='sphere', color=color.red, scale=(0.22, 0.22, 0.22), parent=root, position=(0, 0.65, 0))
        Entity(model='cube', color=color.black, scale=(0.15, 0.6, 0.15), parent=root, position=(0, 0.05, 0))
    elif item_type == "wood":
        if config.is_texture(config.WOOD_TEXTURE):
            Entity(model='cube', texture=config.WOOD_TEXTURE, scale=(0.6, 0.2, 0.2), parent=root, position=(0, 0.3, 0), texture_scale=(1, 1))
        else:
            Entity(model='cube', color=config.WOOD_TEXTURE, scale=(0.6, 0.2, 0.2), parent=root, position=(0, 0.3, 0))
    elif item_type == "stone":
        Entity(model='cube', color=color.gray, scale=(0.6, 0.6, 0.6), parent=root, position=(0, 0.5, 0))
    elif item_type == "seed":
        try:
            seed_texture = load_texture('texture/seed.png')
            if hasattr(seed_texture, 'width'):
                Entity(model='cube', texture=seed_texture, scale=(0.3, 0.3, 0.1), parent=root, position=(0, 0.2, 0), texture_scale=(1, 1), color=color.rgb(180/255, 120/255, 60/255))
            else:
                Entity(model='cube', color=color.rgb(180/255, 120/255, 60/255), scale=(0.3, 0.3, 0.1), parent=root, position=(0, 0.2, 0))
        except Exception as e:
            print(f"Failed to load seed texture: {e}")
            Entity(model='cube', color=color.rgb(180/255, 120/255, 60/255), scale=(0.3, 0.3, 0.1), parent=root, position=(0, 0.2, 0))
    elif item_type == "peashooter seed":
        try:
            seed_texture = load_texture('texture/peashooter_seed.png')
            if hasattr(seed_texture, 'width'):
                Entity(model='cube', texture=seed_texture, scale=(0.3, 0.3, 0.1), parent=root, position=(0, 0.2, 0), texture_scale=(1, 1), color=color.rgb(255/255, 220/255, 80/255))
            else:
                Entity(model='cube', color=color.rgb(255/255, 220/255, 80/255), scale=(0.3, 0.3, 0.1), parent=root, position=(0, 0.2, 0))
        except Exception as e:
            print(f"Failed to load peashooter seed texture: {e}")
            Entity(model='cube', color=color.rgb(255/255, 220/255, 80/255), scale=(0.3, 0.3, 0.1), parent=root, position=(0, 0.2, 0))
    elif item_type == "wheat":
        try:
            wheat_model = load_model('model/wheat_sack/source/WheatSack.fbx')
            # load albedo texture if available
            wheat_tex = None
            try:
                wheat_tex = load_texture('model/wheat_sack/textures/WheatSack_albedo.jpg')
            except Exception:
                wheat_tex = None
            if wheat_model:
                # scale to ~1/100 (0.35 * 0.01 = 0.0035)
                if wheat_tex:
                    Entity(model=wheat_model, texture=wheat_tex, scale=(0.0035, 0.0035, 0.0035), parent=root, position=(0, 0.0, 0), rotation=(0, 180, 0))
                else:
                    Entity(model=wheat_model, scale=(0.0035, 0.0035, 0.0035), parent=root, position=(0, 0.0, 0), rotation=(0, 180, 0))
            else:
                raise Exception('wheat_model returned None')
        except Exception:
            Entity(model='cube', color=color.yellow, scale=(0.3, 0.3, 0.3), parent=root, position=(0, 0.2, 0))
    elif item_type == "damaged wheat":
        Entity(model='cube', color=color.brown, scale=(0.3, 0.3, 0.3), parent=root, position=(0, 0.2, 0))
    elif item_type == "mì hảo hảo":
        try:
            noodle_model = load_model('model/haohao/source/Mitomhaohao.glb')
            if noodle_model:
                Entity(model=noodle_model, scale=(0.4, 0.4, 0.4), parent=root, position=(0, 0.1, 0), rotation=(0, 180, 0))
            else:
                raise Exception('noodle_model returned None')
        except Exception:
            Entity(model='cube', color=color.red, scale=(0.3, 0.1, 0.3), parent=root, position=(0, 0.2, 0))
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


def spawn_thrown_item(item_type, position, velocity):
    """Spawn a lightweight projectile representing a thrown item.
    The projectile is updated by `update_thrown_items` until it hits the ground,
    at which point a regular ground item is spawned and the projectile destroyed.
    """
    proj = Entity(position=position, collider=None)
    proj.item_type = item_type
    proj.velocity = Vec3(velocity)

    # Create a lightweight visual copy for the flying item by spawning a
    # temporary ground item and moving its children under a new visual parent.
    try:
        temp = spawn_ground_item(item_type, position)
        visual = Entity(parent=proj, position=Vec3(0, 0, 0))
        # reparent children from temp into visual
        for child in list(temp.children):
            child.parent = visual
            # keep child's local transform (positions are preserved on reparent)
        try:
            destroy(temp)
        except Exception:
            pass
        proj.visual = visual
    except Exception:
        proj.visual = None

    thrown_items.append(proj)
    return proj


def update_thrown_items(dt):
    # iterate a copy since we may remove while iterating
    for proj in list(thrown_items):
        # integrate motion
        proj.position += proj.velocity * dt
        proj.velocity.y -= GRAVITY * dt

        # when hitting (or below) ground level, convert visual into ground item and remove projectile
        ground_y = 0.0
        if proj.y <= ground_y + 0.15:
            spawn_pos = Vec3(proj.x, ground_y + 0.15, proj.z)
            # spawn a fresh ground item at the landing position
            try:
                spawn_ground_item(proj.item_type, spawn_pos)
            except Exception:
                pass

            # destroy the flying projectile (and its visual)
            try:
                destroy(proj)
            except Exception:
                pass
            if proj in thrown_items:
                thrown_items.remove(proj)

