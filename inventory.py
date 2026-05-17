from ursina import Text, color

TOOL_ITEMS = {"gun", "axe", "pickaxe", "hoe", "hammer", "sword", "scythe"}

inventory = [None] * 10
selected_slot = 0
inventory_text = Text(text="", position=(0, -0.45), origin=(0, 0), scale=1.0, background=True)
message_text = Text(text="", position=(0, 0.35), origin=(0, 0), scale=1.2, color=color.azure)


def make_slot(item_type, count=1):
    return {"type": item_type, "count": count}


def get_item(slot):
    return slot["type"] if slot is not None else None


def get_count(slot):
    return slot["count"] if slot is not None else 0


def is_tool(item_type):
    return item_type in TOOL_ITEMS


def is_stackable(item_type):
    return item_type is not None and item_type not in TOOL_ITEMS


def slot_text(slot):
    item_type = get_item(slot)
    if item_type is None:
        return "empty"
    count = get_count(slot)
    return f"{item_type} x{count}" if count > 1 else item_type


def find_stack_slot(item_type):
    for i, slot in enumerate(inventory):
        if get_item(slot) == item_type:
            return i
    return None


def update_inventory_ui():
    slots = []
    for i, it in enumerate(inventory):
        label = slot_text(it)
        if i == selected_slot:
            slots.append(f"[{i+1}:{label}]")
        else:
            slots.append(f"{i+1}:{label}")
    inventory_text.text = "   ".join(slots)


def show_message(txt, duration=2):
    message_text.text = txt
    from ursina import invoke
    invoke(lambda: setattr(message_text, "text", ""), delay=duration)


def first_empty_slot():
    for i, it in enumerate(inventory):
        if it is None:
            return i
    return None


def add_item(item_type, amount=1):
    if item_type is None:
        return False
    if is_stackable(item_type):
        slot = find_stack_slot(item_type)
        if slot is not None:
            inventory[slot]["count"] += amount
            return True
    slot = first_empty_slot()
    if slot is None:
        return False
    inventory[slot] = make_slot(item_type, amount)
    return True


def remove_item(slot_index, amount=1):
    slot = inventory[slot_index]
    if slot is None:
        return False
    if slot["count"] > amount:
        slot["count"] -= amount
        return True
    inventory[slot_index] = None
    return True
