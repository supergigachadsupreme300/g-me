import math

from ursina import Entity, Text, Vec3, camera, color, destroy, load_model, load_texture, mouse, scene, time, window

import game
import inventory
import player as player_mod
import tools
import world
from rendering import DUSK_START, NIGHT_START

TETO_MODEL_PATH = 'model/teto/source/VOICEPEAKTetoPlush.fbx'
TETO_TEXTURE_PATH = 'model/teto/textures/tetoplush_voicepeak-textured.png'

WALK_SPEED = 4.5
LATERAL_SWING = 1.6
JUMP_HEIGHT = 0.55
SWING_SPEED = 2.8
JUMP_SPEED = 9.0

_state = 'idle'  # idle | walking | ended
_pending = False
_elapsed = 0.0
_teto = None
_teto_mesh = None
_ending_ui = None
_saved_camera_parent = None
_saved_camera_position = None
_saved_camera_rotation = None
_saved_mouse_locked = True
_hidden_tools = []
_saved_time_of_day = None
_saved_player_collider = None
_saved_player_gravity = None
_saved_player_jump = None

TETO_SCALE = 10.0
TETO_Y_OFFSET = 0
SUNSET_HOUR = DUSK_START + (NIGHT_START - DUSK_START) * 0.45


def _apply_texture_to_model(mesh, model, texture_path):
    try:
        texture = load_texture(texture_path)
        if texture is None:
            try:
                import os
                tex_folder = os.path.join('model', 'teto', 'textures')
                files = [f for f in os.listdir(tex_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
                if files:
                    texture = load_texture(os.path.join(tex_folder, files[0]))
            except Exception:
                texture = None

        if texture is None:
            return

        try:
            mesh.texture = texture
        except Exception:
            pass
        mesh.color = color.white

        for container in (getattr(model, 'children', []) or []) + (getattr(mesh, 'children', []) or []):
            try:
                container.texture = texture
            except Exception:
                pass
    except Exception as e:
        print(f'Teto texture: {e}')


def _save_and_disable_player_for_cutscene():
    """Temporarily remove player's collider/gravity/jump but keep entity enabled/visible."""
    global _saved_player_collider, _saved_player_gravity, _saved_player_jump
    try:
        _saved_player_collider = getattr(world.player, 'collider', None)
        world.player.collider = None
    except Exception:
        _saved_player_collider = None
    try:
        _saved_player_gravity = getattr(world.player, 'gravity', None)
        if hasattr(world.player, 'gravity'):
            world.player.gravity = 0
    except Exception:
        _saved_player_gravity = None
    try:
        _saved_player_jump = getattr(world.player, 'jump_height', None)
        if hasattr(world.player, 'jump_height'):
            world.player.jump_height = 0
    except Exception:
        _saved_player_jump = None
    world.player.ignore_input = True
    world.player.speed = 0
    try:
        world.player.visible = True
        if hasattr(world, 'player_model') and world.player_model is not None:
            world.player_model.visible = True
    except Exception:
        pass


def _restore_player_after_cutscene():
    global _saved_player_collider, _saved_player_gravity, _saved_player_jump
    try:
        if _saved_player_collider is not None:
            world.player.collider = _saved_player_collider
            _saved_player_collider = None
    except Exception:
        pass
    try:
        if _saved_player_gravity is not None and hasattr(world.player, 'gravity'):
            world.player.gravity = _saved_player_gravity
            _saved_player_gravity = None
    except Exception:
        pass
    try:
        if _saved_player_jump is not None and hasattr(world.player, 'jump_height'):
            world.player.jump_height = _saved_player_jump
            _saved_player_jump = None
    except Exception:
        pass



def is_active():
    return _state in ('walking', 'ended')


def request_happy_ending():
    global _pending
    if _state != 'idle':
        return
    _pending = True


def _hide_tools():
    global _hidden_tools
    _hidden_tools = []
    tool_list = [
        tools.arm, tools.axe, tools.pickaxe, tools.hoe,
        tools.hammer, tools.sword, tools.gun, tools.scythe,
        tools.fertilizer, tools.seed, tools.peashooter_seed,
        tools.mi_hao_hao, tools.wheat, tools.damaged_wheat,
    ]
    for tool in tool_list:
        if tool is not None and tool.visible:
            tool.visible = False
            _hidden_tools.append(tool)


def _restore_tools():
    global _hidden_tools
    for tool in _hidden_tools:
        if tool is not None:
            tool.visible = True
    _hidden_tools = []


def _create_teto(position):
    root = Entity(position=position, rotation_y=0)
    mesh = Entity(parent=root, double_sided=True, unlit=True)
    try:
        model = load_model(TETO_MODEL_PATH)
        if model is None:
            raise ValueError('teto model returned None')
        mesh.model = model
        _apply_texture_to_model(mesh, model, TETO_TEXTURE_PATH)
        mesh.scale = (TETO_SCALE, TETO_SCALE, TETO_SCALE)
        mesh.y = TETO_Y_OFFSET
        mesh._base_y = TETO_Y_OFFSET
        # Simple default: face forward like the player.
        mesh.rotation_y = 0
    except Exception as e:
        print(f'Failed to load Teto model: {e}')
        mesh.model = 'cube'
        mesh.color = color.rgb(220 / 255, 80 / 255, 120 / 255)
        mesh.scale = (0.85, 1.7, 0.85)
        mesh._base_y = 0
    return root, mesh


def _apply_sunset():
    game.set_time_of_day(SUNSET_HOUR)


def _restore_time():
    global _saved_time_of_day
    if _saved_time_of_day is not None:
        game.set_time_of_day(_saved_time_of_day)
        _saved_time_of_day = None


def _road_start_z():
    if world.ROAD_Z_START is not None:
        return world.ROAD_Z_START + 8
    return -42


def _road_end_z():
    if world.ROAD_Z_END is not None:
        return world.ROAD_Z_END - 4
    return 66


def _road_x():
    return world.ROAD_CX if world.ROAD_CX is not None else 14.0


def start_happy_ending():
    global _state, _elapsed, _teto, _teto_mesh, _ending_ui
    global _saved_camera_parent, _saved_camera_position, _saved_camera_rotation, _saved_mouse_locked
    global _saved_time_of_day

    if world.player is None:
        return

    _state = 'walking'
    _elapsed = 0.0
    _saved_time_of_day = game.time_of_day
    window.render_mode = 'default'
    _apply_sunset()

    start_z = _road_start_z()
    road_x = _road_x()

    # Align the player's entity Y so the blocky model's feet rest on the ground.
    # The block model is created with a local root offset (see `create_block_player_model`),
    # stored as `_walk_base_y` on `world.player_model`. Use its negative to position the
    # player entity such that the feet are at y=0.
    model_base_y = getattr(world.player_model, '_walk_base_y', None)
    if model_base_y is not None:
        player_y = -model_base_y
    else:
        # fallback to current player.y (or 1.0) if model info isn't available
        player_y = getattr(world.player, 'y', 1.0)

    world.player.position = Vec3(road_x - 0.8, player_y, start_z)
    world.player.rotation_y = 0

    # Save and reparent camera to scene BEFORE altering player state so camera isn't affected.
    _saved_camera_parent = camera.parent
    _saved_camera_position = Vec3(camera.position)
    _saved_camera_rotation = Vec3(camera.rotation)
    camera.parent = scene
    _saved_mouse_locked = mouse.locked
    mouse.locked = False
    mouse.visible = False

    # Tweak player for cutscene without disabling the entity (prevents hiding).
    _save_and_disable_player_for_cutscene()

    _teto, _teto_mesh = _create_teto(Vec3(road_x + 0.8, player_y, start_z - 1.5))

    _hide_tools()
    inventory.show_message('Happy Ending — đi cùng Teto tới cuối con đường!', 4)

    if _ending_ui is not None:
        destroy(_ending_ui)
        _ending_ui = None


def _show_ending_ui():
    global _ending_ui
    if _ending_ui is not None:
        return
    _ending_ui = Entity(parent=camera.ui)
    Text(
        text='HAPPY ENDING',
        parent=_ending_ui,
        scale=2.5,
        origin=(0, 0),
        y=0.22,
        color=color.rgb(255 / 255, 220 / 255, 80 / 255),
    )
    Text(
        text='Bạn và Teto đã cùng nhau đến cuối con đường!',
        parent=_ending_ui,
        scale=1.2,
        origin=(0, 0),
        y=0.08,
        color=color.white,
    )
    Text(
        text='Nhấn Enter để tiếp tục chơi',
        parent=_ending_ui,
        scale=0.9,
        origin=(0, 0),
        y=-0.08,
        color=color.light_gray,
    )


def end_happy_ending(restore_control=True):
    global _state, _teto, _teto_mesh, _ending_ui, _pending
    global _saved_camera_parent, _saved_camera_position, _saved_camera_rotation

    if _teto is not None:
        destroy(_teto)
        _teto = None
        _teto_mesh = None

    if _ending_ui is not None:
        destroy(_ending_ui)
        _ending_ui = None

    _restore_tools()
    _pending = False
    _state = 'idle'
    _restore_time()

    if not restore_control or world.player is None:
        return

    _restore_player_after_cutscene()
    player_mod.reset_walk_animation(world.player_model)
    world.player.ignore_input = False
    world.player.speed = world.player.base_speed

    if _saved_camera_parent is not None:
        camera.parent = _saved_camera_parent
        camera.position = _saved_camera_position or Vec3(0, 0, 0)
        camera.rotation = _saved_camera_rotation or Vec3(0, 0, 0)
    else:
        camera.parent = world.player.camera_pivot if hasattr(world.player, 'camera_pivot') else world.player
        camera.position = Vec3(0, 0, 0)
        camera.rotation = Vec3(0, 0, 0)

    mouse.locked = _saved_mouse_locked


def update():
    global _state, _elapsed, _pending, _teto, _teto_mesh

    if _pending and _state == 'idle':
        _pending = False
        start_happy_ending()
        return True

    if _state == 'idle':
        return False

    if _state == 'ended':
        _apply_sunset()
        return True

    if world.player is None or _teto is None:
        end_happy_ending()
        return True

    dt = time.dt
    _elapsed += dt

    end_z = _road_end_z()
    road_x = _road_x()

    if world.player.z < end_z:
        world.player.z += WALK_SPEED * dt
        world.player.x = road_x - 0.8
        world.player.rotation_y = 0

        side = math.sin(_elapsed * SWING_SPEED)
        teto_x = road_x + side * LATERAL_SWING
        teto_z = world.player.z - 1.2 + math.cos(_elapsed * SWING_SPEED) * 0.3
        _teto.position = Vec3(teto_x, world.player.y, teto_z)
        # Keep Teto generally facing forward like the player; add a small sway.
        _teto.rotation_y = 10 if side >= 0 else -10

        if _teto_mesh is not None:
            jump = max(0.0, math.sin(_elapsed * JUMP_SPEED)) ** 2 * JUMP_HEIGHT
            base_y = getattr(_teto_mesh, '_base_y', TETO_Y_OFFSET)
            _teto_mesh.y = base_y + jump

        player_mod.animate_walk(world.player_model, _elapsed)
    else:
        player_mod.reset_walk_animation(world.player_model)
        world.player.z = end_z
        _state = 'ended'
        _show_ending_ui()
        inventory.show_message('Chúc mừng! Hành trình đã hoàn thành.', 5)

    mid = (world.player.position + _teto.position) * 0.5
    cam_offset = Vec3(-6, 4.5, -9)
    camera.position = mid + cam_offset
    camera.look_at(mid + Vec3(0, 1.8, 0))

    return True


def handle_input(key):
    if _state == 'ended' and key in ('enter', 'return'):
        end_happy_ending(restore_control=True)
        inventory.show_message('Tiếp tục cuộc phiêu lưu!', 2)
        return True
    if _state == 'walking':
        return True
    return False
