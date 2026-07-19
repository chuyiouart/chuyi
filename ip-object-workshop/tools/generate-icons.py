from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
CANVAS = 512
INK = (11, 12, 14, 255)
WHITE = (255, 255, 255, 255)


def render_master() -> Image.Image:
    source = Image.open(ASSETS / "workshop-logo-gpt-source.png").convert("L")
    mask = source.point(lambda value: 255 if value >= 128 else 0)
    bbox = mask.getbbox()
    if bbox is None:
        raise RuntimeError("Generated logo source does not contain a white mark.")

    mark = mask.crop(bbox)
    target_width = 340
    target_height = round(mark.height * target_width / mark.width)
    mark = mark.resize((target_width, target_height), Image.Resampling.LANCZOS)

    image = Image.new("RGBA", (CANVAS, CANVAS), INK)
    white_layer = Image.new("RGBA", mark.size, WHITE)
    position = ((CANVAS - target_width) // 2, (CANVAS - target_height) // 2)
    image.paste(white_layer, position, mark)
    return image


def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    master = render_master()
    master.save(ASSETS / "workshop-logo-v2.png")
    master.save(ASSETS / "icon-512-v2.png")

    for filename, size in (
        ("icon-192-v2.png", 192),
        ("apple-touch-icon-v2.png", 180),
        ("favicon-48-v2.png", 48),
        ("favicon-32-v2.png", 32),
    ):
        master.resize((size, size), Image.Resampling.LANCZOS).save(ASSETS / filename)

    maskable = Image.new("RGBA", (CANVAS, CANVAS), INK)
    safe_mark = master.resize((410, 410), Image.Resampling.LANCZOS)
    maskable.alpha_composite(safe_mark, (51, 51))
    maskable.save(ASSETS / "icon-512-maskable-v2.png")

    master.save(
        ROOT / "favicon.ico",
        format="ICO",
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48)],
    )


if __name__ == "__main__":
    main()
