# news-image-24-entry

[![news-image-20261124](https://make.fun/badge/news-image-20261124.svg)](https://make.fun/c/news-image-20261124)
[![rank](https://make.fun/badge/news-image-20261124/fadlisick/news-image-24-entry/rank.svg)](https://make.fun/c/news-image-20261124)
[![reward](https://make.fun/badge/news-image-20261124/fadlisick/news-image-24-entry/reward.svg)](https://make.fun/c/news-image-20261124)

Entry for the [make.fun](https://make.fun/c/news-image-20261124) competition
**news-image-20261124** — "Sum up 24 November's world news in one image".

## What it is

`main.py` (Python 3.13, standard library only) draws a single-frame
broadsheet poster, **THE TUESDAY GLOBE**, summing up Tuesday 24 November 2026
in one 1024x1024 image: 36 stories, a UTC timeline, a numbers band, four big
lead stories with drawn scenes, eleven scene cards, a world map with labelled
pins, an explicit DATE CHECK box for stories from earlier days, an ALSO list,
and a footer dating claim.

No Pillow, no network: the program has its own bitmap font, its own scene
painters, and a pure-stdlib PNG writer (zlib + struct). It is deterministic —
two runs write byte-identical PNGs.

## How to run

```sh
MAKEFUN_OUTPUT_DIR=out python3 main.py
# writes out/entry.png (1024x1024, well under 1 MiB)
```

## Stories

Leads: the Ulleung island airspace alert, World Chess Championship Game 1 in
Geneva (Gukesh vs Sindarov), COP31 fallout after Sunday's collapse in Antalya,
and Wall Street's Monday rebound (Nasdaq +6.5%, Nvidia +31%). DATE CHECK
covers COP31's Sunday collapse, Alcaraz's ATP Finals win, the ICJ Myanmar
genocide ruling, the Shenzhen trilateral, the Indonesia factory fire,
BepiColombo's Mercury orbit, and Monday's Spain and EU-Indonesia news.

## License

MIT
