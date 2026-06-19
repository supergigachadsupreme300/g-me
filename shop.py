from ursina import Entity, Text, Button, color, camera, Vec3, Vec2
import inventory
import rendering
import world
import pet

SHOP_PANEL = None
SHOP_ITEM_BUTTONS = []
SHOP_PAGE_LABEL = None
SHOP_PAGE = 1
SHOP_PREV_BUTTON = None
SHOP_NEXT_BUTTON = None
ORIGINAL_SENSITIVITY = None  # Biến mới để sửa lỗi camera
ITEMS_PER_PAGE = 9

ITEMS = [
    {'type': 'wheat', 'price': 5},
    {'type': 'corn', 'price': 6},
    {'type': 'potato', 'price': 6},
    {'type': 'damaged wheat', 'price': 2},
    {'type': 'seed', 'price': 3},
    {'type': 'corn seed', 'price': 4},
    {'type': 'peashooter seed', 'price': 10},
    {'type': 'fertilizer', 'price': 8},
    {'type': 'axe', 'price': 25},
    {'type': 'pickaxe', 'price': 25},
    {'type': 'hoe', 'price': 20},
    {'type': 'gun', 'price': 60},
    {'type': 'ammo', 'price': 5},
    {'type': 'mì hảo hảo', 'price':10},
    {'type': 'dog', 'price': 100, 'pet_type': 'dog'},
    {'type': 'toad', 'price': 80, 'pet_type': 'toad'},
]


def setup_shop_ui():
    global SHOP_PANEL, SHOP_ITEM_BUTTONS, SHOP_PAGE_LABEL, SHOP_PREV_BUTTON, SHOP_NEXT_BUTTON
    SHOP_PANEL = Entity(parent=camera.ui, enabled=False, scale=0.66)
    Entity(parent=SHOP_PANEL, model='quad', color=color.hex('#2E3440'), scale=(1.2, 0.95), position=(0, 0, 0.1))
    Text(parent=SHOP_PANEL, text='Shop', y=0.38, z=-0.1, scale=2, color=color.hex('#ECEFF4'), origin=(0, 0))

    b_close = Button(
        parent=SHOP_PANEL,
        text='',
        position=(0.52, 0.39, -0.1),
        scale=(0.08, 0.08),
        color=color.hex('#BF616A'),
        text_color=color.hex('#ECEFF4'),
        on_click=close_shop
    )
    b_close.highlight_color = color.hex('#D08770')
    Text(parent=SHOP_PANEL, text='X', position=(0.52, 0.39, -0.15), origin=(0, 0), color=color.hex('#ECEFF4'), use_tags=False)

    cols = 3
    rows = 3
    spacing_x = 0.35
    spacing_y = 0.16
    start_x = -0.35
    start_y = 0.18

    SHOP_ITEM_BUTTONS = []
    for slot in range(ITEMS_PER_PAGE):
        x = start_x + (slot % cols) * spacing_x
        y = start_y - (slot // cols) * spacing_y
        b = Button(
            parent=SHOP_PANEL,
            text='',
            position=(x, y, -0.1),
            scale=(0.3, 0.12),
            color=color.hex('#434C5E'),
            text_color=color.hex('#ECEFF4'),
            enabled=False
        )
        b.highlight_color = color.hex('#4C566A')
        # parent label to the button so it always renders above the button quad
        # increase label scale for readability
        b._label = Text(parent=b, text='', position=(0, 0, -0.15), origin=(0, 0), scale=(4,8), color=color.hex('#ECEFF4'), use_tags=False)
        SHOP_ITEM_BUTTONS.append(b)

    SHOP_PREV_BUTTON = Button(
        parent=SHOP_PANEL,
        text='',
        position=(-0.35, -0.35, -0.1),
        scale=(0.28, 0.1),
        color=color.hex('#4C566A'),
        text_color=color.hex('#ECEFF4'),
        on_click=lambda _=None: change_shop_page(SHOP_PAGE - 1)
    )
    SHOP_PREV_BUTTON.highlight_color = color.hex('#81A1C1')
    # label as a child of the button to avoid duplicate texts and layering issues
    Text(parent=SHOP_PREV_BUTTON, text='< Trang trước', position=(0, 0, -0.15), origin=(0, 0), scale=(4,8), color=color.hex('#ECEFF4'))

    SHOP_NEXT_BUTTON = Button(
        parent=SHOP_PANEL,
        text='',
        position=(0.35, -0.35, -0.1),
        scale=(0.28, 0.1),
        color=color.hex('#4C566A'),
        text_color=color.hex('#ECEFF4'),
        on_click=lambda _=None: change_shop_page(SHOP_PAGE + 1)
    )
    SHOP_NEXT_BUTTON.highlight_color = color.hex('#81A1C1')
    # next label as a child of the button for consistent layering
    Text(parent=SHOP_NEXT_BUTTON, text='Trang sau >', position=(0, 0, -0.15), origin=(0, 0), scale=(4,8), color=color.hex('#ECEFF4'), use_tags=False)

    SHOP_PAGE_LABEL = Text(
        parent=SHOP_PANEL,
        text='',
        y=-0.35,
        z=-0.1,
        scale=1.3,
        color=color.hex('#ECEFF4'),
        origin=(0, 0)
    )

    update_shop_page()


def get_total_shop_pages():
    return max(1, (len(ITEMS) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)


def update_shop_page():
    global SHOP_PAGE
    total_pages = get_total_shop_pages()
    SHOP_PAGE = max(1, min(SHOP_PAGE, total_pages))
    start_index = (SHOP_PAGE - 1) * ITEMS_PER_PAGE

    for slot, button in enumerate(SHOP_ITEM_BUTTONS):
        item_index = start_index + slot
        if item_index < len(ITEMS):
            item = ITEMS[item_index]
            label_text = f"{item['type']}\n{item['price']}g"
            if hasattr(button, '_label'):
                button._label.text = label_text
            else:
                button.text = label_text
            button.enabled = True
            button.on_click = (lambda _=None, current=item: buy_item(current))
        else:
            if hasattr(button, '_label'):
                button._label.text = ''
            else:
                button.text = ''
            button.enabled = False
            button.on_click = lambda _=None: None

    if SHOP_PAGE_LABEL is not None:
        SHOP_PAGE_LABEL.text = f"Trang {SHOP_PAGE}/{total_pages}"

    if SHOP_PREV_BUTTON is not None:
        SHOP_PREV_BUTTON.enabled = SHOP_PAGE > 1
    if SHOP_NEXT_BUTTON is not None:
        SHOP_NEXT_BUTTON.enabled = SHOP_PAGE < total_pages


def change_shop_page(new_page):
    global SHOP_PAGE
    total_pages = get_total_shop_pages()
    SHOP_PAGE = max(1, min(new_page, total_pages))
    update_shop_page()


def open_shop():
    global ORIGINAL_SENSITIVITY, SHOP_PAGE
    if SHOP_PANEL is None:
        setup_shop_ui()
    SHOP_PAGE = 1
    update_shop_page()
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

    pet_type = item.get('pet_type')
    if pet_type is not None:
        world.player.money -= price
        rendering.update_player_hud(world.player.hp, world.player.max_hp, world.player.stamina, world.player.max_stamina, world.player.money)
        try:
            if pet_type == 'dog':
                pet.spawn_dog(world.player.position + Vec3(2, 0, 0))
            elif pet_type == 'toad':
                pet.spawn_toad(world.player.position + Vec3(-2, 0, 0))
        except Exception as e:
            print(f'Failed to spawn pet: {e}')
        inventory.show_message(f'Bought {item["type"]}', 1.5)
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