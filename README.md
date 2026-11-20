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
- **Combat effects** — drawn in code, no art needed: melee slash arcs, muzzle bursts, spell charge-ups before each cast (units listed in `CAST`), impact sparks and blasts, hit recoil, footstep dust in time with the walk cycle, a shadow that shrinks when a unit leaves the ground, speed lines on divers, and a dust ring when a unit arrives.
- **Faction powers** — each power has a cast flash, a ground rune, its own effect while active (tornado, vines, storm cloud, ground cracks, EMP rings and arcs, meteors, bombers with falling bombs, holy beam) and marks left on the ground. These are visual only: `wishFx`, `drawZone` and `blastFx` in `index.html`.
- **Champion abilities and the shield** — champion specials get matching effects (`champFx`, including fire and acid cones), and the shield is a rising hex dome that ripples where it absorbs a hit.

To preview, open `index.html#anim`. Options are separated by `;`, e.g. `index.html#anim=wyv,gry;t=2;s=move;z=4` (units, tier, state `idle|move|atk|die`, zoom). After editing `anim.json` or `meta.json`, run `python3 tools/embed.py`.

## Install as an app
`manifest.json`, `sw.js` and `icon-*.png` make the game installable (home-screen icon, fullscreen, works offline) when `index.html` is served from its own web address, e.g. GitHub Pages. The claude.ai artifact can't install because its frame blocks service workers. Bump `VERSION` in `sw.js` whenever `index.html` changes.

## Champion poses
`art/poses/src/` holds the drawn pose strips (idle, walk, attack, death on magenta). `python3 tools/poses.py` cuts them into frames + `art/poses/poses.json`; `python3 tools/embed_poses.py` embeds them in `index.html` as `SPR_POSE`. Champions with poses for a tier use them; other tiers keep their single painted sprite.

## Match end
A match lasts 6 minutes. The last minute is overtime (`OVERTIME` in `index.html`): the home-defence bonus is off and bases take double damage. If both bases still have the same HP at the time limit, the side whose front line has pushed further wins, then the side with more kills; only then is it a draw. A campaign win decided this way earns 1 star.
