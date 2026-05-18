from ursina import Entity, color, Vec3, destroy
from math import cos, sin, radians

buildings = []
available_buildings = [
    {"name": "wood_wall",   "size": (6, 3, 0.5), "color": color.rgb(160/255, 100/255, 45/255)},
    {"name": "stone_wall",  "size": (5, 3, 0.5), "color": color.rgb(105/255, 105/255, 105/255)},
    {"name": "fence",       "size": (4, 1.5, 0.3), "color": color.rgb(175/255, 130/255, 65/255)},
    {"name": "watchtower",  "size": (3, 8, 3),   "color": color.rgb(130/255, 85/255, 40/255)},
    {"name": "small_house", "size": (8, 5, 8),   "color": color.rgb(200/255, 160/255, 100/255)},
    {"name": "wood_floor",  "size": (4, 0.3, 4), "color": color.rgb(180/255, 135/255, 70/255)},
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
        existing_size = tuple(b["entity"].scale)
        existing_bounds = get_building_bounds(b["position"], existing_size, b["rotation"])
        if check_bounds_overlap(target_bounds, existing_bounds):
            return False
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
    building_preview.color = color.rgba(0, 1, 0, 0.5) if valid else color.rgba(1, 0, 0, 0.5)
    building_preview.enabled = True


def hide_building_preview():
    if building_preview:
        building_preview.enabled = False


# ── Visual detail helpers ──────────────────────────────────────────────────────

def _lx(t, rot):
    """World (dx, dz) for t units along the building's local X axis."""
    r = radians(rot)
    return t * cos(r), t * sin(r)


def _lz(t, rot):
    """World (dx, dz) for t units along the building's local Z axis."""
    r = radians(rot)
    return -t * sin(r), t * cos(r)


def _detail(pos, scale, col, rot=0):
    return Entity(model='cube', color=col, scale=scale,
                  position=pos, rotation=(0, rot, 0))


def _create_details(name, pos, size, rot):
    details = []
    x, y, z = pos.x, pos.y, pos.z
    w, h, d = size

    if name == "wood_wall":
        plank = color.rgb(100/255, 58/255, 18/255)
        post  = color.rgb(120/255, 72/255, 28/255)
        # Horizontal plank dividers
        for yf in (-0.3, 0.0, 0.3):
            details.append(_detail((x, y + yf*h, z), (w+0.06, 0.12, d+0.1), plank, rot))
        # End posts
        for tf in (-0.5, 0.5):
            ox, oz = _lx(tf * w, rot)
            details.append(_detail((x+ox, y, z+oz), (0.3, h+0.12, d+0.22), post, rot))

    elif name == "stone_wall":
        mortar = color.rgb(148/255, 143/255, 138/255)
        for yf in (-0.32, 0.0, 0.32):
            details.append(_detail((x, y + yf*h, z), (w+0.05, 0.09, d+0.09), mortar, rot))

    elif name == "fence":
        post_c = color.rgb(150/255, 100/255, 50/255)
        # 5 evenly-spaced vertical posts
        for i in range(5):
            t = -0.5 + i / 4.0
            ox, oz = _lx(t * w, rot)
            details.append(_detail((x+ox, y, z+oz), (0.22, h+0.3, 0.22), post_c, rot))

    elif name == "watchtower":
        plat_c  = color.rgb(110/255, 70/255, 30/255)
        batt_c  = color.rgb(100/255, 62/255, 25/255)
        # Wide platform cap at top
        details.append(_detail((x, y + h/2 + 0.15, z), (w+1.8, 0.4, d+1.8), plat_c, rot))
        # 4 corner battlement blocks
        for fx, fz in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
            ox = fx*(w/2+0.6)*cos(radians(rot)) - fz*(d/2+0.6)*sin(radians(rot))
            oz = fx*(w/2+0.6)*sin(radians(rot)) + fz*(d/2+0.6)*cos(radians(rot))
            details.append(_detail((x+ox, y+h/2+0.55, z+oz), (0.55, 0.85, 0.55), batt_c, rot))
        # Mid-height horizontal band
        details.append(_detail((x, y, z), (w+0.05, 0.3, d+0.05),
                               color.rgb(105/255, 68/255, 33/255), rot))

    elif name == "small_house":
        roof_c = color.rgb(155/255, 65/255, 40/255)
        ridge_c = color.rgb(130/255, 48/255, 28/255)
        door_c = color.rgb(75/255, 45/255, 15/255)
        win_c  = color.rgb(135/255, 195/255, 215/255)
        # Overhanging flat roof
        details.append(_detail((x, y+h/2+0.2, z), (w+1.5, 0.55, d+1.5), roof_c, rot))
        details.append(_detail((x, y+h/2+0.48, z), (w+1.8, 0.25, d+1.8), ridge_c, rot))
        # Door on front face (local +Z direction)
        dox, doz = _lz(d/2 + 0.02, rot)
        details.append(_detail((x+dox, y - h/2 + 1.3, z+doz), (1.5, 2.6, 0.18), door_c, rot))
        # Door frame
        details.append(_detail((x+dox, y - h/2 + 1.3, z+doz),
                               (1.8, 2.9, 0.12), color.rgb(60/255, 35/255, 10/255), rot))
        # Windows either side of door
        for tf in (-1.8, 1.8):
            wx, wz = _lx(tf, rot)
            details.append(_detail((x+dox+wx, y+0.4, z+doz+wz), (1.3, 1.3, 0.14), win_c, rot))
            # Window cross
            details.append(_detail((x+dox+wx, y+0.4, z+doz+wz),
                                   (0.1, 1.3, 0.15), color.rgb(60/255, 50/255, 40/255), rot))
            details.append(_detail((x+dox+wx, y+0.4, z+doz+wz),
                                   (1.3, 0.1, 0.15), color.rgb(60/255, 50/255, 40/255), rot))

    elif name == "wood_floor":
        plank_c = color.rgb(140/255, 100/255, 50/255)
        # Two plank lines running across
        for tf in (-0.25, 0.25):
            ox, oz = _lx(tf * w, rot)
            details.append(_detail((x+ox, y+0.16, z+oz), (0.12, 0.35, d+0.05), plank_c, rot))

    return details


# ── Placement ─────────────────────────────────────────────────────────────────

def place_building(position):
    building = get_current_building()
    entity = Entity(
        model='cube',
        position=position,
        scale=building["size"],
        color=building["color"],
        collider='box',
        rotation=(0, current_rotation, 0),
    )
    details = _create_details(building["name"], position, building["size"], current_rotation)
    building_data = {
        "entity": entity,
        "type": building["name"],
        "position": position,
        "rotation": current_rotation,
        "max_health": 100,
        "current_health": 100,
        "health_bar": None,
        "details": details,
    }
    buildings.append(building_data)
    return building_data


def rotate_building():
    global current_rotation
    current_rotation = (current_rotation + 90) % 360


def next_building():
    global current_building_index
    current_building_index = (current_building_index + 1) % len(available_buildings)


def prev_building():
    global current_building_index
    current_building_index = (current_building_index - 1) % len(available_buildings)


def damage_building(building_data, damage):
    building_data["current_health"] -= damage
    if building_data["health_bar"]:
        building_data["health_bar"].scale_x = max(0, building_data["current_health"] / building_data["max_health"])
    if building_data["current_health"] <= 0:
        destroy(building_data["entity"])
        if building_data["health_bar"]:
            destroy(building_data["health_bar"])
        for d in building_data.get("details", []):
            destroy(d)
        buildings.remove(building_data)


def find_building_by_entity(entity):
    for b in buildings:
        if b["entity"] == entity:
            return b
    return None
