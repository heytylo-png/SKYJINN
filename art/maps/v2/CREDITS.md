# Map texture credits

The four scrolling maps (`desert.png`, `volcano.png`, `frost.png`, `jungle.png`) were edited so their backdrop and ground strips join cleanly under the game's **mirror** tiling (`tileRow` in `index.html` flips every other tile). The original painted compositions were kept; CC0 photo textures were color-matched and blended mainly into the ground strips (stronger at the edges) so the joins don't smear.

Sky Bridge (`bridge.png`) was not changed.

All textures below are from [Poly Haven](https://polyhaven.com/) and are released under [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/) (free for any use, including commercial, with no attribution required). Listed here for provenance.

| File used | Asset | URL | License |
|---|---|---|---|
| Desert ground (primary) | cracked_red_ground | https://polyhaven.com/a/cracked_red_ground | CC0 1.0 |
| Desert ground (blend) | mud_cracked_dry_03 | https://polyhaven.com/a/mud_cracked_dry_03 | CC0 1.0 |
| Volcano ground (primary) | volcanic_rock_tiles | https://polyhaven.com/a/volcanic_rock_tiles | CC0 1.0 |
| Volcano ground (blend) | burned_ground_01 | https://polyhaven.com/a/burned_ground_01 | CC0 1.0 |
| Frost ground (primary) | snow_floor | https://polyhaven.com/a/snow_floor | CC0 1.0 |
| Frost ground (blend) | snow_02 | https://polyhaven.com/a/snow_02 | CC0 1.0 |
| Jungle ground (primary) | grass_ground | https://polyhaven.com/a/grass_ground | CC0 1.0 |
| Jungle ground (blend) | forest_floor | https://polyhaven.com/a/forest_floor | CC0 1.0 |

Downloads were the 1K JPEG diffuse maps from Poly Haven's public CDN (`*_diff_1k.jpg`).

The backdrop strips were made seam-friendly by inward-cloning calmer slices over cut-off edge landmarks (arches, columns, ribs, framing trees) and a narrow edge flatten so a mirrored join is smooth. Horizon rows (`desert` 726, `volcano` 656, `frost` 658, `jungle` 656) were left at the same image rows so `MAPART` does not need to change.
