from ursina import Entity, Text, Button, color, scene, camera, mouse, window, load_texture
import world

starry_texture = None

time_text = None
ammo_text = None
player_hp_text = None
player_stamina_text = None
player_money_text = None
quest_text = None
mobspawner_text = None
pause_menu = None
bed_confirm_menu = None
bed_confirm_yes = None
bed_confirm_no = None
marriage_menu = None
marriage_yes  = None
marriage_no   = None
quest_close_callback = None

quest_close_callback = None


def setup_ui():
    global time_text, ammo_text, player_hp_text, player_stamina_text, player_money_text
    global mobspawner_text
    global pause_menu, bed_confirm_menu, bed_confirm_yes, bed_confirm_no
    global marriage_menu, marriage_yes, marriage_no
    global stats_panel, stats_lines, stats_button, quest_text
    global quest_panel, quest_lines, quest_button
    global instructions_panel, instructions_button
    global instructions_content, btn_prev_page, btn_next_page

    # --- 1. GIAO DIỆN HUD NGƯỜI CHƠI ---
    time_text = Text(parent=camera.ui, text='', position=(-0.8, 0.22), origin=(0, 0), scale=1.2, color=color.white, background=True)
    ammo_text = Text(parent=camera.ui, text='Ammo: 0/0', position=(0, -0.37), origin=(0, 0), scale=1.2, color=color.white, background=True)
    ammo_text.enabled = False
    
    player_hp_text = Text(parent=camera.ui, text='HP: 100/100', position=(-0.8, 0.41), origin=(0, 0), scale=1.2, color=color.rgb(255/255, 80/255, 80/255), background=True)
    player_stamina_text = Text(parent=camera.ui, text='Stamina: 100/100', position=(-0.75, 0.345), origin=(0, 0), scale=1.2, color=color.rgb(100/255, 200/255, 255/255), background=True)
    player_money_text = Text(parent=camera.ui, text='Money: 0', position=(-0.8, 0.275), origin=(0, 0), scale=1.2, color=color.rgb(255/255, 220/255, 100/255), background=True)
    quest_text = Text(parent=camera.ui, text='Quest: Harvest wheat 0/100', position=(-0.7, 0.21), origin=(0, 0), scale=1.1, color=color.white, background=True)
    mobspawner_text = Text(parent=camera.ui, text='', position=(0, -0.37), origin=(0, 0), scale=1.0, color=color.yellow, background=True, enabled=False)

    # --- 2. GIAO DIỆN MENU SETTINGS ---
    pause_menu = Entity(parent=camera.ui, enabled=False)
    Entity(parent=pause_menu, model='quad', color=color.rgba(15, 15, 20, 230/255), scale=(0.6, 0.9), z=1)
    
    Text(text='SETTINGS', parent=pause_menu, y=0.38, origin=(0, 0), scale=2.5, color=color.orange)
    
    Button(parent=pause_menu, text='Continue', scale=(0.4, 0.08), y=0.22, color=color.dark_gray, highlight_color=color.azure)
    
    import save_manager
    Button(parent=pause_menu, text='Save Game', scale=(0.4, 0.08), y=0.10, color=color.dark_gray, highlight_color=color.rgb(100, 255, 100), on_click=save_manager.save_game)
    
    stats_button = Button(parent=pause_menu, text='Stats', scale=(0.4, 0.08), y=-0.02, color=color.dark_gray, highlight_color=color.azure)
    stats_button.on_click = lambda: show_stats(True)

    quest_button = Button(parent=pause_menu, text='Quests', scale=(0.4, 0.08), y=-0.14, color=color.dark_gray, highlight_color=color.azure)
    quest_button.on_click = lambda: show_quests(True)

    instructions_button = Button(parent=pause_menu, text='Instructions', scale=(0.4, 0.08), y=-0.26, color=color.dark_gray, highlight_color=color.azure)
    instructions_button.on_click = lambda: show_instructions(True)

    Button(parent=pause_menu, text='Exit', scale=(0.4, 0.08), y=-0.38, color=color.red, highlight_color=color.rgb(255, 100, 100))

    # --- 3. GIAO DIỆN BẢNG GIƯỜNG NGỦ & HỘI THOẠI TRÂU ---
    bed_confirm_menu = Entity(parent=camera.ui, enabled=False)
    Entity(parent=bed_confirm_menu, model='quad', color=color.rgba(0, 0, 0, 180/255), scale=(1.4, 0.6), position=(0, 0, 0))
    # Center the bed prompt text inside the dialog so it is visible on all resolutions
    Text(parent=bed_confirm_menu, text='Use the bed?\nSkip to next day/night cycle.', x=0, y=0.12, origin=(0, 0.5), scale=1.2, color=color.white)
    bed_confirm_yes = Button(parent=bed_confirm_menu, text='Yes', scale=(0.3, 0.13), x=-0.18, y=-0.12)
    bed_confirm_no = Button(parent=bed_confirm_menu, text='No', scale=(0.3, 0.13), x=0.18, y=-0.12)

    marriage_menu = Entity(parent=camera.ui, enabled=False)
    Entity(parent=marriage_menu, model='quad', color=color.rgba(30/255, 0, 10/255, 210/255), scale=(1.7, 0.58))
    Text(parent=marriage_menu, text='Will you marry me?\\nPrice: 10,000,000 coins', y=0.1, scale=1.4, color=color.rgb(255/255, 220/255, 120/255))
    marriage_yes = Button(parent=marriage_menu, text='Yes!', scale=(0.35, 0.12), x=-0.2, y=-0.13, color=color.rgb(180/255, 40/255, 60/255), highlight_color=color.rgb(220/255, 80/255, 100/255))
    marriage_no  = Button(parent=marriage_menu, text='Not now', scale=(0.35, 0.12), x=0.2, y=-0.13, color=color.dark_gray, highlight_color=color.gray)

    # buffalo dialog removed; buffalo shop uses dedicated UI in `buffalo_shop.py`

    # --- 4. GIAO DIỆN BẢNG THỐNG KÊ (STATS PANEL) ---
    stats_panel = Entity(parent=camera.ui, enabled=False)
    Entity(parent=stats_panel, model='quad', color=color.rgba(15/255, 15/255, 20/255, 0.95), scale=(0.9, 0.9), z=1)
    
    Text(parent=stats_panel, text='PLAYER STATS', y=0.35, origin=(0, 0), scale=2.5, color=color.azure)
    
    text_x = -0.35
    stats_lines = {
        'harvested': Text(parent=stats_panel, text='Harvested wheat: 0', x=text_x, y=0.15, origin=(-0.5, 0), scale=1.3, color=color.white),
        'enemies': Text(parent=stats_panel, text='Enemies killed: 0', x=text_x, y=0.05, origin=(-0.5, 0), scale=1.3, color=color.white),
        'earned': Text(parent=stats_panel, text='Money earned: 0', x=text_x, y=-0.05, origin=(-0.5, 0), scale=1.3, color=color.rgb(100, 255, 100)),
        'stolen': Text(parent=stats_panel, text='Money stolen: 0', x=text_x, y=-0.15, origin=(-0.5, 0), scale=1.3, color=color.rgb(255, 100, 100)),
    }
    
    Button(parent=stats_panel, text='Back', y=-0.35, scale=(0.3, 0.08), color=color.dark_gray, highlight_color=color.azure, on_click=lambda: show_stats(False))

    # --- Quests panel ---
    quest_panel = Entity(parent=camera.ui, enabled=False, position=(0, 0.18))
    Entity(parent=quest_panel, model='quad', color=color.rgba(15/255, 15/255, 20/255, 0.95), scale=(0.6, 0.7), z=1)
    Text(parent=quest_panel, text='QUESTS', y=0.26, origin=(0, 0), scale=1.8, color=color.azure)

    quest_lines = []
    quest_line_buttons = []
    q_x = -0.28
    # Create 5 visible quest lines and a small 'Focus' button to the right
    for i in range(5):
        qy = 0.12 - i * 0.10
        t = Text(parent=quest_panel, text='', x=q_x, y=qy, origin=(-0.5, 0), scale=1.0, color=color.white)
        quest_lines.append(t)
        # small focus button on the right of each line
        fb = Button(parent=quest_panel, text='Focus', x=0.18, y=qy, scale=(0.18, 0.08), color=color.dark_gray, highlight_color=color.azure)
        # attach focus handler to update tasks and HUD
        try:
            fb.on_click = (lambda i=i: set_quest_focus(i))
        except Exception:
            pass
        quest_line_buttons.append(fb)

    global quest_panel_lines, quest_panel_buttons
    quest_panel_lines = quest_lines
    quest_panel_buttons = quest_line_buttons

    def _on_close_quests():
        global quest_close_callback
        try:
            if quest_close_callback is not None:
                quest_close_callback()
        except Exception:
            pass
        show_quests(False)

    Button(parent=quest_panel, text='X', x=0.26, y=0.28, scale=(0.06, 0.06), color=color.dark_gray, highlight_color=color.gray, on_click=_on_close_quests)

    # --- 5. GIAO DIỆN HƯỚNG DẪN (INSTRUCTIONS PANEL) ---
    instructions_panel = Entity(parent=camera.ui, enabled=False)
    Entity(parent=instructions_panel, model='quad', color=color.rgba(15/255, 15/255, 20/255, 0.95), scale=(0.9, 0.9), z=1)
    
    Text(parent=instructions_panel, text='HƯỚNG DẪN', y=0.35, origin=(0, 0), scale=2.5, color=color.azure)
    
    instructions_content = Text(parent=instructions_panel, text='', x=0, y=0, origin=(0, 0), color=color.white)
    
    Button(parent=instructions_panel, text='Back', y=-0.38, scale=(0.2, 0.08), color=color.dark_gray, highlight_color=color.azure, on_click=lambda: show_instructions(False))
    
    btn_prev_page = Button(parent=instructions_panel, text='< Trang trước', x=-0.28, y=-0.38, scale=(0.25, 0.08), color=color.dark_gray, highlight_color=color.azure, on_click=lambda: change_inst_page(1))
    btn_next_page = Button(parent=instructions_panel, text='Trang sau >', x=0.28, y=-0.38, scale=(0.25, 0.08), color=color.dark_gray, highlight_color=color.azure, on_click=lambda: change_inst_page(2))
    
    change_inst_page(1)


# =========================================================================
# CÁC HÀM XỬ LÝ (HELPER FUNCTIONS)
# =========================================================================

def change_inst_page(page_num):
    global instructions_content, btn_prev_page, btn_next_page
    
    # Khoảng cách được tạo ra bởi \n\n
    page_1_text = (
        "Phím di chuyển: A, W, S, D\n\n"
        "Nhảy: Space\n\n"
        "Nhặt đồ: E\n\n"
        "Quăng đồ: Q\n\n"
        "Thay đạn: R\n\n"
        "Setting: Esc\n\n"
        "chuột trái:sử dụng item "
    )
    
    page_2_text = (
        "• Cuốc (hoe): dùng xới đất, trồng cây\n\n"
        "• Rìu (axe): dùng chặt gỗ\n\n"
        "• Cuốc chim (pickaxe): dùng đào đá\n\n"
        "• Hạt giống (seed): trồng trên đất đã xới\n\n"
        "• Sword: dùng chiến đấu với quái vật/kẻ trộm\n\n"
        "• Súng (gun): chiến đấu xa, cần có đạn\n\n"
        "• Đạn (ammo): dùng để nạp vào súng\n\n"
        "• Lưỡi hái (scythe): dùng để thu hoạch lúa\n\n"
        "• Búa (hammer): dùng để xây dựng\n\n"
        "• Mì hảo hảo: có thể hồi máu"
    )
    
    if page_num == 1:
        instructions_content.text = page_1_text
        # origin=(-0.5, 0.5) ép toàn bộ chữ về lề trái
        instructions_content.origin = (-0.5, 0.5) 
        instructions_content.x = -0.25
        instructions_content.y = 0.2
        instructions_content.scale = 1.3
        
        if btn_prev_page: btn_prev_page.enabled = False
        if btn_next_page: btn_next_page.enabled = True
        
    elif page_num == 2:
        instructions_content.text = page_2_text
        instructions_content.origin = (-0.5, 0.5) 
        instructions_content.x = -0.42
        instructions_content.y = 0.28  # Đẩy lên một xíu để các dòng giãn ra mà không tràn đáy
        instructions_content.scale = 0.95 # Chỉnh nhỏ xíu để vừa 10 món đồ
        
        if btn_prev_page: btn_prev_page.enabled = True
        if btn_next_page: btn_next_page.enabled = False


# Thêm biến này để lưu tốc độ chuột cũ
_inst_original_sensitivity = None

_inst_original_sensitivity = None

_inst_original_sensitivity = None

def show_instructions(enabled: bool):
    global instructions_panel, pause_menu, _inst_original_sensitivity
    if instructions_panel is None:
        return
    
    instructions_panel.enabled = enabled
    import world
    import game
    
    if enabled:
        change_inst_page(1)
        mouse.locked = False
        mouse.visible = True
        
        # SỬA LỖI HIỆN SONG SONG: Ẩn bảng Setting đi
        if pause_menu is not None:
            pause_menu.enabled = False
            
        # KHÓA DI CHUYỂN VÀ CAMERA
        if hasattr(world, 'player') and world.player is not None:
            world.player.ignore_input = True 
            if hasattr(world.player, 'mouse_sensitivity'):
                if _inst_original_sensitivity is None:
                    _inst_original_sensitivity = world.player.mouse_sensitivity
                world.player.mouse_sensitivity = (0, 0)
    else:
        # MỞ KHÓA DI CHUYỂN VÀ CAMERA
        if hasattr(world, 'player') and world.player is not None:
            world.player.ignore_input = False
            if hasattr(world.player, 'mouse_sensitivity') and _inst_original_sensitivity is not None:
                world.player.mouse_sensitivity = _inst_original_sensitivity
                
        # Xử lý đóng bảng
        if game.game_paused:
            if pause_menu is not None:
                pause_menu.enabled = True # Bật lại bảng setting khi ấn Back
        else:
            mouse.locked = True
            mouse.visible = False


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
        if time_text is not None:
            time_text.y = quest_text.y - 0.06


def update_mobspawner_text(target_name: str = None):
    global mobspawner_text
    if mobspawner_text is None:
        return
    mobspawner_text.text = f"Spawn target: {target_name}" if target_name else "Spawn target: Unknown"


def show_mobspawner(enabled: bool):
    global mobspawner_text
    if mobspawner_text is None:
        return
    mobspawner_text.enabled = enabled


def show_stats(enabled: bool):
    global stats_panel, pause_menu
    if stats_panel is None:
        return
    
    stats_panel.enabled = enabled
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


# NOTE: `update_quest_display` removed — use `refresh_quest_panel(quests, focused_index)` instead


def show_quests(enabled: bool):
    global quest_panel, pause_menu
    if quest_panel is None:
        return

    quest_panel.enabled = enabled
    if enabled:
        try:
            import tasks as tasks_mod
            refresh_quest_panel(tasks_mod.get_quests(), tasks_mod.get_focused_index())
        except Exception:
            # fallback: nothing to do if refresh fails
            pass

    if pause_menu is not None:
        pause_menu.enabled = not enabled


def set_quest_close_callback(callback):
    global quest_close_callback
    quest_close_callback = callback


def show_quest_panel(enabled: bool):
    # backward-compatible alias used by game.py
    show_quests(enabled)


def refresh_quest_panel(quests: list, focused_index: int, scroll: int = 0):
    # populate visible quest lines and highlight focused
    try:
        lines = globals().get('quest_panel_lines', [])
        buttons = globals().get('quest_panel_buttons', [])
    except Exception:
        return

    for i, txt in enumerate(lines):
        idx = scroll + i
        if idx < len(quests):
            q = quests[idx]
            status = 'Completed' if q.completed else f"{q.progress}/{q.goal}"
            # make focused quest visually obvious (color + chevron)
            prefix = '> ' if idx == focused_index else '   '
            txt.text = f"{prefix}{q.name}: {status}"
            if i < len(buttons):
                buttons[i].enabled = True
                buttons[i].text = 'Focus'
        else:
            txt.text = ''
            if i < len(buttons):
                buttons[i].enabled = False
                buttons[i].text = ''


def set_quest_focus_callbacks(callbacks: list):
    btns = globals().get('quest_panel_buttons', [])
    for i, b in enumerate(btns):
        try:
            if i < len(callbacks) and callbacks[i] is not None:
                b.on_click = callbacks[i]
            else:
                b.on_click = None
        except Exception:
            pass


def set_quest_focus(index: int):
    # Called when a quest 'Focus' button is pressed — update tasks and UI
    try:
        import tasks as tasks_mod
        quests = tasks_mod.get_quests()
        if not quests:
            return
        if index < 0 or index >= len(quests):
            return
        tasks_mod.set_focused_quest(index)
        active = tasks_mod.get_active_quest()
        if active is not None:
            update_quest_text(active.name, active.progress, active.goal)
        # refresh the panel to highlight the focused quest
        refresh_quest_panel(quests, tasks_mod.get_focused_index())
    except Exception:
        pass


def update_time_ui(current_day, time_of_day):
    if time_text is None:
        return
    hours = int(time_of_day)
    minutes = int((time_of_day - hours) * 60)
    time_text.text = f"Day {current_day} - {hours:02d}:{minutes:02d}"


DAY_START = 6.0
DUSK_START = 17.0
NIGHT_START = 19.0

DAY_SKY = (135 / 255, 206 / 255, 235 / 255)
DUSK_SKY = (255 / 255, 145 / 255, 75 / 255)
NIGHT_SKY = (15 / 255, 20 / 255, 55 / 255)
DAY_SUN = (255 / 255, 255 / 255, 235 / 255)
DUSK_SUN = (255 / 255, 125 / 255, 45 / 255)
NIGHT_SUN = (120 / 255, 140 / 255, 255 / 255)


def get_time_stage(time_of_day: float) -> str:
    if DAY_START <= time_of_day < DUSK_START:
        return 'day'
    if DUSK_START <= time_of_day < NIGHT_START:
        return 'dusk'
    return 'night'


def _blend_rgb(a, b, t):
    t = max(0.0, min(1.0, t))
    return color.rgb(
        a[0] + (b[0] - a[0]) * t,
        a[1] + (b[1] - a[1]) * t,
        a[2] + (b[2] - a[2]) * t,
    )


def _apply_sky_colors(sky_rgb, sun_rgb, star_blend=0.0):
    if world.sun is not None:
        world.sun.color = sun_rgb
    window.color = sky_rgb
    scene.fog_color = sky_rgb
    if world.sky is None:
        return
    global starry_texture
    if star_blend > 0.0:
        if starry_texture is None:
            try:
                starry_texture = load_texture('texture/starry.png')
            except Exception:
                starry_texture = None
        if starry_texture is not None:
            world.sky.texture = starry_texture
            world.sky.color = _blend_rgb((1.0, 1.0, 1.0), sky_rgb, 1.0 - star_blend)
        else:
            world.sky.texture = None
            world.sky.color = sky_rgb
    else:
        world.sky.texture = None
        world.sky.color = sky_rgb


def set_day_night(time_of_day):
    if world.sun is None:
        return

    stage = get_time_stage(time_of_day)
    if stage == 'day':
        _apply_sky_colors(
            color.rgb(*DAY_SKY),
            color.rgb(*DAY_SUN),
            star_blend=0.0,
        )
        return

    if stage == 'dusk':
        dusk_progress = (time_of_day - DUSK_START) / (NIGHT_START - DUSK_START)
        if dusk_progress < 0.5:
            blend = dusk_progress * 2.0
            sky_rgb = _blend_rgb(DAY_SKY, DUSK_SKY, blend)
            sun_rgb = _blend_rgb(DAY_SUN, DUSK_SUN, blend)
            star_blend = 0.0
        else:
            blend = (dusk_progress - 0.5) * 2.0
            sky_rgb = _blend_rgb(DUSK_SKY, NIGHT_SKY, blend)
            sun_rgb = _blend_rgb(DUSK_SUN, NIGHT_SUN, blend)
            star_blend = blend * 0.65
        _apply_sky_colors(sky_rgb, sun_rgb, star_blend=star_blend)
        return

    _apply_sky_colors(
        color.rgb(*NIGHT_SKY),
        color.rgb(*NIGHT_SUN),
        star_blend=1.0,
    )


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

# buffalo dialog callbacks removed (buffalo shop uses `buffalo_shop.py` UI)



def set_marriage_callbacks(yes_cb, no_cb):
    if marriage_yes is not None:
        marriage_yes.on_click = yes_cb
    if marriage_no is not None:
        marriage_no.on_click = no_cb


def show_marriage_menu(enabled: bool):
    if marriage_menu is None:
        return
    marriage_menu.enabled = enabled
    if enabled:
        mouse.locked = False
        mouse.visible = True
    else:
        mouse.locked = True
        mouse.visible = False

# show_buffalo_dialog removed; use `buffalo_shop.open_buffalo_shop()` instead


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