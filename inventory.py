from ursina import Text, color

inventory = [None] * 10
selected_slot = 0
inventory_text = Text(text="", position=(0, -0.45), origin=(0, 0), scale=1.0, background=True)
message_text = Text(text="", position=(0, 0.35), origin=(0, 0), scale=1.2, color=color.azure)


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
    from ursina import invoke
    invoke(lambda: setattr(message_text, "text", ""), delay=duration)


def first_empty_slot():
    for i, it in enumerate(inventory):
        if it is None:
            return i
    return None
