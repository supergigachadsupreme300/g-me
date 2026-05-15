from ursina import color
import config

BLOCK_TYPES = {
    'wood': {
        'texture': config.WOOD_TEXTURE,
        'fallback_color': color.rgb(139/255, 69/255, 19/255),
    },
    'dirt': {
        'texture': config.DIRT_TEXTURE,
        'fallback_color': color.rgb(70/255, 35/255, 0/255),
    },
    'grass': {
        'texture': config.GRASS_TEXTURE,
        'fallback_color': color.rgb(20/255, 120/255, 20/255),
    },
}


def get_block_texture(name):
    block = BLOCK_TYPES.get(name)
    if not block:
        return None
    texture = block['texture']
    return texture if config.is_texture(texture) else block['fallback_color']
