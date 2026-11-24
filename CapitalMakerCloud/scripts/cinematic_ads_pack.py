#!/usr/bin/env python3
"""
CAPITAL ALPHA — Fluid 30fps Live-Action Commercial Ads Pack (3 Photorealistic Videos)
NOT cartoonish! Uses photorealistic 35mm cinema film stills + fluid 30fps motion:
  - Smooth handheld micro-sway + continuous optical dolly push-in & lateral parallax pans
  - Dynamic glowing ambient bokeh/light particles + animated glass chart overlays
  - Multi-shot cross-dissolves + snappy fade-to-flash transitions (zero stiff static frames!)
  - Hormozi-style kinetic word-by-word karaoke captions synced to expressive Neural voices
  - Explicitly highlights: "Available on BOTH Apple iPhone (iOS) & Android" + Paper Sim FIRST!

Renders 3 distinct commercial videos:
  1) ad1_glamorous_woman_capitalmoon.mp4  — Confident stylish woman trading Solana effortlessly with CapitalMoon
  2) ad2_busy_worker_paper_sim.mp4        — Busy working guy wanting stress-free investing via Paper Sim FIRST & CapitalMaker
  3) ad3_young_couple_capital_alpha.mp4   — Stylish young guy & woman celebrating wins using CapitalMoon & CapitalMaker
"""

from __future__ import annotations

import argparse
import asyncio
import math
import os
import subprocess
from pathlib import Path
from typing import Any

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
RW, RH = 720, 1280
FPS = 30  # Silky 30fps fluid cinematic motion!


ADS_CONFIG: list[dict[str, Any]] = [
    {
        "id": "ad1_glamorous_woman",
        "filename": "ad1_glamorous_woman_capitalmoon.mp4",
        "voice": "en-US-AvaNeural",
        "badge": "CAPITALMOON  •  APPLE iOS & ANDROID",
        "accent": (18, 238, 166),
        "secondary": (255, 206, 72),
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


def load_oversized_cinema_still(filename: str, fallback_rgb: tuple[int, int, int]) -> Any:
    """Loads a photorealistic 9:16 still at 1.24x resolution for ultra-fluid handheld dolly & parallax motion."""
    from PIL import Image, ImageEnhance, ImageOps  # type: ignore

    tw, th = int(RW * 1.24), int(RH * 1.24)
    path = ASSETS_DIR / filename
    if path.exists():
        img = Image.open(path).convert("RGB")
        fitted = ImageOps.fit(img, (tw, th), method=Image.Resampling.LANCZOS)
        # Crisp subtle cinematic contrast polish
        return ImageEnhance.Contrast(fitted).enhance(1.06)
    return Image.new("RGB", (tw, th), fallback_rgb)


def sample_fluid_camera(oversized: Any, progress: float, t: float, mode: str) -> Any:
    """
    Fluid cinema handheld camera motion (smooth S-curve ease + organic breathing micro-sway + dolly zoom).
    Eliminates stiff slideshow feel!
    """
    from PIL import Image  # type: ignore

    ow, oh = oversized.size
    p = max(0.0, min(1.0, progress))
    # Smooth S-curve easing
    ease = p * p * (3.0 - 2.0 * p)
    # Subtle natural 35mm handheld camera sway (never robotic!)
    sway_x = math.sin(t * 1.65) * 7.0 + math.cos(t * 0.85) * 4.0
    sway_y = math.cos(t * 1.35) * 6.0

    if mode == "dolly_sway_in":
        scale = 1.02 + 0.16 * ease
        cw, ch = int(ow / scale), int(oh / scale)
        cx = (ow - cw) * (0.45 + 0.10 * ease) + sway_x
        cy = (oh - ch) * (0.38 + 0.06 * ease) + sway_y
    elif mode == "parallax_glide":
        scale = 1.15 - 0.09 * ease
        cw, ch = int(ow / scale), int(oh / scale)
        cx = (ow - cw) * (0.15 + 0.70 * ease) + sway_x
        cy = (oh - ch) * (0.44 - 0.08 * ease) + sway_y
    else:  # cinematic_push_right
        scale = 1.06 + 0.14 * ease
        cw, ch = int(ow / scale), int(oh / scale)
        cx = (ow - cw) * (0.78 - 0.56 * ease) + sway_x
        cy = (oh - ch) * (0.40 + 0.08 * ease) + sway_y

    x0 = max(0, min(ow - cw, int(round(cx))))
    y0 = max(0, min(oh - ch, int(round(cy))))
    return oversized.crop((x0, y0, x0 + cw, y0 + ch)).resize((RW, RH), Image.Resampling.BILINEAR)


def draw_ambient_bokeh(canvas: Any, t: float, accent: tuple[int, int, int], secondary: tuple[int, int, int]) -> None:
    """Adds subtle drifting cinematic bokeh light orbs so every frame feels alive and fluid."""
    from PIL import Image, ImageDraw  # type: ignore

    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for i in range(14):
        bx = int(((i * 97 + t * (28 + (i % 4) * 12)) % (RW + 120)) - 60)
        by = int((RH - ((i * 143 + t * (42 + (i % 5) * 14)) % (RH + 160))) + 40)
        r = 6 + (i % 4) * 5
        alpha = int(28 + 22 * (0.5 + 0.5 * math.sin(t * 2.5 + i)))
        col = accent if i % 2 == 0 else secondary
        od.ellipse([(bx - r, by - r), (bx + r, by + r)], fill=(*col, alpha))
    canvas.alpha_composite(overlay)


def render_single_commercial(
    ad: dict[str, Any],
    hub_url: str,
    channel_link: str,
    audio_path: Path,
    timings: list[dict[str, Any]],
    out_mp4: Path,
) -> None:
    from PIL import Image, ImageDraw  # type: ignore

    duration = get_audio_duration_seconds(audio_path)
    total_frames = int(math.ceil(duration * FPS))
    accent = ad["accent"]
    secondary = ad["secondary"]
    white = (248, 252, 255)
    muted = (204, 218, 236)
    dark = (6, 12, 24)

    loaded_shots = [
        (load_oversized_cinema_still(fname, (12, 22, 38)), mode)
        for fname, mode in ad["shots"]
    ]

    # Cinema top/bottom vignette for crisp glass text legibility over live-action faces
    vignette = Image.new("RGBA", (RW, RH), (0, 0, 0, 0))
    vd = ImageDraw.Draw(vignette)
    for y in range(0, 260, 4):
        vd.rectangle([(0, y), (RW, y + 4)], fill=(4, 8, 16, int(165 * (1.0 - y / 260.0))))
    for y in range(RH - 520, RH, 4):
        vd.rectangle([(0, y), (RW, y + 4)], fill=(4, 8, 16, int(225 * ((y - (RH - 520)) / 520.0))))

    caption_chunks = group_caption_chunks(timings, words_per_chunk=3)
    s1 = duration * 0.34
    s2 = duration * 0.72
    xfade = 0.55

    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo", "-vcodec", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{RW}x{RH}", "-r", str(FPS), "-i", "pipe:0",
        "-i", str(audio_path),
        "-f", "lavfi", "-t", f"{duration:.2f}", "-i", "sine=frequency=110:sample_rate=44100",
        "-f", "lavfi", "-t", f"{duration:.2f}", "-i", "sine=frequency=165:sample_rate=44100",
        "-filter_complex",
        "[1:a]loudnorm=I=-15:TP=-1.5:LRA=11[v];"
        "[2:a]volume=0.016,tremolo=f=2.4:d=0.45[b1];"
        "[3:a]volume=0.009,tremolo=f=1.2:d=0.5[b2];"
        "[v][b1][b2]amix=inputs=3:duration=first:dropout_transition=1[aout]",
        "-map", "0:v:0", "-map", "[aout]",
        "-vf", "scale=1080:1920:flags=lanczos,format=yuv420p",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-r", str(FPS),
        "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart",
        str(out_mp4),
    ]

    proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)
    assert proc.stdin is not None
    try:
        for f_idx in range(total_frames):
            t = f_idx / FPS
            pulse = 0.5 + 0.5 * math.sin(t * 7.0)

            if t < s1:
                bg = sample_fluid_camera(loaded_shots[0][0], t / max(s1, 0.1), t, loaded_shots[0][1])
                if t > s1 - xfade:
                    nxt = sample_fluid_camera(loaded_shots[1][0], 0.0, t, loaded_shots[1][1])
                    bg = Image.blend(bg, nxt, (t - (s1 - xfade)) / xfade)
            elif t < s2:
                bg = sample_fluid_camera(loaded_shots[1][0], (t - s1) / max(s2 - s1, 0.1), t, loaded_shots[1][1])
                if t > s2 - xfade:
                    nxt = sample_fluid_camera(loaded_shots[2][0], 0.0, t, loaded_shots[2][1])
                    bg = Image.blend(bg, nxt, (t - (s2 - xfade)) / xfade)
            else:
                bg = sample_fluid_camera(loaded_shots[2][0], (t - s2) / max(duration - s2, 0.1), t, loaded_shots[2][1])

            canvas = bg.convert("RGBA")
            draw_ambient_bokeh(canvas, t, accent, secondary)
            canvas.alpha_composite(vignette)

            # Active karaoke caption lookup
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

            # Top retention bar + sleek header pill
            d = ImageDraw.Draw(canvas)
            d.rectangle([(0, 0), (RW, 7)], fill=(18, 28, 46, 200))
            d.rectangle([(0, 0), (int(RW * (t / max(duration, 0.1))), 7)], fill=accent)

            blend_glass_panel(canvas, (26, 24, RW - 26, 78), (8, 12, 22, 175), (*accent, 210), radius=16, width=2)
            d = ImageDraw.Draw(canvas)
            dot_r = int(5 + pulse * 3)
            d.ellipse([(50 - dot_r, 51 - dot_r), (50 + dot_r, 51 + dot_r)], fill=accent)
            d.text((68, 39), ad["badge"], fill=white, font=load_font(19, bold=True))
            for b_i in range(6):
                bh = int((7 + abs(math.sin(t * 18.0 + b_i * 1.1)) * 18) if is_speaking else (4 + abs(math.sin(t * 3.0 + b_i)) * 4))
                bx = RW - 94 + b_i * 10
                d.rounded_rectangle([(bx, 51 - bh // 2), (bx + 6, 51 + bh // 2)], radius=3, fill=accent if b_i % 2 == 0 else secondary)

            # Non-intrusive sleek overlays keeping the photorealistic human subjects clearly visible!
            if t < s1:
                p = ease_out_cubic(min(1.0, t / 0.55))
                ys = int((1.0 - p) * -36)
                blend_glass_panel(canvas, (26, 94 + ys, RW - 26, 214 + ys), (8, 14, 24, 165), (*accent, 215), radius=20, width=2)
                d = ImageDraw.Draw(canvas)
                d.text((48, 108 + ys), ad["hook_top"], fill=secondary, font=load_font(22, bold=True))
                d.text((48, 144 + ys), ad["hook_big"], fill=white, font=load_font(36, bold=True))

            elif t < s2:
                lt = t - s1
                # Animated translucent floating live profit curve + feature pill near top (leaves face clear!)
                blend_glass_panel(canvas, (26, 94, RW - 26, 332), (8, 14, 26, 178), (*accent, 215), radius=22, width=2)
                d = ImageDraw.Draw(canvas)
                d.text((48, 110), ad["mid_title"], fill=accent, font=load_font(22, bold=True))
                for idx, line in enumerate(ad["mid_bullets"]):
                    sp = ease_out_cubic(min(1.0, max(0.0, (lt - idx * 0.32) / 0.45)))
                    xs = int((1.0 - sp) * 180)
                    d.text((48 + xs, 150 + idx * 36), line, fill=white, font=load_font(20, bold=False))

                # Smooth animated mini breakout sparkline at bottom of panel
                gx0, gy0, gx1, gy1 = 48, 268, RW - 48, 314
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
                blend_glass_panel(canvas, (28, 102, RW - 28, 355), (8, 14, 26, 190), (*accent, 235), radius=24, width=3)
                d = ImageDraw.Draw(canvas)
                d.text((52, 124), ad["cta_big"], fill=white, font=load_font(34, bold=True))
                d.text((52, 174), "🍎 Apple iPhone (iOS)  +  🤖 Android  •  100% Free", fill=secondary, font=load_font(22, bold=True))
                d.rounded_rectangle([(52 - grow, 224 - grow // 2), (RW - 52 + grow, 326 + grow // 2)], radius=18, fill=accent)
                d.text((76, 240), "TAP LINK IN BIO / JOIN FREE RADAR", fill=dark, font=load_font(22, bold=True))
                d.text((76, 274), channel_link, fill=dark, font=load_font(32, bold=True))

            # ---------------- KINETIC HORMOZI KARAOKE CAPTIONS ----------------
            if active_chunk:
                cap_y = 965
                blend_glass_panel(canvas, (26, cap_y - 16, RW - 26, cap_y + 112), (6, 10, 18, 208), (*accent, 210), radius=20, width=2)
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
            proc.stdin.write(canvas.convert("RGB").tobytes())
    finally:
        proc.stdin.close()
        if proc.wait() != 0:
            raise RuntimeError(f"FFmpeg commercial render failed for {ad['id']}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Render 3 Fluid 30fps Live-Action Capital Alpha Commercials")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--only", default="all", help="all | ad1_glamorous_woman | ad2_busy_worker | ad3_young_couple")
    args = parser.parse_args()

    raw_chan = normalize_channel_id(os.getenv("TELEGRAM_CHANNEL_ID", ""))
    handle = raw_chan.lstrip("@") if raw_chan.startswith("@") else "MysolAlpha99"
    channel_link = f"t.me/{handle}"
    hub_url = os.getenv("HUB_URL", f"https://{channel_link}").strip() or f"https://{channel_link}"
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()

    selected = ADS_CONFIG if args.only == "all" else [a for a in ADS_CONFIG if a["id"] == args.only]
    if not selected:
        raise ValueError(f"Unknown --only value: {args.only}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for ad in selected:
        found_shots = [fn for fn, _ in ad["shots"] if (ASSETS_DIR / fn).exists()]
        print(f"[AD PACK] {ad['id']} | Voice: {ad['voice']} | Shots found: {len(found_shots)}/{len(ad['shots'])} ({len(ad['script'].split())} words)")
        if args.dry_run:
            continue

        audio_path = OUT_DIR / f"{ad['id']}.mp3"
        out_mp4 = OUT_DIR / ad["filename"]
        timings = asyncio.run(synthesize_voiceover_with_timings(ad["script"], audio_path, voice=ad["voice"]))
        dur = get_audio_duration_seconds(audio_path)
        if len(timings) < 8:
            timings = build_fallback_word_timings(ad["script"], dur)

        render_single_commercial(ad, hub_url, channel_link, audio_path, timings, out_mp4)
        print(f"[OK] Rendered fluid 30fps commercial ({dur:.1f}s): {out_mp4}")

        if bot_token and raw_chan:
            caption = ad["caption"].format(hub_url=hub_url, channel_link=channel_link)
            send_video_to_telegram(bot_token, raw_chan, out_mp4, caption)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
