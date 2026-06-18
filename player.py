import math

from ursina import Entity, color
from ursina.prefabs.first_person_controller import FirstPersonController

SKIN = color.rgb(255 / 255, 205 / 255, 148 / 255)
SHIRT = color.rgb(13 / 255, 105 / 255, 172 / 255)
PANTS = color.rgb(40 / 255, 127 / 255, 71 / 255)
SHOES = color.rgb(60 / 255, 60 / 255, 60 / 255)
HAIR = color.rgb(62 / 255, 39 / 255, 35 / 255)
EYE = color.black
BELT = color.rgb(99 / 255, 95 / 255, 98 / 255)
LEG_SCALE = 1.5


def _block(parent, position, scale, block_color):
    return Entity(
        model='cube',
        color=block_color,
        position=position,
        scale=scale,
        parent=parent,
    )


def _leg_y_positions():
    shoe_h = 0.2 * LEG_SCALE
    lower_h = 0.3 * LEG_SCALE
    upper_h = 0.3 * LEG_SCALE
    shoe_y = shoe_h / 2
    lower_y = shoe_h + lower_h / 2
    upper_y = shoe_h + lower_h + upper_h / 2
    leg_top = upper_y + upper_h / 2
    return shoe_h, lower_h, upper_h, shoe_y, lower_y, upper_y, leg_top


def _upper_body_y(leg_top):
    """Place torso and head above the legs (no overlap with thighs)."""
    return {
        'belt': leg_top - 0.07,
        'torso': leg_top + 0.15,
        'arm_upper': leg_top + 0.15,
        'arm_lower': leg_top - 0.20,
        'hand': leg_top - 0.45,
        'neck': leg_top + 0.43,
        'head': leg_top + 0.70,
        'hair_top': leg_top + 0.97,
        'hair_back': leg_top + 0.80,
        'hair_side': leg_top + 0.75,
        'eye': leg_top + 0.67,
        'mouth': leg_top + 0.57,
    }


def create_block_player_model(parent):
    """Build a blocky humanoid — longer legs with upper body stacked above."""
    root = Entity(parent=parent, position=(0, -1, 0))
    shoe_h, lower_h, upper_h, shoe_y, lower_y, upper_y, leg_top = _leg_y_positions()
    body = _upper_body_y(leg_top)

    # Feet / shoes (add colliders so they rest on ground during cutscenes)
    left_shoe = _block(root, (-0.25, shoe_y, 0.05), (0.42, shoe_h, 0.5), SHOES)
    right_shoe = _block(root, (0.25, shoe_y, 0.05), (0.42, shoe_h, 0.5), SHOES)
    try:
        left_shoe.collider = 'box'
        right_shoe.collider = 'box'
    except Exception:
        pass

    # Lower legs
    root.left_lower_leg = _block(root, (-0.25, lower_y, 0), (0.4, lower_h, 0.42), PANTS)
    root.right_lower_leg = _block(root, (0.25, lower_y, 0), (0.4, lower_h, 0.42), PANTS)

    # Upper legs
    root.left_upper_leg = _block(root, (-0.25, upper_y, 0), (0.42, upper_h, 0.44), PANTS)
    root.right_upper_leg = _block(root, (0.25, upper_y, 0), (0.42, upper_h, 0.44), PANTS)

    # Torso — sits on top of legs
    _block(root, (0, body['torso'], 0), (0.88, 0.45, 0.46), SHIRT)
    _block(root, (0, body['belt'], 0), (0.9, 0.12, 0.48), BELT)

    # Arms
    root.left_upper_arm = _block(root, (-0.62, body['arm_upper'], 0), (0.36, 0.45, 0.38), SHIRT)
    root.right_upper_arm = _block(root, (0.62, body['arm_upper'], 0), (0.36, 0.45, 0.38), SHIRT)
    root.left_lower_arm = _block(root, (-0.62, body['arm_lower'], 0), (0.34, 0.35, 0.36), SKIN)
    root.right_lower_arm = _block(root, (0.62, body['arm_lower'], 0), (0.34, 0.35, 0.36), SKIN)
    _block(root, (-0.62, body['hand'], 0), (0.32, 0.3, 0.34), SKIN)
    _block(root, (0.62, body['hand'], 0), (0.32, 0.3, 0.34), SKIN)

    # Neck & head
    _block(root, (0, body['neck'], 0), (0.3, 0.12, 0.3), SKIN)
    _block(root, (0, body['head'], 0), (0.5, 0.5, 0.5), SKIN)

    # Hair (top + sides)
    _block(root, (0, body['hair_top'], 0), (0.52, 0.14, 0.52), HAIR)
    _block(root, (0, body['hair_back'], -0.22), (0.48, 0.38, 0.12), HAIR)
    _block(root, (-0.22, body['hair_side'], 0), (0.1, 0.35, 0.42), HAIR)
    _block(root, (0.22, body['hair_side'], 0), (0.1, 0.35, 0.42), HAIR)

    # Face details
    _block(root, (-0.12, body['eye'], 0.26), (0.08, 0.08, 0.04), EYE)
    _block(root, (0.12, body['eye'], 0.26), (0.08, 0.08, 0.04), EYE)
    _block(root, (0, body['mouth'], 0.26), (0.1, 0.06, 0.04), color.rgb(200 / 255, 120 / 255, 120 / 255))

    root._walk_base_y = root.y
    return root


def reset_walk_animation(model_root):
    if model_root is None:
        return
    for attr in (
        'left_upper_leg', 'right_upper_leg', 'left_lower_leg', 'right_lower_leg',
        'left_upper_arm', 'right_upper_arm', 'left_lower_arm', 'right_lower_arm',
    ):
        part = getattr(model_root, attr, None)
        if part is not None:
            part.rotation_x = 0
    if hasattr(model_root, '_walk_base_y'):
        model_root.y = model_root._walk_base_y


def animate_walk(model_root, elapsed, step_rate=10.0, swing=32.0):
    """Swing blocky limbs for a simple walk cycle."""
    if model_root is None:
        return
    phase = math.sin(elapsed * step_rate)
    opposite = -phase

    for leg, value in (
        (getattr(model_root, 'left_upper_leg', None), phase),
        (getattr(model_root, 'right_upper_leg', None), opposite),
        (getattr(model_root, 'left_lower_leg', None), max(0.0, phase) * 0.55),
        (getattr(model_root, 'right_lower_leg', None), max(0.0, opposite) * 0.55),
        (getattr(model_root, 'left_upper_arm', None), opposite * 0.65),
        (getattr(model_root, 'right_upper_arm', None), phase * 0.65),
        (getattr(model_root, 'left_lower_arm', None), max(0.0, opposite) * 0.35),
        (getattr(model_root, 'right_lower_arm', None), max(0.0, phase) * 0.35),
    ):
        if leg is not None:
            leg.rotation_x = value * swing

    base_y = getattr(model_root, '_walk_base_y', model_root.y)
    model_root.y = base_y + abs(math.sin(elapsed * step_rate)) * 0.05


def create_player_display(world_position=(0, 1, 0), rotation_y=0):
    """Spawn a static block player model for preview (e.g. inside the house)."""
    display = Entity(position=world_position, rotation_y=rotation_y)
    create_block_player_model(display)
    return display


def create_player():
    player = FirstPersonController()
    player.cursor.visible = False
    player.hp = 100
    player.max_hp = 100
    player.stamina = 1000
    player.max_stamina = 1000
    player.base_speed = 5.0
    player.sprint_speed_multiplier = 3.0
    player.stamina_regen_rate = 25.0
    player.stamina_sprint_cost = 35.0
    player.is_sprinting = False
    player.money = 10000000000
    player_model = create_block_player_model(player)
    return player, player_model
