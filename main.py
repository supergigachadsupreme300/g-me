import os
import sys
import io

# Ensure console output can handle Unicode paths on Windows when Ursina prints asset_folder.
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)

from ursina import *
import config
import world
import tools
import building_system
import rendering
import game

in_game = False

class MainMenu(Entity):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.camera_angle = 0
        camera.parent = scene
        
        # 1. Khóa người chơi
        if hasattr(world, 'player') and world.player:
            world.player.enabled = False
            
        mouse.locked = False
        mouse.visible = True
        
        # 2. Tàng hình tay và toàn bộ vũ khí/công cụ
        self.all_tools = [
            tools.arm, tools.axe, tools.pickaxe, tools.hoe, 
            tools.hammer, tools.sword, tools.gun, tools.scythe, 
            tools.fertilizer, tools.seed, tools.peashooter_seed, 
            tools.wheat, tools.damaged_wheat
        ]
        for t in self.all_tools:
            if t is not None:
                t.visible = False
                
        # 3. Tạo Giao diện Menu (Nút bấm, Chữ)
        self.ui_group = Entity(parent=camera.ui)
        Text(text="NÔNG TRẠI SINH TỒN", parent=self.ui_group, scale=3, origin=(0, 0), y=0.25, color=color.orange)
        Button(text="Bắt đầu", parent=self.ui_group, scale=(0.25, 0.08), y=0.05, color=color.azure, on_click=self.start_game)
        Button(text="Thoát", parent=self.ui_group, scale=(0.25, 0.08), y=-0.05, color=color.red, on_click=application.quit)

        # 4. THỦ THUẬT AUTO GIẤU HUD (Máu, Tiền, Quest...):
        self.hidden_ui = []
        # Quét mọi thứ đang dán lên màn hình UI
        for child in camera.ui.children:
            # Nếu cái UI đó không phải là cái Menu mình vừa tạo ở bước 3, thì đem giấu đi
            if child != self.ui_group and child.visible:
                child.visible = False
                self.hidden_ui.append(child) # Ghi sổ lại để tí vào game bật lên lại

    def update(self):
        # Tốc độ camera chậm lại (nhân 5 thay vì 15)
        self.camera_angle += time.dt * 5 
        radius = 25
        cam_x = math.sin(math.radians(self.camera_angle)) * radius
        cam_z = math.cos(math.radians(self.camera_angle)) * radius
        
        camera.position = (cam_x, 15, cam_z)
        camera.look_at((0, 3, 0))
        camera.rotation_z = 0

    def start_game(self):
        global in_game
        in_game = True
        
        # Xóa giao diện Menu
        destroy(self.ui_group)
        
        # Bật lại người chơi và gắn camera
        if hasattr(world, 'player') and world.player:
            world.player.enabled = True
            if hasattr(world.player, 'camera_pivot'):
                camera.parent = world.player.camera_pivot
                camera.position = (0, 0, 0)
            else:
                camera.parent = world.player
                camera.position = (0, 2, 0) 
            camera.rotation = (0, 0, 0)
            
        camera.rotation_z = 0
        mouse.locked = True
        mouse.visible = False
        
        # 5. Bật lại Tay / Công cụ
        for t in self.all_tools:
            if t is not None:
                t.visible = True
                
        # 6. Bật lại toàn bộ HUD (Máu, Tiền, Quest...)
        for child in self.hidden_ui:
            if child: # Check an toàn xem UI còn tồn tại không
                child.visible = True
                
        # Tiêu hủy class menu
        destroy(self)

def input(key):
    if not in_game:
        return
    game.handle_input(key)


def update():
    if not in_game:
        return
    game.update()


def setup_tools_for_camera():
    tools.arm.parent = camera
    tools.axe.parent = camera
    tools.pickaxe.parent = camera
    tools.hoe.parent = camera
    tools.hammer.parent = camera
    tools.sword.parent = camera
    tools.gun.parent = camera
    tools.scythe.parent = camera
    tools.fertilizer.parent = camera
    # ensure stackable and plant items are parented to camera so they appear in-hand
    tools.seed.parent = camera
    tools.peashooter_seed.parent = camera
    tools.mi_hao_hao.parent = camera
    tools.wheat.parent = camera
    tools.damaged_wheat.parent = camera

    positions = (0.7, -0.6, 1.5)
    tools.arm.position = positions
    tools.axe.position = positions
    tools.pickaxe.position = positions
    tools.hoe.position = positions
    tools.hammer.position = positions
    tools.sword.position = positions
    tools.gun.position = positions
    tools.fertilizer.position = positions
    tools.seed.position = positions
    tools.peashooter_seed.position = positions
    tools.mi_hao_hao.position = positions
    tools.wheat.position = positions
    tools.damaged_wheat.position = positions


def run_game():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    app = Ursina(development_mode=False)
    application.development_mode = False
    window.render_mode = 'default'
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

    main_menu = MainMenu()

    app.run()


if __name__ == '__main__':
    run_game()
