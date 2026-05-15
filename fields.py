from ursina import Entity, Vec3, color, invoke, curve, destroy
import random
from items import spawn_ground_item

fields = []
field_preview = Entity(model='cube', color=color.rgba(150/255, 100/255, 50/255, 140/255), scale=(1, 0.2, 1), enabled=False)


def create_field(pos):
    root = spawn_ground_item("field", Vec3(pos.x, 0, pos.z))
    fields.append({
        "entity": root,
        "pos": Vec3(pos.x, 0.1, pos.z),
        "rice_planted": False,
        "rice_stage": 0,
        "rice_nodes": [],
        "rice_hp": 0
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


def _update_rice_patch(field_data, stage):
    target_ratio = stage / 4.0
    patch_color = color.lime if stage < 4 else color.yellow
    for patch in field_data["rice_nodes"]:
        target_height = patch.initial_height * target_ratio
        patch.scale_y = target_height
        patch.y = 0.1 + target_height / 2
        patch.color = patch_color


def advance_rice_growth(field_data):
    if not field_data["rice_planted"]:
        return
    if field_data["rice_stage"] >= 4:
        return
    field_data["rice_stage"] += 1
    _update_rice_patch(field_data, field_data["rice_stage"])
    if field_data["rice_stage"] < 4:
        invoke(lambda: advance_rice_growth(field_data), delay=4)


def plant_rice_on_field(field_data):
    if field_data["rice_planted"]:
        return False

    field_data["rice_planted"] = True
    field_data["rice_stage"] = 1
    field_data["rice_hp"] = 20
    field_data["rice_nodes"] = []

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
        field_data["rice_nodes"].append(patch)

    # Add health bar
    field_data["health_bar"] = Entity(model='cube', color=color.red, scale=(1, 0.1, 0.1), position=(0, 1.5, 0), parent=field_data["entity"])
    update_rice_health_bar(field_data)

    _update_rice_patch(field_data, 1)
    invoke(lambda: advance_rice_growth(field_data), delay=4)
    return True


def update_rice_health_bar(field_data):
    if "health_bar" in field_data and field_data["health_bar"]:
        hp_ratio = field_data["rice_hp"] / 20.0
        field_data["health_bar"].scale_x = hp_ratio
        field_data["health_bar"].x = -0.5 + hp_ratio / 2  # Center it


def destroy_rice(field_data):
    for patch in field_data["rice_nodes"]:
        destroy(patch)
    field_data["rice_nodes"] = []
    field_data["rice_planted"] = False
    field_data["rice_stage"] = 0
    field_data["rice_hp"] = 0
    if "health_bar" in field_data and field_data["health_bar"]:
        destroy(field_data["health_bar"])
        field_data["health_bar"] = None
