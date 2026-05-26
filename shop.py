from ursina import Entity, Text, Button, color, camera, Vec2
import inventory
import rendering
import world

SHOP_PANEL = None
ORIGINAL_SENSITIVITY = None  # Biến mới để sửa lỗi camera

ITEMS = [
    {'type': 'wheat', 'price': 5},
    {'type': 'damaged wheat', 'price': 2},
    {'type': 'seed', 'price': 3},
    {'type': 'peashooter seed', 'price': 10},
    {'type': 'fertilizer', 'price': 8},
    {'type': 'axe', 'price': 25},
    {'type': 'pickaxe', 'price': 25},
    {'type': 'hoe', 'price': 20},
    {'type': 'gun', 'price': 60},
    {'type': 'ammo', 'price': 5},
]


def setup_shop_ui():
    global SHOP_PANEL
    # scale=0.66 giúp thu nhỏ UI lại bằng 2/3
    SHOP_PANEL = Entity(parent=camera.ui, enabled=False, scale=0.66)
    
    # z=0.1 đẩy nền ra sau chống nháy
    Entity(parent=SHOP_PANEL, model='quad', color=color.hex('#2E3440'), scale=(1.2, 0.95), position=(0, 0, 0.1))
    Text(parent=SHOP_PANEL, text='Shop', y=0.38, z=-0.1, scale=2, color=color.hex('#ECEFF4'), origin=(0, 0))

    cols = 3
    spacing_x = 0.35
    spacing_y = 0.16
    start_x = -0.35
    start_y = 0.22

    for i, it in enumerate(ITEMS):
        x = start_x + (i % cols) * spacing_x
        y = start_y - (i // cols) * spacing_y
        
        # z=-0.1 kéo nút bấm lên trước chống nháy
        b = Button(
            parent=SHOP_PANEL, 
            text=f"{it['type']}\n{it['price']}g", 
            position=(x, y, -0.1), 
            scale=(0.3, 0.12),
            color=color.hex('#434C5E'),
            text_color=color.hex('#ECEFF4')
        )
        b.highlight_color = color.hex('#4C566A')
        b.on_click = (lambda item=it: buy_item(item))

    b_close = Button(
        parent=SHOP_PANEL, 
        text='Close', 
        position=(0, -0.38, -0.1), 
        scale=(0.25, 0.1), 
        on_click=close_shop, 
        color=color.hex('#BF616A'), 
        text_color=color.hex('#ECEFF4')
    )
    b_close.highlight_color = color.hex('#D08770')


def open_shop():
    global ORIGINAL_SENSITIVITY
    if SHOP_PANEL is None:
        setup_shop_ui()
    SHOP_PANEL.enabled = True
    
    from ursina import mouse
    mouse.locked = False
    mouse.visible = True
    
    if world.player is not None:
        world.player.ignore_input = True
        # Tắt xoay camera
        if hasattr(world.player, 'mouse_sensitivity'):
            if ORIGINAL_SENSITIVITY is None:
                ORIGINAL_SENSITIVITY = world.player.mouse_sensitivity
            world.player.mouse_sensitivity = Vec2(0, 0)


def close_shop():
    if SHOP_PANEL is None:
        return
    SHOP_PANEL.enabled = False
    
    from ursina import mouse
    mouse.locked = True
    mouse.visible = False
    
    if world.player is not None:
        world.player.ignore_input = False
        # Bật lại camera
        if hasattr(world.player, 'mouse_sensitivity') and ORIGINAL_SENSITIVITY is not None:
            world.player.mouse_sensitivity = ORIGINAL_SENSITIVITY


def buy_item(item):
    if world.player is None:
        return
    price = item['price']
    if world.player.money < price:
        inventory.show_message('Not enough money', 1.5)
        return
    
    slot = inventory.first_empty_slot()
    if slot is None:
        inventory.show_message('Inventory full', 1.5)
        return
        
    if inventory.add_item(item['type'], 1):
        world.player.money -= price
        rendering.update_player_hud(world.player.hp, world.player.max_hp, world.player.stamina, world.player.max_stamina, world.player.money)
        inventory.update_inventory_ui()
        inventory.show_message(f'Bought {item["type"]}', 1.5)
    else:
        inventory.show_message('Could not add item', 1.5)