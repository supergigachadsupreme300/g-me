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
import cutscene_manager
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
            tools.corn_seed,
            tools.wheat, tools.damaged_wheat, tools.corn, tools.potato,
            tools.damaged_corn, tools.damaged_potato,
        ]
        for t in self.all_tools:
            if t is not None:
                t.visible = False
                
        # 3. Tạo Giao diện Menu (Nút bấm, Chữ)
        self.ui_group = Entity(parent=camera.ui)
        Text(text="NÔNG TRẠI SINH TỒN", parent=self.ui_group, scale=3, origin=(0, 0), y=0.25, color=color.orange)
        
        Button(text="Game Mới", parent=self.ui_group, scale=(0.25, 0.08), y=0.05, color=color.azure, on_click=self.start_game)
        
        # NÚT LOAD GAME (Nền Xanh lá)
        Button(text="Tiếp tục (Load)", parent=self.ui_group, scale=(0.25, 0.08), y=-0.05, color=color.green, on_click=self.load_game)
        
        Button(text="Thoát", parent=self.ui_group, scale=(0.25, 0.08), y=-0.15, color=color.red, on_click=application.quit)

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

    def load_game(self):
        """Hàm dùng để load game trực tiếp bỏ qua cutscene"""
        import save_manager
        global in_game
        in_game = True
        
        # Xóa giao diện Menu
        destroy(self.ui_group)
        mouse.locked = True
        mouse.visible = False
        
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
        
        for t in self.all_tools:
            if t is not None:
                t.visible = True
                
        for child in self.hidden_ui:
            if child:
                child.visible = True
                
        # Gọi hàm Load từ save_manager
        invoke(save_manager.load_game, delay=0.1)
        destroy(self)

    def start_game(self):
        """Hàm bắt đầu game mới sẽ có Cutscene và Hướng dẫn"""
        global in_game
        in_game = True
        
        # Xóa giao diện Menu
        destroy(self.ui_group)
        mouse.locked = True
        mouse.visible = False
        
        def on_cutscene_finish():
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
            
            # Bật lại Tay / Công cụ
            for t in self.all_tools:
                if t is not None:
                    t.visible = True
                    
            # Bật lại toàn bộ HUD (Máu, Tiền, Quest...)
            for child in self.hidden_ui:
                if child:
                    child.visible = True
            
            # Sửa lỗi màn hình đen
            if cutscene_manager.manager._overlay:
                cutscene_manager.manager._overlay.color = color.black
                cutscene_manager.manager._overlay.animate_color(color.rgba(0,0,0,0), duration=1.0)
                invoke(lambda: setattr(cutscene_manager.manager._overlay, 'enabled', False), delay=1.05)
                
            # -------------------------------------------------------------
            # HIỂN THỊ HƯỚNG DẪN SAU KHI VÀO GAME
            # -------------------------------------------------------------
            import rendering
            rendering.show_instructions(True)
            
            # Khóa input để người chơi không chạy đi khi đang đọc hướng dẫn
            if hasattr(world, 'player') and world.player:
                world.player.ignore_input = True
                    
        # Chạy cutscene lái xe ô tô, xong thì gọi hàm on_cutscene_finish
        cutscene_manager.play_intro_cutscene(on_complete=on_cutscene_finish)
                
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
    tools.corn_seed.parent = camera
    tools.corn.parent = camera
    tools.potato.parent = camera
    tools.damaged_corn.parent = camera
    tools.damaged_potato.parent = camera

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
    tools.corn_seed.position = positions
    tools.corn.position = positions
    tools.potato.position = positions
    tools.damaged_corn.position = positions
    tools.damaged_potato.position = positions


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
