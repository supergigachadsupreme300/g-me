from ursina import Entity, color, Vec3, raycast, destroy, time, mouse, camera, application
import random

import world
import inventory
import items
import fields
import tools
import building_system
import enemies
import rendering

MAX_PLACE_DISTANCE = 20
GUN_MAX_AMMO = 6
gun_ammo = 0
gun_projectiles = []
game_paused = False

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


def spawn_rats_on_edge(count=4):
    for i in range(count):
        edge = world.GROUND_HALF - 2
        if random.random() < 0.5:
            x = random.choice([-edge, edge])
            z = random.uniform(-edge, edge)
        else:
            x = random.uniform(-edge, edge)
            z = random.choice([-edge, edge])
        enemies.spawn_rat(Vec3(x, 1, z))


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
    for i, it in enumerate(inventory.inventory):
        if it == 'ammo':
            inventory.inventory[i] = None
            inventory.update_inventory_ui()
            return True
    return False


def spawn_rats_for_night():
    count = max(3, 2 + current_day)
    spawn_rats_on_edge(count)
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
    current_item = inventory.inventory[index]
    tools.set_active_item(current_item)
    inventory.update_inventory_ui()


def snap_to_grid(position):
    return Vec3(round(position.x), position.y, round(position.z))


def update():
    global time_of_day, current_day, last_time_stage
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

    update_projectiles()
    enemies.update_enemies()


def is_bed_entity(entity):
    current = entity
    while current is not None:
        if getattr(current, 'is_bed', False):
            return True
        current = getattr(current, 'parent', None)
    return False


def input(key):
    handle_input(key)


def handle_input(key):
    global gun_ammo
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
        if hit_info.hit and is_bed_entity(hit_info.entity):
            prompt_sleep()
            return
        if hit_info.hit:
            root = items.find_ground_item_root(hit_info.entity)
            if root is not None:
                slot = inventory.first_empty_slot()
                if slot is None:
                    inventory.show_message("Inventory full!", 2)
                else:
                    inventory.inventory[slot] = root.item_type
                    inventory.update_inventory_ui()
                    inventory.show_message(f"Picked up {root.item_type}", 1.5)
                    destroy(root)
                    if inventory.inventory[inventory.selected_slot] is None:
                        select_slot(slot)
                return

    if key == 'q':
        it = inventory.inventory[inventory.selected_slot]
        if it is None:
            inventory.show_message("No item in selected slot", 1.5)
        else:
            pos = world.player.position + world.player.forward * 2
            items.spawn_ground_item(it, pos)
            inventory.inventory[inventory.selected_slot] = None
            select_slot(inventory.selected_slot)
            inventory.update_inventory_ui()
            inventory.show_message(f"Dropped {it}", 1.2)
        return

    if key == 'escape':
        if rendering.bed_confirm_menu is not None and rendering.bed_confirm_menu.enabled:
            close_sleep_menu()
        else:
            toggle_pause(not game_paused)
        return

    if key == 'left mouse down':
        if inventory.inventory[inventory.selected_slot] == "seed":
            hit_info = raycast(camera.world_position, camera.forward, distance=MAX_PLACE_DISTANCE)
            if hit_info.hit:
                field_data = fields.find_field_by_entity(hit_info.entity)
                if field_data:
                    success = fields.plant_rice_on_field(field_data)
                    if success:
                        inventory.inventory[inventory.selected_slot] = None
                        select_slot(inventory.selected_slot)
                        inventory.update_inventory_ui()
                        inventory.show_message("Rice planted on field", 1.5)
                    else:
                        inventory.show_message("Rice is already growing here", 1.5)
            return

        if inventory.inventory[inventory.selected_slot] == "fertilizer":
            hit_info = raycast(camera.world_position, camera.forward, distance=MAX_PLACE_DISTANCE)
            if hit_info.hit:
                field_data = fields.find_field_by_entity(hit_info.entity)
                if field_data and field_data["rice_planted"] and field_data["rice_hp"] > 0:
                    field_data["rice_hp"] = min(20, field_data["rice_hp"] + 5)
                    fields.update_rice_health_bar(field_data)
                    inventory.inventory[inventory.selected_slot] = None
                    select_slot(inventory.selected_slot)
                    inventory.update_inventory_ui()
                    inventory.show_message("Rice healed with fertilizer", 1.5)
                else:
                    inventory.show_message("No rice to fertilize here", 1.5)
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
                            destroy(tree["trunk"])
                            destroy(tree["leaves"])
                            destroy(tree["bar"])
                            world.trees.remove(tree)
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
                            destroy(rock["rock"])
                            destroy(rock["bar"])
                            world.rocks.remove(rock)
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
    items.spawn_ground_item("hammer", Vec3(6, 1, 0))
    items.spawn_ground_item("seed", Vec3(4, 1, 0))
    items.spawn_ground_item("sword", Vec3(8, 1, 0))
    items.spawn_ground_item("gun", Vec3(10, 1, 0))
    items.spawn_ground_item("ammo", Vec3(12, 1, 0))

    inventory.update_inventory_ui()
    update_time_ui()
    set_day_night()
    spawn_rats_on_edge(4)

    crosshair = Entity(parent=camera, model='quad', color=color.white, scale=0.01, position=(0, 0, 1.2))

    rendering.set_pause_button_callbacks(lambda: toggle_pause(False), application.quit)
    rendering.set_bed_confirm_callbacks(lambda: confirm_sleep(True), lambda: confirm_sleep(False))

    select_slot(0)
