# SKYJINN

Mobile tug-of-war auto-battler (inspired by Art of War: Red Tides). Fantasy mixed with advanced technology.

## Play
Open `index.html` in a phone browser (landscape). Everything — code, sprites, maps — is embedded in that one file.

## Factions (8)
Djinn · Verdant · Mutants · Magic Knights · Goblins · Undead · Automatons · Dragons

Painted unit art done: Djinn, Verdant, Mutants, Magic Knights, Dragons. Placeholder shapes: Goblins, Undead, Automatons.

## Layout
- `index.html` — the full game
- `art/units/` — cut-out unit sprites (`<unit><tier>.png`) + `meta.json` (height, foot anchor)
- `art/source/` — original art on magenta backgrounds
- `art/bases/` — base tower art per faction
- `art/maps/` — map backgrounds (Desert Ruins, Sky Bridge, Volcanic Wastes)
- `tools/cut.py` — removes the magenta background and trims a sprite
- `tools/embed.py` — re-embeds `art/units` into `index.html` (run from repo root)
