"""
Sad Ending cutscene — single scene.

Wife and another man ride a wagon down the road while the camera watches.
Ends with a Quit / Restart screen.
"""

import os, sys, traceback
from ursina import (
    Entity, Text, Button, Vec3, color,
    camera, scene, mouse, time, invoke, destroy, curve, application
)
import world


# ── helpers ──────────────────────────────────────────────────────────────────

def _restart():
    os.execv(sys.executable, [sys.executable] + sys.argv)


# ── manager ──────────────────────────────────────────────────────────────────

class _CutsceneManager:

    def __init__(self):
        self._active   = False
        self._timer    = 0.0
        self._duration = 0.0
        self._spawned  = []
        self._overlay  = None
        self._done     = False   # True once the sequence has fired on_complete

    # public ──────────────────────────────────────────────────────────────────

    @property
    def is_active(self):
        return self._active

    def play(self, duration, fade_in=1.5, fade_out=2.0, on_complete=None):
        if self._active:
            self._cleanup()

        self._active     = True
        self._timer      = 0.0
        self._duration   = duration
        self._fade_out   = fade_out
        self._on_complete = on_complete
        self._done       = False
        self._spawned    = []

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
        remaining = self._duration - self._timer

        if remaining <= self._fade_out and not getattr(self, '_fading', False):
            self._fading = True
            self._overlay.enabled = True
            self._overlay.color   = color.rgba(0, 0, 0, 0)
            self._overlay.animate_color(color.black, duration=self._fade_out)

        if self._timer >= self._duration and not self._done:
            self._done = True
            self._active = False
            self._cleanup_spawned()
            if self._on_complete:
                try:
                    self._on_complete()
                except Exception:
                    traceback.print_exc()

    def stop(self):
        """Emergency abort — restores player control."""
        self._active = False
        self._done   = True
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
        self._active = False
        self._cleanup_spawned()


manager = _CutsceneManager()


# ── sad ending ────────────────────────────────────────────────────────────────

_fired = False   # guard so the cutscene only auto-triggers once


def play_sad_ending():
    global _fired
    _fired = True
    print('[SadEnding] starting')

    # Road / timing constants
    road_x   = 14.0
    start_z  = 25.0
    end_z    = -35.0
    ride_dur = 8.0
    total    = ride_dur + 1.0

    # 1. Start manager first — this reparents camera to scene
    manager.play(
        duration=total,
        fade_in=1.5,
        fade_out=2.0,
        on_complete=_show_end_screen,
    )

    # 2. Now camera.parent == scene, so position is in world space
    try:
        camera.position = Vec3(road_x - 9, 3.0, 0)
        camera.rotation = Vec3(0, 0, 0)
        invoke(_look_at_road, delay=0.05)
    except Exception:
        traceback.print_exc()

    # 3. Spawn wagon
    wx, wy, wz = road_x, 0.0, start_z
    delta_z = end_z - start_z

    bed = manager.spawn(model='cube',
                        color=color.rgb(85/255, 52/255, 22/255),
                        scale=(3.6, 0.30, 1.8),
                        position=(wx, wy + 0.65, wz),
                        unlit=True)
    canopy = manager.spawn(model='cube',
                           color=color.rgb(210/255, 195/255, 160/255),
                           scale=(3.4, 0.08, 1.6),
                           position=(wx, wy + 1.40, wz),
                           unlit=True)
    board_f = manager.spawn(model='cube',
                            color=color.rgb(70/255, 42/255, 16/255),
                            scale=(0.18, 0.70, 1.8),
                            position=(wx - 1.65, wy + 1.0, wz),
                            unlit=True)
    board_b = manager.spawn(model='cube',
                            color=color.rgb(70/255, 42/255, 16/255),
                            scale=(0.18, 0.70, 1.8),
                            position=(wx + 1.65, wy + 1.0, wz),
                            unlit=True)
    wheels = []
    for offx, offz in ((-1.5, -0.9), (-1.5, 0.9), (1.5, -0.9), (1.5, 0.9)):
        wheels.append(manager.spawn(model='cube',
                                    color=color.rgb(45/255, 35/255, 20/255),
                                    scale=(0.20, 0.80, 0.80),
                                    position=(wx + offx, wy + 0.40, wz + offz),
                                    unlit=True))

    all_pieces = [bed, canopy, board_f, board_b] + wheels

    # 4. Groom NPC on wagon
    groom_body = manager.spawn(model='cube',
                               color=color.rgb(28/255, 30/255, 65/255),
                               scale=(0.48, 0.82, 0.32),
                               position=(wx + 0.6, wy + 1.05, wz),
                               unlit=True)
    groom_head = manager.spawn(model='cube',
                               color=color.rgb(220/255, 178/255, 132/255),
                               scale=(0.40, 0.40, 0.40),
                               position=(wx + 0.6, wy + 1.65, wz),
                               unlit=True)

    # 5. Wife — teleport onto wagon
    _place_wife(wx - 0.5, wy + 1.05, wz)

    # 6. Animate everything south
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


def _look_at_road():
    try:
        camera.look_at(Vec3(14, 1.2, 0))
        camera.rotation_z = 0
    except Exception:
        traceback.print_exc()


def _place_wife(x, y, z):
    try:
        if world.wife_entity:
            world.wife_entity.position = Vec3(x, y, z)
            world.wife_entity.rotation_y = 90   # face camera
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
        Entity(parent=camera.ui, model='quad',
               scale=(2, 1), color=color.black, z=-0.01)

        Text(parent=camera.ui,
             text='KẾT THÚC ĐAU BUỒN',
             position=(0, 0.18), origin=(0, 0),
             scale=2.8, color=color.white)

        Text(parent=camera.ui,
             text='"Em không phải người chờ đợi mãi.\nNhưng anh đã không đến kịp."',
             position=(0, -0.02), origin=(0, 0),
             scale=1.1, color=color.rgba(1, 1, 1, 0.75))

        Button(parent=camera.ui, text='Chơi lại',
               scale=(0.22, 0.09), position=(-0.14, -0.25),
               color=color.rgb(40/255, 80/255, 40/255),
               highlight_color=color.rgb(60/255, 120/255, 60/255),
               on_click=_restart)

        Button(parent=camera.ui, text='Thoát',
               scale=(0.22, 0.09), position=(0.14, -0.25),
               color=color.rgb(80/255, 40/255, 40/255),
               highlight_color=color.rgb(120/255, 60/255, 60/255),
               on_click=application.quit)

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
try:
    import cutscene as _cutscene_impl
except Exception:
    _cutscene_impl = None


def request_happy_ending():
    if _cutscene_impl:
        try:
            return _cutscene_impl.request_happy_ending()
        except Exception:
            traceback.print_exc()


def update():
    """Called from `game.update()` to advance any active happy-ending cutscene.
    Returns True if the cutscene consumed the frame update."""
    if _cutscene_impl:
        try:
            return _cutscene_impl.update()
        except Exception:
            traceback.print_exc()
    return False


def handle_input(key):
    if _cutscene_impl:
        try:
            return _cutscene_impl.handle_input(key)
        except Exception:
            traceback.print_exc()
    return False
