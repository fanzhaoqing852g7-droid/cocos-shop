#!/usr/bin/env python3
"""Import one day's photos into the Coco's Shop lookbook.

Each photo is resized so its long edge is at most 1600 pixels, saved as WebP,
and stripped of EXIF metadata (including GPS). Orientation is applied first,
so portraits stay upright. Item codes look like CO-1109-01: the prefix from
data/config.json, the month and day, then a sequence that continues across
the whole catalog so the same month-day in another year does not reuse a code.

Examples:
  python scripts/add_day.py 2026-11-10 ./incoming/2026-11-10
  python scripts/add_day.py 2026-11-10 ./incoming/2026-11-10 --category Dresses
  python scripts/add_day.py 2026-11-10 ./incoming/2026-11-10 --force
  python scripts/add_day.py 2026-11-09 ./incoming/set --one-item --code CO-1109-02 --category Sets

Name a file with its category to override the default:
  dresses-ivory-slip.jpg
  workwear_charcoal_blazer.jpg
  Shoes - nude slingback.jpg

Or put manifest.json in the source folder:

  [
    {"file": "IMG_2210.jpg", "category": "Bags", "title": "Camel tote", "note": "Cowhide"}
  ]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from lookbook import (
    PHOTOS,
    canonical_category,
    categories_from,
    category_from_stem,
    load_config,
    load_items,
    make_code,
    next_sequence,
    parse_date,
    rel_path,
    save_items,
)

try:
    from PIL import Image, ImageOps
except ImportError:
    sys.exit("Pillow is required. Install it with: python -m pip install -r requirements.txt")

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".bmp"}


def flatten(image: Image.Image) -> Image.Image:
    if image.mode == "RGB":
        return image
    has_alpha = image.mode in ("RGBA", "LA") or (
        image.mode == "P" and "transparency" in image.info
    )
    if has_alpha:
        rgba = image.convert("RGBA")
        background = Image.new("RGB", rgba.size, (255, 255, 255))
        background.paste(rgba, mask=rgba.getchannel("A"))
        return background
    return image.convert("RGB")


def downscale(image: Image.Image, long_edge: int) -> Image.Image:
    width, height = image.size
    longest = max(width, height)
    if longest <= long_edge:
        return image
    scale = long_edge / longest
    size = (max(1, round(width * scale)), max(1, round(height * scale)))
    return image.resize(size, Image.Resampling.LANCZOS)


def prepare_photo(src: Path, dest: Path, long_edge: int, quality: int) -> tuple[int, int]:
    """Apply orientation, cap the long edge, and write a WebP with no metadata."""
    with Image.open(src) as raw:
        oriented = ImageOps.exif_transpose(raw)
        image = downscale(flatten(oriented), long_edge)
        # A fresh buffer drops EXIF, ICC, GPS, and any other payload.
        clean = Image.frombytes("RGB", image.size, image.tobytes())
    dest.parent.mkdir(parents=True, exist_ok=True)
    clean.save(dest, format="WEBP", quality=quality, method=6)
    return clean.size


def load_manifest(src: Path) -> dict[str, dict]:
    path = src / "manifest.json"
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"{path} is not valid JSON: {exc}") from exc
    if not isinstance(data, list):
        raise SystemExit(f"{path} must be a list of objects.")
    manifest: dict[str, dict] = {}
    for entry in data:
        if not isinstance(entry, dict) or not entry.get("file"):
            raise SystemExit(f"{path} entries need a file name.")
        manifest[str(entry["file"])] = entry
    return manifest


def collect_images(src: Path) -> list[Path]:
    files = [
        path
        for path in src.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    ]
    return sorted(files, key=lambda path: path.name.casefold())


def photo_dest(day_dir: Path, code: str, index: int, total: int) -> Path:
    if total == 1:
        return day_dir / f"{code}.webp"
    return day_dir / f"{code}-{index + 1:02d}.webp"


def forced_code(value: str, prefix: str, date_str: str) -> str:
    stamp = parse_date(date_str)
    stem = f"{prefix}-{stamp.month:02d}{stamp.day:02d}-"
    tail = value[len(stem) :] if value.startswith(stem) else ""
    if not tail.isdigit() or int(tail) < 1:
        raise SystemExit(f"--code must look like {stem}02, got {value!r}.")
    return value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Add a day's photos to the Coco's Shop lookbook."
    )
    parser.add_argument("date", help="Shoot date, YYYY-MM-DD")
    parser.add_argument("src", help="Folder of photos for that day")
    parser.add_argument(
        "--category",
        default="Other",
        help="Category used when the filename does not name one (default: Other)",
    )
    parser.add_argument(
        "--one-item",
        action="store_true",
        help="Import every photo in the folder as one item, filename order, first file is the cover",
    )
    parser.add_argument("--code", help="Force the item code, such as CO-1109-02. Use with --one-item")
    parser.add_argument("--title", default="", help="Title for a --one-item import")
    parser.add_argument("--note", default="", help="Note for a --one-item import")
    parser.add_argument("--long-edge", type=int, default=1600)
    parser.add_argument("--quality", type=int, default=82)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Reprocess a source filename already imported for this date",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the codes that would be written and leave files untouched",
    )
    return parser


def import_one_item(args, images, items, date_str, day_dir, prefix, category) -> int:
    filenames = [path.name for path in images]
    if args.code:
        code = forced_code(args.code, prefix, date_str)
    else:
        code = make_code(prefix, date_str, next_sequence(items, prefix, date_str))
    title = args.title.strip() or category
    note = args.note.strip()
    existing = next((item for item in items if item.get("code") == code), None)
    if existing and not args.force:
        print(f"skip  {code}  already in the lookbook ({len(filenames)} photos not imported)")
        print("Imported 0, skipped 1.")
        return 0

    paths = []
    for index, image_path in enumerate(images):
        dest = photo_dest(day_dir, code, index, len(images))
        paths.append(rel_path(dest))
        if args.dry_run:
            role = "cover" if index == 0 else f"photo {index + 1}"
            print(f"plan  {image_path.name}  ->  {paths[-1]}  {role}")
            continue
        width, height = prepare_photo(image_path, dest, args.long_edge, args.quality)
        print(f"add   {code}  {paths[-1]}  {width}x{height}  {image_path.name}")

    record = {
        "code": code,
        "date": date_str,
        "category": category,
        "title": title,
        "note": note,
        "image": paths[0],
        "images": paths,
        "source": filenames[0],
        "sources": filenames,
    }
    if not args.dry_run:
        if existing:
            existing.clear()
            existing.update(record)
        else:
            items.append(record)
        save_items(items)
    print(f"{'Planned' if args.dry_run else 'Imported'} 1 item, {len(images)} photos, skipped 0.")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.long_edge < 1:
        raise SystemExit("--long-edge must be at least 1.")
    if not 1 <= args.quality <= 100:
        raise SystemExit("--quality must be between 1 and 100.")

    date_str = parse_date(args.date).strftime("%Y-%m-%d")
    src = Path(args.src).expanduser().resolve()
    if not src.is_dir():
        raise SystemExit(f"Source folder not found: {src}")

    config = load_config()
    categories = categories_from(config)
    prefix = str(config.get("codePrefix") or "CO").strip() or "CO"
    default_category = canonical_category(args.category, categories)
    if default_category is None:
        raise SystemExit(
            f"Unknown category {args.category!r}. Use one of: {', '.join(categories)}."
        )

    manifest = load_manifest(src)
    images = collect_images(src)
    if not images:
        raise SystemExit(f"No images found in {src}.")

    items = load_items()
    added = 0
    skipped = 0
    day_dir = PHOTOS / date_str

    if args.one_item or args.code or args.title or args.note:
        if not args.one_item:
            raise SystemExit("--code, --title, and --note are used with --one-item.")
        return import_one_item(
            args,
            images,
            items,
            date_str,
            day_dir,
            prefix,
            default_category,
        )

    for image_path in images:
        meta = manifest.get(image_path.name, {})
        category, title = category_from_stem(image_path.stem, categories, default_category)
        note = ""
        if meta:
            if meta.get("category"):
                category = canonical_category(str(meta["category"]), categories)
                if category is None:
                    raise SystemExit(
                        f"{image_path.name}: unknown category {meta['category']!r}."
                    )
            if meta.get("title"):
                title = str(meta["title"]).strip() or title
            if meta.get("note"):
                note = str(meta["note"]).strip()

        existing = next(
            (
                item
                for item in items
                if item.get("date") == date_str and item.get("source") == image_path.name
            ),
            None,
        )
        if existing and not args.force:
            print(f"skip  {image_path.name}  ({existing.get('code')})")
            skipped += 1
            continue

        if existing:
            code = str(existing["code"])
        else:
            code = make_code(prefix, date_str, next_sequence(items, prefix, date_str))

        dest = day_dir / f"{code}.webp"
        record = {
            "code": code,
            "date": date_str,
            "category": category,
            "title": title,
            "note": note,
            "image": rel_path(dest),
            "source": image_path.name,
        }
        if args.dry_run:
            print(f"plan  {image_path.name}  ->  {record['image']}  {category}  {title}")
        else:
            width, height = prepare_photo(image_path, dest, args.long_edge, args.quality)
            print(
                f"add   {code}  {record['image']}  {width}x{height}  {category}  {title}"
            )
        if existing:
            existing.update(record)
        else:
            items.append(record)
        added += 1

    if not args.dry_run and added:
        save_items(items)
    print(f"{'Planned' if args.dry_run else 'Imported'} {added}, skipped {skipped}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
