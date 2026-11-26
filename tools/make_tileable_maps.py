#!/usr/bin/env python3
"""Make desert/volcano/frost/jungle map PNGs seam-friendly under SKYJINN's
mirror tiling (tileRow flips odd tiles). Does not touch Sky Bridge.

Usage:
  python3 tools/make_tileable_maps.py [desert|volcano|frost|jungle|all]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
MAP_DIR = ROOT / "art/maps/v2"
PREV = Path("/workspace/skyjinn-previews")
if not PREV.exists():
    PREV = ROOT.parent / "skyjinn-previews"
    PREV.mkdir(parents=True, exist_ok=True)
TEX = Path("/tmp/map_tex")
WORK = Path("/tmp/map_work")
PREV.mkdir(parents=True, exist_ok=True)
WORK.mkdir(parents=True, exist_ok=True)

MAPART = {"desert": 726, "volcano": 656, "frost": 658, "jungle": 656}
BAND = 8  # MAE window, matches the audit

# Per-map backdrop edge treatment: (solid_replace_px, fade_px)
# solid region is fully replaced by a calm inward slice so cut-off landmarks
# don't ghost; fade blends back to the original painting.
BG_EDGE = {
    "desert": {"left": (360, 70), "right": (230, 60)},
    "volcano": {"left": (200, 36), "right": (200, 50)},
    "frost": {"left": (230, 70), "right": (220, 70)},
    "jungle": {"left": (400, 50), "right": (400, 50)},
}
QUIET = 28  # narrow flatten only; wide blur smeared skies

# Ground textures (Poly Haven CC0 1K diffuses)
GROUND_TEX = {
    "desert": "cracked_red_ground_diff_1k.jpg",
    "volcano": "volcanic_rock_tiles_diff_1k.jpg",
    "frost": "snow_floor_diff_1k.jpg",
    "jungle": "grass_ground_diff_1k.jpg",
}
GROUND_TEX2 = {
    "desert": "mud_cracked_dry_03_diff_1k.jpg",
    "volcano": "burned_ground_01_diff_1k.jpg",
    "frost": "snow_02_diff_1k.jpg",
    "jungle": "forest_floor_diff_1k.jpg",
}
GLOW = {"desert": None, "volcano": "lava", "frost": "ice", "jungle": "grass"}


def mirror_mae(arr, band=BAND):
    a = arr.astype(np.float64)
    L, R = a[:, :band], a[:, -band:]
    return float(np.abs(L - L[:, ::-1]).mean()), float(np.abs(R - R[:, ::-1]).mean())


def tile_mirror(arr, n=3):
    return np.concatenate([arr if i % 2 == 0 else arr[:, ::-1] for i in range(n)], axis=1)


def save_tiled(bg, g, path, scale=0.45, marks=True):
    full = np.concatenate([tile_mirror(bg, 3), tile_mirror(g, 3)], axis=0)
    im = Image.fromarray(full)
    W, H = im.size
    im = im.resize((max(1, int(W * scale)), max(1, int(H * scale))), Image.Resampling.LANCZOS)
    if marks:
        d = ImageDraw.Draw(im)
        tw = int(bg.shape[1] * scale)
        hz = int(bg.shape[0] * scale)
        for i in (1, 2):
            d.line([(i * tw, 0), (i * tw, im.height)], fill=(255, 0, 80), width=2)
        d.line([(0, hz), (im.width, hz)], fill=(0, 255, 180), width=1)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    im.save(path)
    return path


def save_seams(bg, g, path):
    tiled = np.concatenate([tile_mirror(bg, 3), tile_mirror(g, 3)], 0)
    tw = bg.shape[1]
    crops = [tiled[:, max(0, sx - 90) : sx + 90] for sx in (tw, 2 * tw)]
    Image.fromarray(np.concatenate(crops, axis=1)).save(path)


def match_rows(src, ref):
    """Match each row's mean/std in src to the corresponding row of ref."""
    s = src.astype(np.float32)
    r = ref.astype(np.float32)
    out = np.empty_like(s)
    for y in range(s.shape[0]):
        for c in range(3):
            sm, ss = float(s[y, :, c].mean()), float(s[y, :, c].std()) + 1e-5
            rm, rs = float(r[y, :, c].mean()), float(r[y, :, c].std()) + 1e-5
            # keep some of the source contrast so it doesn't go flat
            rs = 0.65 * rs + 0.35 * ss
            out[y, :, c] = (s[y, :, c] - sm) / ss * rs + rm
    return np.clip(out, 0, 255)


def calmest_x(img, width, x0, x1, edge_side="left", edge_band=48):
    """Window whose *outer* columns (the ones that become the map edge) are calmest."""
    gray = cv2.cvtColor(img.astype(np.uint8), cv2.COLOR_RGB2GRAY).astype(np.float32)
    gx = np.abs(np.diff(gray, axis=1, prepend=gray[:, :1]))
    col = gx.mean(axis=0)
    csum = np.cumsum(np.concatenate([[0], col]))
    best, best_e = x0, 1e18
    x1 = min(x1, img.shape[1])
    if x1 - x0 < width:
        return x0
    eb = min(edge_band, width // 3)
    for x in range(x0, x1 - width + 1, 2):
        if edge_side == "left":
            e = (csum[x + eb] - csum[x]) * 3.0 + (csum[x + width] - csum[x]) * 0.35
        else:
            e = (csum[x + width] - csum[x + width - eb]) * 3.0 + (csum[x + width] - csum[x]) * 0.35
        if e < best_e:
            best, best_e = x, e
    return best


def replace_edge(bg, side, solid, fade):
    """Cover cut-off edge landmarks with a calm inward slice, then fade back."""
    h, w, _ = bg.shape
    out = bg.astype(np.float32).copy()
    total = int(solid + fade)
    total = min(total, w // 3)
    solid = min(int(solid), total)
    fade = total - solid
    # Search for a calm source just past the treated zone, not too far (lighting).
    if side == "left":
        search0, search1 = total, min(w - total, total + 520)
        sx = calmest_x(out, total, search0, search1, edge_side="left")
        src = out[:, sx : sx + total].copy()
        # Match lighting to the band just inward of the treated zone, not the landmark.
        ref = out[:, total : min(w, total + 120)]
        src = match_rows(src, ref)
        xs = np.arange(total, dtype=np.float32)
        alpha = np.ones(total, np.float32)
        if fade > 0:
            t = np.clip((xs - solid) / fade, 0, 1)
            alpha = 1 - (t * t * (3 - 2 * t))
        # Also a 8px vertical? no
        a = alpha[None, :, None]
        out[:, :total] = a * src + (1 - a) * out[:, :total]
    else:
        search1, search0 = w - total, max(total, w - total - 520)
        sx = calmest_x(out, total, search0, search1, edge_side="right")
        src = out[:, sx : sx + total].copy()
        src = match_rows(src, out[:, max(0, w - total - 80) : w - total + 10 if w - total + 10 > 0 else w])
        xs = np.arange(total, dtype=np.float32)
        alpha = np.ones(total, np.float32)
        if fade > 0:
            # alpha=1 at the outer edge (right), 0 at inner (left of zone)
            t = np.clip((total - 1 - xs) / fade if fade else 1, 0, 1)  # 1 at right, ...
            # wait: xs=0 is the INNER side of the right zone, xs=total-1 is the outer edge
            # We want alpha=0 at xs=0 (inner, keep original) if we use fade on the inner side...
            # solid is the outer part: xs in [total-solid, total) should be alpha=1
            # fade is the inner part: xs in [0, fade) blends
            t = np.clip(xs / fade, 0, 1) if fade else np.ones(total)
            t = t * t * (3 - 2 * t)
            alpha = np.where(xs >= fade, 1.0, t)
        a = alpha[None, :, None]
        sl = out[:, w - total :]
        out[:, w - total :] = a * src + (1 - a) * sl
    return out


def quiet_mirror_edge(img, B=QUIET):
    """Flatten horizontal gradients at both edges so a mirror join is C1-ish.

    Keep the blur local. A wide horizontal blur turns skies into bands.
    """
    h, w, _ = img.shape
    B = min(int(B), w // 4)
    out = img.astype(np.float32).copy()
    pad = B + 4
    padded = cv2.copyMakeBorder(out, 0, 0, pad, pad, cv2.BORDER_REFLECT)
    blur = cv2.GaussianBlur(padded, (0, 0), sigmaX=max(4, B * 0.22), sigmaY=0.6)
    blur = blur[:, pad : pad + w]
    for side, sl in (("left", slice(0, B)), ("right", slice(w - B, w))):
        xs = np.arange(B, dtype=np.float32)
        if side == "left":
            t = xs / max(B - 1, 1)
        else:
            t = (B - 1 - xs) / max(B - 1, 1)
        t = t * t * (3 - 2 * t)
        a = t[None, :, None]
        out[:, sl] = (1 - a) * blur[:, sl] + a * out[:, sl]
    out[:, 0] = 0.5 * out[:, 0] + 0.5 * out[:, 1]
    out[:, -1] = 0.5 * out[:, -1] + 0.5 * out[:, -2]
    return np.clip(out, 0, 255)


def fade_hotspots_near_edges(img, margin=400):
    """Turn a hard sun disk near an edge into a soft glow (mirrors cleanly)."""
    h, w, _ = img.shape
    out = img.astype(np.float32).copy()
    v = cv2.cvtColor(img.astype(np.uint8), cv2.COLOR_RGB2HSV)[:, :, 2]
    blur_v = cv2.GaussianBlur(v, (0, 0), 6)
    region = blur_v.copy()
    region[int(h * 0.58) :, :] = 0
    mx = int(region.max())
    if mx < 220:
        return out
    ys, xs = np.where(region >= mx - 6)
    if len(xs) == 0:
        return out
    cy, cx = int(np.median(ys)), int(np.median(xs))
    if not (cx < margin or cx > w - margin):
        return out
    # Soft radial blend toward a strongly blurred local sky
    soft = cv2.GaussianBlur(out, (0, 0), 18)
    yy, xx = np.ogrid[:h, :w]
    dist = np.sqrt((yy - cy) ** 2 + (xx - cx) ** 2)
    rad = 70.0
    m = np.clip(1.0 - dist / rad, 0, 1).astype(np.float32)
    m = (m * m * (3 - 2 * m))[..., None]
    out = (1 - m) * out + m * soft
    return out


def clear_mid_structures(img, side, width=150, y0_frac=0.38):
    """In the mid/near band, replace leftover edge ruins with inward dunes/rock."""
    h, w, _ = img.shape
    out = img.astype(np.float32).copy()
    width = min(int(width), w // 4)
    y0, y1 = int(h * y0_frac), h  # skip high sky unless y0_frac=0
    band_h = y1 - y0
    if side == "left":
        src_x = min(w - width, width + 20)
        src = out[y0:y1, src_x : src_x + width]
        # prefer a calmer inward mid-band window
        sx = calmest_x(out[y0:y1], width, width, min(w - width, width + 500), edge_side="left")
        src = out[y0:y1, sx : sx + width]
        src = match_rows(src, out[y0:y1, width : min(w, width + 100)])
        xs = np.arange(width, dtype=np.float32)
        # almost full replace in the first 55%, then fade
        cut = int(width * 0.55)
        t = np.clip((xs - cut) / max(width - cut, 1), 0, 1)
        alpha = 1 - (t * t * (3 - 2 * t))
        a = alpha[None, :, None]
        out[y0:y1, :width] = a * src + (1 - a) * out[y0:y1, :width]
    else:
        sx = calmest_x(out[y0:y1], width, max(0, w - width - 500), w - width, edge_side="right")
        src = out[y0:y1, sx : sx + width]
        src = match_rows(src, out[y0:y1, max(0, w - width - 100) : w - width])
        xs = np.arange(width, dtype=np.float32)
        cut = int(width * 0.45)
        t = np.clip(xs / max(cut, 1), 0, 1)
        t = t * t * (3 - 2 * t)
        alpha = np.where(xs >= cut, 1.0, t)
        a = alpha[None, :, None]
        sl = out[y0:y1, w - width :]
        out[y0:y1, w - width :] = a * src + (1 - a) * sl
    return out


def load_tex(name):
    p = TEX / name
    if not p.exists():
        return None
    return np.array(Image.open(p).convert("RGB"))


def perspective_tile(tex, w, h, scale_top=1.4, scale_bot=2.6, v_repeat=0.85):
    th, tw = tex.shape[:2]
    yy, xx = np.indices((h, w), dtype=np.float32)
    scale = scale_top + (scale_bot - scale_top) * (yy / max(h - 1, 1))
    map_x = (xx * scale) % tw
    map_y = (yy * (th * v_repeat) / max(h, 1)) % th
    return cv2.remap(tex, map_x, map_y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)


def glow_mask(img, kind):
    rgb = img.astype(np.float32)
    r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
    if kind == "lava":
        m = np.clip((r - b) / 90.0, 0, 1) * np.clip((r - 70) / 140.0, 0, 1)
    elif kind == "ice":
        m = np.clip((b - r) / 70.0, 0, 1) * np.clip((b - 60) / 140.0, 0, 1)
    elif kind == "grass":
        # keep painted grass tufts (greener than dirt)
        m = np.clip((g - np.maximum(r, b)) / 40.0, 0, 1)
    else:
        m = np.zeros(r.shape, np.float32)
    m = cv2.GaussianBlur(m, (0, 0), 1.2)
    return m[..., None]


def edge_alpha(w, edge=280, mid=0.18, edge_w=1.0):
    xs = np.arange(w, dtype=np.float32)
    d = np.minimum(xs, w - 1 - xs)
    t = np.clip(d / edge, 0, 1)
    t = t * t * (3 - 2 * t)
    return (edge_w + (mid - edge_w) * t)[None, :, None]


def stylize_tex(tex, strength=0.35):
    """Slightly paint-ify a photo texture: mild bilateral + soft contrast."""
    t = tex.astype(np.uint8)
    sm = cv2.bilateralFilter(t, d=7, sigmaColor=28, sigmaSpace=7)
    out = (1 - strength) * t.astype(np.float32) + strength * sm.astype(np.float32)
    # a touch of contrast
    mu = out.mean()
    out = (out - mu) * 1.08 + mu
    return np.clip(out, 0, 255)


def process_ground(g, name):
    h, w, _ = g.shape
    orig = g.astype(np.float32)
    t1 = load_tex(GROUND_TEX[name])
    t2 = load_tex(GROUND_TEX2[name])
    if t1 is None and t2 is None:
        # fallback: just quiet edges
        return quiet_mirror_edge(orig, B=96)
    parts = []
    if t1 is not None:
        parts.append(stylize_tex(perspective_tile(t1, w, h, 1.3, 2.4)))
    if t2 is not None:
        parts.append(stylize_tex(perspective_tile(t2, w, h, 1.5, 2.7, v_repeat=0.7)))
    tex = parts[0] if len(parts) == 1 else (0.65 * parts[0] + 0.35 * parts[1])
    tex = match_rows(tex, orig)
    # Soften photographic sharpness toward the painted original (low-freq lighting)
    low = cv2.GaussianBlur(orig, (0, 0), 8)
    tex_low = cv2.GaussianBlur(tex, (0, 0), 8)
    tex = tex - tex_low + low  # keep tex detail, orig lighting
    tex = np.clip(tex, 0, 255)
    a = edge_alpha(w, edge=int(w * 0.28), mid=0.22, edge_w=0.82)
    # Keep a few rows at the horizon closer to the original painting
    row = np.linspace(0.25, 1.0, h, dtype=np.float32)[:, None, None]
    a = a * row
    out = (1 - a) * orig + a * tex
    kind = GLOW[name]
    if kind:
        m = glow_mask(orig, kind)
        out = (1 - m) * out + m * orig
    # Quiet both edges so the texture itself is mirror-friendly at the join
    out = quiet_mirror_edge(out, B=40)
    # Restore a thin horizon band in the *center* so backdrop still meets ground
    protect = min(5, h // 8)
    # edges of horizon still need to be quiet; only restore inner 70%
    x0, x1 = int(w * 0.18), int(w * 0.82)
    out[:protect, x0:x1] = 0.55 * out[:protect, x0:x1] + 0.45 * orig[:protect, x0:x1]
    return np.clip(out, 0, 255)


def fill_top_corners(bg, width=430, height=230):
    """Replace hanging corner foliage with a calm center-sky patch."""
    h, w, _ = bg.shape
    out = bg.astype(np.float32).copy()
    width = min(int(width), w // 3)
    height = min(int(height), h // 2)
    src0 = (w - width) // 2
    src = out[:height, src0 : src0 + width].copy()
    yy = np.arange(height, dtype=np.float32)[:, None]
    # fade out in the bottom 35% of the patch so mountains aren't hard-cut
    vf = np.clip((height - 1 - yy) / max(height * 0.35, 1), 0, 1)
    vf = vf * vf * (3 - 2 * vf)
    for side in ("left", "right"):
        xs = np.arange(width, dtype=np.float32)[None, :]
        if side == "left":
            hf = np.clip((width - 1 - xs) / max(width * 0.28, 1), 0, 1)  # 1 at outer, 0 inner
        else:
            hf = np.clip(xs / max(width * 0.28, 1), 0, 1)
        hf = hf * hf * (3 - 2 * hf)
        a = (vf * hf)[..., None]
        if side == "left":
            dest = out[:height, :width]
            out[:height, :width] = a * src + (1 - a) * dest
        else:
            dest = out[:height, w - width :]
            out[:height, w - width :] = a * src + (1 - a) * dest
    return out


def clear_floating_bones(bg, width=210, y1_frac=0.55):
    """Remove disconnected bone fragments left in the sky near the left edge."""
    h, w, _ = bg.shape
    out = bg.astype(np.float32).copy()
    width = min(int(width), w // 4)
    y1 = int(h * y1_frac)
    src_x = min(w - width, width + 30)
    # prefer a window of sky/rock without beige bones: minimize 'bone' chroma in the top
    src = out[:y1, src_x : src_x + width].copy()
    src = match_rows(src, out[:y1, width : min(w, width + 80)])
    xs = np.arange(width, dtype=np.float32)
    cut = int(width * 0.62)
    t = np.clip((xs - cut) / max(width - cut, 1), 0, 1)
    alpha = 1 - (t * t * (3 - 2 * t))
    yy = np.arange(y1, dtype=np.float32)
    vf = np.clip((y1 - 1 - yy) / max(y1 * 0.25, 1), 0, 1)
    vf = vf * vf * (3 - 2 * vf)
    a = (vf[:, None] * alpha[None, :])[..., None]
    out[:y1, :width] = a * src + (1 - a) * out[:y1, :width]
    return out


def wipe_corner_foliage(bg, width=460, height=260):
    """Inpaint green canopy pixels in the top corners (hanging branches)."""
    h, w, _ = bg.shape
    out = np.clip(bg, 0, 255).astype(np.uint8)
    rgb = out.astype(np.float32)
    r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
    foliage = ((g > r + 10) & (g > b + 6) & (g > 40)).astype(np.uint8) * 255
    mask = np.zeros((h, w), np.uint8)
    mask[:height, :width] = foliage[:height, :width]
    mask[:height, w - width :] = foliage[:height, w - width :]
    if mask.any():
        mask = cv2.dilate(mask, np.ones((9, 9), np.uint8))
        out = cv2.inpaint(out, mask, 6, cv2.INPAINT_TELEA)
    return out.astype(np.float32)


def process_backdrop(bg, name):
    orig = bg.astype(np.float32)
    out = orig.copy()
    out = fade_hotspots_near_edges(out, margin=420 if name == "desert" else 300)
    cfg = BG_EDGE[name]
    out = replace_edge(out, "left", *cfg["left"])
    out = replace_edge(out, "right", *cfg["right"])
    # Second pass: knock down any ruin still hugging the edge in the mid band.
    mid_w = {"desert": 150, "volcano": 110, "frost": 150, "jungle": 90}.get(name, 150)
    y0f = 0.0 if name == "jungle" else 0.38
    out = clear_mid_structures(out, "left", mid_w, y0_frac=y0f)
    out = clear_mid_structures(out, "right", mid_w, y0_frac=y0f)
    out = quiet_mirror_edge(out, B=QUIET)
    if name == "jungle":
        out = fill_top_corners(out, width=440, height=240)
        out = quiet_mirror_edge(out, B=QUIET)
    if name == "volcano":
        out = clear_floating_bones(out, width=220, y1_frac=0.52)
        out = quiet_mirror_edge(out, B=QUIET)
    return np.clip(out, 0, 255)


def process_map(name):
    hz = MAPART[name]
    src = MAP_DIR / f"{name}.png"
    im = np.array(Image.open(src).convert("RGB"))
    assert im.shape[1] == 1672 and im.shape[0] == 941, im.shape
    bg, g = im[:hz], im[hz:]
    before = {
        "backdrop_left": round(mirror_mae(bg)[0], 2),
        "backdrop_right": round(mirror_mae(bg)[1], 2),
        "ground_left": round(mirror_mae(g)[0], 2),
        "ground_right": round(mirror_mae(g)[1], 2),
    }
    bg2 = process_backdrop(bg, name).astype(np.uint8)
    g2 = process_ground(g, name).astype(np.uint8)
    # Re-lock a consistent horizon meeting in the inner region
    # (outer edges stay processed so they stay tileable)
    x0, x1 = int(im.shape[1] * 0.2), int(im.shape[1] * 0.8)
    # average the two sides of hz slightly so they still sit together
    # keep mostly original meeting in the center
    bg2[-2:, x0:x1] = (0.4 * bg2[-2:, x0:x1] + 0.6 * bg[-2:, x0:x1]).astype(np.uint8)
    g2[:2, x0:x1] = (0.4 * g2[:2, x0:x1] + 0.6 * g[:2, x0:x1]).astype(np.uint8)
    after = {
        "backdrop_left": round(mirror_mae(bg2)[0], 2),
        "backdrop_right": round(mirror_mae(bg2)[1], 2),
        "ground_left": round(mirror_mae(g2)[0], 2),
        "ground_right": round(mirror_mae(g2)[1], 2),
    }
    out = np.concatenate([bg2, g2], axis=0)
    out_path = WORK / f"{name}.png"
    Image.fromarray(out).save(out_path)
    save_tiled(bg2, g2, PREV / f"after_{name}_tiled.png")
    save_seams(bg2, g2, PREV / f"after_{name}_seams.png")
    # also a mid-scale full painting (not tiled) for style check
    Image.fromarray(out).resize((836, 470), Image.Resampling.LANCZOS).save(PREV / f"after_{name}_full.png")
    print(name, "BEFORE", before)
    print(name, "AFTER ", after)
    print("  wrote", out_path)
    return {"before": before, "after": after, "path": str(out_path)}


def main(argv):
    names = argv[1:] or ["all"]
    if names == ["all"]:
        names = ["desert", "volcano", "frost", "jungle"]
    report = {}
    for n in names:
        if n not in MAPART:
            print("skip unknown", n)
            continue
        report[n] = process_map(n)
    (PREV / "mae.json").write_text(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    main(sys.argv)
