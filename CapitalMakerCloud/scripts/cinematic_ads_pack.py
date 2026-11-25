#!/usr/bin/env python3
"""
CAPITAL ALPHA — Real Moving Live-Action Commercial Engine (3 Fluid 30fps Videos)
SUPPORTS REAL MOVING LIVE-ACTION HUMAN VIDEO FOOTAGE (NOT stiff zoomed photos!):
  Priority 1: Custom MP4 clips placed in CapitalMakerCloud/assets/videos/
              (ad1_clip1.mp4, ad1_clip2.mp4, ad2_clip1.mp4, ad2_clip2.mp4, ad3_clip1.mp4, ad3_clip2.mp4)
  Priority 2: Automatic free HD vertical live-action human video clips fetched via Pexels Video API
              (add free PEXELS_API_KEY from https://www.pexels.com/api/ to GitHub Secrets!)
  Fallback  : Smooth 30fps handheld dolly & bokeh over photorealistic 35mm stills (if no MP4 & no Pexels key)

All 3 ads explicitly say & display: "Available on Apple iPhone (iOS) & Android" + Paper Simulation FIRST!
"""

from __future__ import annotations

import argparse
import asyncio
import json
import math
import os
import subprocess
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from media_rotator import (
    THEMES_30,
    draw_fluid_ambient_particles,
    fetch_pixabay_photos_for_queries,
    fetch_pixabay_videos_for_queries,
    get_30min_slot,
    get_rotating_voice,
    stitch_live_video_background,
)
from shorts_factory import (
    ASSETS_DIR,
    blend_glass_panel,
    build_fallback_word_timings,
    ease_out_cubic,
    get_audio_duration_seconds,
    group_caption_chunks,
    load_font,
    send_video_to_telegram,
    synthesize_voiceover_with_timings,
)
from signal_broadcaster import normalize_channel_id

OUT_DIR = Path("output/cinematic_ads")
VIDEOS_DIR = ASSETS_DIR / "videos"
CACHE_DIR = OUT_DIR / "stock_cache"
RW, RH = 720, 1280
FPS = 30

ADS_CONFIG: list[dict[str, Any]] = [
    {
        "id": "ad1_glamorous_woman",
        "filename": "ad1_glamorous_woman_capitalmoon.mp4",
        "voice": "en-US-AvaNeural",
        "badge": "CAPITALMOON  •  APPLE iOS & ANDROID",
        "accent": (18, 238, 166),
        "secondary": (255, 206, 72),
        "local_clips": ["ad1_clip1.mp4", "ad1_clip2.mp4"],
        "pexels_queries": [
            "woman smartphone",
            "fashion woman",
            "woman phone",
            "luxury woman",
        ],
        "shots": [
            ("ad1_woman_1.jpg", "dolly_sway_in"),
            ("ad1_woman_2.jpg", "parallax_glide"),
            ("ad1_woman_1.jpg", "cinematic_push_right"),
        ],
        "hook_top": "WHY CHASE CHARTS ALL NIGHT?",
        "hook_big": "LET YOUR PHONE SCAN 24/7.",
        "mid_title": "CAPITALMOON • APPLE iOS & ANDROID",
        "mid_bullets": [
            "• 24/7 Pre-Run Solana Memecoin Spike Radar",
            "• 8-Vector Rug & Honeypot Shield Before Entry",
            "• Online Paper Simulation FIRST ($0 Real Risk)",
        ],
        "cta_big": "AVAILABLE ON APPLE & ANDROID",
        "script": (
            "Why stay glued to stressful charts all night when your phone can watch Solana for you? "
            "Meet CapitalMoon — now available on both Apple iPhone and Android. "
            "It scans live Solana breakouts twenty four seven, runs an eight-vector rug and honeypot shield, "
            "and lets you test automated sleep-trading in live Online Paper Simulation before you ever risk real money. "
            "Zero email, zero KYC, and built-in twenty four seven AI support. "
            "Tap the link in bio to get CapitalMoon free on Apple and Android today. "
            "Crypto carries real risk — always test in paper mode first and do your own research."
        ),
        "caption": (
            "✨ Why watch charts all night? Meet CapitalMoon — NOW available on BOTH Apple iPhone (iOS) & Android! 🍎🤖\n\n"
            "🌙 24/7 Solana Pre-Run Radar & 8-Vector Rug Shield\n"
            "🧪 Online Paper Simulation BEFORE risking real money\n"
            "🔐 Zero Email • Zero KYC • 24/7 AI Support\n\n"
            "🌐 Free Apple & Android Hub: {hub_url}\n"
            "📡 Live Radar: https://{channel_link}\n"
            "(Test in Paper Mode first — DYOR, not financial advice.)"
        ),
    },
    {
        "id": "ad2_busy_worker",
        "filename": "ad2_busy_worker_paper_sim.mp4",
        "voice": "en-US-AndrewNeural",
        "badge": "CAPITALMAKER  •  PAPER SIM FIRST",
        "accent": (16, 206, 255),
        "secondary": (18, 238, 166),
        "local_clips": ["ad2_clip1.mp4", "ad2_clip2.mp4"],
        "pexels_queries": [
            "businessman laptop",
            "man office",
            "office worker",
            "man smartphone",
        ],
        "shots": [
            ("ad2_worker_1.jpg", "dolly_sway_in"),
            ("ad2_worker_2.jpg", "parallax_glide"),
            ("ad2_worker_2.jpg", "cinematic_push_right"),
        ],
        "hook_top": "BUSY AT WORK ALL DAY?",
        "hook_big": "TEST BEFORE RISKING $1.",
        "mid_title": "CAPITALMAKER • APPLE iOS & ANDROID",
        "mid_bullets": [
            "• Live Online Paper Simulation ($0 Money At Risk)",
            "• Native Solana Staking (JitoSOL • jupSOL • mSOL)",
            "• USDC Defense Shield & Empty ATA SOL Rent Reclaim",
        ],
        "cta_big": "APPLE iPHONE & ANDROID FREE",
        "script": (
            "Working nine to five and want to learn Solana investing without stressing over losing hard-earned money? "
            "That is exactly why we built CapitalMaker and CapitalMoon — available on both Apple iPhone and Android. "
            "Start inside live Online Paper Simulation powered by real Solana prices with zero dollars at risk. "
            "Practice liquid staking with JitoSOL, test blue-chip Jupiter swaps, and use the USDC defense shield until you feel confident. "
            "Zero email, zero KYC, and twenty four seven AI support right in your pocket. "
            "Get both apps free for Apple and Android from our link in bio right now. "
            "Investing carries risk — start in paper mode first, not financial advice."
        ),
        "caption": (
            "💼 Busy working all day and worried about risking money blind? Start risk-free first! 🧪\n\n"
            "CapitalMaker & CapitalMoon are FREE on BOTH Apple iPhone (iOS) & Android! 🍎🤖\n"
            "✅ Full Online Paper Simulation using live Solana prices ($0 risk)\n"
            "💎 JitoSOL/jupSOL Staking, USDC Defense Shield & SOL Rent Reclaim\n"
            "🔐 Zero KYC • 24/7 AI Support Built-In\n\n"
            "🌐 Free Apple & Android Hub: {hub_url}\n"
            "📡 Live Radar: https://{channel_link}\n"
            "(Always start in Paper Mode first — DYOR, not financial advice.)"
        ),
    },
    {
        "id": "ad3_young_couple",
        "filename": "ad3_young_couple_capital_alpha.mp4",
        "voice": "en-GB-RyanNeural",
        "badge": "CAPITAL ALPHA  •  iPHONE & ANDROID",
        "accent": (255, 206, 72),
        "secondary": (18, 238, 166),
        "local_clips": ["ad3_clip1.mp4", "ad3_clip2.mp4"],
        "pexels_queries": [
            "happy couple",
            "couple smartphone",
            "couple cafe",
            "young couple",
        ],
        "shots": [
            ("ad3_couple_1.jpg", "dolly_sway_in"),
            ("ad3_couple_2.jpg", "parallax_glide"),
            ("ad3_couple_1.jpg", "cinematic_push_right"),
        ],
        "hook_top": "TWO APPS. ONE SOLANA SUITE.",
        "hook_big": "TRADE SMARTER TOGETHER.",
        "mid_title": "CAPITALMOON + CAPITALMAKER",
        "mid_bullets": [
            "• CapitalMoon: Memecoin Radar & Auto Sleep-Sim",
            "• CapitalMaker: Staking Yield & Quant Rebalance",
            "• 100% Free on BOTH Apple iPhone (iOS) & Android",
        ],
        "cta_big": "GET BOTH ON APPLE & ANDROID",
        "script": (
            "Imagine catching live Solana breakouts with CapitalMoon while growing steady staking yield with CapitalMaker — "
            "both running right on Apple iPhone and Android. "
            "Whether you want fast memecoin pre-run alerts with an eight-vector rug shield, "
            "or calm JitoSOL staking and one-tap SOL rent reclaim, Capital Alpha gives you both tools free. "
            "Test every single strategy in Online Paper Simulation before using real money, "
            "protected by a local PIN vault with zero KYC and twenty four seven AI support. "
            "Available now on Apple and Android — tap our link in bio and join the free Telegram radar today. "
            "Always manage risk and do your own research, not financial advice."
        ),
        "caption": (
            "🚀 Two powerful Solana apps — ONE free suite for BOTH Apple iPhone (iOS) & Android! 🍎🤖\n\n"
            "🌙 CapitalMoon — Live Memecoin Radar, Rug Shield & Auto Sleep-Trader\n"
            "💎 CapitalMaker — JitoSOL/jupSOL Staking Yield & SOL Rent Reclaim\n"
            "🧪 Online Paper Simulation FIRST on both apps!\n\n"
            "🌐 Free Apple & Android Hub: {hub_url}\n"
            "📡 Join Free 24/7 Radar: https://{channel_link}\n"
            "(Test in Paper Mode first — DYOR, not financial advice.)"
        ),
    },
]


def fetch_pexels_live_video_clips(ad: dict[str, Any], api_key: str) -> list[Path]:
    """Downloads up to 3 real moving 1080p vertical live-action MP4 clips from Pexels (free API)."""
    if not api_key.strip():
        return []
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    clips: list[Path] = []
    used_ids: set[int] = set()

    for idx, query in enumerate(ad["pexels_queries"]):
        try:
            url = f"https://api.pexels.com/videos/search?query={urllib.parse.quote(query)}&orientation=portrait&per_page=5"
            req = urllib.request.Request(url, headers={"Authorization": api_key.strip(), "User-Agent": "CapitalAlpha/2.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            videos = data.get("videos") or []
            chosen_url = None
            for v in videos:
                vid_id = int(v.get("id", 0))
                if vid_id in used_ids:
                    continue
                files = v.get("video_files") or []
                # Prefer portrait HD mp4 around 720-1080px wide
                mp4s = [f for f in files if f.get("file_type") == "video/mp4" and f.get("link")]
                mp4s.sort(key=lambda f: abs(int(f.get("width") or 0) - 720))
                if mp4s:
                    used_ids.add(vid_id)
                    chosen_url = mp4s[0]["link"]
                    break
            if chosen_url:
                dst = CACHE_DIR / f"{ad['id']}_pexels_{idx}.mp4"
                dl_req = urllib.request.Request(chosen_url, headers={"User-Agent": "CapitalAlpha/2.0"})
                with urllib.request.urlopen(dl_req, timeout=45) as r_in, dst.open("wb") as f_out:
                    f_out.write(r_in.read())
                if dst.stat().st_size > 50_000:
                    clips.append(dst)
                    print(f"[VIDEO] Downloaded real live-action clip for {ad['id']}: {dst.name}")
        except Exception as exc:
            print(f"[WARN] Pexels clip fetch skipped for '{query}': {exc}")
    return clips


def fetch_pixabay_live_video_clips(ad: dict[str, Any], api_key: str) -> list[Path]:
    """Downloads 3 real moving HD live-action MP4 clips from Pixabay Video API, rotating clips every hour."""
    if not api_key.strip():
        return []
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    clips: list[Path] = []
    used_ids: set[int] = set()
    hour_seed = int(time.time() // 3600)

    for idx, query in enumerate(ad["pexels_queries"]):
        if len(clips) >= 3:
            break
        try:
            q = urllib.parse.quote_plus(query.strip())
            url = f"https://pixabay.com/api/videos/?key={urllib.parse.quote(api_key.strip())}&q={q}&per_page=25&safesearch=true"
            req = urllib.request.Request(url, headers={"User-Agent": "CapitalAlpha/2.0"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            hits = data.get("hits") or []
            print(f"[PIXABAY] Query '{query}' returned {len(hits)} live videos")
            chosen_url = None
            if hits:
                # Rotate starting offset every hour so each hourly video uses fresh new footage!
                start_i = (hour_seed + idx * 3) % len(hits)
                ordered = hits[start_i:] + hits[:start_i]
                for h in ordered:
                    vid_id = int(h.get("id", 0))
                    if vid_id in used_ids:
                        continue
                    vids = h.get("videos") or {}
                    cand = (vids.get("medium") or vids.get("large") or vids.get("small") or {}).get("url")
                    if cand:
                        used_ids.add(vid_id)
                        chosen_url = cand
                        break
            if chosen_url:
                dst = CACHE_DIR / f"{ad['id']}_pixabay_{idx}.mp4"
                dl_req = urllib.request.Request(chosen_url, headers={"User-Agent": "CapitalAlpha/2.0"})
                with urllib.request.urlopen(dl_req, timeout=60) as r_in, dst.open("wb") as f_out:
                    f_out.write(r_in.read())
                if dst.stat().st_size > 50_000:
                    clips.append(dst)
                    print(f"[VIDEO OK] Downloaded real Pixabay MP4 ({dst.stat().st_size} bytes): {dst.name}")
        except Exception as exc:
            print(f"[WARN] Pixabay clip fetch skipped for '{query}': {exc}")
    return clips


def resolve_video_clips(ad: dict[str, Any], pexels_key: str, pixabay_key: str) -> list[Path]:
    """Priority: (1) custom MP4s in assets/videos/, (2) Pixabay API, (3) Pexels API."""
    local = [VIDEOS_DIR / name for name in ad["local_clips"] if (VIDEOS_DIR / name).exists()]
    if local:
        print(f"[VIDEO] Using {len(local)} custom live-action MP4 clips for {ad['id']}!")
        return local
    if pixabay_key.strip():
        pb = fetch_pixabay_live_video_clips(ad, pixabay_key)
        if pb:
            return pb
    return fetch_pexels_live_video_clips(ad, pexels_key)


def build_background_video_track(clips: list[Path], duration: float, out_bg_mp4: Path) -> Path:
    """Stitches real moving MP4 clips into a seamless 720x1280 30fps live-action background track."""
    seg_dur = duration / max(len(clips), 1)
    cmd = ["ffmpeg", "-y"]
    for c in clips:
        cmd += ["-stream_loop", "-1", "-t", f"{seg_dur + 0.4:.2f}", "-i", str(c)]

    filters = []
    for i in range(len(clips)):
        filters.append(
            f"[{i}:v]scale={RW}:{RH}:force_original_aspect_ratio=increase,"
            f"crop={RW}:{RH},fps={FPS},setsar=1,eq=contrast=1.06:saturation=1.08,format=yuv420p[v{i}]"
        )
    concat_in = "".join(f"[v{i}]" for i in range(len(clips)))
    filters.append(f"{concat_in}concat=n={len(clips)}:v=1:a=0,trim=0:{duration:.2f},setpts=PTS-STARTPTS[vout]")

    cmd += [
        "-filter_complex", ";".join(filters),
        "-map", "[vout]", "-an",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
        str(out_bg_mp4),
    ]
    subprocess.run(cmd, check=True)
    return out_bg_mp4


def load_oversized_cinema_still(filename: str, fallback_rgb: tuple[int, int, int]) -> Any:
    from PIL import Image, ImageEnhance, ImageOps  # type: ignore

    tw, th = int(RW * 1.24), int(RH * 1.24)
    for base in (ASSETS_DIR, Path(__file__).resolve().parent / "assets"):
        path = base / filename
        if path.exists():
            img = Image.open(path).convert("RGB")
            return ImageEnhance.Contrast(ImageOps.fit(img, (tw, th), method=Image.Resampling.LANCZOS)).enhance(1.06)
    return Image.new("RGB", (tw, th), fallback_rgb)


def sample_fluid_camera(oversized: Any, progress: float, t: float, mode: str) -> Any:
    from PIL import Image  # type: ignore

    ow, oh = oversized.size
    p = max(0.0, min(1.0, progress))
    ease = p * p * (3.0 - 2.0 * p)
    sway_x = math.sin(t * 1.65) * 7.0 + math.cos(t * 0.85) * 4.0
    sway_y = math.cos(t * 1.35) * 6.0

    if mode == "dolly_sway_in":
        scale = 1.02 + 0.16 * ease
        cw, ch = int(ow / scale), int(oh / scale)
        cx, cy = (ow - cw) * (0.45 + 0.10 * ease) + sway_x, (oh - ch) * (0.38 + 0.06 * ease) + sway_y
    elif mode == "parallax_glide":
        scale = 1.15 - 0.09 * ease
        cw, ch = int(ow / scale), int(oh / scale)
        cx, cy = (ow - cw) * (0.15 + 0.70 * ease) + sway_x, (oh - ch) * (0.44 - 0.08 * ease) + sway_y
    else:
        scale = 1.06 + 0.14 * ease
        cw, ch = int(ow / scale), int(oh / scale)
        cx, cy = (ow - cw) * (0.78 - 0.56 * ease) + sway_x, (oh - ch) * (0.40 + 0.08 * ease) + sway_y

    x0 = max(0, min(ow - cw, int(round(cx))))
    y0 = max(0, min(oh - ch, int(round(cy))))
    return oversized.crop((x0, y0, x0 + cw, y0 + ch)).resize((RW, RH), Image.Resampling.BILINEAR)


def render_overlay_frame(
    bg_rgb: Any,
    vignette: Any,
    ad: dict[str, Any],
    channel_link: str,
    t: float,
    duration: float,
    caption_chunks: list[list[dict[str, Any]]],
) -> bytes:
    from PIL import ImageDraw  # type: ignore

    accent = ad["accent"]
    secondary = ad["secondary"]
    white = (248, 252, 255)
    muted = (204, 218, 236)
    dark = (6, 12, 24)
    pulse = 0.5 + 0.5 * math.sin(t * 7.0)
    s1 = duration * 0.34
    s2 = duration * 0.72

    canvas = bg_rgb.convert("RGBA")
    draw_fluid_ambient_particles(canvas, t, RW, RH, accent, secondary)
    canvas.alpha_composite(vignette)

    active_chunk = None
    is_speaking = False
    for ch in caption_chunks:
        if ch[0]["start"] - 0.10 <= t <= ch[-1]["end"] + 0.22:
            active_chunk = ch
            for w in ch:
                if w["start"] - 0.03 <= t <= w["end"] + 0.05:
                    is_speaking = True
                    break
            break

    d = ImageDraw.Draw(canvas)
    d.rectangle([(0, 0), (RW, 7)], fill=(18, 28, 46, 200))
    d.rectangle([(0, 0), (int(RW * (t / max(duration, 0.1))), 7)], fill=accent)

    blend_glass_panel(canvas, (26, 24, RW - 26, 78), (8, 12, 22, 168), (*accent, 210), radius=16, width=2)
    d = ImageDraw.Draw(canvas)
    dot_r = int(5 + pulse * 3)
    d.ellipse([(50 - dot_r, 51 - dot_r), (50 + dot_r, 51 + dot_r)], fill=accent)
    d.text((68, 39), ad["badge"], fill=white, font=load_font(19, bold=True))
    for b_i in range(6):
        bh = int((7 + abs(math.sin(t * 18.0 + b_i * 1.1)) * 18) if is_speaking else (4 + abs(math.sin(t * 3.0 + b_i)) * 4))
        bx = RW - 94 + b_i * 10
        d.rounded_rectangle([(bx, 51 - bh // 2), (bx + 6, 51 + bh // 2)], radius=3, fill=accent if b_i % 2 == 0 else secondary)

    if t < s1:
        p = ease_out_cubic(min(1.0, t / 0.55))
        ys = int((1.0 - p) * -36)
        blend_glass_panel(canvas, (26, 94 + ys, RW - 26, 214 + ys), (8, 14, 24, 158), (*accent, 215), radius=20, width=2)
        d = ImageDraw.Draw(canvas)
        d.text((48, 108 + ys), ad["hook_top"], fill=secondary, font=load_font(22, bold=True))
        d.text((48, 144 + ys), ad["hook_big"], fill=white, font=load_font(36, bold=True))
    elif t < s2:
        lt = t - s1
        blend_glass_panel(canvas, (26, 94, RW - 26, 326), (8, 14, 26, 168), (*accent, 215), radius=22, width=2)
        d = ImageDraw.Draw(canvas)
        d.text((48, 110), ad["mid_title"], fill=accent, font=load_font(22, bold=True))
        for idx, line in enumerate(ad["mid_bullets"]):
            sp = ease_out_cubic(min(1.0, max(0.0, (lt - idx * 0.32) / 0.45)))
            xs = int((1.0 - sp) * 180)
            d.text((48 + xs, 150 + idx * 36), line, fill=white, font=load_font(20, bold=False))
        gx0, gy0, gx1, gy1 = 48, 266, RW - 48, 308
        frac_vis = ease_out_cubic(min(1.0, lt / max((s2 - s1) * 0.6, 1.2)))
        steps = 20
        vis = max(2, int(round(frac_vis * steps)))
        pts = [
            (
                int(gx0 + (gx1 - gx0) * (i / (steps - 1))),
                int(gy1 - ((i / (steps - 1)) ** 1.3 * 0.78 + 0.12 * math.sin(i * 1.1 + t * 2.0)) * (gy1 - gy0)),
            )
            for i in range(vis)
        ]
        for i in range(len(pts) - 1):
            d.line([pts[i], pts[i + 1]], fill=accent, width=5)
        tx, ty = pts[-1]
        d.ellipse([(tx - 7, ty - 7), (tx + 7, ty + 7)], fill=white, outline=accent, width=3)
    else:
        grow = int(pulse * 7)
        blend_glass_panel(canvas, (28, 102, RW - 28, 355), (8, 14, 26, 185), (*accent, 235), radius=24, width=3)
        d = ImageDraw.Draw(canvas)
        d.text((52, 124), ad["cta_big"], fill=white, font=load_font(34, bold=True))
        d.text((52, 174), "🍎 Apple iPhone (iOS)  +  🤖 Android  •  100% Free", fill=secondary, font=load_font(22, bold=True))
        d.rounded_rectangle([(52 - grow, 224 - grow // 2), (RW - 52 + grow, 326 + grow // 2)], radius=18, fill=accent)
        d.text((76, 240), "TAP LINK IN BIO / JOIN FREE RADAR", fill=dark, font=load_font(22, bold=True))
        d.text((76, 274), channel_link, fill=dark, font=load_font(32, bold=True))

    if active_chunk:
        cap_y = 965
        blend_glass_panel(canvas, (26, cap_y - 16, RW - 26, cap_y + 112), (6, 10, 18, 200), (*accent, 210), radius=20, width=2)
        d = ImageDraw.Draw(canvas)
        cap_font = load_font(36, bold=True)
        widths = [d.textbbox((0, 0), w["word"].upper() + " ", font=cap_font)[2] for w in active_chunk]
        if sum(widths) <= RW - 84:
            cur_x = max(42, (RW - sum(widths)) // 2)
            for item, w_px in zip(active_chunk, widths):
                col = secondary if item["start"] - 0.04 <= t <= item["end"] + 0.08 else white
                d.text((cur_x + 2, cap_y + 24), item["word"].upper(), fill=(0, 0, 0), font=cap_font)
                d.text((cur_x, cap_y + 22), item["word"].upper(), fill=col, font=cap_font)
                cur_x += w_px
        else:
            sm_font = load_font(30, bold=True)
            for r_i, row_w in enumerate([active_chunk[:2], active_chunk[2:]]):
                if not row_w:
                    continue
                rw_px = [d.textbbox((0, 0), w["word"].upper() + " ", font=sm_font)[2] for w in row_w]
                cur_x = max(42, (RW - sum(rw_px)) // 2)
                ry = cap_y + 6 + r_i * 44
                for item, w_px in zip(row_w, rw_px):
                    col = secondary if item["start"] - 0.04 <= t <= item["end"] + 0.08 else white
                    d.text((cur_x + 2, ry + 2), item["word"].upper(), fill=(0, 0, 0), font=sm_font)
                    d.text((cur_x, ry), item["word"].upper(), fill=col, font=sm_font)
                    cur_x += w_px

    d = ImageDraw.Draw(canvas)
    d.text((30, RH - 48), f"APPLE iOS & ANDROID  •  {channel_link}  •  DYOR / NFA", fill=muted, font=load_font(17, bold=True))
    return canvas.convert("RGB").tobytes()


def render_single_commercial(
    ad: dict[str, Any],
    channel_link: str,
    audio_path: Path,
    timings: list[dict[str, Any]],
    out_mp4: Path,
    video_clips: list[Path],
) -> None:
    from PIL import Image, ImageDraw  # type: ignore

    duration = get_audio_duration_seconds(audio_path)
    total_frames = int(math.ceil(duration * FPS))
    caption_chunks = group_caption_chunks(timings, words_per_chunk=3)

    vignette = Image.new("RGBA", (RW, RH), (0, 0, 0, 0))
    vd = ImageDraw.Draw(vignette)
    for y in range(0, 260, 4):
        vd.rectangle([(0, y), (RW, y + 4)], fill=(4, 8, 16, int(155 * (1.0 - y / 260.0))))
    for y in range(RH - 500, RH, 4):
        vd.rectangle([(0, y), (RW, y + 4)], fill=(4, 8, 16, int(215 * ((y - (RH - 500)) / 500.0))))

    decoder = None
    loaded_shots = None
    if video_clips:
        bg_mp4 = OUT_DIR / f"{ad['id']}_bg_live.mp4"
        build_background_video_track(video_clips, duration, bg_mp4)
        decoder = subprocess.Popen(
            ["ffmpeg", "-i", str(bg_mp4), "-f", "rawvideo", "-pix_fmt", "rgb24", "-v", "error", "pipe:1"],
            stdout=subprocess.PIPE,
        )
    else:
        loaded_shots = [(load_oversized_cinema_still(fn, (12, 22, 38)), mode) for fn, mode in ad["shots"]]

    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo", "-vcodec", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{RW}x{RH}", "-r", str(FPS), "-i", "pipe:0",
        "-i", str(audio_path),
        "-f", "lavfi", "-t", f"{duration:.2f}", "-i", "sine=frequency=110:sample_rate=44100",
        "-f", "lavfi", "-t", f"{duration:.2f}", "-i", "sine=frequency=165:sample_rate=44100",
        "-filter_complex",
        "[1:a]loudnorm=I=-15:TP=-1.5:LRA=11[v];"
        "[2:a]volume=0.015,tremolo=f=2.4:d=0.45[b1];"
        "[3:a]volume=0.008,tremolo=f=1.2:d=0.5[b2];"
        "[v][b1][b2]amix=inputs=3:duration=first:dropout_transition=1[aout]",
        "-map", "0:v:0", "-map", "[aout]",
        "-vf", "scale=1080:1920:flags=lanczos,format=yuv420p",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-r", str(FPS),
        "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart",
        str(out_mp4),
    ]

    encoder = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)
    assert encoder.stdin is not None
    frame_bytes = RW * RH * 3
    last_bg = Image.new("RGB", (RW, RH), (10, 18, 32))
    s1, s2, xfade = duration * 0.34, duration * 0.72, 0.55

    try:
        for f_idx in range(total_frames):
            t = f_idx / FPS
            if decoder is not None and decoder.stdout is not None:
                raw = decoder.stdout.read(frame_bytes)
                if len(raw) == frame_bytes:
                    last_bg = Image.frombytes("RGB", (RW, RH), raw)
                bg = last_bg
            else:
                assert loaded_shots is not None
                if t < s1:
                    bg = sample_fluid_camera(loaded_shots[0][0], t / max(s1, 0.1), t, loaded_shots[0][1])
                    if t > s1 - xfade:
                        bg = Image.blend(bg, sample_fluid_camera(loaded_shots[1][0], 0.0, t, loaded_shots[1][1]), (t - (s1 - xfade)) / xfade)
                elif t < s2:
                    bg = sample_fluid_camera(loaded_shots[1][0], (t - s1) / max(s2 - s1, 0.1), t, loaded_shots[1][1])
                    if t > s2 - xfade:
                        bg = Image.blend(bg, sample_fluid_camera(loaded_shots[2][0], 0.0, t, loaded_shots[2][1]), (t - (s2 - xfade)) / xfade)
                else:
                    bg = sample_fluid_camera(loaded_shots[2][0], (t - s2) / max(duration - s2, 0.1), t, loaded_shots[2][1])

            encoder.stdin.write(render_overlay_frame(bg, vignette, ad, channel_link, t, duration, caption_chunks))
    finally:
        encoder.stdin.close()
        if decoder is not None:
            decoder.terminate()
            decoder.wait()
        if encoder.wait() != 0:
            raise RuntimeError(f"FFmpeg commercial render failed for {ad['id']}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Render 3 Real Live-Action Capital Alpha Commercials")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--only", default="rotate", help="rotate | all | ad1_glamorous_woman | ad2_busy_worker | ad3_young_couple")
    args = parser.parse_args()

    raw_chan = normalize_channel_id(os.getenv("TELEGRAM_CHANNEL_ID", ""))
    handle = raw_chan.lstrip("@") if raw_chan.startswith("@") else "MysolAlpha99"
    channel_link = f"t.me/{handle}"
    hub_url = os.getenv("HUB_URL", "https://capitalalpha.pages.dev").strip() or "https://capitalalpha.pages.dev"
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    pexels_key = os.getenv("PEXELS_API_KEY", "").strip()
    pixabay_key = os.getenv("PIXABAY_API_KEY", "").strip()

    if args.only == "rotate":
        slot = get_30min_slot(offset=20)
        base_ad = dict(ADS_CONFIG[slot % len(ADS_CONFIG)])
        theme = THEMES_30[slot]
        voice_pick = get_rotating_voice(slot)
        base_ad["id"] = f"{base_ad['id']}_v{slot + 1}"
        base_ad["filename"] = f"capital_alpha_ad_slot{slot + 1:02d}.mp4"
        base_ad["voice"] = voice_pick["voice"]
        base_ad["badge"] = f"{base_ad['badge']}  #{slot + 1}/30"
        base_ad["pexels_queries"] = list(theme["queries"]) + list(base_ad["pexels_queries"][:1])
        base_ad["theme_label"] = theme["label"]
        base_ad["slot"] = slot
        selected = [base_ad]
    elif args.only == "all":
        selected = [dict(a) for a in ADS_CONFIG]
    else:
        selected = [dict(a) for a in ADS_CONFIG if a["id"] == args.only]
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for ad in selected:
        slot_seed = int(ad.get("slot", get_30min_slot(offset=20)))
        local_mp4s = [n for n in ad["local_clips"] if (VIDEOS_DIR / n).exists()]
        stills = [fn for fn, _ in ad["shots"] if (ASSETS_DIR / fn).exists() or (Path(__file__).resolve().parent / "assets" / fn).exists()]
        mode_str = (
            f"LOCAL MP4 ({len(local_mp4s)})"
            if local_mp4s
            else ("PIXABAY 30x LIVE HD VIDEO" if pixabay_key else ("PEXELS LIVE HD VIDEO" if pexels_key else f"FALLBACK STILLS ({len(stills)}/3)"))
        )
        print(f"[AD PACK 30x] {ad['id']} ({ad.get('theme_label', 'Core')}) | Mode: {mode_str} | Voice: {ad['voice']} ({len(ad['script'].split())} words)")
        if args.dry_run:
            continue

        clips = resolve_video_clips(ad, pexels_key, pixabay_key)
        if not clips and pixabay_key:
            clips = fetch_pixabay_videos_for_queries(
                ad["pexels_queries"], pixabay_key, CACHE_DIR, ad["id"], target_count=3, slot_seed=slot_seed
            )
        audio_path = OUT_DIR / f"{ad['id']}.mp3"
        out_mp4 = OUT_DIR / ad["filename"]
        timings = asyncio.run(synthesize_voiceover_with_timings(ad["script"], audio_path, voice=ad["voice"]))
        dur = get_audio_duration_seconds(audio_path)
        if len(timings) < 8:
            timings = build_fallback_word_timings(ad["script"], dur)

        render_single_commercial(ad, channel_link, audio_path, timings, out_mp4, clips)
        print(f"[OK] Rendered {ad['id']} ({dur:.1f}s, live_video={bool(clips)}): {out_mp4}")

        if bot_token and raw_chan:
            caption = ad["caption"].format(hub_url=hub_url, channel_link=channel_link)
            send_video_to_telegram(bot_token, raw_chan, out_mp4, caption)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
