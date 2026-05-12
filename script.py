import os
import sys

os.environ.setdefault('PYTHONUTF8', '1')
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
import random

import world
import inventory
import items
import fields
import tools
import buildings

app = Ursina()
application.development_mode = False

world.create_world()
tools.setup_tools()
buildings.setup_building_system()

tools.arm.parent = camera
tools.axe.parent = camera
tools.pickaxe.parent = camera
tools.hoe.parent = camera
tools.hammer.parent = camera

tools.arm.position = (0.7, -0.6, 1.5)
tools.axe.position = (0.7, -0.6, 1.5)
tools.pickaxe.position = (0.7, -0.6, 1.5)
tools.hoe.position = (0.7, -0.6, 1.5)
tools.hammer.position = (0.7, -0.6, 1.5)

items.spawn_ground_item("axe", Vec3(0, 1, 0))
items.spawn_ground_item("pickaxe", Vec3(2, 1, 0))
items.spawn_ground_item("hoe", Vec3(-2, 1, 0))
items.spawn_ground_item("hammer", Vec3(6, 1, 0))
items.spawn_ground_item("seed", Vec3(4, 1, 0))

inventory.update_inventory_ui()

crosshair = Entity(parent=camera, model='quad', color=color.white, scale=0.01, position=(0, 0, 1.2))


def select_slot(index):
    inventory.selected_slot = index
    current_item = inventory.inventory[index]
    tools.set_active_item(current_item)
    inventory.update_inventory_ui()


def snap_to_grid(position):
    return Vec3(round(position.x), position.y, round(position.z))


select_slot(0)

MAX_PLACE_DISTANCE = 20


def update():
    if tools.hoe.enabled:
        fields.field_preview.enabled = False
        # Field preview logic
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

        # Find where camera ray hits ground plane (y = 0)
        if abs(direction.y) > 0.0001:

            t = -origin.y / direction.y

            if 0 < t <= MAX_PLACE_DISTANCE:
                point = origin + direction * t

        # No valid ground intersection
        if point is None:
            buildings.hide_building_preview()
            return

        # Keep inside world bounds
        if abs(point.x) > world.GROUND_HALF or abs(point.z) > world.GROUND_HALF:
            buildings.hide_building_preview()
            return

        snapped = snap_to_grid(point)

        rotated_size = buildings.get_rotated_size(
            buildings.get_current_building()
        )

        preview_pos = Vec3(
            snapped.x,
            rotated_size[1] / 2,
            snapped.z
        )

        valid = buildings.can_place_building(preview_pos)

        buildings.update_building_preview(preview_pos, valid)    
    else:
        fields.field_preview.enabled = False
        buildings.hide_building_preview()



def input(key):
    if key in [str(i) for i in range(1, 10)] + ['0']:
        if key == '0':
            idx = 9
        else:
            idx = int(key) - 1
        select_slot(idx)
        return

    if key == 'e':
        hit_info = raycast(camera.world_position, camera.forward, distance=3)
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
        elif tools.hammer.enabled:
            print("Input detected: LEFT CLICK with hammer")
            tools.swing_item(tools.hammer)
            if buildings.building_preview.enabled:
                preview_pos = buildings.building_preview.position
                if buildings.can_place_building(preview_pos):
                    buildings.place_building(preview_pos)
                    buildings.hide_building_preview()
                    inventory.show_message("Building placed", 1.5)
                else:
                    inventory.show_message("Cannot place building here", 1.5)
        return

    if key == 'r' and tools.hammer.enabled:
        print("Input detected: R - rotate building")
        buildings.rotate_building()
        if buildings.building_preview.enabled:
            valid = buildings.can_place_building(buildings.building_preview.position)
            buildings.update_building_preview(buildings.building_preview.position, valid)
        return

    if key == 'z' and tools.hammer.enabled:
        print("Input detected: Z - previous building")
        buildings.prev_building()
        if buildings.building_preview.enabled:
            valid = buildings.can_place_building(buildings.building_preview.position)
            buildings.update_building_preview(buildings.building_preview.position, valid)
        return

    if key == 'x' and tools.hammer.enabled:
        print("Input detected: X - next building")
        buildings.next_building()
        if buildings.building_preview.enabled:
            valid = buildings.can_place_building(buildings.building_preview.position)
            buildings.update_building_preview(buildings.building_preview.position, valid)
        return


inventory.update_inventory_ui()
app.run()
