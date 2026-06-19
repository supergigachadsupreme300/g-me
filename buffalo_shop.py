from ursina import Entity, Text, Button, color, camera, mouse, Vec2
import inventory
import rendering
import world

SHOP_PANEL = None
TAB_BUY = None
TAB_SELL = None
ITEM_BUTTONS = []
PAGE_LABEL = None
PAGE = 1
ACTIVE_TAB = 'buy'
ORIGINAL_SENSITIVITY = None
ITEMS_PER_PAGE = 6

BUY_ITEMS = [
    {'type': 'seed', 'price': 3, 'label': 'Hạt lúa'},
    {'type': 'corn seed', 'price': 4, 'label': 'Hạt ngô'},
    # potato seed removed; use 'potato' item to plant directly
    {'type': 'fertilizer', 'price': 8, 'label': 'Phân bón'},
    {'type': 'peashooter seed', 'price': 10, 'label': 'Hạt peashooter'},
]

SELL_ITEMS = [
    {'type': 'wheat', 'price': 10, 'label': 'Lúa'},
    {'type': 'damaged wheat', 'price': 3, 'label': 'Lúa hỏng'},
    {'type': 'corn', 'price': 12, 'label': 'Ngô'},
    {'type': 'damaged corn', 'price': 4, 'label': 'Ngô hỏng'},
    {'type': 'potato', 'price': 11, 'label': 'Khoai tây'},
    {'type': 'damaged potato', 'price': 3, 'label': 'Khoai hỏng'},
]

# Prices are stored in SELL_ITEMS; import values directly from that list when needed


def _current_items():
    return BUY_ITEMS if ACTIVE_TAB == 'buy' else SELL_ITEMS


def _total_pages():
    items = _current_items()
    return max(1, (len(items) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)


def setup_buffalo_shop_ui():
    global SHOP_PANEL, TAB_BUY, TAB_SELL, ITEM_BUTTONS, PAGE_LABEL

    SHOP_PANEL = Entity(parent=camera.ui, enabled=False, scale=0.72)
    Entity(parent=SHOP_PANEL, model='quad', color=color.hex('#2E3440'), scale=(1.25, 0.95), position=(0, 0, 0.1))
    Text(parent=SHOP_PANEL, text='Cửa hàng Trâu', y=0.38, z=-0.1, scale=2, color=color.hex('#ECEFF4'), origin=(0, 0))

    close_btn = Button(
        parent=SHOP_PANEL, text='', position=(0.54, 0.39, -0.1), scale=(0.08, 0.08),
        color=color.hex('#BF616A'), text_color=color.hex('#ECEFF4'), on_click=close_buffalo_shop,
    )
    close_btn.highlight_color = color.hex('#D08770')
    Text(parent=SHOP_PANEL, text='X', position=(0.54, 0.39, -0.09), origin=(0, 0), color=color.hex('#ECEFF4'), use_tags=False)

    TAB_BUY = Button(
        parent=SHOP_PANEL, text='', position=(-0.18, 0.28, -0.1), scale=(0.24, 0.08),
        color=color.hex('#5E81AC'), text_color=color.hex('#ECEFF4'), on_click=lambda: switch_tab('buy'),
    )
    Text(parent=SHOP_PANEL, text='Mua hàng', position=(-0.18, 0.28, -0.15), origin=(0, 0), color=color.hex('#ECEFF4'), use_tags=False)
    TAB_SELL = Button(
        parent=SHOP_PANEL, text='', position=(0.18, 0.28, -0.1), scale=(0.24, 0.08),
        color=color.hex('#4C566A'), text_color=color.hex('#ECEFF4'), on_click=lambda: switch_tab('sell'),
    )
    Text(parent=SHOP_PANEL, text='Bán hàng', position=(0.18, 0.28, -0.15), origin=(0, 0), color=color.hex('#ECEFF4'), use_tags=False)

    cols = 2
    start_x = -0.22
    start_y = 0.12
    spacing_x = 0.44
    spacing_y = 0.17
    ITEM_BUTTONS = []
    for slot in range(ITEMS_PER_PAGE):
        x = start_x + (slot % cols) * spacing_x
        y = start_y - (slot // cols) * spacing_y
        btn = Button(
            parent=SHOP_PANEL, text='', position=(x, y, -0.1), scale=(0.38, 0.12),
            color=color.hex('#434C5E'), text_color=color.hex('#ECEFF4'), enabled=False,
        )
        btn.highlight_color = color.hex('#4C566A')
        # create a dedicated Text child to avoid Ursina Text.align indexing issues
        btn._label = Text(parent=SHOP_PANEL, text='', position=(x, y, -0.15), origin=(0, 0), color=color.hex('#ECEFF4'), use_tags=False)
        ITEM_BUTTONS.append(btn)

    prev_btn = Button(
        parent=SHOP_PANEL, text='', position=(-0.28, -0.34, -0.1), scale=(0.1, 0.08),
        color=color.hex('#4C566A'), text_color=color.hex('#ECEFF4'),
        on_click=lambda: change_page(PAGE - 1),
    )
    prev_btn.highlight_color = color.hex('#81A1C1')
    Text(parent=SHOP_PANEL, text='<', position=(-0.28, -0.34, -0.15), origin=(0, 0), color=color.hex('#ECEFF4'), use_tags=False)

    next_btn = Button(
        parent=SHOP_PANEL, text='', position=(0.28, -0.34, -0.1), scale=(0.1, 0.08),
        color=color.hex('#4C566A'), text_color=color.hex('#ECEFF4'),
        on_click=lambda: change_page(PAGE + 1),
    )
    next_btn.highlight_color = color.hex('#81A1C1')
    Text(parent=SHOP_PANEL, text='>', position=(0.28, -0.34, -0.15), origin=(0, 0), color=color.hex('#ECEFF4'), use_tags=False)

    PAGE_LABEL = Text(parent=SHOP_PANEL, text='', y=-0.34, z=-0.1, scale=1.1, color=color.hex('#ECEFF4'), origin=(0, 0))
    # Sell All button (sells all items from SELL_ITEMS)
    sell_all_btn = Button(
        parent=SHOP_PANEL, text='Bán tất cả', position=(0.0, -0.42, -0.1), scale=(0.32, 0.06),
        color=color.hex('#BF616A'), text_color=color.hex('#ECEFF4'),
        on_click=lambda: sell_all_items(),
    )
    sell_all_btn.highlight_color = color.hex('#D08770')
    update_page()


def switch_tab(tab_name):
    global ACTIVE_TAB, PAGE
    ACTIVE_TAB = tab_name
    PAGE = 1
    if TAB_BUY is not None and TAB_SELL is not None:
        TAB_BUY.color = color.hex('#5E81AC') if tab_name == 'buy' else color.hex('#4C566A')
        TAB_SELL.color = color.hex('#5E81AC') if tab_name == 'sell' else color.hex('#4C566A')
    update_page()


def change_page(new_page):
    global PAGE
    PAGE = max(1, min(new_page, _total_pages()))
    update_page()


def update_page():
    global PAGE
    items = _current_items()
    total_pages = _total_pages()
    PAGE = max(1, min(PAGE, total_pages))
    start_index = (PAGE - 1) * ITEMS_PER_PAGE

    for slot, button in enumerate(ITEM_BUTTONS):
        item_index = start_index + slot
        if item_index < len(items):
            item = items[item_index]
            if ACTIVE_TAB == 'buy':
                label_text = f"{item['label']}\n{item['price']} vàng"
                button.on_click = (lambda current=item: buy_item(current))
            else:
                owned = inventory.count_item(item['type'])
                label_text = f"{item['label']}\n{owned} cái · {item['price']}g"
                button.on_click = (lambda current=item: sell_item(current))
            if hasattr(button, '_label'):
                button._label.text = label_text
            else:
                button.text = label_text
            button.enabled = True
        else:
            if hasattr(button, '_label'):
                button._label.text = ''
            else:
                button.text = ''
            button.enabled = False
            button.on_click = lambda _=None: None

    if PAGE_LABEL is not None:
        tab_label = 'Mua' if ACTIVE_TAB == 'buy' else 'Bán'
        PAGE_LABEL.text = f'{tab_label} · Trang {PAGE}/{total_pages}'


def open_buffalo_shop():
    global ORIGINAL_SENSITIVITY, PAGE, ACTIVE_TAB
    if SHOP_PANEL is None:
        setup_buffalo_shop_ui()
    PAGE = 1
    ACTIVE_TAB = 'buy'
    switch_tab('buy')
    SHOP_PANEL.enabled = True
    mouse.locked = False
    mouse.visible = True

    if world.player is not None:
        world.player.ignore_input = True
        if hasattr(world.player, 'mouse_sensitivity'):
            if ORIGINAL_SENSITIVITY is None:
                ORIGINAL_SENSITIVITY = world.player.mouse_sensitivity
            world.player.mouse_sensitivity = Vec2(0, 0)


def close_buffalo_shop():
    global ORIGINAL_SENSITIVITY
    if SHOP_PANEL is not None:
        SHOP_PANEL.enabled = False
    mouse.locked = True
    mouse.visible = False

    if world.player is not None:
        # Restore player input and movement state
        try:
            world.player.ignore_input = False
        except Exception:
            pass
        try:
            # ensure sprinting is disabled and speed reset
            if hasattr(world.player, 'is_sprinting'):
                world.player.is_sprinting = False
            if hasattr(world.player, 'base_speed'):
                world.player.speed = getattr(world.player, 'base_speed', world.player.speed)
        except Exception:
            pass
        if hasattr(world.player, 'mouse_sensitivity') and ORIGINAL_SENSITIVITY is not None:
            world.player.mouse_sensitivity = ORIGINAL_SENSITIVITY
            # clear stored original so subsequent opens re-capture current
            ORIGINAL_SENSITIVITY = None
    # Ensure the global game paused flag is cleared when the shop is closed
    try:
        import game
        game.game_paused = False
    except Exception:
        pass


def buy_item(item):
    if world.player is None:
        return
    price = item['price']
    if world.player.money < price:
        inventory.show_message('Không đủ tiền', 1.5)
        return
    if inventory.first_empty_slot() is None and inventory.find_stack_slot(item['type']) is None:
        inventory.show_message('Túi đồ đầy', 1.5)
        return
    if inventory.add_item(item['type'], 1):
        world.player.money -= price
        rendering.update_player_hud(
            world.player.hp, world.player.max_hp,
            world.player.stamina, world.player.max_stamina, world.player.money,
        )
        inventory.update_inventory_ui()
        inventory.show_message(f"Đã mua {item['label']}", 1.5)
    else:
        inventory.show_message('Không thể thêm vật phẩm', 1.5)


def sell_item(item):
    if world.player is None:
        return
    amount = inventory.count_item(item['type'])
    if amount <= 0:
        inventory.show_message(f"Không có {item['label']} để bán", 1.5)
        return
    inventory.remove_all(item['type'])
    earned = amount * item['price']
    world.player.money += earned
    rendering.update_player_hud(
        world.player.hp, world.player.max_hp,
        world.player.stamina, world.player.max_stamina, world.player.money,
    )
    inventory.update_inventory_ui()
    update_page()
    inventory.show_message(f"Đã bán {amount} {item['label']} (+{earned} vàng)", 2.0)


def sell_all_items():
    if world.player is None:
        return
    total_earned = 0
    for item in SELL_ITEMS:
        amount = inventory.count_item(item['type'])
        if amount > 0:
            inventory.remove_all(item['type'])
            earned = amount * item['price']
            world.player.money += earned
            total_earned += earned

    if total_earned > 0:
        rendering.update_player_hud(
            world.player.hp, world.player.max_hp,
            world.player.stamina, world.player.max_stamina, world.player.money,
        )
        inventory.update_inventory_ui()
        update_page()
        inventory.show_message(f"Đã bán tất cả (+{total_earned} vàng)", 2.0)
    else:
        inventory.show_message('Không có gì để bán', 1.5)
