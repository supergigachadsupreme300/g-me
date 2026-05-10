from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
import random
import math

app = Ursina()
application.development_mode = False

# -------------------------
# Basic world & player
# -------------------------
GROUND_SIZE = 150   # map rộng gấp 3 lần
GROUND_HALF = GROUND_SIZE / 2


ground = Entity(
    model='plane',
    scale=(GROUND_SIZE,1,GROUND_SIZE),
    color=color.rgb(0,80,0),   # xanh lá đậm hơn
    collider='mesh'
)



player = FirstPersonController()
player.cursor.visible = False
player_model = Entity(model='cube', color=color.azure, scale=(1,2,1), parent=player, position=(0,-1,0))

Sky()
DirectionalLight().look_at(Vec3(1,-1,-1))

# -------------------------
# Inventory (10 slots)
# -------------------------
inventory = [None] * 10
selected_slot = 0  # 0..9

inventory_text = Text(text="", position=(0,-0.45), origin=(0,0), scale=1.0, background=True)
message_text = Text(text="", position=(0,0.35), origin=(0,0), scale=1.2, color=color.azure)

def update_inventory_ui():
    slots = []
    for i, it in enumerate(inventory):
        label = it if it is not None else "empty"
        if i == selected_slot:
            slots.append(f"[{i+1}:{label}]")
        else:
            slots.append(f"{i+1}:{label}")
    inventory_text.text = "   ".join(slots)

def show_message(txt, duration=2):
    message_text.text = txt
    invoke(lambda: setattr(message_text, "text", ""), delay=duration)

update_inventory_ui()

# -------------------------
# Hand / tools on hand
# -------------------------
arm = Entity(model='cube', color=color.brown, scale=(0.3,1,0.3),
             position=(0.7,-0.6,1.5), rotation=(20,-30,0), parent=camera, enabled=True)

def make_axe_on_parent(parent_entity):
    root = Entity(parent=parent_entity, position=(0,0,0))
    Entity(model='cube', color=color.brown, scale=(0.2,0.8,0.2), parent=root, position=(0,0,0))
    Entity(model='cube', color=color.gray, scale=(0.2,0.3,0.75), parent=root, position=(0,0.5,0.25))
    return root

def make_pick_on_parent(parent_entity):
    root = Entity(parent=parent_entity, position=(0,0,0))
    Entity(model='cube', color=color.brown, scale=(0.2,0.8,0.2), parent=root, position=(0,0,0))
    Entity(model='cube', color=color.gray, scale=(0.2,0.2,0.8), parent=root, position=(0,0.5,0))
    Entity(model='cube', color=color.gray, scale=(0.25,0.125,0.25), parent=root, position=(0,0.4,0.35))
    Entity(model='cube', color=color.gray, scale=(0.25,0.125,0.25), parent=root, position=(0,0.4,-0.35))
    return root

def make_hoe_on_parent(parent_entity):
    root = Entity(parent=parent_entity, position=(0,0,0))
    Entity(model='cube', color=color.brown, scale=(0.18,0.8,0.18), parent=root, position=(0,0,0))
    Entity(model='cube', color=color.gray, scale=(0.5,0.15,0.3), parent=root, position=(0,0.45,0))
    return root

axe = Entity(position=(0.7,-0.6,1.5), rotation=(0,0,0), parent=camera, enabled=False)
make_axe_on_parent(axe)

pickaxe = Entity(position=(0.7,-0.6,1.5), rotation=(0,0,0), parent=camera, enabled=False)
make_pick_on_parent(pickaxe)

hoe = Entity(position=(0.7,-0.6,1.5), rotation=(0,0,0), parent=camera, enabled=False)
make_hoe_on_parent(hoe)

# -------------------------
# Spawn ground items helper
# -------------------------
def spawn_ground_item(item_type, position):
    root = Entity(position=position, collider='box')
    root.item_type = item_type
    if item_type == "axe":
        Entity(model='cube', color=color.brown, scale=(0.2,0.8,0.2), parent=root, position=(0,0,0))
        Entity(model='cube', color=color.gray, scale=(0.2,0.3,0.75), parent=root, position=(0,0.5,0.25))
    elif item_type == "pickaxe":
        Entity(model='cube', color=color.brown, scale=(0.2,0.8,0.2), parent=root, position=(0,0,0))
        Entity(model='cube', color=color.gray, scale=(0.2,0.2,0.8), parent=root, position=(0,0.5,0))
        Entity(model='cube', color=color.gray, scale=(0.25,0.125,0.25), parent=root, position=(0,0.4,0.35))
        Entity(model='cube', color=color.gray, scale=(0.25,0.125,0.25), parent=root, position=(0,0.4,-0.35))
    elif item_type == "hoe":
        Entity(model='cube', color=color.brown, scale=(0.18,0.8,0.18), parent=root, position=(0,0,0))
        Entity(model='cube', color=color.gray, scale=(0.5,0.15,0.3), parent=root, position=(0,0.45,0))
    elif item_type == "wood":
        Entity(model='cube', color=color.rgb(139,69,19), scale=(0.6,0.2,0.2), parent=root, position=(0,0.3,0))
    elif item_type == "stone":
        Entity(model='cube', color=color.gray, scale=(0.6,0.6,0.6), parent=root, position=(0,0.5,0))
    elif item_type == "field":
        Entity(model='cube', color=color.rgb(70,35,0), scale=(1,0.2,1), parent=root, position=(0,0.1,0))  # nâu đậm
    else:
        Entity(model='cube', color=color.white, scale=(0.3,0.3,0.3), parent=root, position=(0,0.3,0))
    return root


axe_ground = spawn_ground_item("axe", Vec3(0,1,0))
pickaxe_ground = spawn_ground_item("pickaxe", Vec3(2,1,0))
hoe_ground = spawn_ground_item("hoe", Vec3(-2,1,0))


# -------------------------
# Trees and rocks
# -------------------------
trees = []
def spawn_trees(num_trees=10):
    for i in range(num_trees):
        while True:
            x = random.randint(-int(GROUND_HALF)+5, int(GROUND_HALF)-5)
            z = random.randint(-int(GROUND_HALF)+5, int(GROUND_HALF)-5)
            # tránh vùng nhà (x,z trong [-8,8])
            if abs(x) > 8 or abs(z) > 8:
                break
        trunk = Entity(model='cube', color=color.brown, scale=(1,4,1), position=(x,2,z), collider='box')
        leaves = Entity(model='sphere', color=color.green, scale=3, position=(x,5,z))
        bar = Entity(model='cube', color=color.red, scale=(2,0.2,0.1), position=(x,4.5,z))
        trees.append({"trunk": trunk, "leaves": leaves, "hp": 10, "bar": bar})
spawn_trees()

rocks = []
def spawn_rocks(num_rocks=8):
    for i in range(num_rocks):
        while True:
            x = random.randint(-int(GROUND_HALF)+5, int(GROUND_HALF)-5)
            z = random.randint(-int(GROUND_HALF)+5, int(GROUND_HALF)-5)
            if abs(x) > 8 or abs(z) > 8:
                break
        rock = Entity(model='cube', color=color.gray, scale=(2,2,2), position=(x,1,z), collider='box')
        bar = Entity(model='cube', color=color.red, scale=(2,0.2,0.1), position=(x,2.5,z))
        rocks.append({"rock": rock, "hp": 15, "bar": bar})
spawn_rocks()

def build_house():
    Entity(model='cube', color=color.rgb(120,72,0), scale=(10,0.5,10), position=(0,0,0))
    Entity(model='cube', color=color.rgb(90,45,0), scale=(10,5,0.5), position=(0,2.5,-5))
    Entity(model='cube', color=color.rgb(90,45,0), scale=(10,5,0.5), position=(0,2.5,5))
    Entity(model='cube', color=color.rgb(90,45,0), scale=(0.5,5,10), position=(-5,2.5,0))
    Entity(model='cube', color=color.rgb(60,30,0), scale=(11,1,11), position=(0,5.5,0))



build_house()


# -------------------------
# Fields & preview (NO GRID)
# -------------------------
fields = []  # list of {"entity": root, "pos": Vec3}

# preview shows exact world point where player is looking (y adjusted)
field_preview = Entity(model='cube', color=color.rgb(150,100,50,140), scale=(1,0.2,1), enabled=False)

# crosshair
crosshair = Entity(parent=camera, model='quad', color=color.white, scale=0.01, position=(0,0,1.2))

# -------------------------
# Utilities
# -------------------------
def swing_item(item_entity):
    item_entity.animate_rotation((120,0,0), duration=0.15, curve=curve.linear)
    invoke(lambda: item_entity.animate_rotation((0,0,0), duration=0.15), delay=0.15)

def find_ground_item_root(entity):
    e = entity
    while e is not None:
        if hasattr(e, "item_type"):
            return e
        e = e.parent
    return None

def first_empty_slot():
    for i, it in enumerate(inventory):
        if it is None:
            return i
    return None

def select_slot(index):
    global selected_slot
    selected_slot = index
    it = inventory[selected_slot]
    arm.enabled = (it is None)
    axe.enabled = (it == "axe")
    pickaxe.enabled = (it == "pickaxe")
    hoe.enabled = (it == "hoe")
    update_inventory_ui()

select_slot(0)

# -------------------------
# Per-frame update: preview logic (no grid, exact look point)
# -------------------------
MAX_PLACE_DISTANCE = 20

def update():
    if not hoe.enabled:
        field_preview.enabled = False
        return

    # raycast kiểm tra xem có trúng field hay vật thể nào
    hit = raycast(camera.world_position, camera.forward, distance=MAX_PLACE_DISTANCE, ignore=(player, field_preview))

    point = None
    target_field = None

    # nếu trúng field thì snap cạnh
    if hit.hit:
        for f in fields:
            if hit.entity == f["entity"]:
                target_field = f
                break

    if target_field:
        dx = player.x - target_field["pos"].x
        dz = player.z - target_field["pos"].z
        if abs(dx) > abs(dz):
            offset = Vec3(1 if dx > 0 else -1, 0, 0)
        else:
            offset = Vec3(0, 0, 1 if dz > 0 else -1)
        point = target_field["pos"] + offset
    else:
        # luôn tính giao điểm với mặt phẳng y=0
        dir = camera.forward
        if abs(dir.y) > 1e-5:
            t = -camera.world_position.y / dir.y
            if 0 < t <= MAX_PLACE_DISTANCE:
                point = camera.world_position + dir * t

    if point is None:
        field_preview.enabled = False
        return

    # kiểm tra trong phạm vi ground
    if abs(point.x) > GROUND_HALF or abs(point.z) > GROUND_HALF:
        field_preview.enabled = False
        return

    # kiểm tra chồng lên vật thể khác
    overlap = raycast(point + Vec3(0,2,0), Vec3(0,-1,0), distance=3, ignore=(player, field_preview))
    if overlap.hit and overlap.entity != ground and (target_field is None or overlap.entity != target_field["entity"]):
        field_preview.enabled = False
        return

    # cập nhật preview
    preview_pos = Vec3(point.x, 0.1, point.z)
    field_preview.position = preview_pos
    field_preview.enabled = True


# -------------------------
# Input handling
# -------------------------
def input(key):
    # slot keys 1..9 and 0 -> slots 0..9
    if key in [str(i) for i in range(1,10)] + ['0']:
        if key == '0':
            idx = 9
        else:
            idx = int(key) - 1
        select_slot(idx)
        return

    if key == 'e':
        hit_info = raycast(camera.world_position, camera.forward, distance=3)
        if hit_info.hit:
            root = find_ground_item_root(hit_info.entity)
            if root is not None:
                slot = first_empty_slot()
                if slot is None:
                    show_message("Inventory full!", 2)
                else:
                    inventory[slot] = root.item_type
                    update_inventory_ui()
                    show_message(f"Picked up {root.item_type}", 1.5)
                    destroy(root)
                    if inventory[selected_slot] is None:
                        select_slot(slot)
                return

    if key == 'q':
        it = inventory[selected_slot]
        if it is None:
            show_message("No item in selected slot", 1.5)
        else:
            pos = player.position + player.forward * 2
            spawn_ground_item(it, pos)
            inventory[selected_slot] = None
            select_slot(selected_slot)
            update_inventory_ui()
            show_message(f"Dropped {it}", 1.2)
        return

    if key == 'left mouse down':
        # axe: chop trees
        if axe.enabled:
            swing_item(axe)
            hit_info = raycast(camera.world_position, camera.forward, distance=3)
            if hit_info.hit:
                for tree in trees:
                    if hit_info.entity == tree["trunk"]:
                        tree["hp"] -= 3
                        tree["bar"].scale_x = max(0, tree["hp"]/5)
                        if tree["hp"] <= 0:
                            spawn_ground_item("wood", tree["trunk"].position + Vec3(0,0,2))
                            destroy(tree["trunk"])
                            destroy(tree["leaves"])
                            destroy(tree["bar"])
                            trees.remove(tree)
                        break

        # pickaxe: break rocks
        if pickaxe.enabled:
            swing_item(pickaxe)
            hit_info = raycast(camera.world_position, camera.forward, distance=3)
            if hit_info.hit:
                for rock in rocks:
                    if hit_info.entity == rock["rock"]:
                        rock["hp"] -= 4
                        rock["bar"].scale_x = max(0, rock["hp"]/7.5)
                        if rock["hp"] <= 0:
                            spawn_ground_item("stone", rock["rock"].position + Vec3(0,0,2))
                            destroy(rock["rock"])
                            destroy(rock["bar"])
                            rocks.remove(rock)
                        break

        # hoe: place field at exact look point (no grid)
        if hoe.enabled:
            swing_item(hoe)
            # use the preview position if enabled
            if field_preview.enabled:
                pos = field_preview.position
                # check if a field already exists very close to this position (within 0.5)
                exists = any((abs(f["pos"].x - pos.x) < 0.5 and abs(f["pos"].z - pos.z) < 0.5) for f in fields)
                if not exists:
                    root = spawn_ground_item("field", Vec3(pos.x, 0, pos.z))
                    fields.append({"entity": root, "pos": Vec3(pos.x, 0.1, pos.z)})
                    show_message("Field created", 1.2)
                else:
                    show_message("Field already exists here", 1.2)

# -------------------------
# Final UI init and run
# -------------------------
update_inventory_ui()
app.run()
