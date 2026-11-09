#!/usr/bin/env python3
"""Draw placeholder Sample looks for two days so the grid can be previewed.

Regenerates photos for the built-in sample codes and refreshes those records
in data/items.json. Items with any other code are left as they are.

  python scripts/make_samples.py
"""

from __future__ import annotations

import sys
from pathlib import Path

from lookbook import PHOTOS, load_items, make_code, rel_path, save_items

try:
    from PIL import Image, ImageDraw, ImageFilter, ImageFont
except ImportError:
    sys.exit("Pillow is required. Install it with: python -m pip install -r requirements.txt")

WIDTH = 1280
HEIGHT = 1600
CX = WIDTH // 2

SERIF = "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf"
SANS = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
SANS_BOLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"

SAMPLE_DATES = ("2026-11-09", "2026-11-08")


def rgb(value: str) -> tuple[int, int, int]:
    hex_color = value.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def mix(a: tuple[int, int, int], b: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))  # type: ignore[return-value]


def load_font(path: str, size: int) -> ImageFont.ImageFont:
    if Path(path).exists():
        return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def gradient(top: str, bottom: str) -> Image.Image:
    column = Image.new("RGB", (1, HEIGHT))
    pixels = column.load()
    color_top = rgb(top)
    color_bottom = rgb(bottom)
    for y in range(HEIGHT):
        pixels[0, y] = mix(color_top, color_bottom, y / (HEIGHT - 1))
    return column.resize((WIDTH, HEIGHT), Image.Resampling.BILINEAR)


class Pen:
    def __init__(self, draw: ImageDraw.ImageDraw, ox: int = 0, oy: int = 0):
        self.draw = draw
        self.ox = ox
        self.oy = oy

    def pts(self, points: list[tuple[int, int]]) -> list[tuple[int, int]]:
        return [(x + self.ox, y + self.oy) for x, y in points]

    def box(self, rect: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
        x0, y0, x1, y1 = rect
        return (x0 + self.ox, y0 + self.oy, x1 + self.ox, y1 + self.oy)

    def polygon(self, points: list[tuple[int, int]], fill: tuple) -> None:
        self.draw.polygon(self.pts(points), fill=fill)

    def ellipse(self, rect: tuple[int, int, int, int], **kwargs) -> None:
        self.draw.ellipse(self.box(rect), **kwargs)

    def rounded(self, rect: tuple[int, int, int, int], radius: int, fill: tuple) -> None:
        self.draw.rounded_rectangle(self.box(rect), radius=radius, fill=fill)

    def line(self, points: list[tuple[int, int]], fill: tuple, width: int) -> None:
        self.draw.line(self.pts(points), fill=fill, width=width, joint="curve")

    def arc(self, rect: tuple[int, int, int, int], start: int, end: int, fill: tuple, width: int) -> None:
        self.draw.arc(self.box(rect), start=start, end=end, fill=fill, width=width)


def draw_dress(pen: Pen, palette: dict, shadow: bool) -> None:
    fabric = palette["fabric"]
    pen.rounded((CX - 86, 300, CX - 46, 430), 10, fabric)
    pen.rounded((CX + 46, 300, CX + 86, 430), 10, fabric)
    pen.polygon(
        [
            (CX - 118, 400),
            (CX - 72, 640),
            (CX - 250, 1220),
            (CX + 250, 1220),
            (CX + 72, 640),
            (CX + 118, 400),
        ],
        fabric,
    )
    if shadow:
        return
    pen.line([(CX, 430), (CX, 1190)], palette["detail"], 3)
    pen.polygon(
        [
            (CX - 118, 400),
            (CX - 20, 470),
            (CX + 20, 470),
            (CX + 118, 400),
            (CX + 78, 455),
            (CX, 510),
            (CX - 78, 455),
        ],
        palette["sheen"],
    )


def draw_column(pen: Pen, palette: dict, shadow: bool) -> None:
    pen.polygon(
        [
            (CX - 108, 390),
            (CX - 86, 700),
            (CX - 130, 1220),
            (CX + 130, 1220),
            (CX + 86, 700),
            (CX + 108, 390),
        ],
        palette["fabric"],
    )
    if shadow:
        return
    pen.polygon(
        [
            (CX + 8, 460),
            (CX + 48, 560),
            (CX + 28, 1160),
            (CX - 8, 1100),
        ],
        palette["sheen"],
    )


def draw_day_dress(pen: Pen, palette: dict, shadow: bool) -> None:
    pen.polygon([(CX - 230, 610), (CX - 150, 500), (CX - 70, 650)], palette["fabric"])
    pen.polygon([(CX + 230, 610), (CX + 150, 500), (CX + 70, 650)], palette["fabric"])
    pen.polygon(
        [
            (CX - 155, 520),
            (CX - 118, 760),
            (CX - 270, 1240),
            (CX + 270, 1240),
            (CX + 118, 760),
            (CX + 155, 520),
        ],
        palette["fabric"],
    )
    if shadow:
        return
    pen.rounded((CX - 78, 840, CX + 78, 882), 12, palette["detail"])


def draw_blazer(pen: Pen, palette: dict, shadow: bool, top: int = 340, scale: float = 1) -> None:
    def s(value: int, origin: int = top) -> int:
        return origin + round((value - 340) * scale)

    def x(value: int) -> int:
        return CX + round((value - CX) * scale)

    fabric = palette["fabric"]
    dark = palette["detail"]
    pen.polygon(
        [(x(CX - 150), s(390)), (x(CX - 430), s(560)), (x(CX - 340), s(860)), (x(CX - 150), s(760))],
        fabric,
    )
    pen.polygon(
        [(x(CX + 150), s(390)), (x(CX + 430), s(560)), (x(CX + 340), s(860)), (x(CX + 150), s(760))],
        fabric,
    )
    pen.rounded((x(CX - 170), s(360), x(CX + 170), s(1040)), 20, fabric)
    if shadow:
        return
    pen.polygon([(x(CX - 8), s(400)), (x(CX - 150), s(380)), (x(CX - 46), s(700))], dark)
    pen.polygon([(x(CX + 8), s(400)), (x(CX + 150), s(380)), (x(CX + 46), s(700))], dark)
    pen.line([(x(CX - 110), s(820)), (x(CX - 28), s(820))], palette["sheen"], 4)
    pen.line([(x(CX + 28), s(820)), (x(CX + 110), s(820))], palette["sheen"], 4)
    for step in range(3):
        button_y = s(760 + step * 70)
        pen.ellipse((x(CX - 8), button_y, x(CX + 8), button_y + 16), fill=palette["sheen"])


def draw_suit(pen: Pen, palette: dict, shadow: bool) -> None:
    pen.polygon(
        [
            (CX - 160, 860),
            (CX - 230, 1320),
            (CX - 48, 1320),
            (CX - 18, 940),
            (CX + 18, 940),
            (CX + 48, 1320),
            (CX + 230, 1320),
            (CX + 160, 860),
        ],
        palette["fabric"],
    )
    draw_blazer(pen, palette, shadow, top=300, scale=0.92)


def draw_loafer(pen: Pen, origin: tuple[int, int], palette: dict, shadow: bool) -> None:
    x, y = origin
    pen.rounded((x + 24, y + 168, x + 150, y + 214), 12, palette["detail"])
    pen.rounded((x, y + 128, x + 560, y + 196), 34, palette["detail"])
    pen.polygon(
        [
            (x + 30, y + 150),
            (x + 90, y + 58),
            (x + 250, y + 36),
            (x + 430, y + 78),
            (x + 530, y + 142),
            (x + 500, y + 168),
            (x + 40, y + 168),
        ],
        palette["fabric"],
    )
    if shadow:
        return
    pen.polygon(
        [
            (x + 170, y + 72),
            (x + 250, y + 60),
            (x + 390, y + 96),
            (x + 250, y + 118),
        ],
        palette["sheen"],
    )
    pen.polygon(
        [
            (x + 188, y + 108),
            (x + 470, y + 128),
            (x + 458, y + 150),
            (x + 180, y + 132),
        ],
        palette["detail"],
    )


def draw_loafers(pen: Pen, palette: dict, shadow: bool) -> None:
    draw_loafer(pen, (180, 520), palette, shadow)
    draw_loafer(pen, (340, 780), palette, shadow)


def draw_heel(pen: Pen, origin: tuple[int, int], palette: dict, shadow: bool) -> None:
    x, y = origin
    pen.polygon(
        [(x + 86, y + 132), (x + 112, y + 132), (x + 118, y + 228), (x + 74, y + 228)],
        palette["detail"],
    )
    pen.polygon(
        [
            (x + 48, y + 150),
            (x + 130, y + 136),
            (x + 500, y + 168),
            (x + 470, y + 196),
            (x + 40, y + 184),
        ],
        palette["detail"],
    )
    pen.polygon(
        [
            (x + 150, y + 148),
            (x + 190, y + 42),
            (x + 330, y + 36),
            (x + 470, y + 156),
            (x + 300, y + 150),
            (x + 200, y + 156),
        ],
        palette["fabric"],
    )
    if shadow:
        return
    pen.line([(x + 168, y + 78), (x + 250, y + 66)], palette["sheen"], 8)


def draw_heels(pen: Pen, palette: dict, shadow: bool) -> None:
    draw_heel(pen, (160, 540), palette, shadow)
    draw_heel(pen, (360, 800), palette, shadow)


def draw_tote(pen: Pen, palette: dict, shadow: bool) -> None:
    pen.ellipse((CX - 210, 300, CX - 10, 760), outline=palette["detail"], width=22)
    pen.ellipse((CX + 10, 300, CX + 210, 760), outline=palette["detail"], width=22)
    pen.rounded((CX - 250, 560, CX + 250, 1240), 22, palette["fabric"])
    if shadow:
        return
    pen.polygon(
        [
            (CX + 170, 590),
            (CX + 250, 620),
            (CX + 250, 1210),
            (CX + 170, 1180),
        ],
        palette["detail"],
    )
    pen.line([(CX, 590), (CX, 1200)], palette["sheen"], 4)
    pen.rounded((CX - 70, 760, CX + 70, 900), 8, palette["sheen"])


def draw_shoulder(pen: Pen, palette: dict, shadow: bool) -> None:
    pen.line(
        [
            (CX - 150, 860),
            (CX - 230, 620),
            (CX, 470),
            (CX + 240, 620),
            (CX + 160, 860),
        ],
        palette["detail"],
        16,
    )
    pen.rounded((CX - 220, 720, CX + 230, 1220), 72, palette["fabric"])
    if shadow:
        return
    pen.line([(CX - 150, 880), (CX + 160, 880)], palette["detail"], 6)
    pen.ellipse((CX + 120, 980, CX + 164, 1024), fill=palette["sheen"])


def draw_scarf(pen: Pen, palette: dict, shadow: bool) -> None:
    ribbon = [
        (160, 980),
        (360, 620),
        (620, 860),
        (860, 520),
        (1120, 760),
    ]
    pen.line(ribbon, palette["fabric"], 150)
    if shadow:
        return
    edge = [(x + 28, y - 36) for x, y in ribbon]
    pen.line(edge, palette["detail"], 16)


def draw_hoops(pen: Pen, palette: dict, shadow: bool) -> None:
    rings = (
        (CX - 360, 520, CX - 40, 840),
        (CX + 20, 640, CX + 380, 1000),
    )
    for rect in rings:
        pen.ellipse(rect, outline=palette["fabric"], width=36)
        if shadow:
            continue
        inset = (rect[0] + 18, rect[1] + 18, rect[2] - 18, rect[3] - 18)
        pen.arc(inset, 200, 350, palette["sheen"], 8)


DRAWINGS = {
    "dress": draw_dress,
    "column": draw_column,
    "day-dress": draw_day_dress,
    "blazer": draw_blazer,
    "suit": draw_suit,
    "loafers": draw_loafers,
    "heels": draw_heels,
    "tote": draw_tote,
    "shoulder": draw_shoulder,
    "scarf": draw_scarf,
    "hoops": draw_hoops,
}


SAMPLES = [
    {
        "date": "2026-11-09",
        "seq": 1,
        "category": "Dresses",
        "title": "Ivory slip dress",
        "note": "Sample · bias-cut satin",
        "kind": "dress",
        "bg_top": "#d9cfc3",
        "bg_bottom": "#c9bbaa",
        "fabric": "#f6f1e8",
        "detail": "#cbbba6",
        "sheen": "#fffaf3",
        "ink": "#2a241e",
    },
    {
        "date": "2026-11-09",
        "seq": 2,
        "category": "Workwear",
        "title": "Charcoal tailored blazer",
        "note": "Sample · structured wool",
        "kind": "blazer",
        "bg_top": "#e4e0db",
        "bg_bottom": "#cfc9c2",
        "fabric": "#2c2a28",
        "detail": "#1a1918",
        "sheen": "#b7aa9a",
        "ink": "#241f1b",
    },
    {
        "date": "2026-11-09",
        "seq": 3,
        "category": "Shoes",
        "title": "Black leather loafers",
        "note": "Sample · leather, ask for sizes",
        "kind": "loafers",
        "bg_top": "#efe8de",
        "bg_bottom": "#ddd3c6",
        "fabric": "#1b1b1b",
        "detail": "#8d7762",
        "sheen": "#3a3532",
        "ink": "#2a241e",
    },
    {
        "date": "2026-11-09",
        "seq": 4,
        "category": "Bags",
        "title": "Structured camel tote",
        "note": "Sample · boxed calf",
        "kind": "tote",
        "bg_top": "#f3e7d6",
        "bg_bottom": "#e4d0b4",
        "fabric": "#c49655",
        "detail": "#8a5a2b",
        "sheen": "#e6c48a",
        "ink": "#3a2a16",
    },
    {
        "date": "2026-11-09",
        "seq": 5,
        "category": "Dresses",
        "title": "Wine satin midi",
        "note": "Sample · evening weight",
        "kind": "column",
        "bg_top": "#eadfdb",
        "bg_bottom": "#d9c9c4",
        "fabric": "#6e2432",
        "detail": "#4d1522",
        "sheen": "#9a4454",
        "ink": "#2c161a",
    },
    {
        "date": "2026-11-09",
        "seq": 6,
        "category": "Other",
        "title": "Ink silk scarf",
        "note": "Sample · rolled edge",
        "kind": "scarf",
        "bg_top": "#ece7df",
        "bg_bottom": "#ddd4c8",
        "fabric": "#1d3557",
        "detail": "#c6a15b",
        "sheen": "#2d4d73",
        "ink": "#1c1916",
    },
    {
        "date": "2026-11-08",
        "seq": 1,
        "category": "Workwear",
        "title": "Cream wide-leg suit",
        "note": "Sample · suiting, unlined jacket",
        "kind": "suit",
        "bg_top": "#ddd6cb",
        "bg_bottom": "#ccc3b6",
        "fabric": "#f7f3ea",
        "detail": "#2b2926",
        "sheen": "#d9d0c2",
        "ink": "#24211d",
    },
    {
        "date": "2026-11-08",
        "seq": 2,
        "category": "Shoes",
        "title": "Nude slingback heels",
        "note": "Sample · leather, 7 cm heel",
        "kind": "heels",
        "bg_top": "#f6ebe3",
        "bg_bottom": "#ead8cc",
        "fabric": "#e0b79a",
        "detail": "#6d4634",
        "sheen": "#f3d7c4",
        "ink": "#3c2b22",
    },
    {
        "date": "2026-11-08",
        "seq": 3,
        "category": "Bags",
        "title": "Mini black shoulder bag",
        "note": "Sample · adjustable strap",
        "kind": "shoulder",
        "bg_top": "#eeeae4",
        "bg_bottom": "#ddd6ce",
        "fabric": "#161616",
        "detail": "#3a342e",
        "sheen": "#c2b09a",
        "ink": "#1c1916",
    },
    {
        "date": "2026-11-08",
        "seq": 4,
        "category": "Dresses",
        "title": "Blush day dress",
        "note": "Sample · short puff sleeve",
        "kind": "day-dress",
        "bg_top": "#f8ece8",
        "bg_bottom": "#efd8d2",
        "fabric": "#f0c3bb",
        "detail": "#c45b62",
        "sheen": "#f8e4df",
        "ink": "#4a2c2c",
    },
    {
        "date": "2026-11-08",
        "seq": 5,
        "category": "Other",
        "title": "Gold hoop pair",
        "note": "Sample · polished metal",
        "kind": "hoops",
        "bg_top": "#f7f1e6",
        "bg_bottom": "#e7dcc8",
        "fabric": "#c6a15b",
        "detail": "#8d6b32",
        "sheen": "#f0ddb0",
        "ink": "#3a301c",
    },
]


def draw_tracked(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, font, fill, tracking: int) -> None:
    x, y = xy
    for char in text:
        draw.text((x, y), char, font=font, fill=fill)
        x += int(draw.textlength(char, font=font)) + tracking


def paint(spec: dict, code: str) -> Image.Image:
    base = gradient(spec["bg_top"], spec["bg_bottom"]).convert("RGBA")
    shadow_layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    shadow_pen = Pen(ImageDraw.Draw(shadow_layer), ox=0, oy=18)
    palette = {
        "fabric": (40, 32, 24, 80),
        "detail": (40, 32, 24, 80),
        "sheen": (40, 32, 24, 80),
    }
    DRAWINGS[spec["kind"]](shadow_pen, palette, True)
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(18))
    base = Image.alpha_composite(base, shadow_layer)

    colors = {
        "fabric": rgb(spec["fabric"]),
        "detail": rgb(spec["detail"]),
        "sheen": rgb(spec["sheen"]),
    }
    DRAWINGS[spec["kind"]](Pen(ImageDraw.Draw(base)), colors, False)
    image = base.convert("RGB")
    draw = ImageDraw.Draw(image)
    ink = rgb(spec["ink"])
    label_fill = mix(rgb(spec["bg_top"]), ink, 0.62)
    draw_tracked(draw, (56, 56), "SAMPLE", load_font(SANS_BOLD, 22), label_fill, 6)

    code_font = load_font(SANS_BOLD, 28)
    text_box = draw.textbbox((0, 0), code, font=code_font)
    text_width = text_box[2] - text_box[0]
    text_height = text_box[3] - text_box[1]
    plate_fill = mix(rgb(spec["bg_bottom"]), ink, 0.72)
    x, y = 52, HEIGHT - 92
    draw.rounded_rectangle(
        (x, y, x + text_width + 36, y + text_height + 22),
        radius=8,
        fill=plate_fill,
    )
    draw.text((x + 18, y + 8), code, font=code_font, fill=(255, 252, 247))
    return image


def sample_record(spec: dict) -> dict:
    code = make_code("CO", spec["date"], spec["seq"])
    dest = PHOTOS / spec["date"] / f"{code}.webp"
    return {
        "code": code,
        "date": spec["date"],
        "category": spec["category"],
        "title": spec["title"],
        "note": spec["note"],
        "image": rel_path(dest),
        "source": f"sample:{spec['kind']}",
    }


def main() -> int:
    items = load_items()
    sample_codes = {make_code("CO", spec["date"], spec["seq"]) for spec in SAMPLES}
    kept = [item for item in items if item.get("code") not in sample_codes]
    written: list[dict] = []
    for spec in SAMPLES:
        record = sample_record(spec)
        dest = PHOTOS / spec["date"] / f"{record['code']}.webp"
        image = paint(spec, record["code"])
        dest.parent.mkdir(parents=True, exist_ok=True)
        image.save(dest, format="WEBP", quality=82, method=6)
        written.append(record)
        print(f"sample  {record['code']}  {record['image']}  {spec['category']}")
    save_items(kept + written)
    print(f"Wrote {len(written)} sample looks across {', '.join(SAMPLE_DATES)}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
