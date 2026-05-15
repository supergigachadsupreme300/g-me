from pathlib import Path
from ursina import color
from asset_loader import load_texture_safe, is_valid_texture

# Ursina doesn't support .webp, use .png instead or fallback to colors
WOOD_TEXTURE = None
DIRT_TEXTURE = None
GRASS_TEXTURE = None


def is_texture(value):
    return is_valid_texture(value)


def load_textures():
    global WOOD_TEXTURE, DIRT_TEXTURE, GRASS_TEXTURE
    WOOD_TEXTURE = load_texture_safe('texture/wood_texture.png', color.rgb(139/255, 69/255, 19/255))
    DIRT_TEXTURE = load_texture_safe('texture/dirt_texture.png', color.rgb(70/255, 35/255, 0/255))
    GRASS_TEXTURE = load_texture_safe('texture/grass.png', color.rgb(20/255, 120/255, 20/255))

    print(f"Final WOOD_TEXTURE: {WOOD_TEXTURE}")
    print(f"Final DIRT_TEXTURE: {DIRT_TEXTURE}")
    print(f"Final GRASS_TEXTURE: {GRASS_TEXTURE}")

