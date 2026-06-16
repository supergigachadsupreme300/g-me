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
    elif item_type == "corn seed":
        try:
            seed_texture = load_texture('texture/seed.png')
            if hasattr(seed_texture, 'width'):
                Entity(model='cube', texture=seed_texture, scale=(0.35, 0.35, 0.1), parent=root, position=(0, 0.2, 0), texture_scale=(1, 1), color=color.rgb(255/255, 220/255, 60/255))
            else:
                Entity(model='cube', color=color.rgb(255/255, 220/255, 60/255), scale=(0.35, 0.35, 0.1), parent=root, position=(0, 0.2, 0))
        except Exception:
            Entity(model='cube', color=color.rgb(255/255, 220/255, 60/255), scale=(0.35, 0.35, 0.1), parent=root, position=(0, 0.2, 0))
    # potato seed removed; potatoes are planted directly using the 'potato' item
    elif item_type == "corn":
        # create a ground corn visual composed of multiple thin rectangles like the held version
        ear_color = color.rgb(255/255, 210/255, 60/255)
        rect_thickness = 0.05
        rect_height = 0.25
        rect_depth = 0.12
        pos = (0, 0.12, 0)
        count = 5
        for i in range(count):
            angle = i * (360.0 / float(count))
            Entity(model='cube', color=ear_color, parent=root,
                   position=pos, scale=(rect_thickness, rect_height, rect_depth), rotation=(0, angle, 0))
    elif item_type == "damaged corn":
        Entity(model='cube', color=color.brown, scale=(0.3, 0.3, 0.3), parent=root, position=(0, 0.2, 0))
    elif item_type == "potato":
        try:
            Entity(model='sphere', color=color.rgb(160/255, 110/255, 60/255), scale=(0.28, 0.22, 0.22), parent=root, position=(-0.04, 0.06, 0))
            Entity(model='sphere', color=color.rgb(150/255, 100/255, 55/255), scale=(0.22, 0.18, 0.22), parent=root, position=(0.06, 0.03, 0))
        except Exception:
            Entity(model='cube', color=color.rgb(160/255, 110/255, 60/255), scale=(0.35, 0.25, 0.35), parent=root, position=(0, 0.15, 0))
    elif item_type == "damaged potato":
        Entity(model='cube', color=color.brown, scale=(0.3, 0.25, 0.3), parent=root, position=(0, 0.15, 0))
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
    # Spawn the actual ground-item entity but disable its collider while
    # it's flying. Use the same entity as the projectile (no wrapper).
    visual = spawn_ground_item(item_type, position)
    # keep collider enabled so the item can collide/picked while flying
    visual.velocity = Vec3(velocity)
    # flight tracking to avoid immediate landing
    visual.flying_time = 0.0
    visual.start_pos = Vec3(position)
    # ensure item_type attribute exists on the entity root
    visual.item_type = item_type

    thrown_items.append(visual)
    return visual


def update_thrown_items(dt):
    # iterate a copy since we may remove while iterating
    for proj in list(thrown_items):
        try:
            # integrate motion
            proj.position += proj.velocity * dt
            proj.velocity.y -= GRAVITY * dt

            # flight time and distance tracking
            proj.flying_time = getattr(proj, 'flying_time', 0.0) + dt
            start_pos = getattr(proj, 'start_pos', proj.position)
            dist = (proj.position - start_pos).length()

            ground_y = 0.0
            # allow a small grace period / distance to avoid immediate landing
            MIN_FLIGHT_TIME = 0.08
            MIN_FLIGHT_DIST = 0.3

            # stuck detection: if velocity nearly zero while above ground
            speed = getattr(proj, 'velocity', Vec3(0, 0, 0)).length()
            if speed < 0.01 and proj.y > ground_y + 0.2:
                proj.stuck_time = getattr(proj, 'stuck_time', 0.0) + dt
            else:
                proj.stuck_time = 0.0

            # normal landing condition (after minimal flight time/distance)
            if proj.y <= ground_y + 0.15 and (proj.flying_time >= MIN_FLIGHT_TIME or dist >= MIN_FLIGHT_DIST):
                proj.position = Vec3(proj.x, ground_y + 0.15, proj.z)
                try:
                    proj.collider = 'box'
                except Exception:
                    pass
                proj.velocity = Vec3(0, 0, 0)
                if proj in thrown_items:
                    thrown_items.remove(proj)
                continue

            # if stuck in mid-air for too long, force it to land to avoid blocking future throws
            STUCK_TIMEOUT = 0.6
            if getattr(proj, 'stuck_time', 0.0) > STUCK_TIMEOUT:
                proj.position = Vec3(proj.x, ground_y + 0.15, proj.z)
                try:
                    proj.collider = 'box'
                except Exception:
                    pass
                proj.velocity = Vec3(0, 0, 0)
                if proj in thrown_items:
                    thrown_items.remove(proj)
                continue
        except Exception:
            # if any per-projectile error occurs, remove it so it won't break future throws
            try:
                if proj in thrown_items:
                    thrown_items.remove(proj)
            except Exception:
                pass

