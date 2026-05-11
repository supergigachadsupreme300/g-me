from ursina import Entity, Vec3, color, invoke, curve
import random
from items import spawn_ground_item
from config import DIRT_TEXTURE

fields = []
field_preview = Entity(model='cube', color=color.rgb(150, 100, 50, 140), scale=(1, 0.2, 1), enabled=False)


def create_field(pos):
    root = spawn_ground_item("field", Vec3(pos.x, 0, pos.z))
    fields.append({
        "entity": root,
        "pos": Vec3(pos.x, 0.1, pos.z),
        "rice_planted": False,
        "rice_stage": 0,
        "rice_nodes": []
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

    _update_rice_patch(field_data, 1)
    invoke(lambda: advance_rice_growth(field_data), delay=4)
    return True
