from ursina import Entity, Vec3, color, invoke, curve, destroy, time as ursina_time
import time as pytime
from math import atan2, degrees
import random
from items import spawn_ground_item

# projectiles fired by peashooters
peashooter_projectiles = []

fields = []
field_preview = Entity(model='cube', color=color.rgba(150/255, 100/255, 50/255, 140/255), scale=(1, 0.2, 1), enabled=False)


def create_field(pos):
    root = spawn_ground_item("field", Vec3(pos.x, 0, pos.z))
    fields.append({
        "entity": root,
        "pos": Vec3(pos.x, 0.1, pos.z),
        "wheat_planted": False,
        "wheat_stage": 0,
        "wheat_nodes": [],
        "wheat_hp": 0,
        "peashooter_planted": False,
        "peashooter_entity": None,
        "peashooter_hp": 0
    })
    return root


def find_field_by_entity(entity):
    e = entity
    while e is not None:
        for field_data in fields:
            if field_data["entity"] == e:
                return field_data
        e = e.parent
    return None


def _update_wheat_patch(field_data, stage):
    target_ratio = stage / 4.0
    patch_color = color.lime if stage < 4 else color.yellow
    for patch in field_data["wheat_nodes"]:
        target_height = patch.initial_height * target_ratio
        patch.scale_y = target_height
        patch.y = 0.1 + target_height / 2
        patch.color = patch_color


def advance_wheat_growth(field_data):
    if not field_data["wheat_planted"]:
        return
    if field_data["wheat_stage"] >= 4:
        return
    field_data["wheat_stage"] += 1
    _update_wheat_patch(field_data, field_data["wheat_stage"])
    if field_data["wheat_stage"] < 4:
        invoke(lambda: advance_wheat_growth(field_data), delay=4)


def plant_wheat_on_field(field_data):
    if field_data["wheat_planted"]:
        return False

    field_data["wheat_planted"] = True
    field_data["wheat_stage"] = 1
    field_data["wheat_hp"] = 20
    field_data["wheat_nodes"] = []

    num_patches = random.randint(4, 5)
    for i in range(num_patches):
        width = random.uniform(0.25, 0.45)
        depth = random.uniform(0.15, 0.30)
        offset_x = random.uniform(-0.35, 0.35)
        offset_z = random.uniform(-0.35, 0.35)
        initial_height = random.uniform(0.6, 1.2)
        patch = Entity(
            model='cube',
            color=color.lime,
            scale=(width, initial_height * 0.25, depth),
            position=(offset_x, 0.1 + initial_height * 0.25 / 2, offset_z),
            parent=field_data["entity"]
        )
        patch.initial_height = initial_height
        field_data["wheat_nodes"].append(patch)

    # Add health bar
    field_data["health_bar"] = Entity(model='cube', color=color.red, scale=(1, 0.1, 0.1), position=(0, 1.5, 0), parent=field_data["entity"])
    update_wheat_health_bar(field_data)

    _update_wheat_patch(field_data, 1)
    invoke(lambda: advance_wheat_growth(field_data), delay=4)
    return True


def plant_peashooter_on_field(field_data):
    if field_data["wheat_planted"] or field_data["peashooter_planted"]:
        return False

    field_data["peashooter_planted"] = True
    field_data["peashooter_hp"] = 20

    try:
        from ursina import load_model, load_texture
        model = load_model('model\peashooter\source\PVZ_Peashooter.glb')
        texture = load_texture('model\peashooter\textures\peashooter.png')
        field_data["peashooter_entity"] = Entity(
            model=model,
            texture=texture,
            scale=0.55,
            position=(0, 0.5, 0),
            parent=field_data["entity"],
            collider='box'
        )
    except Exception as e:
        print(f"Failed to load peashooter model or texture: {e}")
        field_data["peashooter_entity"] = Entity(
            model='cube',
            color=color.lime,
            scale=(0.8, 1.0, 0.5),
            position=(0, 0.6, 0),
            parent=field_data["entity"],
            collider='box'
        )

    return True


def update_peashooters():
    # Called once per frame from game.update()
    # Use a local detection zone per peashooter: acquire target when an enemy
    # enters the peashooter's range and keep targeting it until it leaves or dies.
    import enemies as enemies_mod
    now = pytime.time()
    for field_data in fields:
        if not field_data.get("peashooter_planted"):
            continue
        pe = field_data.get("peashooter_entity")
        if pe is None:
            continue
        # detection range (units)
        rng = field_data.get('peashooter_range', 16.0)
        last = field_data.get("last_shot", 0)
        cooldown = field_data.get('peashooter_cooldown', 1.0)

        target = field_data.get('peashooter_target')
        # acquire target if none
        if target is None:
            for enemy in enemies_mod.enemies:
                if getattr(enemy, 'entity', None) is None:
                    continue
                try:
                    dist = (enemy.entity.world_position - pe.world_position).length()
                except Exception:
                    continue
                if dist <= rng:
                    field_data['peashooter_target'] = enemy
                    target = enemy
                    print(f"Peashooter at {pe.world_position} acquired target: {enemy.__class__.__name__} at {enemy.entity.world_position}")
                    break
        else:
            # validate existing target
            if target not in enemies_mod.enemies or getattr(target, 'entity', None) is None:
                field_data['peashooter_target'] = None
                target = None
            else:
                try:
                    if (target.entity.world_position - pe.world_position).length() > rng:
                        field_data['peashooter_target'] = None
                        target = None
                except Exception:
                    field_data['peashooter_target'] = None
                    target = None

        # if we have a valid target, attempt to shoot
        if target is not None and (now - last) >= cooldown:
            spawn_pos = pe.world_position + Vec3(0, 0.5, 0)
            proj = Entity(model='sphere', color=color.lime, scale=0.12, position=spawn_pos, collider='box')
            direction = (target.entity.world_position - spawn_pos).normalized()
            proj.velocity = direction * field_data.get('peashooter_bullet_speed', 18)
            proj.damage = field_data.get('peashooter_damage', 6)
            proj.age = 0.0
            proj.lifetime = field_data.get('peashooter_bullet_life', 3.0)
            # avoid immediate self-collision by offsetting slightly and ignoring field root on intersects
            proj._ignore = field_data.get('entity')
            peashooter_projectiles.append(proj)
            field_data['last_shot'] = now
            # rotate peashooter to face the target (world-space yaw)
            try:
                dir_vec = target.entity.world_position - pe.world_position
                ang = degrees(atan2(dir_vec.x, dir_vec.z))
                pe.rotation_y = ang-90
            except Exception:
                pass
            print(f"Peashooter fired at {target.entity.world_position} from {spawn_pos}")


def update_peashooter_projectiles():
    import enemies as enemies_mod
    for proj in list(peashooter_projectiles):
        proj.position += proj.velocity * ursina_time.dt
        proj.age += ursina_time.dt
        # ignore collision with own field entity if set
        try:
            ignore_list = (proj._ignore,) if getattr(proj, '_ignore', None) is not None else ()
        except Exception:
            ignore_list = ()
        hit_info = proj.intersects(ignore=ignore_list)
        if hit_info.hit:
            enemy = enemies_mod.find_enemy_by_entity(hit_info.entity)
            if enemy:
                enemy.take_damage(proj.damage)
                try:
                    destroy(proj)
                except Exception:
                    pass
                if proj in peashooter_projectiles:
                    peashooter_projectiles.remove(proj)
                continue
        if proj.age >= proj.lifetime:
            try:
                destroy(proj)
            except Exception:
                pass
            if proj in peashooter_projectiles:
                peashooter_projectiles.remove(proj)


def update_wheat_health_bar(field_data):
    if "health_bar" in field_data and field_data["health_bar"]:
        hp_ratio = field_data["wheat_hp"] / 20.0
        field_data["health_bar"].scale_x = hp_ratio
        field_data["health_bar"].x = -0.5 + hp_ratio / 2  # Center it


def destroy_wheat(field_data):
    for patch in field_data["wheat_nodes"]:
        destroy(patch)
    field_data["wheat_nodes"] = []
    field_data["wheat_planted"] = False
    field_data["wheat_stage"] = 0
    field_data["wheat_hp"] = 0
    if "health_bar" in field_data and field_data["health_bar"]:
        destroy(field_data["health_bar"])
        field_data["health_bar"] = None
