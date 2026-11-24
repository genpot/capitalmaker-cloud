#!/usr/bin/env python3
"""
CAPITAL ALPHA — 30-Theme Live-Action Video & Photo Rotator (Pixabay HD Engine)
Provides 30 distinct diverse human/lifestyle live-action visual themes + 8 rotating Neural voices
so EVERY 30-minute video across Auto-Shorts (#5), Official 90s Promo, and Commercial Ads uses
fresh, real moving HD footage (never repeating the same single static character!).
"""

from __future__ import annotations

import json
import math
import subprocess
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

VOICES_8: list[dict[str, str]] = [
    {"name": "CLAIRE", "role": "ALPHA HOST", "voice": "en-US-AvaNeural"},
    {"name": "ANDREW", "role": "SOLANA ANALYST", "voice": "en-US-AndrewNeural"},
    {"name": "SOPHIE", "role": "MARKET REPORTER", "voice": "en-GB-SoniaNeural"},
    {"name": "RYAN", "role": "CRYPTO STRATEGIST", "voice": "en-GB-RyanNeural"},
    {"name": "EMMA", "role": "DEFI PRESENTER", "voice": "en-US-EmmaNeural"},
    {"name": "BRIAN", "role": "QUANT DESK", "voice": "en-US-BrianNeural"},
    {"name": "NATASHA", "role": "RADAR HOST", "voice": "en-AU-NatashaNeural"},
    {"name": "WILLIAM", "role": "ON-CHAIN LEAD", "voice": "en-AU-WilliamNeural"},
]

# 30 distinct, proven Pixabay Video/Photo search themes (diverse glamorous women, busy professionals,
# young couples, luxury lifestyle, city skylines, traders — clean 2-word queries for high hit rates!)
THEMES_30: list[dict[str, Any]] = [
    {"id": 1,  "label": "Penthouse Woman Night",    "queries": ["woman smartphone", "fashion woman", "city night"]},
    {"id": 2,  "label": "Office Worker Focus",      "queries": ["businessman laptop", "man office", "coffee desk"]},
    {"id": 3,  "label": "Young Couple Cafe",        "queries": ["happy couple", "couple smartphone", "couple coffee"]},
    {"id": 4,  "label": "Luxury Lounge Woman",      "queries": ["woman phone", "luxury woman", "hotel lounge"]},
    {"id": 5,  "label": "Executive Trader Desk",    "queries": ["stock market", "man laptop", "office window"]},
    {"id": 6,  "label": "Rooftop Couple Sunset",    "queries": ["couple sunset", "young couple", "city skyline"]},
    {"id": 7,  "label": "Stylish Blonde City",      "queries": ["blonde woman", "woman city", "woman smiling"]},
    {"id": 8,  "label": "Remote Founder Laptop",    "queries": ["working laptop", "man coffee", "modern office"]},
    {"id": 9,  "label": "Couple Beach Freedom",     "queries": ["couple beach", "couple laughing", "ocean sunset"]},
    {"id": 10, "label": "Glamorous Evening Dress",  "queries": ["glamour woman", "woman cocktail", "night lights"]},
    {"id": 11, "label": "Busy Commuter Phone",      "queries": ["man smartphone", "city street", "business man"]},
    {"id": 12, "label": "Couple Luxury Travel",     "queries": ["couple travel", "luxury resort", "couple smiling"]},
    {"id": 13, "label": "Woman Coffee Morning",     "queries": ["woman coffee", "morning light", "woman laptop"]},
    {"id": 14, "label": "Late Night Hustler",       "queries": ["man computer", "night office", "trading chart"]},
    {"id": 15, "label": "Couple Celebrating Toast", "queries": ["couple party", "champagne toast", "friends celebrating"]},
    {"id": 16, "label": "Yacht Lifestyle",          "queries": ["luxury yacht", "woman ocean", "summer luxury"]},
    {"id": 17, "label": "Architect Studio Desk",    "queries": ["creative office", "man desk", "typing laptop"]},
    {"id": 18, "label": "Young Couple Apartment",   "queries": ["couple home", "couple sofa", "couple phone"]},
    {"id": 19, "label": "Fashion Model Street",     "queries": ["model city", "stylish woman", "urban sunset"]},
    {"id": 20, "label": "Financial District Walk",  "queries": ["wall street", "suit man", "skyscrapers"]},
    {"id": 21, "label": "Couple Sports Car Drive",  "queries": ["luxury car", "couple driving", "highway sunset"]},
    {"id": 22, "label": "Woman Balcony Sunrise",    "queries": ["woman balcony", "sunrise city", "woman relaxing"]},
    {"id": 23, "label": "Tech Startup Workspace",   "queries": ["startup office", "developer screen", "business team"]},
    {"id": 24, "label": "Couple Dinner Night",      "queries": ["couple dinner", "restaurant night", "couple smiling"]},
    {"id": 25, "label": "Fitness Woman Lifestyle",  "queries": ["woman fitness", "woman running", "modern city"]},
    {"id": 26, "label": "Home Office Investor",     "queries": ["home office", "man smiling", "finance chart"]},
    {"id": 27, "label": "Young Couple City Walk",   "queries": ["couple walking", "downtown lights", "couple happy"]},
    {"id": 28, "label": "Poolside Luxury Woman",    "queries": ["woman pool", "resort luxury", "sunlight water"]},
    {"id": 29, "label": "Crypto Trading Charts",    "queries": ["cryptocurrency", "stock chart", "digital finance"]},
    {"id": 30, "label": "Future Skyline Victory",   "queries": ["futuristic city", "neon skyline", "luxury penthouse"]},
]


def get_30min_slot(offset: int = 0) -> int:
    """Returns a deterministic 0..29 index that advances every 30 minutes 24/7."""
    return (int(time.time() // 1800) + offset) % len(THEMES_30)


def get_rotating_voice(slot: int) -> dict[str, str]:
    return dict(VOICES_8[slot % len(VOICES_8)])


def fetch_pixabay_videos_for_queries(
    queries: list[str],
    api_key: str,
    cache_dir: Path,
    prefix: str,
    target_count: int = 3,
    slot_seed: int = 0,
) -> list[Path]:
    """Fetches real moving HD MP4 clips from Pixabay Video API with rotating offsets."""
    if not api_key.strip():
        return []
    cache_dir.mkdir(parents=True, exist_ok=True)
    clips: list[Path] = []
    used_ids: set[int] = set()

    expanded = list(queries) + ["woman smartphone", "man laptop", "happy couple", "city skyline"]
    for idx, query in enumerate(expanded):
        if len(clips) >= target_count:
            break
        try:
            q = urllib.parse.quote_plus(query.strip())
            url = f"https://pixabay.com/api/videos/?key={urllib.parse.quote(api_key.strip())}&q={q}&per_page=25&safesearch=true"
            req = urllib.request.Request(url, headers={"User-Agent": "CapitalAlpha/3.0"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            hits = data.get("hits") or []
            if not hits:
                continue
            start_i = (slot_seed * 3 + idx * 5) % len(hits)
            ordered = hits[start_i:] + hits[:start_i]
            chosen_url = None
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
                dst = cache_dir / f"{prefix}_slot{slot_seed}_{idx}.mp4"
                dl_req = urllib.request.Request(chosen_url, headers={"User-Agent": "CapitalAlpha/3.0"})
                with urllib.request.urlopen(dl_req, timeout=60) as r_in, dst.open("wb") as f_out:
                    f_out.write(r_in.read())
                if dst.stat().st_size > 40_000:
                    clips.append(dst)
                    print(f"[MEDIA 30x] Downloaded Pixabay HD clip #{len(clips)} ('{query}'): {dst.name}")
        except Exception as exc:
            print(f"[WARN] Pixabay video skip '{query}': {exc}")
    return clips


def fetch_pixabay_photos_for_queries(
    queries: list[str],
    api_key: str,
    cache_dir: Path,
    prefix: str,
    target_count: int = 4,
    slot_seed: int = 0,
) -> list[Path]:
    """Backup: fetches real high-res human/lifestyle photos from Pixabay Photo API (zero cartoons!)."""
    if not api_key.strip():
        return []
    cache_dir.mkdir(parents=True, exist_ok=True)
    photos: list[Path] = []
    used_ids: set[int] = set()

    for idx, query in enumerate(list(queries) + ["woman portrait", "businessman", "happy couple"]):
        if len(photos) >= target_count:
            break
        try:
            q = urllib.parse.quote_plus(query.strip())
            url = (
                f"https://pixabay.com/api/?key={urllib.parse.quote(api_key.strip())}"
                f"&q={q}&image_type=photo&orientation=vertical&per_page=20&safesearch=true"
            )
            req = urllib.request.Request(url, headers={"User-Agent": "CapitalAlpha/3.0"})
            with urllib.request.urlopen(req, timeout=18) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            hits = data.get("hits") or []
            if not hits:
                continue
            start_i = (slot_seed * 2 + idx * 3) % len(hits)
            ordered = hits[start_i:] + hits[:start_i]
            chosen_url = None
            for h in ordered:
                pid = int(h.get("id", 0))
                if pid in used_ids:
                    continue
                u = h.get("largeImageURL") or h.get("webformatURL")
                if u:
                    used_ids.add(pid)
                    chosen_url = u
                    break
            if chosen_url:
                dst = cache_dir / f"{prefix}_photo_{slot_seed}_{idx}.jpg"
                dl_req = urllib.request.Request(chosen_url, headers={"User-Agent": "CapitalAlpha/3.0"})
                with urllib.request.urlopen(dl_req, timeout=30) as r_in, dst.open("wb") as f_out:
                    f_out.write(r_in.read())
                if dst.stat().st_size > 15_000:
                    photos.append(dst)
                    print(f"[MEDIA 30x] Downloaded Pixabay photo #{len(photos)} ('{query}'): {dst.name}")
        except Exception as exc:
            print(f"[WARN] Pixabay photo skip '{query}': {exc}")
    return photos


def stitch_live_video_background(
    clips: list[Path],
    duration: float,
    rw: int,
    rh: int,
    fps: int,
    out_mp4: Path,
) -> Path:
    """Stitches multiple real moving HD clips into one smooth, color-graded vertical background video."""
    seg_dur = duration / max(len(clips), 1)
    cmd = ["ffmpeg", "-y"]
    for c in clips:
        cmd += ["-stream_loop", "-1", "-t", f"{seg_dur + 0.5:.2f}", "-i", str(c)]

    filters = []
    for i in range(len(clips)):
        filters.append(
            f"[{i}:v]scale={rw}:{rh}:force_original_aspect_ratio=increase,"
            f"crop={rw}:{rh},fps={fps},setsar=1,eq=contrast=1.06:saturation=1.08:brightness=0.02,format=yuv420p[v{i}]"
        )
    concat_in = "".join(f"[v{i}]" for i in range(len(clips)))
    filters.append(f"{concat_in}concat=n={len(clips)}:v=1:a=0,trim=0:{duration:.2f},setpts=PTS-STARTPTS[vout]")

    cmd += [
        "-filter_complex", ";".join(filters),
        "-map", "[vout]", "-an",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "19",
        str(out_mp4),
    ]
    subprocess.run(cmd, check=True)
    return out_mp4


def draw_fluid_ambient_particles(canvas: Any, t: float, rw: int, rh: int, col1: tuple[int, int, int], col2: tuple[int, int, int]) -> None:
    """Subtle floating cinematic bokeh light orbs for polished motion-graphics depth."""
    from PIL import Image, ImageDraw  # type: ignore

    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for i in range(12):
        bx = int(((i * 103 + t * (26 + (i % 4) * 11)) % (rw + 100)) - 50)
        by = int((rh - ((i * 139 + t * (38 + (i % 5) * 12)) % (rh + 140))) + 30)
        r = 4 + (i % 4) * 4
        alpha = int(24 + 20 * (0.5 + 0.5 * math.sin(t * 2.6 + i)))
        col = col1 if i % 2 == 0 else col2
        od.ellipse([(bx - r, by - r), (bx + r, by + r)], fill=(*col, alpha))
    canvas.alpha_composite(overlay)
