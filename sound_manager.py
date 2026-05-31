from ursina import Audio
import os

SOUNDS = {}

def _load_sound(name, path):
    try:
        snd = Audio(path, autoplay=False, loop=False)
        SOUNDS[name] = snd
    except Exception as e:
        print(f"Failed to load sound {name} at {path}: {e}")


def init():
    base_dir = os.path.join(os.path.dirname(__file__), 'sound')
    mapping = {
        'mexican_truck': 'sound/mexican_truck.mp3',
        'pop': 'sound/pop.mp3',
        'tree': 'sound/tree.mp3',
        'axe': 'sound/axe.mp3',
        'pickaxe': 'sound/pickaxe.mp3',
        'gun': 'sound/gun.mp3',
        'hoe': 'sound/hoe.mp3',
        'sword': 'sound/sword.mp3',
        'hammer': 'sound/hammer.mp3',
        'sickle': 'sound/sickle.mp3',
        'bonk':'sound/bonk.mp3',
    }
    for key, filename in mapping.items():
        path = os.path.join(base_dir, filename)
        if os.path.exists(path):
            _load_sound(key, path)
        else:
            # try fallback to relative path
            try:
                _load_sound(key, filename)
            except Exception:
                print(f"Sound file not found: {path}")


def play(name, pitch=1.0):
    snd = SOUNDS.get(name)
    if not snd:
        return
    try:
        snd.pitch = pitch
        snd.play()
    except Exception as e:
        print(f"Failed to play sound {name}: {e}")


# initialize on import
try:
    init()
except Exception:
    pass
