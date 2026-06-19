"""
Sad Ending cutscene — single cinematic scene.

Wife and groom ride a wagon south along the road.
Camera tracks alongside, falling further behind as they depart.
Ends with a Quit / Restart screen.
"""

import os, sys, traceback
from ursina import (
    Entity, Text, Button, Vec3, color,
    camera, scene, mouse, time, invoke, destroy, curve, application
)
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
_good_fired = False


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


def play_good_ending():
    global _good_fired
    _good_fired = True
    print('[GoodEnding] starting')

    road_x   = 14.0
    start_z  = 25.0
    end_z    = -35.0
    ride_dur = 8.0
    total    = 11.0

    delta_z  = end_z - start_z

    _hide_hud()

    manager.play(
        duration=total,
        fade_in=1.5,
        fade_out=2.0,
        on_complete=_show_good_end_screen,
    )

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

    try:
        camera.position = Vec3(road_x + 5, 2.8, start_z + 3)
        camera.rotation = Vec3(0, 0, 0)
        invoke(lambda: _look_at(Vec3(road_x, 1.4, start_z)), delay=0.05)
    except Exception:
        traceback.print_exc()

    wx, wy, wz = road_x, 0.0, start_z

    bed = manager.spawn(
        model='cube', color=color.rgb(85/255, 52/255, 22/255),
        scale=(1.8, 0.30, 3.6),
        position=(wx, wy + 0.65, wz), unlit=True)

    canopy = manager.spawn(
        model='cube', color=color.rgb(210/255, 195/255, 160/255),
        scale=(1.6, 0.08, 3.4),
        position=(wx, wy + 1.40, wz), unlit=True)

    board_f = manager.spawn(
        model='cube', color=color.rgb(70/255, 42/255, 16/255),
        scale=(1.8, 0.70, 0.18),
        position=(wx, wy + 1.0, wz - 1.65), unlit=True)

    board_b = manager.spawn(
        model='cube', color=color.rgb(70/255, 42/255, 16/255),
        scale=(1.8, 0.70, 0.18),
        position=(wx, wy + 1.0, wz + 1.65), unlit=True)

    wheels = []
    for offx, offz in ((-0.9, -1.5), (0.9, -1.5), (-0.9, 1.5), (0.9, 1.5)):
        wheels.append(manager.spawn(
            model='cube', color=color.rgb(45/255, 35/255, 20/255),
            scale=(0.20, 0.80, 0.80),
            position=(wx + offx, wy + 0.40, wz + offz), unlit=True))

    all_pieces = [bed, canopy, board_f, board_b] + wheels

    groom_body = manager.spawn(
        model='cube', color=color.rgb(28/255, 30/255, 65/255),
        scale=(0.48, 0.82, 0.32),
        position=(wx + 0.35, wy + 1.05, wz), unlit=True)
    groom_head = manager.spawn(
        model='cube', color=color.rgb(220/255, 178/255, 132/255),
        scale=(0.40, 0.40, 0.40),
        position=(wx + 0.35, wy + 1.65, wz), unlit=True)

    _place_wife(wx - 0.3, wy + 1.05, wz)

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

    def _cam_track(t):
        if t >= ride_dur:
            return
        t_norm  = t / ride_dur
        wagon_z = start_z + delta_z * t_norm
        lag_z   = 3.0 + 22.0 * t_norm
        cam_x   = road_x + 5.0
        cam_y   = 2.8 + 0.4 * t_norm
        cam_z   = wagon_z + lag_z
        look_y  = 1.4 - 0.4 * t_norm
        camera.position  = Vec3(cam_x, cam_y, cam_z)
        camera.look_at(Vec3(road_x, look_y, wagon_z))
        camera.rotation_z = 0

    manager._cam_update_fn = _cam_track


def _show_good_end_screen():
    print('[GoodEnding] showing end screen')
    try:
        if manager._overlay is not None:
            manager._overlay.enabled = False

        Entity(parent=camera.ui, model='quad',
               scale=(2, 1), color=color.black, z=-0.010)

        Entity(parent=camera.ui, model='quad',
               scale=(1.15, 0.76),
               color=color.rgba(20/255, 10/255, 35/255, 0.96),
               z=-0.011)

        Text(parent=camera.ui,
             text='KẾT THÚC HẠNH PHÚC',
             position=(0, 0.22), origin=(0, 0),
             scale=2.6,
             color=color.rgb(255/255, 200/255, 220/255),
             z=-0.012)

        Entity(parent=camera.ui, model='quad',
               scale=(0.72, 0.004), position=(0, 0.135),
               color=color.rgba(255/255, 200/255, 220/255, 0.45),
               z=-0.012)

        Text(parent=camera.ui,
             text='"Chúc mừng hôn nhân!\nSống hạnh phúc mãi mãi."',
             position=(0, 0.025), origin=(0, 0),
             scale=1.15,
             color=color.rgba(220/255, 208/255, 220/255, 0.92),
             z=-0.012)

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
