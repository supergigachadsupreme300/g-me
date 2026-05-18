from pathlib import Path
from ursina import color
from asset_loader import load_texture_safe, is_valid_texture

# Ursina doesn't support .webp, use .png instead or fallback to colors
WOOD_TEXTURE = None
DIRT_TEXTURE = None
GRASS_TEXTURE = None
BARK_TEXTURE = None
ROCK_TEXTURE = None
LEAVES_TEXTURE = None


def is_texture(value):
    return is_valid_texture(value)


def load_textures():
    global WOOD_TEXTURE, DIRT_TEXTURE, GRASS_TEXTURE, BARK_TEXTURE, ROCK_TEXTURE, LEAVES_TEXTURE
    WOOD_TEXTURE   = load_texture_safe('texture/wood_texture.png',   color.rgb(139/255, 69/255, 19/255))
    DIRT_TEXTURE   = load_texture_safe('texture/dirt_texture.png',   color.rgb(70/255,  35/255,  0/255))
    GRASS_TEXTURE  = load_texture_safe('texture/grass_blade.png',    color.rgb(20/255, 120/255, 20/255))
    BARK_TEXTURE   = load_texture_safe('texture/bark_texture.png',   color.rgb(90/255,  60/255, 28/255))
    ROCK_TEXTURE   = load_texture_safe('texture/rock_texture.png',   color.rgb(118/255,112/255,100/255))
    LEAVES_TEXTURE = load_texture_safe('texture/leaves_texture.png', color.rgb(32/255, 108/255, 32/255))

