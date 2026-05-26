from ursina import Entity, color, Vec3, raycast, destroy, time, mouse, camera, application, held_keys

from math import atan2, degrees
import random
import pet

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


MAX_PLACE_DISTANCE = 20

GUN_MAX_AMMO = 6

gun_ammo = 0

gun_projectiles = []

game_paused = False

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



def toggle_pause(paused: bool):

    global game_paused
    game_paused = paused
    rendering.toggle_pause(paused)

    # Freeze player movement when paused

    try:

        if world.player is not None:

            if paused:

                world.player.speed = 0

            else:

                # restore base speed

                world.player.speed = getattr(world.player, 'base_speed', 5.0)

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



def update_quest_ui():

    quest_name, quest_progress, quest_goal = tasks.get_quest_status()

    rendering.update_quest_text(quest_name, quest_progress, quest_goal)



def should_spawn_night_enemies():

    global next_enemy_spawn_absolute

    absolute_time = current_day * 24 + time_of_day


    # Initialize the first night spawn point when night starts

    if next_enemy_spawn_absolute is None:

        if 18.5 <= time_of_day < 24:

            next_enemy_spawn_absolute = current_day * 24 + 18.5

        elif 0 <= time_of_day < 6.5:

            next_enemy_spawn_absolute = current_day * 24 + 0.5


    if next_enemy_spawn_absolute is None:

        return False


    if absolute_time >= next_enemy_spawn_absolute:

        if next_enemy_spawn_absolute % 24 >= 6.5 and next_enemy_spawn_absolute % 24 < 18.5:

            next_enemy_spawn_absolute = None

            return False


        # Advance to the next spawn time for the night cycle

        next_enemy_spawn_absolute += 1.0

        if next_enemy_spawn_absolute % 24 == 6.5:

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

        if 6 <= time_of_day < 18:

            advance_time_to(18)

            inventory.show_message('Slept until 6:00 PM.', 2)

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

    global time_of_day, current_day, last_time_stage, next_enemy_spawn_absolute

    if game_paused:
        return


    previous_stage = last_time_stage

    time_of_day += time.dt * TIME_SPEED / 60.0

    if time_of_day >= 24:

        time_of_day -= 24

        current_day += 1

        spawn_rats_for_night()

    current_stage = 'day' if 6 <= time_of_day < 18 else 'night'

    if current_stage != previous_stage:
        last_time_stage = current_stage

        if current_stage == 'day':

            inventory.show_message('It is now daytime.', 1.5)

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

    if tasks.get_active_quest() is None:

        tasks.set_active_quest(tasks.create_harvest_wheat_quest())

    if world.player is not None:

        rendering.update_player_hud(world.player.hp, world.player.max_hp, world.player.stamina, world.player.max_stamina, world.player.money)

        current_item = inventory.get_item(inventory.inventory[inventory.selected_slot])

        rendering.show_ammo(current_item == "gun")

    update_quest_ui()



def handle_input(key):

    #=============================

    if key == 't':

        # Bấm phím T để gọi ĐÍCH DANH Tung Tung Sahur ra trước mặt

        pos = world.player.position + world.player.forward * 5 

        pos.y = 1 

        enemies.spawn_sahur(pos)

        inventory.show_message("Tung Tung Sahur xuất hiện!", 2.5)
        return

    if key == 'p':

        # Bấm phím P để triệu hồi Boss Khủng Long

        pos = world.player.position + world.player.forward * 8 # Sinh ra xa xa một chút vì nó rất to

        pos.y = 2 
        enemies.spawn_dinosaur(pos)

        inventory.show_message("CẢNH BÁO: BOSS KHỦNG LONG XUẤT HIỆN!", 3)
        return

    if key == 'm': 

        # Bấm phím M để gọi ngẫu nhiên 5 con quái vật từ danh sách bốc thăm
        spawn_enemy_on_edge(5)

        inventory.show_message("Đã triệu hồi 5 quái vật ngẫu nhiên!", 2)
        return


    if key == 'k': 

        # Bấm phím K để gọi ĐÍCH DANH 1 con Zombie ra ngay trước mặt người chơi 5 mét

        pos = world.player.position + world.player.forward * 5

        pos.y = 1 # Đảm bảo quái sinh ra ở trên mặt đất

        enemies.spawn_zombie(pos)

        inventory.show_message("Cảnh báo: Zombie xuất hiện!", 2)
        return
        

    if key == 'l':

        # Bấm phím L để gọi ĐÍCH DANH Lúa Kiêu Ngạo

        pos = world.player.position + world.player.forward * 5

        pos.y = 1

        enemies.spawn_arrogant_wheat(pos)

        inventory.show_message("Cảnh báo: Lúa không cúi đầu!", 2)
        return

    if key == 'n':

        # Bấm phím N (Nấm) để triệu hồi Quái vật Nấm

        pos = world.player.position + world.player.forward * 4 

        pos.y = 1 

        enemies.spawn_mushroom(pos)

        inventory.show_message("Nấm độc đã mọc lên!", 2)
        return

    #=============================

    global gun_ammo, game_paused

    if key in [str(i) for i in range(1, 10)] + ['0']:

        idx = 9 if key == '0' else int(key) - 1

        select_slot(idx)
        return


    if key == 'e':

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

            pos = world.player.position + world.player.forward * 2

            items.spawn_ground_item(item_type, pos)

            if inventory.is_stackable(item_type) and inventory.get_count(slot) > 1:

                inventory.remove_item(inventory.selected_slot)

            else:

                inventory.inventory[inventory.selected_slot] = None

                select_slot(inventory.selected_slot)

            inventory.update_inventory_ui()

            inventory.show_message(f"Dropped {item_type}", 1.2)
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

                inventory.show_message("Shot fired", 1.0)

            else:

                inventory.show_message("No ammo. Press R to reload with ammo item", 1.5)
            return


        if tools.axe.enabled:

            tools.swing_item(tools.axe)

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

            tools.swing_item(tools.hoe)

            if fields.field_preview.enabled:

                pos = fields.field_preview.position

                exists = any((abs(f["pos"].x - pos.x) < 0.5 and abs(f["pos"].z - pos.z) < 0.5) for f in fields.fields)

                if not exists:
                    fields.create_field(pos)

                    inventory.show_message("Field created", 1.2)

                else:

                    inventory.show_message("Field already exists here", 1.2)

        elif tools.sword.enabled:
            tools.swing_item(tools.sword)

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

    items.spawn_ground_item("seed", Vec3(4, 1, 0))

    items.spawn_ground_item("sword", Vec3(8, 1, 0))

    items.spawn_ground_item("gun", Vec3(10, 1, 0))

    items.spawn_ground_item("ammo", Vec3(12, 1, 0))

    items.spawn_ground_item("scythe", Vec3(14, 1, 0))

    pet.spawn_dog(Vec3(2, 1, 2))

    pet.spawn_toad(Vec3(-2, 1, 2))

    items.spawn_ground_item("peashooter seed", Vec3(6, 1, 0))


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

