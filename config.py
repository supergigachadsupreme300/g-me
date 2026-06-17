from pathlib import Path
from ursina import color, load_texture, load_model


# --- embedded asset loader helpers (merged to avoid separate module) ---
def is_valid_texture(texture):
    if texture is None:
        return False
    return any(hasattr(texture, attr) for attr in ('setMagfilter', 'width', 'height', 'uvs', 'texture'))


def load_texture_safe(path, fallback_color):
    try:
        texture = load_texture(path)
        if not is_valid_texture(texture):
            print(f"Failed to load texture or invalid texture: {path}")
            return fallback_color
        return texture
    except Exception as e:
        print(f"Failed to load texture {path}: {e}")
        return fallback_color


def load_model_safe(path, fallback='cube'):
    try:
        model = load_model(path)
        if model is None:
            print(f"Failed to load model or invalid model: {path}")
            return fallback
        return model
    except Exception as e:
        print(f"Failed to load model {path}: {e}")
        return fallback

# --- end embedded asset loader helpers ---

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


def diagnose_textures():
    """Developer helper: print debug info about loaded textures.
    Kept here as a function instead of a separate script so it can be invoked
    during debugging if needed.
    """
    try:
        print('WOOD_TYPE', type(WOOD_TEXTURE))
        print('WOOD_REPR', repr(WOOD_TEXTURE))
        print('WOOD_ATTRS', [attr for attr in dir(WOOD_TEXTURE) if attr in ('width', 'height', 'uvs', 'path')])
        print('WOOD_WIDTH', hasattr(WOOD_TEXTURE, 'width'))
        print('DIRT_TYPE', type(DIRT_TEXTURE))
        print('DIRT_REPR', repr(DIRT_TEXTURE))
        print('DIRT_ATTRS', [attr for attr in dir(DIRT_TEXTURE) if attr in ('width', 'height', 'uvs', 'path')])
        print('DIRT_WIDTH', hasattr(DIRT_TEXTURE, 'width'))
        print('GRASS_TYPE', type(GRASS_TEXTURE))
        print('GRASS_REPR', repr(GRASS_TEXTURE))
        print('GRASS_ATTRS', [attr for attr in dir(GRASS_TEXTURE) if attr in ('width', 'height', 'uvs', 'path')])
        print('GRASS_WIDTH', hasattr(GRASS_TEXTURE, 'width'))
    except Exception as e:
        print('diagnose_textures failed:', e)

