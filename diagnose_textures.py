from config import WOOD_TEXTURE, DIRT_TEXTURE, GRASS_TEXTURE

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
