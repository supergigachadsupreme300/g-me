from ursina import Entity, color, Vec3, destroy
import random

buildings = []
available_buildings = [
    {"name": "small_house", "size": (4, 3, 4), "color": color.rgb(150, 75, 0)},
    {"name": "tower", "size": (2, 6, 2), "color": color.gray},
    {"name": "wall", "size": (6, 2, 1), "color": color.rgb(100, 50, 0)},
]

building_preview = None
current_building_index = 0
current_rotation = 0


def setup_building_system():
    global building_preview
    building_preview = Entity(model='cube', color=color.green, scale=(1, 1, 1), enabled=False)


def get_current_building():
    return available_buildings[current_building_index]


def get_rotated_size(building):
    if current_rotation % 180 != 0:
        return (building["size"][2], building["size"][1], building["size"][0])
    return building["size"]


def get_building_bounds(position, size, rotation):
    if rotation % 180 != 0:
        size = (size[2], size[1], size[0])
    half_x = size[0] / 2
    half_z = size[2] / 2
    return (position.x - half_x, position.x + half_x, position.z - half_z, position.z + half_z)


def check_bounds_overlap(bounds_a, bounds_b):
    min_x_a, max_x_a, min_z_a, max_z_a = bounds_a
    min_x_b, max_x_b, min_z_b, max_z_b = bounds_b
    overlap_x = max_x_a > min_x_b and max_x_b > min_x_a
    overlap_z = max_z_a > min_z_b and max_z_b > min_z_a
    return overlap_x and overlap_z


def can_place_building(position, building=None):
    building = building or get_current_building()
    size = get_rotated_size(building)
    target_bounds = get_building_bounds(position, size, current_rotation)
    for b in buildings:
        existing_size = get_rotated_size({"size": tuple(b["entity"].scale)})
        existing_bounds = get_building_bounds(b["position"], existing_size, b["rotation"])
        if check_bounds_overlap(target_bounds, existing_bounds):
            print(f"Placement overlap detected with {b['type']} at {b['position']}")
            return False
    print(f"Can place building at {position} with rotation={current_rotation}° and size={size}")
    return True


def update_building_preview(position, valid=True):
    if building_preview is None:
        return
    building = get_current_building()
    rotated_size = get_rotated_size(building)
    building_preview.parent = None
    building_preview.world_position = position
    building_preview.scale = rotated_size
    building_preview.rotation_y = current_rotation
    building_preview.color = color.green if valid else color.red
    building_preview.enabled = True
    print(f"Preview updated: building={building['name']}, pos={position}, world_position={building_preview.world_position}, scale={rotated_size}, rotation={current_rotation}, valid={valid}")


def hide_building_preview():
    if building_preview:
        building_preview.enabled = False
        print("Preview hidden")


def place_building(position):
    building = get_current_building()
    entity = Entity(
        model='cube',
        position=position,
        scale=building["size"],
        color=building["color"],
        collider='box',
        rotation=(0, current_rotation, 0)
    )
    building_data = {
        "entity": entity,
        "type": building["name"],
        "position": position,
        "rotation": current_rotation,
        "max_health": 100,
        "current_health": 100,
        "health_bar": None
    }
    buildings.append(building_data)
    print(f"Building placed: {building['name']} at {position}")
    return building_data


def rotate_building():
    global current_rotation
    current_rotation = (current_rotation + 90) % 360
    print(f"Rotation set to {current_rotation}°")


def next_building():
    global current_building_index
    current_building_index = (current_building_index + 1) % len(available_buildings)
    building = get_current_building()
    print(f"Selected building: {building['name']}")


def prev_building():
    global current_building_index
    current_building_index = (current_building_index - 1) % len(available_buildings)
    building = get_current_building()
    print(f"Selected building: {building['name']}")


def damage_building(building_data, damage):
    building_data["current_health"] -= damage
    if building_data["health_bar"]:
        building_data["health_bar"].scale_x = max(0, building_data["current_health"] / building_data["max_health"])
    print(f"Building damaged: {building_data['current_health']}/{building_data['max_health']}")
    if building_data["current_health"] <= 0:
        destroy(building_data["entity"])
        if building_data["health_bar"]:
            destroy(building_data["health_bar"])
        buildings.remove(building_data)
        print("Building destroyed")


def find_building_by_entity(entity):
    for b in buildings:
        if b["entity"] == entity:
            return b
    return None