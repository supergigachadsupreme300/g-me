import os
import sys
import io

# Ensure console output can handle Unicode paths on Windows when Ursina prints asset_folder.
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)

from ursina import Ursina, mouse, window, application, camera
import config
import world
import tools
import building_system
import rendering
import game


def input(key):
    game.handle_input(key)


def update():
    game.update()


def setup_tools_for_camera():
    tools.arm.parent = camera
    tools.axe.parent = camera
    tools.pickaxe.parent = camera
    tools.hoe.parent = camera
    tools.hammer.parent = camera
    tools.sword.parent = camera
    tools.gun.parent = camera
    tools.fertilizer.parent = camera

    positions = (0.7, -0.6, 1.5)
    tools.arm.position = positions
    tools.axe.position = positions
    tools.pickaxe.position = positions
    tools.hoe.position = positions
    tools.hammer.position = positions
    tools.sword.position = positions
    tools.gun.position = positions
    tools.fertilizer.position = positions


def run_game():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    app = Ursina()
    application.development_mode = False
    mouse.locked = True
    mouse.visible = False
    window.exit_button.visible = False

    config.load_textures()
    world.create_world()
    tools.setup_tools()
    building_system.setup_building_system()
    setup_tools_for_camera()

    rendering.setup_ui()
    game.setup_game()

    app.run()


if __name__ == '__main__':
    run_game()
