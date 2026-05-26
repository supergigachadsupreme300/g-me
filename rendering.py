from ursina import Entity, Text, Button, color, scene, camera, mouse, window, load_texture
import world

starry_texture = None

time_text = None
ammo_text = None
player_hp_text = None
player_stamina_text = None
player_money_text = None
quest_text = None
pause_menu = None
bed_confirm_menu = None
bed_confirm_yes = None
bed_confirm_no = None
buffalo_dialog = None
buffalo_dialog_text = None
buffalo_sell = None
buffalo_leave = None


def setup_ui():
    global time_text, ammo_text, player_hp_text, player_stamina_text, player_money_text
    global pause_menu, bed_confirm_menu, bed_confirm_yes, bed_confirm_no
    global buffalo_dialog, buffalo_dialog_text, buffalo_sell, buffalo_leave
    global stats_panel, stats_lines, stats_button, quest_text

    # --- 1. GIAO DIỆN HUD NGƯỜI CHƠI (GIỮ NGUYÊN GỐC CỦA ÔNG) ---
    time_text = Text(parent=camera.ui, text='', position=(-0.8, 0.22), origin=(0, 0), scale=1.2, color=color.white, background=True)
    ammo_text = Text(parent=camera.ui, text='Ammo: 0/0', position=(0, -0.37), origin=(0, 0), scale=1.2, color=color.white, background=True)
    ammo_text.enabled = False
    
    player_hp_text = Text(parent=camera.ui, text='HP: 100/100', position=(-0.8, 0.41), origin=(0, 0), scale=1.2, color=color.rgb(255/255, 80/255, 80/255), background=True)
    player_stamina_text = Text(parent=camera.ui, text='Stamina: 100/100', position=(-0.75, 0.345), origin=(0, 0), scale=1.2, color=color.rgb(100/255, 200/255, 255/255), background=True)
    player_money_text = Text(parent=camera.ui, text='Money: 0', position=(-0.8, 0.275), origin=(0, 0), scale=1.2, color=color.rgb(255/255, 220/255, 100/255), background=True)
    quest_text = Text(parent=camera.ui, text='Quest: Harvest wheat 0/100', position=(-0.7, 0.21), origin=(0, 0), scale=1.1, color=color.white, background=True)

    # --- 2. GIAO DIỆN MENU SETTINGS CHUẨN ĐỒ ĐỒNG ĐỀU ---
    pause_menu = Entity(parent=camera.ui, enabled=False)
    # Nền đen mờ tỷ lệ gọn gàng, thanh lịch
    Entity(parent=pause_menu, model='quad', color=color.rgba(15, 15, 20, 230/255), scale=(0.6, 0.8), z=1)
    # Tiêu đề canh giữa tuyệt đối
    Text(text='SETTINGS', parent=pause_menu, y=0.3, origin=(0, 0), scale=2.5, color=color.orange)
    
    # Nút bấm đồng đều scale, có highlight_color đổi màu khi di chuột vào
    Button(parent=pause_menu, text='Continue', scale=(0.4, 0.08), y=0.1, color=color.dark_gray, highlight_color=color.azure)
    
    stats_button = Button(parent=pause_menu, text='Stats', scale=(0.4, 0.08), y=-0.05, color=color.dark_gray, highlight_color=color.azure)
    stats_button.on_click = lambda: show_stats(True)
    
    Button(parent=pause_menu, text='Exit', scale=(0.4, 0.08), y=-0.2, color=color.red, highlight_color=color.rgb(255, 100, 100))

    # --- 3. GIAO DIỆN BẢNG GIƯỜNG NGỦ & HỘI THOẠI TRÂU (GIỮ NGUYÊN GỐC) ---
    bed_confirm_menu = Entity(parent=camera.ui, enabled=False)
    Entity(parent=bed_confirm_menu, model='quad', color=color.rgba(0, 0, 0, 180/255), scale=(1.4, 0.6), position=(0, 0, 0))
    Text(parent=bed_confirm_menu, text='Use the bed?\nSkip to next day/night cycle.', y=0.12, scale=1.2, color=color.white)
    bed_confirm_yes = Button(parent=bed_confirm_menu, text='Yes', scale=(0.3, 0.13), x=-0.18, y=-0.12)
    bed_confirm_no = Button(parent=bed_confirm_menu, text='No', scale=(0.3, 0.13), x=0.18, y=-0.12)

    buffalo_dialog = Entity(parent=camera.ui, enabled=False)
    Entity(parent=buffalo_dialog, model='quad', color=color.rgba(0, 0, 0, 180/255), scale=(1.4, 0.7), position=(0, 0, 0))
    buffalo_dialog_text = Text(parent=buffalo_dialog, text='Tôi thích ăn lúa', y=0.15, scale=1.2, color=color.white)
    buffalo_sell = Button(parent=buffalo_dialog, text='Sell wheat', scale=(0.4, 0.13), x=-0.2, y=-0.15)
    buffalo_leave = Button(parent=buffalo_dialog, text='Leave', scale=(0.4, 0.13), x=0.2, y=-0.15)

    # --- 4. GIAO DIỆN BẢNG THỐNG KÊ (STATS PANEL) CANH LỀ SẠCH SẼ ---
    stats_panel = Entity(parent=camera.ui, enabled=False)
    # Khung nền chứa danh sách text
    Entity(parent=stats_panel, model='quad', color=color.rgba(15/255, 15/255, 20/255, 0.95), scale=(0.9, 0.9), z=1)
    
    # Tiêu đề bảng thống kê
    Text(parent=stats_panel, text='PLAYER STATS', y=0.35, origin=(0, 0), scale=2.5, color=color.azure)
    
    # Toàn bộ danh sách text được ép chung một trục x, căn lề trái (origin=(-0.5, 0)) để thẳng hàng tăm tắp
    text_x = -0.35
    stats_lines = {
        'harvested': Text(parent=stats_panel, text='Harvested wheat: 0', x=text_x, y=0.15, origin=(-0.5, 0), scale=1.3, color=color.white),
        'enemies': Text(parent=stats_panel, text='Enemies killed: 0', x=text_x, y=0.05, origin=(-0.5, 0), scale=1.3, color=color.white),
        
        # Tiền kiếm được màu xanh, tiền bị mất trộm màu đỏ trực quan
        'earned': Text(parent=stats_panel, text='Money earned: 0', x=text_x, y=-0.05, origin=(-0.5, 0), scale=1.3, color=color.rgb(100, 255, 100)),
        'stolen': Text(parent=stats_panel, text='Money stolen: 0', x=text_x, y=-0.15, origin=(-0.5, 0), scale=1.3, color=color.rgb(255, 100, 100)),
    }
    # Nút quay trở lại Menu Settings
    Button(parent=stats_panel, text='Back', y=-0.35, scale=(0.3, 0.08), color=color.dark_gray, highlight_color=color.azure, on_click=lambda: show_stats(False))

def update_ammo_text(gun_ammo, gun_max_ammo):
    if ammo_text is not None and ammo_text.enabled:
        ammo_text.text = f"Ammo: {gun_ammo}/{gun_max_ammo}"


def show_ammo(enabled: bool):
    if ammo_text is not None:
        ammo_text.enabled = enabled


def update_player_hud(hp, max_hp, stamina, max_stamina, money):
    if player_hp_text is not None:
        player_hp_text.text = f"HP: {int(hp)}/{int(max_hp)}"
    if player_stamina_text is not None:
        player_stamina_text.text = f"Stamina: {int(stamina)}/{int(max_stamina)}"
    if player_money_text is not None:
        player_money_text.text = f"Money: {int(money)}"


def update_quest_text(name, progress, goal):
    global quest_text, time_text
    if quest_text is not None:
        status = 'Completed' if progress >= goal else f'{progress}/{goal}'
        quest_text.text = f"Quest: {name} {status}"
        quest_text.enabled = True
        # also ensure time UI sits below quest UI
        if time_text is not None:
            time_text.y = quest_text.y - 0.06


def show_stats(enabled: bool):
    global stats_panel, pause_menu
    if stats_panel is None:
        return
    
    # Bật/tắt trang Stats
    stats_panel.enabled = enabled
    
    # Ẩn/hiện trang Menu chính (để không bị đè)
    if pause_menu is not None:
        pause_menu.enabled = not enabled
        
    if enabled:
        update_stats_display()

def update_stats_display():
    try:
        import stats as stats_mod
        s = stats_mod.get_summary()
        stats_lines['harvested'].text = f"Harvested wheat: {s.get('harvested_wheat', 0)}"
        enemies = s.get('enemies_killed', {})
        enemies_str = ', '.join([f"{k}:{v}" for k, v in enemies.items()]) or '0'
        stats_lines['enemies'].text = f"Enemies killed: {enemies_str}"
        stats_lines['earned'].text = f"Money earned: {s.get('money_earned', 0)}"
        stats_lines['stolen'].text = f"Money stolen: {s.get('money_stolen', 0)}"
    except Exception:
        pass


def update_time_ui(current_day, time_of_day):
    if time_text is None:
        return
    hours = int(time_of_day)
    minutes = int((time_of_day - hours) * 60)
    time_text.text = f"Day {current_day} - {hours:02d}:{minutes:02d}"


def set_day_night(time_of_day):
    if world.sun is None:
        return
    if 6 <= time_of_day < 18:
        world.sun.color = color.rgb(255/255, 255/255, 235/255)
        window.color = color.rgb(135/255, 206/255, 235/255)
        scene.fog_color = color.rgb(135/255, 206/255, 235/255)
        if world.sky is not None:
            world.sky.texture = None
            world.sky.color = color.rgb(135/255, 206/255, 235/255)
    else:
        world.sun.color = color.rgb(120/255, 140/255, 255/255)
        window.color = color.rgb(15/255, 20/255, 55/255)
        scene.fog_color = color.rgb(15/255, 20/255, 55/255)
        if world.sky is not None:
            global starry_texture
            if starry_texture is None:
                try:
                    starry_texture = load_texture('texture/starry.png')
                    print('Loaded night sky texture: texture/starry.png')
                except Exception as e:
                    print(f'Failed to load night sky texture: {e}')
                    starry_texture = None
            if starry_texture is not None:
                world.sky.texture = starry_texture
                world.sky.color = color.white
            else:
                world.sky.texture = None
                world.sky.color = color.rgb(15/255, 20/255, 55/255)


def set_pause_button_callbacks(continue_callback, exit_callback):
    if pause_menu is None:
        return
    buttons = [child for child in pause_menu.children if getattr(child, 'text', None) in ('Continue', 'Exit')]
    if len(buttons) >= 2:
        buttons[0].on_click = continue_callback
        buttons[1].on_click = exit_callback


def set_bed_confirm_callbacks(yes_callback, no_callback):
    if bed_confirm_yes is not None:
        bed_confirm_yes.on_click = yes_callback
    if bed_confirm_no is not None:
        bed_confirm_no.on_click = no_callback


def set_buffalo_dialog_callbacks(sell_callback, leave_callback):
    if buffalo_sell is not None:
        buffalo_sell.on_click = sell_callback
    if buffalo_leave is not None:
        buffalo_leave.on_click = leave_callback


def show_buffalo_dialog(enabled: bool, text: str = None):
    global buffalo_dialog, buffalo_dialog_text
    if buffalo_dialog is None:
        return
    buffalo_dialog.enabled = enabled
    if text is not None and buffalo_dialog_text is not None:
        buffalo_dialog_text.text = text
    if enabled:
        mouse.locked = False
        mouse.visible = True
    else:
        mouse.locked = True
        mouse.visible = False


def toggle_pause(paused: bool):
    global pause_menu
    if pause_menu is None:
        return
    pause_menu.enabled = paused
    if paused:
        mouse.locked = False
        mouse.visible = True
    else:
        mouse.locked = True
        mouse.visible = False


def toggle_bed_menu(enabled: bool):
    global bed_confirm_menu
    if bed_confirm_menu is None:
        return
    bed_confirm_menu.enabled = enabled
    if enabled:
        mouse.locked = False
        mouse.visible = True
    else:
        mouse.locked = True
        mouse.visible = False
