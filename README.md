# Coco's Shop

Daily lookbook for Coco, a Guangzhou fashion buyer. Newest day first, with category filters and a full-screen viewer. Each piece has a code such as `CO-1109-01`. The contact button is **Ask on WhatsApp**.

Live site: [https://fanzhaoqing852g7-droid.github.io/cocos-shop/](https://fanzhaoqing852g7-droid.github.io/cocos-shop/)

## Daily update

Put that day's photos in a folder, then import them. Pillow resizes the long edge to at most 1600 pixels, saves WebP, applies orientation, and drops EXIF metadata including GPS.

```bash
python3 -m pip install -r requirements.txt
python3 scripts/add_day.py 2026-11-10 ./incoming/2026-11-10
git add data/items.json photos/2026-11-10
git commit -m "Add 2026-11-10 looks"
git push
```

Use `python` instead of `python3` if that is how Python 3 is installed on your machine.

GitHub Pages publishes the `main` branch root, so the new day appears after the push finishes building.

Name files with a category when you know it. The default category is `Other`.

```text
dresses-ivory-slip.jpg
workwear_charcoal-blazer.jpg
Shoes - nude slingback.jpg
```

Or add `manifest.json` beside the photos:

```json
[
  {
    "file": "IMG_2210.jpg",
    "category": "Bags",
    "title": "Structured camel tote",
    "note": "Cowhide, ask for colours"
  }
]
```

Run the same command again and existing filenames for that date are skipped. Pass `--force` to rebuild them in place. `--dry-run` prints the codes without writing files.

Several photos of one look stay in one folder. The first filename is the cover, and the rest open in the viewer in that order:

```bash
python3 scripts/add_day.py 2026-11-09 ./incoming/lantern-set \
  --one-item --code CO-1109-02 --category Sets \
  --title "Embroidered lantern-sleeve set" \
  --note "Embroidered lantern-sleeve shirt + wide-leg trousers set. Colours: black, burgundy brown"
```

`--code` keeps a number free. `CO-1109-01` is reserved for a skirt, so the first published looks are `CO-1109-02`, `CO-1109-03`, and `CO-1109-04`.

Codes use the month and day, then the lowest free sequence for that day: 9 November can still use `CO-1109-01` while `02`–`04` are taken.

## Preview locally

```bash
python3 -m http.server 8080
```

Open [http://127.0.0.1:8080](http://127.0.0.1:8080). Fetching the JSON files needs a local server; opening `index.html` as a file will not load the grid.

Regenerate the built-in placeholder days (8 and 9 November 2026) with:

```bash
python3 scripts/make_samples.py
```

That refreshes placeholder codes only. A code already used by a real look is left alone.

## Where things live

| Path | Role |
| --- | --- |
| `index.html`, `styles.css`, `app.js` | The lookbook |
| `data/config.json` | Shop name, WhatsApp number, categories, code prefix |
| `data/items.json` | One record per look, newest day first |
| `photos/YYYY-MM-DD/` | WebP images named by item code |
| `scripts/add_day.py` | Import a day of photos |
| `scripts/make_samples.py` | Draw placeholder Sample images |

An item looks like this:

```json
{
  "code": "CO-1109-02",
  "date": "2026-11-09",
  "category": "Sets",
  "title": "Embroidered lantern-sleeve set",
  "note": "Embroidered lantern-sleeve shirt + wide-leg trousers set. Colours: black, burgundy brown",
  "image": "photos/2026-11-09/CO-1109-02-01.webp",
  "images": [
    "photos/2026-11-09/CO-1109-02-01.webp",
    "photos/2026-11-09/CO-1109-02-02.webp"
  ],
  "source": "B-1.jpg"
}
```

Categories are Dresses, Jumpsuits, Tops, Shirts, Skirts, Sets, Trousers, Workwear, Shoes, Bags, and Other. Filter chips only show categories that have looks. Empty ones stay in `data/config.json` and appear when a piece is added.

## WhatsApp and Instagram

`data/config.json` holds the WhatsApp number `8613602437622`. **Ask on WhatsApp** opens `https://wa.me/8613602437622` with a message that already includes the item code and title. The header button uses `whatsappGeneral` and does not attach a code.

Instagram stays hidden while `showInstagram` is `false` or `instagram` is empty. To show it, set both:

```json
"instagram": "cocos.shop",
"showInstagram": true
```

A handle or a full profile URL both work.

## GitHub Pages

Pages is set to deploy from the **main** branch, folder **/ (root)**.

- Site: [https://fanzhaoqing852g7-droid.github.io/cocos-shop/](https://fanzhaoqing852g7-droid.github.io/cocos-shop/)
- Settings: [https://github.com/fanzhaoqing852g7-droid/cocos-shop/settings/pages](https://github.com/fanzhaoqing852g7-droid/cocos-shop/settings/pages)

`.nojekyll` is in the repo so Pages serves the files as they are. Paths in the page are relative, which is what a project site on `github.io` needs.

To turn that source on again:

```bash
gh api --method PUT repos/fanzhaoqing852g7-droid/cocos-shop/pages \
  --input - <<'EOF'
{"build_type":"legacy","source":{"branch":"main","path":"/"}}
EOF
```

The first build after a push can take a minute. Reload the site URL if it still shows the previous day.
