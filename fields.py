from ursina import Entity, Vec3, color, invoke, curve, destroy, time as ursina_time
import time as pytime
from math import atan2, degrees
import random
from items import spawn_ground_item

peashooter_projectiles = []

fields = []
field_preview = Entity(model='cube', color=color.rgba(150/255, 100/255, 50/255, 140/255), scale=(1, 0.2, 1), enabled=False)

CROP_STAGES = 4
CROP_MAX_HP = 20

CROP_VISUALS = {
    'wheat': {
        'young': color.lime,
        'ripe': color.yellow,
        'patches': 5,
        'style': 'tall',
    },
    'corn': {
        'young': color.lime,
        'ripe': color.rgb(255 / 255, 210 / 255, 60 / 255),
        'patches': 4,
        'style': 'stalk',
    },
    'potato': {
        'young': color.rgb(90 / 255, 150 / 255, 70 / 255),
        'ripe': color.rgb(120 / 255, 180 / 255, 80 / 255),
        'patches': 6,
        'style': 'low',
    },
}


def create_field(pos):
    # Tạo một mảnh ruộng mới và đăng ký vào danh sách `fields`.
    # GFI (hiển thị thông tin mảnh ruộng) sử dụng các thuộc tính sau:
    # - entity: Entity của mảnh ruộng (vị trí / parent cho các node)
    # - pos: vị trí hiển thị / tham chiếu
    # - crop_type: loại cây đang trồng (ví dụ 'wheat', 'corn', 'potato')
    # - wheat_planted / peashooter_planted: flag cho biết có cây/peashooter
    # - wheat_stage: giai đoạn sinh trưởng (dùng để render kích thước)
    # - wheat_hp / peashooter_hp: máu của cây / peashooter (dùng cho health bar)
    # - wheat_nodes: các Entity con biểu diễn từng cụm cây (dùng để render)
    # - peashooter_entity: Entity peashooter (nếu được trồng)
    # - health_bar: Entity thanh máu (nếu có)
    root = spawn_ground_item("field", Vec3(pos.x, 0, pos.z))
    fields.append({
        "entity": root,                       # Entity gốc của mảnh ruộng (GFI)
        "pos": Vec3(pos.x, 0.1, pos.z),      # Vị trí hiển thị / tham chiếu (GFI)
        "crop_type": None,                    # Loại cây đang trồng (GFI)
        "wheat_planted": False,               # Có cây hay không (GFI)
        "wheat_stage": 0,                     # Giai đoạn sinh trưởng (GFI)
        "wheat_nodes": [],                    # Danh sách Entity các cụm cây (render)
        "wheat_hp": 0,                        # Máu cây (GFI)
        "peashooter_planted": False,          # Có peashooter hay không (GFI)
        "peashooter_entity": None,            # Entity peashooter (render / GFI)
        "peashooter_hp": 0,                   # Máu peashooter (GFI)
        "health_bar": None,                   # Entity thanh máu (hiển thị GFI)
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


def has_crop(field_data):
    return field_data.get("crop_type") is not None and field_data.get("wheat_hp", 0) > 0


def _sync_wheat_flag(field_data):
    field_data["wheat_planted"] = field_data.get("crop_type") is not None


def _make_crop_patch(field_data, crop_type, offset_x, offset_z, initial_height, width, depth):
    style = CROP_VISUALS[crop_type]['style']
    if style == 'stalk':
        patch = Entity(
            model='cube',
            color=CROP_VISUALS[crop_type]['young'],
            scale=(0.12, initial_height * 0.25, 0.12),
            position=(offset_x, 0.1 + initial_height * 0.25 / 2, offset_z),
            parent=field_data["entity"],
        )
    elif style == 'low':
        patch = Entity(
            model='cube',
            color=CROP_VISUALS[crop_type]['young'],
            scale=(width, initial_height * 0.2, depth),
            position=(offset_x, 0.08 + initial_height * 0.2 / 2, offset_z),
            parent=field_data["entity"],
        )
    else:
        patch = Entity(
            model='cube',
            color=CROP_VISUALS[crop_type]['young'],
            scale=(width, initial_height * 0.25, depth),
            position=(offset_x, 0.1 + initial_height * 0.25 / 2, offset_z),
            parent=field_data["entity"],
        )
    patch.initial_height = initial_height
    patch.crop_style = style
    return patch


def _update_crop_patch(field_data, stage):
    crop_type = field_data["crop_type"]
    if crop_type is None:
        return
    visuals = CROP_VISUALS[crop_type]
    target_ratio = stage / float(CROP_STAGES)
    patch_color = visuals['young'] if stage < CROP_STAGES else visuals['ripe']
    for patch in field_data["wheat_nodes"]:
        target_height = patch.initial_height * target_ratio
        style = getattr(patch, 'crop_style', 'tall')
        if style == 'stalk':
            patch.scale_y = target_height
            patch.y = 0.1 + target_height / 2
        elif style == 'low':
            patch.scale_y = target_height * 0.25
            patch.y = 0.08 + patch.scale_y / 2
        else:
            patch.scale_y = target_height
            patch.y = 0.1 + target_height / 2
        patch.color = patch_color


def advance_crop_growth(field_data):
    if not has_crop(field_data):
        return
    if field_data["wheat_stage"] >= CROP_STAGES:
        return
    field_data["wheat_stage"] += 1
    _update_crop_patch(field_data, field_data["wheat_stage"])
    if field_data["wheat_stage"] < CROP_STAGES:
        invoke(lambda: advance_crop_growth(field_data), delay=4)


def plant_crop_on_field(field_data, crop_type):
    if has_crop(field_data) or field_data.get("peashooter_planted"):
        return False
    if crop_type not in CROP_VISUALS:
        return False

    field_data["crop_type"] = crop_type
    field_data["wheat_stage"] = 1
    field_data["wheat_hp"] = CROP_MAX_HP
    field_data["wheat_nodes"] = []
    _sync_wheat_flag(field_data)

    visuals = CROP_VISUALS[crop_type]
    num_patches = random.randint(max(3, visuals['patches'] - 1), visuals['patches'])
    for _ in range(num_patches):
        width = random.uniform(0.22, 0.42)
        depth = random.uniform(0.15, 0.30)
        offset_x = random.uniform(-0.35, 0.35)
        offset_z = random.uniform(-0.35, 0.35)
        initial_height = random.uniform(0.55, 1.15)
        patch = _make_crop_patch(field_data, crop_type, offset_x, offset_z, initial_height, width, depth)
        field_data["wheat_nodes"].append(patch)

    field_data["health_bar"] = Entity(
        model='cube', color=color.red, scale=(1, 0.1, 0.1),
        position=(0, 1.5, 0), parent=field_data["entity"],
    )
    update_wheat_health_bar(field_data)
    _update_crop_patch(field_data, 1)
    invoke(lambda: advance_crop_growth(field_data), delay=4)
    return True


def plant_wheat_on_field(field_data):
    return plant_crop_on_field(field_data, 'wheat')


def plant_corn_on_field(field_data):
    return plant_crop_on_field(field_data, 'corn')


def plant_potato_on_field(field_data):
    return plant_crop_on_field(field_data, 'potato')


def get_harvest_item(field_data):
    crop_type = field_data.get("crop_type")
    if crop_type == 'corn':
        return 'corn' if field_data["wheat_stage"] >= CROP_STAGES else 'damaged corn'
    if crop_type == 'potato':
        return 'potato' if field_data["wheat_stage"] >= CROP_STAGES else 'damaged potato'
    return 'wheat' if field_data["wheat_stage"] >= CROP_STAGES else 'damaged wheat'


def plant_peashooter_on_field(field_data):
    if has_crop(field_data) or field_data["peashooter_planted"]:
        return False

    field_data["peashooter_planted"] = True
    field_data["peashooter_hp"] = 20

    try:
        from ursina import load_model, load_texture
        model = load_model('model\\peashooter\\source\\PVZ_Peashooter.glb')
        texture = load_texture('model\\peashooter\\textures\\peashooter.png')
        field_data["peashooter_entity"] = Entity(
            model=model,
            texture=texture,
            scale=0.55,
            position=(0, 0.5, 0),
            parent=field_data["entity"],
            collider='box',
        )
    except Exception as e:
        print(f"Failed to load peashooter model or texture: {e}")
        field_data["peashooter_entity"] = Entity(
            model='cube',
            color=color.lime,
            scale=(0.8, 1.0, 0.5),
            position=(0, 0.6, 0),
            parent=field_data["entity"],
            collider='box',
        )

    return True


def update_peashooters():
    import enemies as enemies_mod
    now = pytime.time()
    for field_data in fields:
        if not field_data.get("peashooter_planted"):
            continue
        pe = field_data.get("peashooter_entity")
        if pe is None:
            continue
        rng = field_data.get('peashooter_range', 16.0)
        last = field_data.get("last_shot", 0)
        cooldown = field_data.get('peashooter_cooldown', 1.0)

        target = field_data.get('peashooter_target')
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
                    break
        else:
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

        if target is not None and (now - last) >= cooldown:
            spawn_pos = pe.world_position + Vec3(0, 0.5, 0)
            proj = Entity(model='sphere', color=color.lime, scale=0.12, position=spawn_pos, collider='box')
            direction = (target.entity.world_position - spawn_pos).normalized()
            proj.velocity = direction * field_data.get('peashooter_bullet_speed', 18)
            proj.damage = field_data.get('peashooter_damage', 6)
            proj.age = 0.0
            proj.lifetime = field_data.get('peashooter_bullet_life', 3.0)
            proj._ignore = field_data.get('entity')
            peashooter_projectiles.append(proj)
            field_data['last_shot'] = now
            try:
                dir_vec = target.entity.world_position - pe.world_position
                ang = degrees(atan2(dir_vec.x, dir_vec.z))
                pe.rotation_y = ang - 90
            except Exception:
                pass


def update_peashooter_projectiles():
    import enemies as enemies_mod
    for proj in list(peashooter_projectiles):
        proj.position += proj.velocity * ursina_time.dt
        proj.age += ursina_time.dt
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
    if field_data.get("health_bar"):
        hp_ratio = field_data["wheat_hp"] / float(CROP_MAX_HP)
        field_data["health_bar"].scale_x = hp_ratio
        field_data["health_bar"].x = -0.5 + hp_ratio / 2


def destroy_wheat(field_data):
    for patch in field_data["wheat_nodes"]:
        destroy(patch)
    field_data["wheat_nodes"] = []
    field_data["crop_type"] = None
    field_data["wheat_planted"] = False
    field_data["wheat_stage"] = 0
    field_data["wheat_hp"] = 0
    if field_data.get("health_bar"):
        destroy(field_data["health_bar"])
        field_data["health_bar"] = None
