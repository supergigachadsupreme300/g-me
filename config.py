from pathlib import Path
from ursina import load_texture, color

# Ursina doesn't support .webp, use .png instead or fallback to colors
wood_path = 'texture/wood_texture.png'
print(f"Loading WOOD_TEXTURE from: {wood_path}")
try:
    WOOD_TEXTURE = load_texture(wood_path)
    print(f"WOOD_TEXTURE loaded: {WOOD_TEXTURE}, type: {type(WOOD_TEXTURE)}, hasattr width: {hasattr(WOOD_TEXTURE, 'width') if WOOD_TEXTURE else 'N/A'}")
    if WOOD_TEXTURE is None or not hasattr(WOOD_TEXTURE, 'width'):
        WOOD_TEXTURE = color.rgb(139, 69, 19)  # Brown fallback
        print("Using WOOD fallback color")
except Exception as e:
    WOOD_TEXTURE = color.rgb(139, 69, 19)
    print(f"Exception loading WOOD_TEXTURE: {e}")

dirt_path = 'texture/dirt_texture.png'
print(f"Loading DIRT_TEXTURE from: {dirt_path}")
try:
    DIRT_TEXTURE = load_texture(dirt_path)
    print(f"DIRT_TEXTURE loaded: {DIRT_TEXTURE}, type: {type(DIRT_TEXTURE)}, hasattr width: {hasattr(DIRT_TEXTURE, 'width') if DIRT_TEXTURE else 'N/A'}")
    if DIRT_TEXTURE is None or not hasattr(DIRT_TEXTURE, 'width'):
        DIRT_TEXTURE = color.rgb(70, 35, 0)  # Dark brown fallback
        print("Using DIRT fallback color")
except Exception as e:
    DIRT_TEXTURE = color.rgb(70, 35, 0)
    print(f"Exception loading DIRT_TEXTURE: {e}")

grass_path = 'texture/grass.png'
print(f"Loading GRASS_TEXTURE from: {grass_path}")
try:
    GRASS_TEXTURE = load_texture(grass_path)
    print(f"GRASS_TEXTURE loaded: {GRASS_TEXTURE}, type: {type(GRASS_TEXTURE)}, hasattr width: {hasattr(GRASS_TEXTURE, 'width') if GRASS_TEXTURE else 'N/A'}")
    if GRASS_TEXTURE is None or not hasattr(GRASS_TEXTURE, 'width'):
        GRASS_TEXTURE = color.rgb(20, 120, 20)  # fallback green grass
        print("Using GRASS fallback color")
except Exception as e:
    GRASS_TEXTURE = color.rgb(20, 120, 20)
    print(f"Exception loading GRASS_TEXTURE: {e}")

print(f"Final WOOD_TEXTURE: {WOOD_TEXTURE}")
print(f"Final DIRT_TEXTURE: {DIRT_TEXTURE}")
print(f"Final GRASS_TEXTURE: {GRASS_TEXTURE}")

