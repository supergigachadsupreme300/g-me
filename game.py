from ursina import Entity, color, Vec3, raycast, destroy, time, mouse, camera, application, held_keys

from math import atan2, degrees
import random
import pet
import sound_manager

import world

import inventory
import items
import fields
import tools

import building_system
import enemies
import rendering

import tasks
import stats

import cutscene_manager

_sad_ending_fired = False



MAX_PLACE_DISTANCE = 20

AXE_STAMINA_COST = 15
HOE_STAMINA_COST = 20
FIELD_PLACE_STAMINA_COST = 50

GUN_MAX_AMMO = 6

gun_ammo = 0

gun_projectiles = []

MOB_SPAWNER_TYPES = [
    ("Rat", enemies.spawn_rat),
    ("Grasshopper", enemies.spawn_grasshopper),
    ("Wolf", enemies.spawn_wolf),
    ("Sahur", enemies.spawn_sahur),
    ("Thief", enemies.spawn_thief),
    ("Dog Thief", enemies.spawn_dog_thief),
    ("Zombie", enemies.spawn_zombie),
    ("Mushroom", enemies.spawn_mushroom),
    ("Arrogant Wheat", enemies.spawn_arrogant_wheat),
    ("Dinosaur", enemies.spawn_dinosaur),
]

mob_spawner_index = 0

game_paused = False
quest_menu_open = False
quest_panel_scroll = 0

stamina_regen_rate = 25.0  # per second

stamina_sprint_cost = 35.0  # per second while sprinting

sprint_speed_multiplier = 2.0

next_enemy_spawn_absolute = None


WHEAT_PRICE = 10

DAMAGED_WHEAT_PRICE = 3

TIME_SPEED = 1.0  # in-game minutes per real second

current_day = 1

time_of_day = 8.0

last_time_stage = None


crosshair = None



def update_ammo_text():

    rendering.update_ammo_text(gun_ammo, GUN_MAX_AMMO)



def get_mobspawner_name():
    return MOB_SPAWNER_TYPES[mob_spawner_index][0]


def set_mobspawner_index(index):
    global mob_spawner_index
    mob_spawner_index = index % len(MOB_SPAWNER_TYPES)
    inventory.set_mobspawner_target(get_mobspawner_name())


def cycle_mobspawner(delta):
    set_mobspawner_index(mob_spawner_index + delta)
    inventory.show_message(f"Mob spawner: {get_mobspawner_name()}", 1.5)


def spawn_selected_mob(position):
    name, spawn_fn = MOB_SPAWNER_TYPES[mob_spawner_index]
    try:
        spawn_fn(position)
        inventory.show_message(f"Spawned {name}", 1.5)
    except Exception as e:
        print(f"Failed to spawn {name}: {e}")
        inventory.show_message(f"Unable to spawn {name}", 1.5)


def toggle_pause(paused: bool):
    global game_paused
    game_paused = paused
    rendering.toggle_pause(paused)

    # Đóng băng hoàn toàn người chơi và camera khi pause
    try:
        if world.player is not None:
            if paused:
                world.player.enabled = False  # Vô hiệu hóa cả di chuyển lẫn góc nhìn camera
            else:
                world.player.enabled = True   # Kích hoạt lại bình thường
    except Exception:
        pass

    if paused:
        inventory.show_message('Game paused', 1.5)
    else:
        inventory.show_message('Resumed', 1.0)



def format_time():

    hours = int(time_of_day)

    minutes = int((time_of_day - hours) * 60)

    return f"Day {current_day} - {hours:02d}:{minutes:02d}"



def update_time_ui():

    rendering.update_time_ui(current_day, time_of_day)



def set_day_night():

    rendering.set_day_night(time_of_day)


def set_time_of_day(hour: float):
    global time_of_day
    time_of_day = float(hour) % 24
    update_time_ui()
    set_day_night()


def get_time_stage():
    return rendering.get_time_stage(time_of_day)



def update_quest_ui():

    quest_name, quest_progress, quest_goal = tasks.get_quest_status()

    rendering.update_quest_text(quest_name, quest_progress, quest_goal)


def update_quest_panel():
    global quest_panel_scroll
    quests = tasks.get_quests()
    max_scroll = max(0, len(quests) - len(rendering.quest_panel_lines))
    quest_panel_scroll = max(0, min(quest_panel_scroll, max_scroll))
    rendering.refresh_quest_panel(quests, tasks.get_focused_index(), quest_panel_scroll)
    rendering.set_quest_focus_callbacks([lambda i=i: set_quest_focus(i + quest_panel_scroll) for i in range(len(rendering.quest_panel_lines))])


def set_quest_focus(index: int):
    tasks.set_focused_quest(index)
    update_quest_ui()
    update_quest_panel()

def scroll_quest_panel(delta: int):
    global quest_panel_scroll
    quests = tasks.get_quests()
    max_scroll = max(0, len(quests) - len(rendering.quest_panel_lines))
    quest_panel_scroll = max(0, min(quest_panel_scroll + delta, max_scroll))
    if quest_menu_open:
        update_quest_panel()


def should_spawn_night_enemies():

    global next_enemy_spawn_absolute

    absolute_time = current_day * 24 + time_of_day


    # Initialize the first night spawn point when night starts

    if next_enemy_spawn_absolute is None:

        if rendering.NIGHT_START <= time_of_day < 24:

            next_enemy_spawn_absolute = current_day * 24 + rendering.NIGHT_START

        elif 0 <= time_of_day < rendering.DAY_START:

            next_enemy_spawn_absolute = current_day * 24 + 0.5


    if next_enemy_spawn_absolute is None:

        return False


    if absolute_time >= next_enemy_spawn_absolute:

        if rendering.DAY_START <= next_enemy_spawn_absolute % 24 < rendering.NIGHT_START:

            next_enemy_spawn_absolute = None

            return False


        # Advance to the next spawn time for the night cycle

        next_enemy_spawn_absolute += 1.0

        if next_enemy_spawn_absolute % 24 == rendering.DAY_START:

            next_enemy_spawn_absolute = None

        return True


    return False


def spawn_enemy_on_edge(count=4):

    spawn_functions = [

        enemies.spawn_rat,

        enemies.spawn_grasshopper,

        enemies.spawn_wolf,

        enemies.spawn_sahur,

        enemies.spawn_thief,       

        enemies.spawn_dog_thief,   

        enemies.spawn_zombie,

        enemies.spawn_dinosaur,

        enemies.spawn_mushroom

    ]

    MAX_ENEMIES = 12

    if len(enemies.enemies) >= MAX_ENEMIES:
        return


    for i in range(count):

        if len(enemies.enemies) >= MAX_ENEMIES:

            break


        edge = world.GROUND_HALF - 2

        if random.random() < 0.5:

            x = random.choice([-edge, edge])

            z = random.uniform(-edge, edge)

        else:

            x = random.uniform(-edge, edge)

            z = random.choice([-edge, edge])

        rand = random.random()

        if rand < 0.7:

            enemies.spawn_rat(Vec3(x, 1, z))

        elif rand < 0.82:

            enemies.spawn_grasshopper(Vec3(x, 1, z))

        elif rand < 0.90:

            enemies.spawn_wolf(Vec3(x, 1, z))

        elif rand < 0.96:

            enemies.spawn_thief(Vec3(x, 1, z))

        else:

            enemies.spawn_sahur(Vec3(x, 1, z))


def spawn_projectile(position, direction):

    projectile = Entity(model='sphere', color=color.yellow, scale=0.15, position=position, collider='box')

    projectile.velocity = direction.normalized() * 30

    projectile.damage = 12

    projectile.lifetime = 2.0

    projectile.age = 0.0

    gun_projectiles.append(projectile)

    return projectile



def update_projectiles():

    for projectile in list(gun_projectiles):

        projectile.position += projectile.velocity * time.dt

        projectile.age += time.dt

        hit_info = projectile.intersects(ignore=(world.player,))

        if hit_info.hit:

            enemy = enemies.find_enemy_by_entity(hit_info.entity)

            if enemy:

                enemy.take_damage(projectile.damage)

            destroy(projectile)

            gun_projectiles.remove(projectile)
            continue

        if projectile.age >= projectile.lifetime:

            destroy(projectile)

            gun_projectiles.remove(projectile)



def consume_ammo_item():

    for i, slot in enumerate(inventory.inventory):

        if inventory.get_item(slot) == 'ammo':

            inventory.remove_item(i)

            inventory.update_inventory_ui()

            return True

    return False



def spawn_rats_for_night():

    count = max(3, 2 + current_day)
    spawn_enemy_on_edge(count)

    inventory.show_message(f"Midnight: {count} rats have appeared!", 2.5)



def advance_time_to(target_hour):

    global time_of_day, current_day

    if target_hour <= time_of_day:

        current_day += 1

        spawn_rats_for_night()

    time_of_day = float(target_hour)
    update_time_ui()

    set_day_night()



def prompt_sleep():

    global game_paused

    game_paused = True

    rendering.toggle_bed_menu(True)



def close_sleep_menu():

    global game_paused

    rendering.toggle_bed_menu(False)

    game_paused = False



def confirm_sleep(should_sleep: bool):

    if should_sleep:

        if get_time_stage() in ('day', 'dusk'):

            advance_time_to(int(rendering.NIGHT_START))

            inventory.show_message('Slept until nightfall.', 2)

        else:

            advance_time_to(6)

            inventory.show_message('Slept until 6:00 AM.', 2)
    close_sleep_menu()



def select_slot(index):

    inventory.selected_slot = index

    current_item = inventory.get_item(inventory.inventory[index])

    tools.set_active_item(current_item)

    rendering.show_ammo(current_item == "gun")

    inventory.update_inventory_ui()



def snap_to_grid(position):

    return Vec3(round(position.x), position.y, round(position.z))



def update():

    global time_of_day, current_day, last_time_stage, next_enemy_spawn_absolute, _sad_ending_fired, game_paused

    cutscene_manager.manager.update()

    # Sad ending trigger: day 11+ and player never married the wife
    if (not _sad_ending_fired
            and current_day >= 11
            and not world.wife_married
            and not cutscene_manager.manager.is_active):
        _sad_ending_fired = True
        game_paused = True
        cutscene_manager.play_sad_ending()
        return

    # Happy ending cutscene (delegated through cutscene_manager)
    if cutscene_manager.update():
        return

    if game_paused:
        return


    previous_stage = last_time_stage

    time_of_day += time.dt * TIME_SPEED / 60.0

    if time_of_day >= 24:

        time_of_day -= 24

        current_day += 1

        spawn_rats_for_night()

    current_stage = get_time_stage()

    if current_stage != previous_stage:
        last_time_stage = current_stage

        if current_stage == 'day':

            inventory.show_message('It is now daytime.', 1.5)

        elif current_stage == 'dusk':

            inventory.show_message('Hoàng hôn đang buông xuống...', 2.0)

        else:

            inventory.show_message('The night has arrived.', 1.5)
    update_time_ui()

    set_day_night()


    if should_spawn_night_enemies():
        spawn_enemy_on_edge(max(3, 2 + current_day))

        inventory.show_message('Night enemies have spawned!', 2.0)


    if world.player is not None:

        # Sprint stamina handling

        if held_keys['shift'] or held_keys['left shift'] or held_keys['right shift']:

            if world.player.stamina > 0:

                world.player.is_sprinting = True

                world.player.speed = world.player.base_speed * world.player.sprint_speed_multiplier

                world.player.stamina -= stamina_sprint_cost * time.dt

                if world.player.stamina < 0:

                    world.player.stamina = 0

            else:

                world.player.is_sprinting = False

                world.player.speed = world.player.base_speed

        else:

            world.player.is_sprinting = False

            world.player.speed = world.player.base_speed

            if world.player.stamina < world.player.max_stamina:

                world.player.stamina += stamina_regen_rate * time.dt

                if world.player.stamina > world.player.max_stamina:

                    world.player.stamina = world.player.max_stamina


        # Update HUD

        rendering.update_player_hud(world.player.hp, world.player.max_hp, world.player.stamina, world.player.max_stamina, world.player.money)


    update_projectiles()
    enemies.update_enemies()
    pet.update_pets()

    # Peashooter auto-fire and projectile updates

    try:

        fields.update_peashooters()

        fields.update_peashooter_projectiles()

    except Exception:
        pass
    # update thrown items (projectiles) so they move and become ground items on impact
    try:
        items.update_thrown_items(time.dt)
    except Exception:
        pass

    update_quest_ui()

    # world frame updates (vendor movement, etc.)

    try:
        world.update()

    except Exception:
        pass


    if tools.hoe.enabled:

        fields.field_preview.enabled = False

        hit = raycast(camera.world_position, camera.forward, distance=MAX_PLACE_DISTANCE, ignore=(world.player, fields.field_preview))

        point = None

        target_field = None


        if hit.hit:

            target_field = fields.find_field_by_entity(hit.entity)


        if target_field:

            dx = world.player.x - target_field["pos"].x

            dz = world.player.z - target_field["pos"].z

            if abs(dx) > abs(dz):

                offset = Vec3(1 if dx > 0 else -1, 0, 0)

            else:

                offset = Vec3(0, 0, 1 if dz > 0 else -1)

            point = target_field["pos"] + offset

        else:
            dir = camera.forward

            if abs(dir.y) > 1e-5:

                t = -camera.world_position.y / dir.y

                if 0 < t <= MAX_PLACE_DISTANCE:

                    point = camera.world_position + dir * t


        if point is None:

            fields.field_preview.enabled = False
            return


        if abs(point.x) > world.GROUND_HALF or abs(point.z) > world.GROUND_HALF:

            fields.field_preview.enabled = False
            return


        overlap = raycast(point + Vec3(0, 2, 0), Vec3(0, -1, 0), distance=3, ignore=(world.player, fields.field_preview))

        if overlap.hit and overlap.entity != world.ground and (target_field is None or overlap.entity != target_field["entity"]):

            fields.field_preview.enabled = False
            return


        fields.field_preview.position = Vec3(point.x, 0.1, point.z)

        fields.field_preview.enabled = True


    elif tools.hammer.enabled:

        fields.field_preview.enabled = False

        point = None
        origin = camera.world_position
        direction = camera.forward


        if abs(direction.y) > 0.0001:

            t = -origin.y / direction.y

            if 0 < t <= MAX_PLACE_DISTANCE:

                point = origin + direction * t


        if point is None:

            building_system.hide_building_preview()
            return


        if abs(point.x) > world.GROUND_HALF or abs(point.z) > world.GROUND_HALF:

            building_system.hide_building_preview()
            return

        snapped = snap_to_grid(point)

        rotated_size = building_system.get_rotated_size(building_system.get_current_building())

        preview_pos = Vec3(snapped.x, rotated_size[1] / 2, snapped.z)

        valid = building_system.can_place_building(preview_pos)

        building_system.update_building_preview(preview_pos, valid)

    else:

        fields.field_preview.enabled = False

        building_system.hide_building_preview()



def is_bed_entity(entity):
    current = entity

    while current is not None:

        if getattr(current, 'is_bed', False):

            return True

        current = getattr(current, 'parent', None)

    return False



def is_buffalo_entity(entity):
    current = entity

    while current is not None:

        if getattr(current, 'is_buffalo', False):
            return current

        current = getattr(current, 'parent', None)

    return None



def is_vendor_entity(entity):
    current = entity

    while current is not None:

        if getattr(current, 'is_vendor', False):
            return current

        current = getattr(current, 'parent', None)

    return None



def show_buffalo_dialog():

    global game_paused

    game_paused = True

    rendering.show_buffalo_dialog(True)



def close_buffalo_dialog():

    global game_paused

    game_paused = False

    rendering.show_buffalo_dialog(False)



def sell_wheat_to_buffalo():

    wheat_amount = inventory.count_item('wheat')

    damaged_amount = inventory.count_item('damaged wheat')

    if wheat_amount == 0 and damaged_amount == 0:

        inventory.show_message('No wheat to sell', 2)

        close_buffalo_dialog()
        return

    inventory.remove_all('wheat')

    inventory.remove_all('damaged wheat')

    total_money = wheat_amount * WHEAT_PRICE + damaged_amount * DAMAGED_WHEAT_PRICE

    if world.player is not None:

        world.player.money += total_money

    inventory.show_message(f'Sold {wheat_amount} wheat + {damaged_amount} damaged wheat for {total_money} coins', 3)

    inventory.update_inventory_ui()

    close_buffalo_dialog()



def input(key):

    handle_input(key)


def face_buffalo_towards_player(buffalo_entity):

    if buffalo_entity is None:
        return

    dx = world.player.x - buffalo_entity.x

    dz = world.player.z - buffalo_entity.z

    if dx == 0 and dz == 0:
        return

    # Adjust yaw so the model faces the player on the horizontal plane.

    angle = degrees(atan2(dx, dz)) + 180

    buffalo_entity.rotation_x = 0

    buffalo_entity.rotation_z = 0

    buffalo_entity.rotation_y = angle % 360



def setup_game():

    if world.player is not None:

        try:

            world.player.speed = world.player.base_speed

        except Exception:
            pass

    tasks.initialize_quests()
    if tasks.get_active_quest() is None:

        tasks.set_active_quest(tasks.create_harvest_wheat_quest())

    if world.player is not None:

        rendering.update_player_hud(world.player.hp, world.player.max_hp, world.player.stamina, world.player.max_stamina, world.player.money)

        current_item = inventory.get_item(inventory.inventory[inventory.selected_slot])

        rendering.show_ammo(current_item == "gun")

    update_quest_ui()


def _marry_yes():
    rendering.show_marriage_menu(False)
    if world.player.money >= 10_000_000:
        world.player.money -= 10_000_000
        world.wife_married = True
        inventory.show_message('You are now married! Congratulations!', 5)
    else:
        needed = 10_000_000 - int(world.player.money)
        inventory.show_message(f'Not enough coins! You need {needed:,} more.', 3)


def _marry_no():
    rendering.show_marriage_menu(False)
    inventory.show_message('Maybe another time...', 2)


def handle_input(key):
    # (Summon keys removed: t,p,m,k,l,n)
    # Input for summoning debug monsters was intentionally removed.

    global gun_ammo, game_paused, _sad_ending_fired

    if key == 'f12':
        if not cutscene_manager.manager.is_active:
            _sad_ending_fired = True
            game_paused = True
            cutscene_manager.play_sad_ending()
        return

    if cutscene_manager.manager.is_active:
        return

    # Happy ending input handling delegated to cutscene_manager
    if cutscene_manager.handle_input(key):
        return

    if key == 'f9':
        cutscene_manager.request_happy_ending()
        return

    if key == 'f10':
        from ursina import window
        window.render_mode = 'default'
        inventory.show_message('Đã tắt chế độ wireframe', 1.5)
        return

    if key == 'f11':
        from ursina import window
        # Toggle between wireframe and default render modes
        try:
            if getattr(window, 'render_mode', 'default') == 'wireframe':
                window.render_mode = 'default'
                inventory.show_message('Đã tắt chế độ wireframe', 1.5)
            else:
                window.render_mode = 'wireframe'
                inventory.show_message('Đã bật chế độ wireframe', 1.5)
        except Exception:
            # Fallback: set to default if anything goes wrong
            try:
                window.render_mode = 'default'
            except Exception:
                pass
        return

    if key in [str(i) for i in range(1, 10)] + ['0']:

        idx = 9 if key == '0' else int(key) - 1

        select_slot(idx)
        return


    if key == 'e':

        # Wife marriage interaction (check before door so it takes priority when near)
        if world.wife_entity is not None and not world.wife_married:
            _wp = Vec3(world.wife_entity.x, 0, world.wife_entity.z)
            _pp = Vec3(world.player.x,      0, world.player.z)
            if (_pp - _wp).length() < 5:
                rendering.show_marriage_menu(True)
                rendering.set_marriage_callbacks(_marry_yes, _marry_no)
                return

        # Wife house door
        if world.wife_door_pivot is not None:
            _dp = Vec3(world.wife_door_pivot.x, 0, world.wife_door_pivot.z)
            _pp = Vec3(world.player.x, 0, world.player.z)
            if (_pp - _dp).length() < 5:
                world.wife_door_open = not world.wife_door_open
                world.wife_door_pivot.animate(
                    'rotation_y', -90 if world.wife_door_open else 0, duration=0.35)
                return

        if rendering.bed_confirm_menu is not None and rendering.bed_confirm_menu.enabled:
            return

        hit_info = raycast(

            camera.world_position,

            camera.forward,

            distance=3,

            ignore=(world.player, world.ground, fields.field_preview, building_system.building_preview)
        )

        if hit_info.hit:

            root = items.find_ground_item_root(hit_info.entity)

            if root is not None:

                added = inventory.add_item(root.item_type)

                if not added:

                    inventory.show_message("Inventory full!", 2)

                else:

                    inventory.update_inventory_ui()

                    inventory.show_message(f"Picked up {root.item_type}", 1.5)
                    destroy(root)

                    if inventory.get_item(inventory.inventory[inventory.selected_slot]) is None:

                        non_empty_slot = next((i for i, slot in enumerate(inventory.inventory) if inventory.get_item(slot) is not None), None)

                        if non_empty_slot is not None:
                            select_slot(non_empty_slot)
                return


    if key == 'q':

        slot = inventory.inventory[inventory.selected_slot]

        item_type = inventory.get_item(slot)

        if item_type is None:

            inventory.show_message("No item in selected slot", 1.5)

        else:
            # spawn a thrown projectile from player's position with forward velocity
            start_pos = world.player.position + Vec3(0, 1.2, 0) + world.player.forward * 1.2
            throw_speed = 10.0
            upward_speed = 5.0
            velocity = world.player.forward * throw_speed + Vec3(0, upward_speed, 0)
            items.spawn_thrown_item(item_type, start_pos, velocity)

            # remove item from inventory immediately and refresh UI
            if inventory.is_stackable(item_type) and inventory.get_count(slot) > 1:
                inventory.remove_item(inventory.selected_slot)
            else:
                inventory.inventory[inventory.selected_slot] = None

            # if selected slot became empty, try to auto-select next non-empty slot
            if inventory.get_item(inventory.inventory[inventory.selected_slot]) is None:
                non_empty_slot = next((i for i, s in enumerate(inventory.inventory) if inventory.get_item(s) is not None), None)
                if non_empty_slot is not None:
                    select_slot(non_empty_slot)
                else:
                    # no other items — clear held-item visuals by re-selecting the same slot
                    select_slot(inventory.selected_slot)
                    inventory.update_inventory_ui()
            else:
                inventory.update_inventory_ui()
        return


    if key == 'j':
        global quest_menu_open
        quest_menu_open = not quest_menu_open
        if quest_menu_open:
            update_quest_panel()
        rendering.show_quest_panel(quest_menu_open)
        return

    if quest_menu_open and key in ('wheel down', 'scroll down', 'wheel_down'):
        scroll_quest_panel(1)
        return

    if quest_menu_open and key in ('wheel up', 'scroll up', 'wheel_up'):
        scroll_quest_panel(-1)
        return


    if key == 'escape':

        if rendering.bed_confirm_menu is not None and rendering.bed_confirm_menu.enabled:
            close_sleep_menu()

        else:
            toggle_pause(not game_paused)
        return


    if key == 'left mouse down':

        if rendering.buffalo_dialog is not None and rendering.buffalo_dialog.enabled:
            return

        current_item = inventory.get_item(inventory.inventory[inventory.selected_slot])
        if current_item == "mì hảo hảo":
            if world.player is not None:
                world.player.hp = min(world.player.max_hp, world.player.hp + 30)
            inventory.remove_item(inventory.selected_slot)
            if inventory.get_item(inventory.inventory[inventory.selected_slot]) is None:
                select_slot(inventory.selected_slot)
            inventory.update_inventory_ui()
            inventory.show_message("Ăn mì hảo hảo, hồi 30 HP", 2)
            return
        if current_item == "mobspawner":
            pos = world.player.position + world.player.forward * 5
            pos.y = 1
            spawn_selected_mob(pos)
            return

        hit_info = raycast(camera.world_position, camera.forward, distance=MAX_PLACE_DISTANCE)

        if hit_info.hit and is_bed_entity(hit_info.entity):
            prompt_sleep()
            return

        if hit_info.hit:

            buffalo_entity = is_buffalo_entity(hit_info.entity)

            if buffalo_entity is not None:

                face_buffalo_towards_player(buffalo_entity)

                rendering.show_buffalo_dialog(True)

                game_paused = True
                return

            # vendor interaction (mirror buffalo interaction)

            # vendor spawn button: always attempt to spawn a new vendor regardless of current vendor

            spawn_btn = None

            try:

                if hit_info.hit:

                    spawn_btn = world.is_vendor_spawn_entity(hit_info.entity)

            except Exception:

                spawn_btn = None

            # second raycast that ignores current vendor to catch the button behind it

            if spawn_btn is None:

                ignore_tuple = (world.vendor_root,) if getattr(world, 'vendor_root', None) is not None else ()

                try:

                    hit2 = raycast(camera.world_position, camera.forward, distance=MAX_PLACE_DISTANCE, ignore=ignore_tuple)

                    if hit2.hit:

                        spawn_btn = world.is_vendor_spawn_entity(hit2.entity)

                except Exception:

                    spawn_btn = None

            if spawn_btn is not None:

                # spawn_vendor_cart destroys any existing vendor already; always call it

                world.spawn_vendor_cart()
                return

            # vendor interaction (mirror buffalo interaction)

            vendor_entity = is_vendor_entity(hit_info.entity)

            if vendor_entity is not None:

                try:

                    import shop

                    shop.open_shop()

                except Exception as e:

                    print('Failed to open shop from game input:', e)
                return

        if inventory.get_item(inventory.inventory[inventory.selected_slot]) == "seed":

            hit_info = raycast(camera.world_position, camera.forward, distance=MAX_PLACE_DISTANCE)

            if hit_info.hit:

                field_data = fields.find_field_by_entity(hit_info.entity)

                if field_data:

                    success = fields.plant_wheat_on_field(field_data)

                    if success:

                        inventory.remove_item(inventory.selected_slot)

                        if inventory.get_item(inventory.inventory[inventory.selected_slot]) is None:

                            select_slot(inventory.selected_slot)

                        inventory.update_inventory_ui()

                        inventory.show_message("Wheat planted on field", 1.5)

                    else:

                        inventory.show_message("Wheat is already growing here", 1.5)
            return


        if inventory.get_item(inventory.inventory[inventory.selected_slot]) == "peashooter seed":

            hit_info = raycast(camera.world_position, camera.forward, distance=MAX_PLACE_DISTANCE)

            if hit_info.hit:

                field_data = fields.find_field_by_entity(hit_info.entity)

                if field_data:

                    success = fields.plant_peashooter_on_field(field_data)

                    if success:

                        inventory.remove_item(inventory.selected_slot)

                        if inventory.get_item(inventory.inventory[inventory.selected_slot]) is None:

                            select_slot(inventory.selected_slot)

                        inventory.update_inventory_ui()

                        inventory.show_message("Peashooter planted on field", 1.5)

                    else:

                        inventory.show_message("Cannot plant here", 1.5)
            return


        if inventory.get_item(inventory.inventory[inventory.selected_slot]) == "fertilizer":

            hit_info = raycast(camera.world_position, camera.forward, distance=MAX_PLACE_DISTANCE)

            if hit_info.hit:

                field_data = fields.find_field_by_entity(hit_info.entity)

                if field_data and field_data["wheat_planted"] and field_data["wheat_hp"] > 0:

                    field_data["wheat_hp"] = min(20, field_data["wheat_hp"] + 5)

                    fields.update_wheat_health_bar(field_data)

                    inventory.remove_item(inventory.selected_slot)

                    if inventory.get_item(inventory.inventory[inventory.selected_slot]) is None:

                        select_slot(inventory.selected_slot)

                    inventory.update_inventory_ui()

                    inventory.show_message("Wheat healed with fertilizer", 1.5)

                else:

                    inventory.show_message("No wheat to fertilize here", 1.5)
            return


        if tools.scythe.enabled:

            tools.swing_item(tools.scythe)
            try:
                sound_manager.play('sickle')
            except Exception:
                pass

            hit_info = raycast(camera.world_position, camera.forward, distance=MAX_PLACE_DISTANCE)

            if hit_info.hit:

                field_data = fields.find_field_by_entity(hit_info.entity)

                if field_data and field_data["wheat_planted"] and field_data["wheat_stage"] >= 4 and field_data["wheat_hp"] > 0:

                    harvested = "wheat" if field_data["wheat_stage"] >= 4 else "damaged wheat"

                    inventory.show_message("Harvested ripe wheat", 1.5)

                    fields.destroy_wheat(field_data)

                    # record stats before updating quest progress

                    try:

                        stats.record_harvest(1)

                    except Exception:
                        pass

                    completed = tasks.add_progress(1)

                    if completed:

                        reward = tasks.claim_reward()

                        if reward is not None and reward.get('money') and world.player is not None:

                            world.player.money += reward['money']

                            inventory.show_message(f'Quest completed: {tasks.active_quest.name} (+{reward["money"]} coins)', 3.0)

                    update_quest_ui()

                    if not inventory.add_item(harvested):

                        items.spawn_ground_item(harvested, world.player.position + world.player.forward * 2)

                        inventory.show_message("Inventory full, dropped harvested wheat", 2)

                    else:

                        inventory.update_inventory_ui()

                else:

                    inventory.show_message("No ripe wheat to harvest here", 1.5)
            return


        if tools.gun.enabled:

            if gun_ammo > 0:

                gun_ammo -= 1

                update_ammo_text()

                spawn_projectile(camera.world_position + camera.forward * 1.5, camera.forward)
                try:
                    sound_manager.play('gun')
                except Exception:
                    pass

                inventory.show_message("Shot fired", 1.0)

            else:

                inventory.show_message("No ammo. Press R to reload with ammo item", 1.5)
            return


        if tools.axe.enabled:

            if world.player is None or world.player.stamina < AXE_STAMINA_COST:
                inventory.show_message("Not enough stamina to swing axe", 1.5)
                return

            world.player.stamina -= AXE_STAMINA_COST
            tools.swing_item(tools.axe)
            try:
                sound_manager.play('axe')
            except Exception:
                pass

            hit_info = raycast(camera.world_position, camera.forward, distance=3)

            if hit_info.hit:

                for tree in world.trees:

                    if hit_info.entity == tree["trunk"]:

                        tree["hp"] -= 3

                        tree["bar"].scale_x = max(0, tree["hp"] / 5)

                        if tree["hp"] <= 0:

                            items.spawn_ground_item("wood", tree["trunk"].position + Vec3(0, 0, 2))

                            world.remove_tree(tree)

                        break


        if tools.pickaxe.enabled:

            tools.swing_item(tools.pickaxe)
            try:
                sound_manager.play('pickaxe')
            except Exception:
                pass

            hit_info = raycast(camera.world_position, camera.forward, distance=3)

            if hit_info.hit:

                for rock in world.rocks:

                    if hit_info.entity == rock["rock"]:

                        rock["hp"] -= 4

                        rock["bar"].scale_x = max(0, rock["hp"] / 7.5)

                        if rock["hp"] <= 0:

                            items.spawn_ground_item("stone", rock["rock"].position + Vec3(0, 0, 2))

                            world.remove_rock(rock)

                        break


        if tools.hoe.enabled:

            if world.player is None or world.player.stamina < HOE_STAMINA_COST:
                inventory.show_message("Not enough stamina to use hoe (20 needed)", 1.5)
                return

            tools.swing_item(tools.hoe)
            try:
                sound_manager.play('hoe')
            except Exception:
                pass

            world.player.stamina -= HOE_STAMINA_COST

            if fields.field_preview.enabled:

                pos = fields.field_preview.position

                if world.player is None or world.player.stamina < FIELD_PLACE_STAMINA_COST:
                    inventory.show_message("Not enough stamina to place field (50 needed)", 1.5)
                    return

                # Check existing field overlap
                exists = any((abs(f["pos"].x - pos.x) < 0.5 and abs(f["pos"].z - pos.z) < 0.5) for f in fields.fields)

                if exists:
                    inventory.show_message("Field already exists here", 1.2)
                    return

                # Prevent placement on road
                try:
                    if world.is_on_road(pos):
                        inventory.show_message("Cannot place field on road", 1.5)
                        return
                except Exception:
                    pass

                # Prevent placement overlapping house area
                if abs(pos.x) < 6.0 and abs(pos.z) < 6.0:
                    inventory.show_message("Cannot place field on or inside the house area", 1.5)
                    return

                # Prevent placement overlapping trees, rocks, buildings, vendors
                overlap = False
                try:
                    px = float(pos.x)
                    pz = float(pos.z)

                    def close2d(ax, az, bx, bz, thresh):
                        dx = ax - bx
                        dz = az - bz
                        return (dx*dx + dz*dz) <= (thresh * thresh)

                    # trees (use larger threshold to account for model footprint)
                    for t in getattr(world, 'trees', []):
                        try:
                            tx = float(t['trunk'].position.x)
                            tz = float(t['trunk'].position.z)
                            if close2d(px, pz, tx, tz, 5.0):
                                overlap = True
                                break
                        except Exception:
                            continue

                    # rocks
                    if not overlap:
                        for r in getattr(world, 'rocks', []):
                            try:
                                rx = float(r['rock'].position.x)
                                rz = float(r['rock'].position.z)
                                if close2d(px, pz, rx, rz, 2.5):
                                    overlap = True
                                    break
                            except Exception:
                                continue

                    # buildings
                    if not overlap:
                        for b in getattr(building_system, 'buildings', []):
                            try:
                                ent = b.get('entity') if isinstance(b, dict) else getattr(b, 'entity', None)
                                if ent is not None:
                                    bx = float(ent.position.x)
                                    bz = float(ent.position.z)
                                    if close2d(px, pz, bx, bz, 4.0):
                                        overlap = True
                                        break
                            except Exception:
                                continue

                    # vendors
                    if not overlap and getattr(world, 'vendor_root', None) is not None:
                        try:
                            vx = float(world.vendor_root.position.x)
                            vz = float(world.vendor_root.position.z)
                            if close2d(px, pz, vx, vz, 4.5):
                                overlap = True
                        except Exception:
                            pass
                except Exception:
                    overlap = False

                if overlap:
                    inventory.show_message("Cannot place field overlapping other objects", 1.5)
                    return

                # All checks passed: create field
                world.player.stamina -= FIELD_PLACE_STAMINA_COST
                fields.create_field(pos)
                inventory.show_message("Field created", 1.2)

        elif tools.sword.enabled:
            tools.swing_item(tools.sword)
            try:
                sound_manager.play('sword')
            except Exception:
                pass

            hit_info = raycast(camera.world_position, camera.forward, distance=3)

            if hit_info.hit:

                enemy = enemies.find_enemy_by_entity(hit_info.entity)

                if enemy:

                    enemy.take_damage(6)

                    inventory.show_message(f"Hit {enemy.__class__.__name__}", 1.5)
                    return

            inventory.show_message("Missed the attack", 1.0)

        elif tools.gun.enabled:
            pass

        elif tools.hammer.enabled:

            tools.swing_item(tools.hammer)
            try:
                sound_manager.play('hammer')
            except Exception:
                pass

            if building_system.building_preview.enabled:

                preview_pos = building_system.building_preview.position

                if building_system.can_place_building(preview_pos):

                    building_system.place_building(preview_pos)

                    building_system.hide_building_preview()

                    inventory.show_message("Building placed", 1.5)

                else:

                    inventory.show_message("Cannot place building here", 1.5)
        return


    if key == 'r' and tools.gun.enabled:

        if consume_ammo_item():

            gun_ammo = GUN_MAX_AMMO

            update_ammo_text()

            inventory.show_message("Reloaded gun", 1.5)

        else:

            inventory.show_message("No ammo item to reload", 1.5)
        return


    if key == 'r' and tools.hammer.enabled:

        building_system.rotate_building()

        if building_system.building_preview.enabled:

            valid = building_system.can_place_building(building_system.building_preview.position)

            building_system.update_building_preview(building_system.building_preview.position, valid)
        return


    if key == 'z' and inventory.get_item(inventory.inventory[inventory.selected_slot]) == "mobspawner":
        cycle_mobspawner(-1)
        return

    if key == 'x' and inventory.get_item(inventory.inventory[inventory.selected_slot]) == "mobspawner":
        cycle_mobspawner(1)
        return

    if key == 'z' and tools.hammer.enabled:

        building_system.prev_building()

        if building_system.building_preview.enabled:

            valid = building_system.can_place_building(building_system.building_preview.position)

            building_system.update_building_preview(building_system.building_preview.position, valid)
        return


    if key == 'x' and tools.hammer.enabled:

        building_system.next_building()

        if building_system.building_preview.enabled:

            valid = building_system.can_place_building(building_system.building_preview.position)

            building_system.update_building_preview(building_system.building_preview.position, valid)
        return



def setup_game():

    global crosshair

    items.spawn_ground_item("axe", Vec3(0, 1, 0))

    items.spawn_ground_item("pickaxe", Vec3(2, 1, 0))

    items.spawn_ground_item("hoe", Vec3(-2, 1, 0))

    items.spawn_ground_item("hammer", Vec3(-3, 1, 0))

    items.spawn_ground_item("seed", Vec3(4, 1, 0))

    items.spawn_ground_item("sword", Vec3(8, 1, 0))

    items.spawn_ground_item("gun", Vec3(10, 1, 0))

    items.spawn_ground_item("ammo", Vec3(12, 1, 0))

    items.spawn_ground_item("scythe", Vec3(14, 1, 0))

    items.spawn_ground_item("mobspawner", Vec3(16, 1, 0))

    items.spawn_ground_item("mì hảo hảo", Vec3(18, 1, 0))

    items.spawn_ground_item("wheat", Vec3(20,1,0))

    pet.spawn_dog(Vec3(2, 1, 2))

    pet.spawn_toad(Vec3(-2, 1, 2))

    items.spawn_ground_item("peashooter seed", Vec3(6, 1, 0))


    set_mobspawner_index(0)
    inventory.update_inventory_ui()

    if tasks.get_active_quest() is None:

        tasks.set_active_quest(tasks.create_harvest_wheat_quest())


    rendering.update_player_hud(world.player.hp, world.player.max_hp, world.player.stamina, world.player.max_stamina, world.player.money)

    update_quest_ui()

    update_time_ui()

    set_day_night()
    spawn_enemy_on_edge(8)


    crosshair = Entity(parent=camera, model='quad', color=color.white, scale=0.01, position=(0, 0, 1.2))


    rendering.set_pause_button_callbacks(lambda: toggle_pause(False), application.quit)

    rendering.set_bed_confirm_callbacks(lambda: confirm_sleep(True), lambda: confirm_sleep(False))

    rendering.set_buffalo_dialog_callbacks(lambda: sell_wheat_to_buffalo(), lambda: close_buffalo_dialog())


    select_slot(0)

