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

## Install as an app
`manifest.json`, `sw.js` and `icon-*.png` make the game installable (home-screen icon, fullscreen, works offline) when `index.html` is served from its own web address, e.g. GitHub Pages. The claude.ai artifact can't install because its frame blocks service workers. Bump `VERSION` in `sw.js` whenever `index.html` changes.

## Champion poses
`art/poses/src/` holds the drawn pose strips (idle, walk, attack, death on magenta). `python3 tools/poses.py` cuts them into frames + `art/poses/poses.json`; `python3 tools/embed_poses.py` embeds them in `index.html` as `SPR_POSE`. Champions with poses for a tier use them; other tiers keep their single painted sprite.

## Lane Prototype (`lane-prototype.html`)
A separate, self-contained prototype: one HTML file, no libraries, no image assets. All sprites, the fortresses, the background and the sound are generated in code (Canvas 2D, Web Audio).
- Open `lane-prototype.html` on a phone. It plays in landscape and rotates itself if the phone is locked to portrait.
- Stats for every unit live in the `FACTIONS` table near the top of the file.
- Replace any sprite via the `SPRITES` table (`'knights.melee.0': 'my.png'`; 64x64, facing right, magenta `#FF00FF` = transparent).
- Debug views: `#gallery` (all sprites), `#fps` (frame counter).
- `node tools/lane_balance.js 5` simulates AI-vs-AI matches for every pairing and prints win rates.
- Keyboard (desktop): 1-4 deploy, Q/W/E/R upgrade, A/S/D attack/hold/retreat, Esc pause, M sound.
