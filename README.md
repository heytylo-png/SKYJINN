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

## Unit sprite sheets
Drawn idle, walk, attack and death animation for any unit. When a unit has a sheet for its tier (or a lower tier), the game plays it instead of the single sprite, region warps and champion poses. Combat effects (slashes, muzzle bursts, dust) still apply.

**Making a sheet**
- One PNG per unit per tier, named `<faction>_<unit>_t<tier>.png`, e.g. `mutant_leaper_t1.png` or `knight_grand_paladin_t1.png`. The unit part can be the full name with underscores, one distinctive word, or the 3-letter key (`lep`). Faction can be singular or plural (`mutant`, `mutants`, `auto`, `automatons`).
- 4 rows × 4 columns on solid magenta. Row 1 idle, row 2 walk, row 3 attack (the hit lands on frame 2), row 4 death. Frames read left to right. Flying units: hover idle, fly, attack, death fall.
- Every frame faces right; the enemy side is mirrored in code.
- Frames don't need to be evenly spaced: each sprite is assigned to a cell by where its centre falls, then trimmed.
- **Already-cleaned sheets** (transparent background, 4 rows of equal square frames with feet bottom-centre, e.g. 512×512 with 128×128 frames) are kept as they are. A row can have more frames than the others (e.g. an 8-frame walk on a 1024×512 sheet): each row's frame count is read from the sheet, counting from the left up to the first empty cell. The tool only measures them: idle height (the game scales the unit to its usual on-screen height), baseline, and any projectile or slash drawn into the attack row.
- If an attack frame draws its own projectile or slash, that frame becomes the hit frame. The game's projectile then launches from the drawn glob, and the game's own muzzle burst, spell charge-up and melee slash are skipped for that unit so nothing doubles up. Damage still travels with the game's projectile. Where auto-detection misses or misplaces a drawn effect, set its position by hand in `art/sheets/src/effects.json` (frame pixels on the hit frame, or `null` for none). To also fix a wrongly picked hit frame, use `{"mz": [x, y], "hit": 2}` (0-based frame index).

**Adding sheets**
1. Put them in `art/sheets/src/`.
2. `python3 tools/sheets.py` (for magenta sheets) keys out the magenta, trims each frame, scales the whole sheet by one factor so the unit never changes size, and normalizes to 64×64 frames (128×128 for champions), bottom-centre aligned with the feet on one baseline. Output: `art/sheets/out/<key><tier>.png` and `sheets.json`. It prints a warning if a row doesn't have 4 frames.
3. `python3 tools/embed_sheets.py` embeds them into `index.html` as `SPR_SHEET` (lossy WebP).
4. Check them with `index.html#anim=lep;s=atk` (states `idle`, `move`, `atk`, `die`), then bump `VERSION` in `sw.js`.

**Fire glow and embers** (`FIRE_GLOW` in `index.html`, Dragons): bright fire pixels in each frame (flames, breath, fireballs, lava) get a soft orange halo baked into the frames once at match start, and small embers drift up from them, more on attack frames. Fire projectiles trail embers, fire impacts and meteors burst into them, and burning units shed them. Tunables: `FIRE_GLOW_ALPHA`, `FIRE_EMBER_RATE`, `FIRE_EMBER_ATK`.

**Shell casings** (`SHELL` in `index.html`): gun units throw spent brass out behind the gun each time they fire. Casings tumble, bounce, lie on the ground (fliers' casings fall to the ground below them), then fade after 3.5 s; at most 140 at once. Each entry is `[casings per shot, size]` with size 0 small, 1 rifle, 2 cannon. Currently: Grunt Squad, Sniper, Dirt Bike Raider, Gyrocopter, Flak Truck, Junk Tank and Warboss Mega-Mech.

**Tier 3** units drawn with their own tier-3 sheet are drawn 15% bigger to show off the tier-3 glow (`SHEET_TIER_SCALE` in `index.html`); the health bar and projectile launch point scale with them.

**Playback** (`SHEET_FPS` and `SHEET_HIT` in `index.html`): idle 4 fps loop, walk 8 fps loop, attack 10 fps timed so the hit frame shows at the moment of the hit (frame 2 by default; for cleaned sheets, the frame with the drawn effect or the furthest reach), death 8 fps then holds the last frame while it fades.

## Hit effects and ground decals
Drawn effect sheets live in `art/fx/src/` (4×4 on magenta). `python3 tools/fx.py` keys out the magenta (translucent smoke drawn over magenta is un-mixed back to grey), keeps each frame where it was drawn in its cell so a row plays back as drawn, scales each row to fit 112 px, and embeds everything in `index.html` as `FX_DATA` and `DECAL_DATA`.

| Sheet | Rows (top to bottom) |
|---|---|
| `fx_explosions.png` | explosion, debris, fire, smoke |
| `fx_hits_a.png` | Mutant blood, Dragon fire, Undead ghost, Automaton lightning |
| `fx_hits_b.png` | Knight holy, Verdant sap, Djinn sand, Goblin shrapnel |
| `fx_impacts.png` | blood, spark, dust, crystal |
| `decals_ground.png` | 16 stills: blood, scorch, rubble, bile (4 each) |

Row names and blending are set in `SHEETS` in `tools/fx.py`: additive for fire, magic, electric and holy rows, normal for blood, dust, smoke and debris (the explosion's last frame is smoke, so it's drawn normally).

**In the game** (`FX_FPS`, `FX_MAX`, `DECAL_FADE`, `DECAL_MAX` in `index.html`): each effect plays once at 14 fps with its base at the target's feet, then is removed; at most 90 play at once.
- Every hit plays the attacker's faction row on the target, flipped to face away from the attacker. Hits on a shielded unit play `crystal`; base-tower shots play `spark`.
- Siege splash hits and airstrike bombs play `explosion` (fire-type siege plays `fire`), meteors add `smoke`, and each leaves a scorch decal.
- Deaths play an effect and leave a decal by what the unit is made of (`MATERIAL` and `MAT_UNIT`): flesh → blood, Mutants → bile, machines → explosion and rubble, golems → debris and rubble, Undead → ghost and rubble, plants (Verdant) and spirits → their effect, no decal. Fliers leave no decal.
- Decals use a random variant and random horizontal flip, draw beneath units, fade out over 8 s, and at most 40 stay on the ground (oldest removed first).

## Match end
A match lasts 6 minutes. The last minute is overtime (`OVERTIME` in `index.html`): the home-defence bonus is off and bases take double damage. If both bases still have the same HP at the time limit, the side whose front line has pushed further wins, then the side with more kills; only then is it a draw. A campaign win decided this way earns 1 star.
