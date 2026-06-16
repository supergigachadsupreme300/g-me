"""
Sad Ending cutscene — single cinematic scene.

Wife and groom ride a wagon south along the road.
Camera tracks alongside, falling further behind as they depart.
Ends with a Quit / Restart screen.
"""

import os, sys, traceback
from ursina import (
    Entity, Text, Button, Vec3, color,
    camera, scene, mouse, time, invoke, destroy, curve, application,
    load_model, load_texture, window
)
import math
import game
import inventory
import player as player_mod
import tools
from rendering import DUSK_START, NIGHT_START
import world
import tools


# ── helpers ──────────────────────────────────────────────────────────────────

def _restart():
    os.execv(sys.executable, [sys.executable] + sys.argv)


def _hide_hud():
    """Hide every gameplay HUD element. Nothing is restored — game ends."""
    try:
        import rendering as _rend
        import inventory as _inv
        for el in (
            _rend.player_hp_text, _rend.player_stamina_text,
            _rend.player_money_text, _rend.quest_text,
            _rend.time_text, _rend.ammo_text, _rend.mobspawner_text,
        ):
            if el is not None:
                el.enabled = False
        for el in (_inv.inventory_text, _inv.message_text):
            if el is not None:
                el.enabled = False
        for t in (
            tools.arm, tools.axe, tools.pickaxe, tools.hoe,
            tools.hammer, tools.sword, tools.gun, tools.scythe,
            tools.fertilizer, tools.seed, tools.peashooter_seed,
            tools.wheat, tools.damaged_wheat,
        ):
            if t is not None:
                t.visible = False
    except Exception:
        traceback.print_exc()


def _look_at(target: Vec3):
    try:
        camera.look_at(target)
        camera.rotation_z = 0
    except Exception:
        traceback.print_exc()


# ── manager ──────────────────────────────────────────────────────────────────

class _CutsceneManager:

    def __init__(self):
        self._active        = False
        self._timer         = 0.0
        self._duration      = 0.0
        self._spawned       = []
        self._overlay       = None
        self._done          = False
        self._cam_update_fn = None   # called every frame with current timer value

    # public ──────────────────────────────────────────────────────────────────

    @property
    def is_active(self):
        return self._active

    def play(self, duration, fade_in=1.5, fade_out=2.0, on_complete=None):
        if self._active:
            self._cleanup()

        self._active        = True
        self._timer         = 0.0
        self._duration      = duration
        self._fade_out      = fade_out
        self._on_complete   = on_complete
        self._done          = False
        self._spawned       = []
        self._cam_update_fn = None

        self._build_overlay()
        self._freeze()
        self._detach_camera()

        if fade_in > 0:
            self._overlay.enabled = True
            self._overlay.color   = color.black
            self._overlay.animate_color(color.rgba(0, 0, 0, 0), duration=fade_in)
            invoke(lambda: setattr(self._overlay, 'enabled', False), delay=fade_in + 0.05)

    def update(self):
        if not self._active:
            return
        self._timer += time.dt

        # Per-frame camera tracking
        if self._cam_update_fn is not None:
            try:
                self._cam_update_fn(self._timer)
            except Exception:
                traceback.print_exc()

        remaining = self._duration - self._timer
        if remaining <= self._fade_out and not getattr(self, '_fading', False):
            self._fading = True
            self._overlay.enabled = True
            self._overlay.color   = color.rgba(0, 0, 0, 0)
            self._overlay.animate_color(color.black, duration=self._fade_out)

        if self._timer >= self._duration and not self._done:
            self._done          = True
            self._active        = False
            self._cam_update_fn = None
            self._cleanup_spawned()
            if self._on_complete:
                try:
                    self._on_complete()
                except Exception:
                    traceback.print_exc()

    def stop(self):
        """Emergency abort — restores player control."""
        self._active        = False
        self._done          = True
        self._cam_update_fn = None
        self._cleanup_spawned()
        self._restore()

    def spawn(self, **kwargs):
        e = Entity(**kwargs)
        self._spawned.append(e)
        return e

    # internal ────────────────────────────────────────────────────────────────

    def _build_overlay(self):
        if self._overlay is None:
            self._overlay = Entity(
                parent=camera.ui,
                model='quad',
                scale=(2, 1),
                color=color.black,
                z=-0.01,
                enabled=False,
            )
        self._fading = False

    def _freeze(self):
        try:
            world.player.enabled = False
        except Exception:
            pass
        mouse.locked  = False
        mouse.visible = False

    def _detach_camera(self):
        try:
            camera.parent   = scene
            camera.rotation = Vec3(0, 0, 0)
        except Exception:
            traceback.print_exc()

    def _restore(self):
        try:
            camera.parent   = world.player.camera_pivot
            camera.position = Vec3(0, 0, 0)
            camera.rotation = Vec3(0, 0, 0)
        except Exception:
            pass
        try:
            world.player.enabled = True
        except Exception:
            pass
        mouse.locked  = True
        mouse.visible = False
        if self._overlay:
            self._overlay.enabled = False

    def _cleanup_spawned(self):
        for e in self._spawned:
            try:
                destroy(e)
            except Exception:
                pass
        self._spawned.clear()

    def _cleanup(self):
        self._active        = False
        self._cam_update_fn = None
        self._cleanup_spawned()


manager = _CutsceneManager()


# ── sad ending ────────────────────────────────────────────────────────────────

_fired = False


def play_sad_ending():
    global _fired
    _fired = True
    print('[SadEnding] starting')

    # Road runs along Z at x=14 (north-south). Wagon travels south (decreasing Z).
    road_x   = 14.0
    start_z  = 25.0
    end_z    = -35.0
    ride_dur = 8.0
    total    = 11.0   # ride (8s) + 2s static distance shot + 1s buffer for fade

    delta_z  = end_z - start_z   # -60

    # 1. Hide all gameplay HUD
    _hide_hud()

    # 2. Start manager — reparents camera to scene, sets up fade overlay
    manager.play(
        duration=total,
        fade_in=1.5,
        fade_out=2.0,
        on_complete=_show_end_screen,
    )

    # 3. Letterbox bars — 12% screen height, fade in with the opening
    bar_h = 0.12
    bar_t = manager.spawn(
        parent=camera.ui, model='quad',
        color=color.rgba(0, 0, 0, 0),
        scale=(2, bar_h),
        position=(0, 0.5 - bar_h * 0.5, 0),
        z=-0.008,
    )
    bar_b = manager.spawn(
        parent=camera.ui, model='quad',
        color=color.rgba(0, 0, 0, 0),
        scale=(2, bar_h),
        position=(0, -0.5 + bar_h * 0.5, 0),
        z=-0.008,
    )
    bar_t.animate_color(color.black, duration=1.5)
    bar_b.animate_color(color.black, duration=1.5)

    # 4. Camera opening position — behind and to the right of wagon start
    #    Camera is at x=road_x+5 (east side), slightly north of wagon (z=start_z+3)
    try:
        camera.position = Vec3(road_x + 5, 2.8, start_z + 3)
        camera.rotation = Vec3(0, 0, 0)
        invoke(lambda: _look_at(Vec3(road_x, 1.4, start_z)), delay=0.05)
    except Exception:
        traceback.print_exc()

    # 5. Spawn wagon — long axis along Z (direction of travel)
    wx, wy, wz = road_x, 0.0, start_z

    bed = manager.spawn(
        model='cube', color=color.rgb(85/255, 52/255, 22/255),
        scale=(1.8, 0.30, 3.6),
        position=(wx, wy + 0.65, wz), unlit=True)

    canopy = manager.spawn(
        model='cube', color=color.rgb(210/255, 195/255, 160/255),
        scale=(1.6, 0.08, 3.4),
        position=(wx, wy + 1.40, wz), unlit=True)

    # Front and back endboards (span wagon width, face the road direction)
    board_f = manager.spawn(
        model='cube', color=color.rgb(70/255, 42/255, 16/255),
        scale=(1.8, 0.70, 0.18),
        position=(wx, wy + 1.0, wz - 1.65), unlit=True)

    board_b = manager.spawn(
        model='cube', color=color.rgb(70/255, 42/255, 16/255),
        scale=(1.8, 0.70, 0.18),
        position=(wx, wy + 1.0, wz + 1.65), unlit=True)

    # 4 wheels — at sides (X) and front/back (Z corners)
    wheels = []
    for offx, offz in ((-0.9, -1.5), (0.9, -1.5), (-0.9, 1.5), (0.9, 1.5)):
        wheels.append(manager.spawn(
            model='cube', color=color.rgb(45/255, 35/255, 20/255),
            scale=(0.20, 0.80, 0.80),
            position=(wx + offx, wy + 0.40, wz + offz), unlit=True))

    all_pieces = [bed, canopy, board_f, board_b] + wheels

    # 6. Groom NPC — seated on wagon, right side (camera-facing side)
    groom_body = manager.spawn(
        model='cube', color=color.rgb(28/255, 30/255, 65/255),
        scale=(0.48, 0.82, 0.32),
        position=(wx + 0.35, wy + 1.05, wz), unlit=True)
    groom_head = manager.spawn(
        model='cube', color=color.rgb(220/255, 178/255, 132/255),
        scale=(0.40, 0.40, 0.40),
        position=(wx + 0.35, wy + 1.65, wz), unlit=True)

    # 7. Wife — teleport onto wagon left side, face toward camera (+X direction)
    _place_wife(wx - 0.3, wy + 1.05, wz)

    # 8. Animate all pieces south
    for piece in all_pieces:
        piece.animate_position(
            Vec3(piece.x, piece.y, piece.z + delta_z),
            duration=ride_dur, curve=curve.linear)
    groom_body.animate_position(
        Vec3(groom_body.x, groom_body.y, groom_body.z + delta_z),
        duration=ride_dur, curve=curve.linear)
    groom_head.animate_position(
        Vec3(groom_head.x, groom_head.y, groom_head.z + delta_z),
        duration=ride_dur, curve=curve.linear)
    _animate_wife(delta_z, ride_dur)

    # 9. Per-frame camera tracking
    #    0–ride_dur: follow wagon with increasing lag → wagon shrinks into distance
    #    after ride_dur: hold final frame (wagon small and far)
    def _cam_track(t):
        if t >= ride_dur:
            return   # hold last frame; fade-out overlay will cover
        t_norm  = t / ride_dur                       # 0 → 1
        wagon_z = start_z + delta_z * t_norm         # 25 → -35
        lag_z   = 3.0 + 22.0 * t_norm               # 3 behind → 25 behind
        cam_x   = road_x + 5.0
        cam_y   = 2.8 + 0.4 * t_norm                # 2.8 → 3.2 (gentle rise)
        cam_z   = wagon_z + lag_z
        look_y  = 1.4 - 0.4 * t_norm                # 1.4 → 1.0 (look lower at distance)
        camera.position  = Vec3(cam_x, cam_y, cam_z)
        camera.look_at(Vec3(road_x, look_y, wagon_z))
        camera.rotation_z = 0

    manager._cam_update_fn = _cam_track


def _place_wife(x, y, z):
    try:
        if world.wife_entity:
            world.wife_entity.position  = Vec3(x, y, z)
            world.wife_entity.rotation_y = 180   # face +Z (90° left from previous)
    except Exception:
        traceback.print_exc()


def _animate_wife(delta_z, duration):
    try:
        if world.wife_entity:
            w = world.wife_entity
            w.animate_position(
                Vec3(w.x, w.y, w.z + delta_z),
                duration=duration, curve=curve.linear)
    except Exception:
        traceback.print_exc()


def _show_end_screen():
    print('[SadEnding] showing end screen')
    try:
        # Disable the cutscene fade overlay so it no longer covers the screen
        if manager._overlay is not None:
            manager._overlay.enabled = False

        # Full black backdrop
        Entity(parent=camera.ui, model='quad',
               scale=(2, 1), color=color.black, z=-0.010)

        # Central card — slightly off-black for depth
        Entity(parent=camera.ui, model='quad',
               scale=(1.15, 0.76),
               color=color.rgba(18/255, 15/255, 28/255, 0.96),
               z=-0.011)

        # Title
        Text(parent=camera.ui,
             text='KẾT THÚC ĐAU BUỒN',
             position=(0, 0.22), origin=(0, 0),
             scale=2.6,
             color=color.rgb(255/255, 210/255, 100/255),
             z=-0.012)

        # Thin separator line
        Entity(parent=camera.ui, model='quad',
               scale=(0.72, 0.004), position=(0, 0.135),
               color=color.rgba(255/255, 210/255, 100/255, 0.45),
               z=-0.012)

        # Quote
        Text(parent=camera.ui,
             text='"Skibidi.\ndop dop."',
             position=(0, 0.025), origin=(0, 0),
             scale=1.15,
             color=color.rgba(220/255, 208/255, 185/255, 0.92),
             z=-0.012)

        # Buttons
        Button(parent=camera.ui, text='Chơi lại',
               scale=(0.24, 0.092), position=(-0.145, -0.21),
               color=color.rgb(30/255, 72/255, 30/255),
               highlight_color=color.rgb(50/255, 115/255, 50/255),
               z=-0.012, on_click=_restart)

        Button(parent=camera.ui, text='Thoát',
               scale=(0.24, 0.092), position=(0.145, -0.21),
               color=color.rgb(72/255, 28/255, 28/255),
               highlight_color=color.rgb(115/255, 45/255, 45/255),
               z=-0.012, on_click=application.quit)

        mouse.locked  = False
        mouse.visible = True
    except Exception:
        traceback.print_exc()


# ---------------------------------------------------------------------------
# Backwards-compatible wrappers for the "happy ending" cutscene that used to
# live in `cutscene.py`. If `cutscene.py` is present we delegate to it so other
# modules that call `cutscene.request_happy_ending()`, `cutscene.update()` and
# `cutscene.handle_input()` continue to work while the happy-ending logic is
# consolidated here over time.
# ---------------------------------------------------------------------------
### Happy-ending (Teto) cutscene implementation merged from cutscene.py ###

# Teto model + appearance
TETO_MODEL_PATH = 'model/teto/source/VOICEPEAKTetoPlush.fbx'
TETO_TEXTURE_PATH = 'model/teto/textures/tetoplush_voicepeak-textured.png'

WALK_SPEED = 4.5
LATERAL_SWING = 1.6
JUMP_HEIGHT = 0.55
SWING_SPEED = 2.8
JUMP_SPEED = 9.0

_state = 'idle'  # idle | walking | facing | celebrating | ended
_pending = False
_elapsed = 0.0
_phase_timer = 0.0
_jump_count = 0
_hearts = []
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
_sun_entity = None
_saved_fog_density = None

TETO_SCALE = 10.0
TETO_Y_OFFSET = -1
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
        tools.corn_seed, tools.corn, tools.potato,
        tools.damaged_corn, tools.damaged_potato,
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
    # spawn a distant, large yellow 'sun' cube at the end of the road so it's visible
    global _sun_entity, _saved_fog_density
    # If we've already created the sun, do nothing (prevents re-creating/blinking)
    try:
        if _sun_entity is not None:
            return
    except Exception:
        pass
    try:
        # reduce fog so the sun is more visible (save previous value if not saved)
        if _saved_fog_density is None:
            _saved_fog_density = getattr(scene, 'fog_density', None)
        try:
            scene.fog_density = 0.002
        except Exception:
            pass
        road_x = _road_x()
        sun_z = _road_end_z() + 60
        # place high above ground and large enough to be seen
        _sun_entity = Entity(parent=scene, model='cube', color=color.rgb(255/255, 220/255, 60/255),
                             scale=(80, 80, 80), position=Vec3(road_x + 0.0, 0, sun_z + 200.0), unlit=True)
    except Exception:
        pass


def _restore_time():
    global _saved_time_of_day
    if _saved_time_of_day is not None:
        game.set_time_of_day(_saved_time_of_day)
        _saved_time_of_day = None


def _road_start_z():
    if world.ROAD_Z_START is not None:
        return world.ROAD_Z_START + 40
    return -42


def _road_end_z():
    start = _road_start_z()
    full_end = world.ROAD_Z_END - 4 if world.ROAD_Z_END is not None else 66
    # shorten the walking distance: use half of the previous half-distance
    # (previously 0.5 → now 0.25 of the full span) to reduce walk time
    return start + (full_end - start) * 0.5


def _face_each_other():
    if world.player is None or _teto is None:
        return
    road_x = _road_x()
    z = world.player.z
    world.player.position = Vec3(road_x - 0.9, world.player.y, z)
    world.player.rotation_y = 90
    _teto.position = Vec3(road_x + 0.9, world.player.y, z)
    _teto.rotation_y = -90
    player_mod.reset_walk_animation(world.player_model)


def _spawn_heart(position):
    heart = Text(
        text='♥',
        parent=scene,
        position=position + Vec3(0, 2.2, 0),
        scale=3,
        color=color.rgb(255 / 255, 80 / 255, 120 / 255),
        billboard=True,
        origin=(0, 0),
    )
    heart.animate_position(position + Vec3(0, 3.4, 0), duration=0.9, curve=curve.out_expo)
    heart.animate_scale(4.5, duration=0.9, curve=curve.out_expo)
    _hearts.append(heart)
    invoke(lambda: _destroy_heart(heart), delay=1.0)


def _destroy_heart(heart):
    try:
        destroy(heart)
    except Exception:
        pass
    if heart in _hearts:
        _hearts.remove(heart)


def _clear_hearts():
    for heart in list(_hearts):
        _destroy_heart(heart)


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
    _phase_timer = 0.0
    _jump_count = 0
    _clear_hearts()
    _saved_time_of_day = game.time_of_day
    window.render_mode = 'default'
    _apply_sunset()

    start_z = _road_start_z()
    road_x = _road_x()

    model_base_y = getattr(world.player_model, '_walk_base_y', None)
    if model_base_y is not None:
        player_y = -model_base_y
    else:
        player_y = getattr(world.player, 'y', 1.0)

    world.player.position = Vec3(road_x - 0.8, player_y, start_z)
    world.player.rotation_y = 0

    _saved_camera_parent = camera.parent
    _saved_camera_position = Vec3(camera.position)
    _saved_camera_rotation = Vec3(camera.rotation)
    camera.parent = scene
    _saved_mouse_locked = mouse.locked
    mouse.locked = False
    mouse.visible = False

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


def end_happy_ending(restore_control=False):
    global _state, _teto, _teto_mesh, _ending_ui, _pending
    global _saved_camera_parent, _saved_camera_position, _saved_camera_rotation

    _clear_hearts()

    if _teto is not None:
        destroy(_teto)
        _teto = None
        _teto_mesh = None

    if _ending_ui is not None:
        destroy(_ending_ui)
        _ending_ui = None

    # remove the distant sun and restore fog density only when restoring control
    global _sun_entity, _saved_fog_density
    if restore_control:
        try:
            if _sun_entity is not None:
                destroy(_sun_entity)
                _sun_entity = None
        except Exception:
            pass
        try:
            if _saved_fog_density is not None:
                scene.fog_density = _saved_fog_density
                _saved_fog_density = None
        except Exception:
            pass

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


def happy_update():
    global _state, _elapsed, _pending, _teto, _teto_mesh, _phase_timer, _jump_count

    if _pending and _state == 'idle':
        _pending = False
        start_happy_ending()
        return True

    if _state == 'idle':
        return False

    if _state == 'ended':
        # ensure sunset/sun is applied once when entering the ended state
        try:
            if _sun_entity is None:
                _apply_sunset()
        except Exception:
            _apply_sunset()
        return True

    if world.player is None or _teto is None:
        end_happy_ending()
        return True

    dt = time.dt
    _elapsed += dt
    end_z = _road_end_z()
    road_x = _road_x()

    if _state == 'walking':
        if world.player.z < end_z:
            world.player.z += WALK_SPEED * dt
            world.player.x = road_x - 1.0
            world.player.rotation_y = 0

            side = math.sin(_elapsed * SWING_SPEED)
            teto_x = road_x + side * LATERAL_SWING
            teto_z = world.player.z - 1.2 + math.cos(_elapsed * SWING_SPEED) * 0.3
            _teto.position = Vec3(teto_x, world.player.y, teto_z)
            _teto.rotation_y = 10 if side >= 0 else -10

            if _teto_mesh is not None:
                jump = max(0.0, math.sin(_elapsed * JUMP_SPEED)) ** 2 * JUMP_HEIGHT
                base_y = getattr(_teto_mesh, '_base_y', TETO_Y_OFFSET)
                _teto_mesh.y = base_y + jump

            player_mod.animate_walk(world.player_model, _elapsed)
        else:
            world.player.z = end_z
            player_mod.reset_walk_animation(world.player_model)
            _face_each_other()
            _state = 'facing'
            _phase_timer = 0.0

    elif _state == 'facing':
        _phase_timer += dt
        if _phase_timer >= 0.8:
            _state = 'celebrating'
            _phase_timer = 0.0
            _jump_count = 0

    elif _state == 'celebrating':
        _phase_timer += dt
        jump_phase = _phase_timer * 8.0
        jump_height = max(0.0, math.sin(jump_phase)) ** 2 * 0.7
        if _teto_mesh is not None:
            base_y = getattr(_teto_mesh, '_base_y', TETO_Y_OFFSET)
            _teto_mesh.y = base_y + jump_height

        jump_marks = (0.35, 1.15)
        for mark in jump_marks:
            if _jump_count < len(jump_marks) and _phase_timer >= mark and _phase_timer - dt < mark:
                _jump_count += 1
                _spawn_heart(_teto.position)

        if _phase_timer >= 2.4:
            if _teto_mesh is not None:
                _teto_mesh.y = getattr(_teto_mesh, '_base_y', TETO_Y_OFFSET)
            _state = 'ended'
            _show_ending_ui()
            inventory.show_message('Chúc mừng! Hành trình đã hoàn thành.', 5)

    mid = (world.player.position + _teto.position) * 0.5
    # Camera behavior: while walking, use trailing elevated view; after walking
    # completes (facing/celebrating/ended), switch to a horizontal side view
    if _state == 'walking':
        cam_offset = Vec3(-6, 4.5, -9)
        camera.position = mid + cam_offset
        camera.look_at(mid + Vec3(0, 1.8, 0))
    else:
        # side-on horizontal view: place camera to the east of the road, level height
        road_x = _road_x()
        # keep camera at similar vertical eye height and align Z with midpoint
        camera.position = Vec3(road_x + 0.0, mid.y + 1.6, mid.z - 4.0)
        # rotate camera 90 degrees around Y so view is horizontal and aligns players vertically
        try:
            camera.rotation = Vec3(0, 0, 0)
        except Exception:
            # fallback to look_at if direct rotation fails
            camera.look_at(mid + Vec3(0, 1.4, 0))
            camera.rotation_z = 0

    return True


def handle_input(key):
    if _state == 'ended' and key in ('enter', 'return'):
        end_happy_ending(restore_control=True)
        inventory.show_message('Tiếp tục cuộc phiêu lưu!', 2)
        return True
    if _state in ('walking', 'facing', 'celebrating'):
        return True
    return False

# Replace the previous delegation wrappers with the internal implementation
def update():
    return happy_update()

# ── intro cutscene (xe hơi đi vào map) ───────────────────────────────────────

def play_intro_cutscene(on_complete=None):
    print('[IntroCutscene] Bắt đầu lái xe vào bản đồ')
    road_x   = 14.0
    start_z  = -55.0
    end_z    = -5.0
    ride_dur = 4.5
    total    = ride_dur + 1.5

    # Khởi tạo camera và hiệu ứng mờ dần
    manager.play(duration=total, fade_in=1.5, fade_out=1.5, on_complete=on_complete)

    # Góc CAMERA CINEMATIC
    try:
        camera.position = Vec3(road_x - 12, 2.2, end_z)
        camera.rotation = Vec3(0, 0, 0)
        invoke(lambda: camera.look_at(Vec3(road_x, 1.0, start_z + 15)), delay=0.05)
        camera.animate_position(
            Vec3(road_x - 9, 2.5, end_z - 3),
            duration=ride_dur,
            curve=curve.linear
        )
    except Exception:
        traceback.print_exc()

    wx, wy, wz = road_x, 0.0, start_z
    delta_z = end_z - start_z

    car = manager.spawn(
        model='model/car/sedan.obj',
        texture='model/car/colormap.png',
        scale=2.0,
        position=(wx, wy, wz),
        rotation=(0, 0, 0),
        unlit=True
    )

    car.animate_position(
        Vec3(car.x, car.y, car.z + delta_z),
        duration=ride_dur, curve=curve.linear
    )