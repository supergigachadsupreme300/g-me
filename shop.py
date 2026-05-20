from ursina import Entity, Text, Button, color, camera
import inventory
import rendering
import world

SHOP_PANEL = None
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
    SHOP_PANEL = Entity(parent=camera.ui, enabled=False)
    Entity(parent=SHOP_PANEL, model='quad', color=color.rgba(10, 10, 10, 220/255), scale=(1.2, 0.8))
    Text(parent=SHOP_PANEL, text='Shop', y=0.34, scale=2, color=color.white)

    # grid of item buttons
    cols = 5
    spacing_x = 0.36
    spacing_y = 0.25
    start_x = -0.8
    start_y = 0.1
    for i, it in enumerate(ITEMS):
        x = start_x + (i % cols) * spacing_x
        y = start_y - (i // cols) * spacing_y
        b = Button(parent=SHOP_PANEL, text=f"{it['type']}\n{it['price']}g", position=(x, y), scale=(0.3, 0.18))
        b.on_click = (lambda item=it: buy_item(item))

    Button(parent=SHOP_PANEL, text='Close', y=-0.33, scale=(0.25, 0.12), on_click=close_shop)


def open_shop():
    if SHOP_PANEL is None:
        setup_shop_ui()
    SHOP_PANEL.enabled = True
    # unlock mouse so player can click
    from ursina import mouse
    mouse.locked = False
    mouse.visible = True


def close_shop():
    if SHOP_PANEL is None:
        return
    SHOP_PANEL.enabled = False
    from ursina import mouse
    mouse.locked = True
    mouse.visible = False


def buy_item(item):
    if world.player is None:
        return
    price = item['price']
    if world.player.money < price:
        inventory.show_message('Not enough money', 1.5)
        return
    # check for space
    slot = inventory.first_empty_slot()
    if slot is None:
        inventory.show_message('Inventory full', 1.5)
        return
    # perform purchase
    if inventory.add_item(item['type'], 1):
        world.player.money -= price
        rendering.update_player_hud(world.player.hp, world.player.max_hp, world.player.stamina, world.player.max_stamina, world.player.money)
        inventory.update_inventory_ui()
        inventory.show_message(f'Bought {item["type"]}', 1.5)
    else:
        inventory.show_message('Could not add item', 1.5)
