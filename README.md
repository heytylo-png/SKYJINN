# SKYJINN

Mobile tug-of-war auto-battler (inspired by Art of War: Red Tides). Fantasy mixed with advanced technology.

## Play
Open `index.html` in a phone browser (landscape). Everything — code, sprites, maps — is embedded in that one file.

## Factions (8)
Djinn · Verdant · Mutants · Magic Knights · Goblins · Undead · Automatons · Dragons

Painted unit art done: Djinn, Verdant, Mutants, Magic Knights, Dragons, Goblins, Undead, Automatons. All eight factions are painted.

## Layout
- `index.html` — the full game
- `art/units/` — cut-out unit sprites (`<unit><tier>.png`) + `meta.json` (height, foot anchor)
- `art/source/` — original art on magenta backgrounds
- `art/bases/` — base tower art per faction
- `art/maps/` — map backgrounds (Desert Ruins, Sky Bridge, Volcanic Wastes)
- `tools/cut.py` — removes the magenta background and trims a sprite
- `art/units/anim.json` — per-unit animation regions (wing flaps, flames, tails, cloth, wheels, glows)
- `tools/embed.py` — re-embeds `art/units` (sprites, `meta.json`, `anim.json`) into `index.html` (run from repo root; needs Pillow). Sprites are embedded as lossless WebP

## Animation
Each unit is one painted pose. Motion comes from two layers:
- **Whole-sprite motion** — movement style per unit (`mv` in `meta.json`: `hop` default, `stomp`, `gallop`, `crawl`, `roll`, `float`), attack wind-up and strike, hit knockback, and a death animation.
- **Region warps** — `anim.json` marks parts of a sprite and how they move. The game bakes a 12-frame loop per sprite the first time it appears. The region format is documented above `prepReg` in `index.html`.

To preview, open `index.html#anim`. Options are separated by `;`, e.g. `index.html#anim=wyv,gry;t=2;s=move;z=4` (units, tier, state `idle|move|atk|die`, zoom). After editing `anim.json` or `meta.json`, run `python3 tools/embed.py`.
