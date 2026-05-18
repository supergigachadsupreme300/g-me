"""
Generate bark, leaves, and rock textures in a warm hand-painted style
matching the rat texture's earthy low-poly aesthetic.
Run once: python gen_textures.py
"""
from PIL import Image, ImageDraw, ImageFilter
import random
import math

SIZE = 512
rng = random.Random(42)


def noise_layer(img, strength=12):
    """Add subtle random noise to an image."""
    pixels = img.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            r, g, b = pixels[x, y]
            d = rng.randint(-strength, strength)
            pixels[x, y] = (
                max(0, min(255, r + d)),
                max(0, min(255, g + d)),
                max(0, min(255, b + d)),
            )
    return img


# ── Bark texture ────────────────────────────────────────────────────────────────
def make_bark(path, size=SIZE):
    img = Image.new("RGB", (size, size), (95, 62, 28))
    draw = ImageDraw.Draw(img)

    # Base gradient — darker at edges
    for y in range(size):
        shade = int(10 * math.sin(math.pi * y / size))
        for x in range(size):
            r = max(0, min(255, 95 + shade + rng.randint(-6, 6)))
            g = max(0, min(255, 62 + shade + rng.randint(-4, 4)))
            b = max(0, min(255, 28 + shade + rng.randint(-3, 3)))
            img.putpixel((x, y), (r, g, b))

    # Vertical grain lines
    for _ in range(60):
        x = rng.randint(0, size - 1)
        length = rng.randint(size // 4, size)
        y0 = rng.randint(0, size - length)
        thickness = rng.randint(1, 3)
        darkness = rng.randint(15, 40)
        for dy in range(length):
            cx = x + rng.randint(-1, 1)
            cy = y0 + dy
            if 0 <= cx < size and 0 <= cy < size:
                r, g, b = img.getpixel((cx, cy))
                img.putpixel((cx, cy), (
                    max(0, r - darkness),
                    max(0, g - darkness // 2),
                    max(0, b - darkness // 3),
                ))

    # Knots
    for _ in range(5):
        kx = rng.randint(size // 6, size * 5 // 6)
        ky = rng.randint(size // 6, size * 5 // 6)
        for ring in range(6, 0, -1):
            shade = 30 - ring * 4
            draw.ellipse(
                [kx - ring * 2, ky - ring, kx + ring * 2, ky + ring],
                outline=(max(0, 70 - shade), max(0, 40 - shade), max(0, 15 - shade)),
                width=1,
            )

    # Light highlight streaks
    for _ in range(20):
        x = rng.randint(0, size - 1)
        y0 = rng.randint(0, size // 2)
        length = rng.randint(20, 80)
        for dy in range(length):
            cx = x + rng.randint(-1, 1)
            cy = y0 + dy
            if 0 <= cx < size and 0 <= cy < size:
                r, g, b = img.getpixel((cx, cy))
                img.putpixel((cx, cy), (
                    min(255, r + 18),
                    min(255, g + 10),
                    min(255, b + 5),
                ))

    img = img.filter(ImageFilter.GaussianBlur(0.6))
    noise_layer(img, 8)
    img.save(path)
    print(f"Saved {path}")


# ── Rock texture ────────────────────────────────────────────────────────────────
def make_rock(path, size=SIZE):
    # Fill with per-pixel gray noise — strictly warm-gray palette
    pixels = []
    for y in range(size):
        for x in range(size):
            v = rng.randint(95, 132)
            pixels.append((v + rng.randint(0, 6), v + rng.randint(-2, 2), v - rng.randint(0, 10)))
    img = Image.new("RGB", (size, size))
    img.putdata(pixels)

    # Blur heavily to get smooth stone variation
    img = img.filter(ImageFilter.GaussianBlur(12))

    draw = ImageDraw.Draw(img)

    # Cracks
    for _ in range(22):
        x, y = rng.randint(0, size), rng.randint(0, size)
        angle = rng.uniform(0, math.pi * 2)
        length = rng.randint(40, 150)
        for step in range(length):
            nx = int(x + math.cos(angle) * step)
            ny = int(y + math.sin(angle) * step)
            angle += rng.uniform(-0.12, 0.12)
            if 0 <= nx < size and 0 <= ny < size:
                pr, pg, pb = img.getpixel((nx, ny))
                img.putpixel((nx, ny), (max(0, pr - 35), max(0, pg - 32), max(0, pb - 28)))

    # Subtle specular flecks
    for _ in range(20):
        sx = rng.randint(0, size - 1)
        sy = rng.randint(0, size - 1)
        rad = rng.randint(1, 4)
        v = rng.randint(148, 168)
        draw.ellipse([sx - rad, sy - rad, sx + rad, sy + rad], fill=(v, v - 2, v - 6))

    img = img.filter(ImageFilter.GaussianBlur(0.4))
    noise_layer(img, 7)
    img.save(path)
    print(f"Saved {path}")


# ── Leaves texture ──────────────────────────────────────────────────────────────
def make_leaves(path, size=SIZE):
    img = Image.new("RGB", (size, size), (35, 105, 35))

    # Colour variation patches
    for _ in range(120):
        px = rng.randint(0, size - 1)
        py = rng.randint(0, size - 1)
        pr = rng.randint(15, 50)
        shade_r = rng.randint(20, 55)
        shade_g = rng.randint(85, 140)
        shade_b = rng.randint(18, 45)
        for dy in range(-pr, pr):
            for dx in range(-pr, pr):
                if dx * dx + dy * dy <= pr * pr:
                    nx, ny = px + dx, py + dy
                    if 0 <= nx < size and 0 <= ny < size:
                        img.putpixel((nx, ny), (shade_r, shade_g, shade_b))

    img = img.filter(ImageFilter.GaussianBlur(2))

    draw = ImageDraw.Draw(img)

    # Leaf veins / highlights
    for _ in range(40):
        lx = rng.randint(0, size)
        ly = rng.randint(0, size)
        angle = rng.uniform(0, math.pi * 2)
        length = rng.randint(20, 70)
        pts = []
        for step in range(length):
            nx = int(lx + math.cos(angle) * step)
            ny = int(ly + math.sin(angle) * step)
            angle += rng.uniform(-0.1, 0.1)
            if 0 <= nx < size and 0 <= ny < size:
                pts.append((nx, ny))
        for px, py in pts:
            r, g, b = img.getpixel((px, py))
            img.putpixel((px, py), (
                min(255, r + 12),
                min(255, g + 22),
                min(255, b + 10),
            ))

    # Autumn accent dots (warm spots like the rat's warm tones)
    for _ in range(30):
        ax = rng.randint(0, size - 1)
        ay = rng.randint(0, size - 1)
        rad = rng.randint(3, 9)
        draw.ellipse([ax - rad, ay - rad, ax + rad, ay + rad],
                     fill=(rng.randint(160, 200), rng.randint(100, 140), rng.randint(20, 50)))

    noise_layer(img, 8)
    img.save(path)
    print(f"Saved {path}")


# ── Run ──────────────────────────────────────────────────────────────────────────
base = "texture"
make_bark(f"{base}/bark_texture.png")
make_rock(f"{base}/rock_texture.png")
make_leaves(f"{base}/leaves_texture.png")
print("All textures generated.")
