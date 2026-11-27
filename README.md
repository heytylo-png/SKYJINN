# SKYJINN

Mobile tug-of-war auto-battler (inspired by Art of War: Red Tides). Fantasy mixed with advanced technology.

## Play
Open `index.html` in a phone browser. Everything (code, sprites, maps) is embedded in that one file, except the music in `audio/`.

**Landscape only.** In portrait, a full-screen prompt (logo, rotating phone, "Rotate your phone to play") covers the game, and a running match pauses behind it, resuming when the phone is turned back. The first tap on any start-menu button asks the browser for fullscreen and a landscape orientation lock. Where that's unsupported (iOS Safari), the game just continues. The ⛶ button next to music toggles fullscreen.

**Install.** `manifest.json` declares `"display": "fullscreen"` and `"orientation": "landscape"`, with the dark `#140e09` background and icons made from the logo. Together with `sw.js`, "Add to Home screen" launches SKYJINN fullscreen with no browser bar.

**Camera.** Each map shows a vertical slice of the 300-unit world (`VIEW`, set in `setView()`), cropped from the top so the sky and mid layers lose their upper part instead of shrinking.

- **Slice size:** the slice ends just below the lane. It is only as tall as needed for the lane to sit in the bottom 40% and for the towers to clear the top HUD. That works out to about 199 units on Desert Ruins, 206 on Sky Bridge and 231 on Volcanic Wastes.
- **Unit size:** a normal unit is about 16% of battlefield height (14% on Volcanic Wastes).
- **Fliers:** they cruise at 30–47% of the visible slice.

**Unit spacing.**
- Every ground unit spawns at a random depth across the full lane (`GY`) and drifts back to that depth while marching.
- Units close only 35% of the vertical gap to a target, so groups move in loose ranks.
- The separation radius is 40% larger.
- At most 3 ground units can share a 14×8 spot; extras slide toward the emptier lane edge.

**Toasts.** Toasts show in a small strip just above the unit bar for 1.8 s. A wish description appears only the first time that wish is armed in each match.

**Wish effects.** The `wish_fx` sheets play at 10 fps, and each frame crossfades into the next by its fractional time.
- **Timing:** frames 1–4 build up once, frames 5–12 ping-pong for the whole power's duration, and frames 13–16 close it out. The effect fades in over 0.25 s and out over 0.4 s.
- **Layout:** each faction power is 3 copies across its area (left, centre, right). Each copy is 70–100% scale with a 0–0.3 s start offset, and some are mirrored, so one sheet's edges are covered by the next. Every copy draws the full 256×256 cell, bottom-centre on the lane's feet line at the tapped world x, and scrolls with the camera.
- **Draw order:** Sandstorm, Airstrike, Meteor Shower and Divine Judgment draw in front of units. The other powers draw behind them.
- **Damage timing:** a power's damage, zone and summons land when the loop starts (0.4 s after the cast), in sync with the art.
- **Particles:** each power adds particles on top:
  - dust streaks for Sandstorm
  - falling leaves for Overgrowth
  - crimson drops and splashes for Acid Rain
  - spark bursts for EMP
  - embers for Meteor Shower, with a shake of 4 on each impact
  - smoke and shake for Airstrike
  - rising gold sparkles for Divine Judgment, plus a white 0.1 s flash at the peak
  - teal wisps for Plague of Bones
  - teal sparkles on the Shield Dome, which stays a single centred copy

**Airstrike and Meteor Shower** no longer loop their sheets over the area. The bomb and the meteor are cut out of their sheets and fall for real. Each impact plays the sheet's ground explosion once, on landing, which is also when the damage happens.
- **Airstrike:** a Gyrocopter bomber flies in from off-screen just under the HUD. It drops a bomb every 26 world px while over the target, leading for the forward carry. Each bomb arcs down to a random lane depth, then blasts within 30 px.
- **Meteor Shower:** meteors start high above the view, 150 px back, and fly in at 250 px/s. A pulsing orange glow marks each landing spot until the meteor hits.

**Readability.**
- Every unit sprite has a 1px dark outline: a cached silhouette of its sheet, drawn 1 screen px out in four directions.
- The mid and ground map layers are dimmed: Volcanic Wastes ×0.75, Desert Ruins and Sky Bridge ×0.85. The sky is unchanged.
- Buffed units shed 3 small gold sparkles every 0.4 s.
- A unit in Holy Rage gets a pulsing gold team ring; there is no glow shape over the sprite.
- Heal and ability rings are 1.5px wide, start at 60% opacity, expand once and are gone within 0.4 s.
- Team rings under units are 1.0× unit width at 55% opacity.

**Pixel UI kit.** The menus and HUD use the art in `art/ui_kit/`, which `tools/uikit.py` embeds as `UI_KIT`. At startup each piece becomes a `--k-<name>` CSS variable. Frames are drawn with `border-image` 9-slicing at the slice insets from `ui_kit.json`, with corners scaled uniformly to phone size and `image-rendering: pixelated`.

- **Windows:** every overlay sits in a `panel_large` window. Sub-sections use `panel_medium`, and titles sit on `bar_top`.
- **Buttons:** `btn_brass` for normal actions and `btn_teal` for main actions (Play, Next stage, Resume, Fight, Upgrade).
  - When pressed, teal buttons switch to `btn_teal_pressed`. Brass buttons shift their content down 2px, because their pressed art matches the normal art.
  - Disabled buttons use `btn_*_disabled`.
- **Cards:** faction picker, campaign stages and unit cards use `card_normal`.
  - `card_selected` marks the chosen faction, the next stage, and the unit whose info sheet is open.
  - `card_locked` marks locked stages.
  - `card_champion` is the champion card. Its crown is split off by the embed tool so the 9-slice does not stretch it.
- **HUD:** `bar_hp` and `bar_progress` are drawn on the canvas around the base health bars and the wave timer.
  - `badge_teal` shows owned-unit counts. `badge_red` marks warnings: can't afford, and army full.
  - `star_*` icons show stars on campaign stages and the end screen.
  - The icons replace the old top-left buttons and also mark gold, income, settings and Play.
- **Start menu changes:** the difficulty is now picked first (and remembered), then ⚔ PLAY starts the match. A ⚙ settings window toggles sound, music and fullscreen.

**Music.** Real MP3 tracks in `audio/` replace the old procedural loop:
- `music_menu` loops on the start menu and campaign screen.
- `music_desert`, `music_bridge` and `music_volcano` loop in battle on the matching map.
- `sting_victory` or `sting_defeat` plays once on the end screen, after the battle music stops.

One `<audio>` element plays the music (loop, volume 0.5) and crossfades over 1 s when the track changes. Stings play at 0.7 on their own element. Browsers block autoplay, so music starts on the first tap. The 🎵 toggle is saved to localStorage. Music pauses while the tab is hidden and resumes when it comes back. The service worker pre-caches the tracks for offline play. 

**Sound effects.** Sampled SFX from `art/sfx/` (Kenney Impact Sounds, CC0) are embedded as `SFX_DATA` by `tools/sfx.py`. At startup they are decoded into Web Audio buffers. Each play picks a random variant at ±8% playback rate and goes through the SFX gain, so 🔊 mutes them. Per-sound minimum gaps still apply, and off-screen sounds are skipped.
- Melee unit attacks play a `slash` swing, and the impact lands about 0.09 s later.
- Tank and champion melee plays `hit_heavy`.
- Every other hit on a unit sounds like the target's material:
  - `hit_metal`: Knights, Automatons, Goblin vehicles and armored units.
  - `hit_flesh`: Mutants, Dragons and other organic units.
  - `hit_wood`: Verdant and wooden siege.
  - `hit_bone`: Undead.
  - `hit_stone`: Magma Golem and Storm Coil.
  - `hit_light`: swarm units.
- `base_hit`: anything hitting a tower.
- `wave_start`: each wave.
- `buy`: buying a unit or income.
- `upgrade`: unit tier ups and Forge upgrades.
- `ui_click`: menu buttons.
- `ui_nope`: can't afford.

- Projectile launches, by shooter:
  - `zap`: Sparkcaster, Storm Coil, Wraith, Lich, Necromancer casts, and tower shots.
  - `laser`: Drone Swarm, Arc Gunner, Aero Drone.
  - `bolt`: Rail Cannon, Interceptor.
  - `rocket`: Rocket Battery, Warboss and Gyrocopter rockets.
  - Synth `gun`: Goblin rifles, gatlings, flak and the Junk Tank.
  - Other shooters are silent at launch; their impacts still play a sound.
- `explosion`: lobbed and siege impacts, machine deaths, and most champion abilities and wishes.
- `explosion_big`: tower state changes, meteor and airstrike impacts, and champion deaths.
- `bolt`: Sandstorm, Divine Judgment and lightning.
- `emp`: EMP Blast and the Colossus shockwave.
- `shield`: Shield Dome casts and hits on energy shields.
- `splat`: Mutant bile hits, bile lobs and Acid Rain.
- `heal`: every heal tick.

Only the synth `gun`, plus the death and lob-launch thumps, are still synthesized.

## Factions (8)
Djinn · Verdant · Mutants · Magic Knights · Goblins · Undead · Automatons · Dragons

Drawn sprite sheets (idle, walk, attack, death) done for all eight factions. Painted unit art done: Djinn, Verdant, Mutants, Magic Knights, Dragons, Goblins, Undead, Automatons. All eight factions are painted.

## Layout
- `index.html` — the full game
- `art/units/` — cut-out unit sprites (`<unit><tier>.png`) + `meta.json` (height, foot anchor)
- `art/source/` — original art on magenta backgrounds
- `art/wish_fx/` — faction power effect sheets (`tools/wishfx.py`)
- `art/ui/` — menu background, logo, faction emblems, wish icons (`tools/ui.py`)
- `art/projectiles/` — projectile sheets (`tools/projectiles.py`)
- `art/towers/src/` — faction towers, 4 damage states each (`tools/towers.py`)
- `art/bases/` — the earlier single-image base art (used only if a tower sheet is missing)
- `art/maps/layers/` — the battle maps: `<map>_sky/_mid/_ground.png` for Desert Ruins, Sky Bridge and Volcanic Wastes (`tools/maps.py`)
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

**Energy glow and discharge motes** (Automatons; `FIRE_GLOW` and `GLOW_KIND` in `index.html`): the same baked-halo system as the dragon fire, with a cool blue-white halo on bright blue energy pixels (weapon barrels, cores, shields, beams, thrusters). Glowing parts shed very fine discharge motes, more on attack frames (`MOTE_RATE`, `MOTE_ATK`). Motes drift with a slow random jitter, flicker, and fade like radiation. Beam hits (`MOTE_HIT`: Drone Swarm, Aero Drone, Arc Gunner, Interceptor, Rail Cannon) release a burst of motes in the beam's colour mixed with pale cyan. The Rail Cannon also leaves a charged trail of motes along the whole beam line. Automaton deaths release a mote cloud on top of the explosion.

**Soulfire glow and souls** (Undead): the glow system's third kind, `soul`, puts a teal halo on the drawn soulfire (eyes, flames, ghost trails, spells). Glowing parts shed rising soul motes. When an Undead unit dies, its soul leaves the body and floats away: a small ghost with dark eyes and a wavy tail, swaying as it rises and trailing motes, fading over 2.8 s (`soulRise`, `SOUL_LIFE`, `SOUL_MAX` in `index.html`). Bigger units have bigger souls.

**Magic glow** (Djinn): a fourth glow kind, `magic`, puts a soft cyan halo on the drawn teal magic (orbs, beams, lamp light, Storm Coil lightning), and glowing parts shed fine sparkles.

**Holy glow** (Knights): a fifth glow kind, `holy`, puts a warm gold halo on the brightest pale gold in the art: crowns, halos, blades, bow tips, holy slashes and the trebuchet's fireball. The ordinary gold trim and white robes don't glow. Glowing parts shed rising golden sparkles.

**Field flowers** (Verdant): small pixel flowers (white, yellow, pink, lilac) sprout where Verdant units walk, bloom around the Bloom Shrine when it heals, and spring up where a Verdant unit falls. Each grows a stem, opens its petals, sways, then wilts and fades (`FLOWER_RATE`, `FLOWER_LIFE`, `FLOWER_MAX` in `index.html`).

**Cut-off art** (`tools/declip.py`): some drawn frames have art running into the frame edge (a lance tip, a lightning bolt, a slash, a dust cloud), which ends in a hard straight line, or small pieces of the neighbouring frame spilled across the cell boundary. `python3 tools/declip.py art/sheets/src/<files>.png` fixes both in place. It removes small detached pieces that sit against the edge, then fades art touching the top, left or right edge to transparent over 12 px, only along the stretch of edge it touches. The bottom edge is the ground line and is left alone. Edges the unit's idle pose already reaches (a trebuchet wider than its frame, wings taller than it) are also left alone, so solid parts never fade. Run it once on new sheets before `tools/sheets.py`. Frames with nothing at the edge are untouched.

**Launch angle** (`LAUNCH_ANG` in `index.html`): for units whose drawn missiles leave the launcher at an angle (Interceptor: 30° at tiers 1–2, 20° at tier 3; Bone Ballista: 40°, 35° at tier 3; Skyward Arbalest: 45°, 40° at tier 3), the projectile is drawn on a curve that starts along that angle and bends onto the target. Only the drawing bends, so hits land at the same moment as before.

**Ability-only frames** (`SHEET_SALVO` in `index.html`): an attack frame can be kept for the champion ability instead of playing on every shot. The Warboss Mega-Mech's rocket frame plays only when its 6-second barrage fires, held for 0.5 s (`SALVO_HOLD`); the six rockets launch from just past the drawn missile tips (a point per tier, in frame pixels). Ordinary gatling shots play the first three attack frames.

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

**Depth**: every effect (hit and death effects, blood and debris, sparks, embers and motes, slashes, muzzle bursts and rings) takes the ground depth of the unit it belongs to when it is created, and is drawn right after that unit. A unit standing in front covers it, and nothing shows through a foreground character. Effects on fliers draw with the fliers. Effects that belong to no unit (projectile trails, faction powers) stay on top (`zItems`, `drawZ`, `zInstall` in `index.html`).

**Size**: hit effects are capped at 34 px (0.75× the target's height), death effects at 54 px, and splash explosions at 1.2× the splash radius. Blood and acid sprays fly about half as far with fewer drops, so splatter stays around the unit.

## Battle maps
Desert Ruins, Sky Bridge and Volcanic Wastes are drawn from three layers in `art/maps/layers/`: `<map>_sky.png` (opaque), `<map>_mid.png` and `<map>_ground.png` (transparent). All are 720 px tall and loop seamlessly left to right. `python3 tools/maps.py` embeds them in `index.html` as `MAP_LAYERS`: mid and ground lossless (crisp pixels), sky lossy.

- **Drawing**: each layer is scaled to the canvas height with nearest-neighbour scaling, then tiled across the screen with whole-pixel tile edges (no gaps). The order is sky, mid, ground, then the battle.
- **Parallax**: sky scrolls at 0.05× the camera, mid at 0.45×, ground at 1× (`MAP_PAR`).
- **Lanes** (`gy` in `MAPS`, world px where 300 = canvas height): unit feet stay between the ground layer's walkable line and the bottom 5% of the screen. That is 83–95% for the desert and 74–95% for the volcano. The bridge uses 74–88%: on the planks below the rope rail, ending at the deck's bottom edge, since below that is open sky.
- These three are the only maps. Campaign stages and daily challenges that used the former Frozen Spire and Verdant Falls now use Sky Bridge and Volcanic Wastes.

**Unit size**: the battlefield is 300 world units tall and fills all the height above the unit bar. Units are drawn at `UNIT_SCALE` 1.54 and champions at `CHAMP_SCALE` 1.27 (35% and 30% smaller than the earlier 2.37 and 1.81). A full tower is about 45% of the battlefield height (`TOWER_H` 135). This is visual only: hit boxes, ranges and the balance simulator are unchanged.

**Team marker** (`teamRing`): sprites are drawn plain, with no team-coloured outline or glow.
- **Ground units** stand on a thin flat ring in the team colour (player `#3fe0d0`, enemy `#ff7a3a`): about 1.2× the unit's width and 0.3× as tall, 2 px, 70% opacity, with a soft dark shadow inside.
- **Champions** get a 3 px ring and a small gold diamond at the front.
- **Flyers** get a smaller ring at 40% opacity on the ground below them.
- **Health bars** use the team colour. The white hit flash is unchanged.

**Sky**: the sky layer keeps its aspect ratio and is scaled to the battlefield height. It tiles at a very slow 0.05× parallax, alternating its own tile with a copy that has the moon (Desert Ruins) or sun (Sky Bridge) painted out (`SKY_BODY`, `skyAlt`). The moon stays round, and only one is ever on screen.

**Unit icons** (`iconFrame`, `iconTo` in `index.html`): every unit icon is frame 1 of the idle row of the unit's sheet for its current tier, trimmed to its opaque pixels, then centred and scaled to the icon box with nearest-neighbour scaling. That covers the unit cards, the hold sheet, and the last-wave rows. Trimmed frames are cached per sheet and side, so each is built once; enemy icons face left. When a unit is upgraded or ascends, its card and open sheet switch to the new tier's frame. The old hand-drawn vector unit art has been removed.

**Last wave**: the units each side sent last wave are shown on a small dark strip directly under that side's HP bar, scaled to fit its width, so they never cover a tower.

## UI art
`art/ui/` holds the menu art; `python3 tools/ui.py` embeds it as `UI_ART`.
- **Start menu background**: `title_bg.png`, cover-fit, under a 40% black overlay.
- **Logo**: `logo.png` replaces the text title. It is at most 80% of the screen width, keeps its aspect ratio, is capped in height so the whole menu fits without scrolling, and floats 3 px up and down.
- **Faction emblems** (`emblem_<faction>.png`): shown on the faction picker buttons, on the Campaign stage cards (the opponent's emblem), and beside each side's label in the AI vs AI HUD.
- **Wish buttons**: the Wish button shows `wish_<faction>.png` for the player's faction, and the Shield button shows `wish_shield.png`. Icons are greyed and dim while charging, and turn full colour with a pulse when ready.

## Projectiles
Drawn projectiles come from `art/projectiles/proj_<sheet>.png`: four 256×256 sheets, each a 4×4 grid of 64×64 cells. Each row is one projectile with 4 looping frames, all pointing right. `python3 tools/projectiles.py` embeds them as `PROJ_DATA`.

| Sheet | Row 1 | Row 2 | Row 3 | Row 4 |
|---|---|---|---|---|
| `physical` | wooden arrow (Bone Archer T1–2) | gold rune arrow (Runebow Archer, Skyward Arbalest) | ghost arrow (Bone Archer T3, Bone Ballista) | chained harpoon (Harpoon Crew) |
| `magic` | fireball (Firecaller, Wyvern, Ancient Wyrm) | spirit bolt (Sparkcaster, Storm Coil, Skyskiff, Wraith, Lich King) | plasma (Arc Gunner, Aero Drone, Drone Swarm, Interceptor, Rail Cannon) | holy orb (Sun Trebuchet T2–3, Knight tower shots) |
| `siege` | boulder (Corpse Catapult, Sun Trebuchet T1) | lava rock (Magma Golem) | rune shell (Rune Mortar) | rocket (Rocket Battery, Gyrocopter, Warboss barrage) |
| `organic` | bile glob (Acid Spitter, Gore Wing, Bile Cannon) | bone spine (Spine Hurler) | sap blob (Sap Gunner) | seed pod (Grove Catapult) |

- **Animation and rotation**: frames loop at 12 fps (`PROJ_FPS`). Each projectile is rotated to its flight angle. Lobbed shots follow the arc, and bent shots (Interceptor, Bone Ballista, Skyward Arbalest) follow the bend. A shot flying left is flipped so it stays right side up.
- **Size and blending**: drawn at half the unit sprite scale (`PROJ_SCALE`), with the head on the target. The magic sheet is drawn additively.
- **Unchanged**: Goblin guns (Grunt Squad, Sniper, Flak Truck, Junk Tank, the Warboss's gatling) keep their tracer lines. Vine Lasher, Mothwing and Gryphon Rider shots keep their drawn shapes.
- **Mapping**: `PROJ_SPR` in `index.html` maps each unit to its sheet and row.

## Faction power effects
`art/wish_fx/wish_fx_<name>.png`: 1024×1024, a 4×4 grid of 256×256 frames read left to right, top to bottom. `python3 tools/wishfx.py` embeds them as `WFX_DATA`, along with each sheet's drawn width and base line measured from its loop frames.

- **Playback** (12 fps): frames 1–4 build up once, frames 5–12 loop while the power is active (at least one full loop, so short powers still read), and frames 13–16 fade out once after it ends.
- **Placement**: each effect is drawn bottom-centre at the target on the ground, scaled so its drawn width matches the power's area. Effects draw over ground units and under fliers.
- **Blending**: additive for `emp` and `divine_judgment`, normal for the rest.

| Sheet | Power | Notes |
|---|---|---|
| `sandstorm` | Djinn Sandstorm | moves forward with the storm |
| `overgrowth` | Verdant Overgrowth | 3 copies side by side, offset in time and mirrored |
| `acid_rain` | Mutant Acid Rain | |
| `emp` | Automaton EMP Blast | |
| `airstrike` | Goblin Airstrike | the sheet draws the bombs and blasts; damage is unchanged |
| `divine_judgment` | Knight Divine Judgment | |
| `shield_dome` | Shield Dome (all factions) | a 20% teal ellipse on the ground behind units |
| `meteor_shower` | Dragon Meteor Shower | the sheet draws the meteors and impacts; the meteors still hit as before |
| `plague_of_bones` | Undead Plague of Bones | the 6 skeletons rise one by one during the loop frames |

Every faction power keeps its short screen flash; the old vector drawings, runes and rings are no longer drawn.

## Faction towers
Each side's Sky Anchor is drawn from `art/towers/src/tower_<faction>.png` (512×512, a 2×2 grid of 256×256 states, base bottom-centre). `python3 tools/towers.py` measures each state's base line and the top of the structure (ignoring the painted smoke), then embeds them in `index.html` as `TOWER_DATA`.

- **State by base HP**: top-left above 66%, top-right 33–66%, bottom-left 1–33%, bottom-right at 0 (destroyed).
- **Breaking**: when a tower drops to a worse state, three `debris` bursts (`fx_explosions` row 2) play over it, and the tower and screen shake briefly (`towerBreak`).
- **Drawing**: the enemy tower is mirrored. All towers share one scale (`TOWER_H`, 138 world px for full-height art), so they keep their drawn proportions.
- **Shots**: the tower's shot starts just below the top of its current state's art (`towerShotY`).
- **End screen**: shows both towers in their final state, so the loser's is rubble.

## Match end
A match lasts 6 minutes. The last minute is overtime (`OVERTIME` in `index.html`): the home-defence bonus is off and bases take double damage. If both bases still have the same HP at the time limit, the side whose front line has pushed further wins, then the side with more kills; only then is it a draw. A campaign win decided this way earns 1 star.
