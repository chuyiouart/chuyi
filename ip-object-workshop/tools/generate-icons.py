from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
CANVAS = 512
SCALE = 4
INK = (11, 12, 14, 255)
WHITE = (255, 255, 255, 255)


def scaled(value: int) -> int:
    return value * SCALE


def point(x: int, y: int) -> tuple[int, int]:
    return scaled(x), scaled(y)


def render_master() -> Image.Image:
    image = Image.new("RGBA", (scaled(CANVAS), scaled(CANVAS)), INK)
    draw = ImageDraw.Draw(image)

    draw.rectangle(
        [point(78, 166), point(220, 346)],
        outline=WHITE,
        width=scaled(28),
    )
    draw.line(
        [point(220, 206), point(278, 256), point(220, 306)],
        fill=WHITE,
        width=scaled(24),
        joint="curve",
    )

    cube = [
        point(332, 160),
        point(428, 215),
        point(428, 326),
        point(332, 381),
        point(236, 326),
        point(236, 215),
        point(332, 160),
    ]
    draw.line(cube, fill=WHITE, width=scaled(24), joint="curve")
    draw.line(
        [point(236, 215), point(332, 271), point(428, 215)],
        fill=WHITE,
        width=scaled(20),
        joint="curve",
    )
    draw.line(
        [point(332, 271), point(332, 381)],
        fill=WHITE,
        width=scaled(20),
    )
    draw.rectangle([point(318, 242), point(346, 270)], fill=WHITE)

    return image.resize((CANVAS, CANVAS), Image.Resampling.LANCZOS)


def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    master = render_master()
    master.save(ASSETS / "icon-512.png")

    for filename, size in (
        ("icon-192.png", 192),
        ("apple-touch-icon.png", 180),
        ("favicon-48.png", 48),
        ("favicon-32.png", 32),
    ):
        master.resize((size, size), Image.Resampling.LANCZOS).save(ASSETS / filename)

    maskable = Image.new("RGBA", (CANVAS, CANVAS), INK)
    safe_mark = master.resize((410, 410), Image.Resampling.LANCZOS)
    maskable.alpha_composite(safe_mark, (51, 51))
    maskable.save(ASSETS / "icon-512-maskable.png")

    master.save(
        ROOT / "favicon.ico",
        format="ICO",
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48)],
    )


if __name__ == "__main__":
    main()
