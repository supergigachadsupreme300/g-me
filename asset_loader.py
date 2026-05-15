from ursina import load_texture, load_model


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
