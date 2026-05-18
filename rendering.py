from ursina import Entity, Text, Button, color, scene, camera, mouse, window
import world


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

    time_text = Text(parent=camera.ui, text='', position=(-0.88, -0.45), origin=(0, 0), scale=1.4, color=color.white, background=True)
    ammo_text = Text(parent=camera.ui, text='Ammo: 0/0', position=(0.8, 0.44), origin=(0, 0), scale=1.2, color=color.white, background=True)
    player_hp_text = Text(parent=camera.ui, text='HP: 100/100', position=(-0.96, 0.45), origin=(0, 0), scale=1.2, color=color.rgb(255/255, 80/255, 80/255), background=True)
    player_stamina_text = Text(parent=camera.ui, text='Stamina: 100/100', position=(-0.96, 0.39), origin=(0, 0), scale=1.2, color=color.rgb(100/255, 200/255, 255/255), background=True)
    player_money_text = Text(parent=camera.ui, text='Money: 0', position=(-0.96, 0.33), origin=(0, 0), scale=1.2, color=color.rgb(255/255, 220/255, 100/255), background=True)
    quest_text = Text(parent=camera.ui, text='Quest: Harvest wheat 0/100', position=(-0.96, 0.27), origin=(0, 0), scale=1.1, color=color.white, background=True)

    pause_menu = Entity(parent=camera.ui, enabled=False)
    Entity(parent=pause_menu, model='quad', color=color.rgba(0, 0, 0, 180/255), scale=(1.6, 1.2), position=(0, 0, 0))
    Text(text='Settings', parent=pause_menu, y=0.35, scale=2, color=color.white)
    Button(parent=pause_menu, text='Continue', scale=(0.5, 0.13), y=0.08)
    Button(parent=pause_menu, text='Exit', scale=(0.5, 0.13), y=-0.15)

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


def update_ammo_text(gun_ammo, gun_max_ammo):
    if ammo_text is not None:
        ammo_text.text = f"Ammo: {gun_ammo}/{gun_max_ammo}"


def update_player_hud(hp, max_hp, stamina, max_stamina, money):
    if player_hp_text is not None:
        player_hp_text.text = f"HP: {int(hp)}/{int(max_hp)}"
    if player_stamina_text is not None:
        player_stamina_text.text = f"Stamina: {int(stamina)}/{int(max_stamina)}"
    if player_money_text is not None:
        player_money_text.text = f"Money: {int(money)}"


def update_quest_text(name, progress, goal):
    if quest_text is not None:
        status = 'Completed' if progress >= goal else f'{progress}/{goal}'
        quest_text.text = f"Quest: {name} ({status})"


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
    else:
        world.sun.color = color.rgb(120/255, 140/255, 255/255)
        window.color = color.rgb(15/255, 20/255, 55/255)
        scene.fog_color = color.rgb(15/255, 20/255, 55/255)


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
