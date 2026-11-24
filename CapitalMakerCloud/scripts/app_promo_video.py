#!/usr/bin/env python3
"""
CAPITAL ALPHA — v2 Director's Cut Cinematic Promo Video (CapitalMoon + CapitalMaker)
6-chapter dynamic 24fps 3D storytelling showcase:
  1) Scroll-stopping hook with 3D Human Storyteller & live radar scanlines
  2) Deep-Dive on CapitalMoon: Autonomous 24/7 memecoin scanner, trailing TP/SL, 8-Vector Rug Shield
  3) Risk-Free Online Paper Simulation BEFORE Real Money (on BOTH CapitalMoon & CapitalMaker!)
  4) CapitalMaker: Real Solana Staking Yield (JitoSOL/jupSOL), Jupiter Quant Swaps & 1-Tap SOL Rent Reclaim
  5) Zero-KYC Privacy Vault (Biometrics + 6-Digit PIN + Android Keystore + Built-in 24/7 AI Support Bot)
  6) Epic Solana Skyline Finale + Pulsing Free Download & Telegram CTA
"""

from __future__ import annotations

import argparse
import asyncio
import math
import os
import subprocess
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
    FPS,
    RH,
    RW,
    blend_glass_panel,
    build_fallback_word_timings,
    ease_out_cubic,
    get_audio_duration_seconds,
    group_caption_chunks,
    load_cinematic_asset,
    load_font,
    sample_camera_frame,
    send_video_to_telegram,
    synthesize_voiceover_with_timings,
)
from signal_broadcaster import normalize_channel_id

OUT_DIR = Path("output")
PROMO_AUDIO = OUT_DIR / "promo_v2_voice.mp3"
PROMO_VIDEO = OUT_DIR / "capital_alpha_official_promo.mp4"


def build_directors_cut_script(channel_link: str) -> str:
    return (
        "What if your phone could scan Solana memecoins, filter out obvious rugs, and manage trades autonomously while you sleep — "
        "and let you test everything in live paper simulation before you ever risk a single dollar? "
        "Welcome to the Capital Alpha mobile suite: two free, non-custodial apps for both Apple iPhone and Android built for modern Solana traders. "
        "First up, meet CapitalMoon — our flagship autonomous memecoin radar and sniper terminal. "
        "CapitalMoon watches live DexScreener breakouts and pre-run signals around the clock, runs an eight-vector rug and honeypot check, "
        "and executes automated entries with trailing profit locks and stop-loss protection right from your phone while you sleep. "
        "Worried about risking real money right away? Both CapitalMoon and CapitalMaker include full online Paper Simulation powered by real live Solana prices — "
        "so you can test, practice, and verify strategies risk-free before ever switching to your Live SOL Vault! "
        "And when you want steady Solana management, open CapitalMaker — built for real on-chain liquid staking like JitoSOL and jupSOL, "
        "deep-liquidity Jupiter quant swaps, USDC capital defense, and one-tap empty account SOL rent reclaim. "
        "No email, no phone number, and zero KYC — just biometrics, a six-digit local PIN, non-custodial vault encryption, "
        "and a 24 7 AI support bot built straight into both Apple iOS and Android apps. "
        "Download CapitalMoon and CapitalMaker free from our link in bio, and join our free 24 7 Telegram radar right now. "
        "Crypto and memecoins carry real market risk — always test in paper mode first and do your own research, not financial advice."
    )


def render_directors_cut_mp4(
    hub_url: str,
    channel_link: str,
    audio_path: Path,
    timings: list[dict[str, Any]],
    out_mp4: Path,
) -> None:
    from PIL import Image, ImageDraw  # type: ignore

    duration = get_audio_duration_seconds(audio_path)
    total_frames = int(math.ceil(duration * FPS))

    # 30-Theme rotating real moving live-action Pixabay HD scenes (6 distinct clips per 90s promo!)
    pixabay_key = os.getenv("PIXABAY_API_KEY", "").strip()
    slot = get_30min_slot(offset=10)
    queries_6 = []
    for k in range(6):
        th = THEMES_30[(slot + k * 5) % len(THEMES_30)]
        queries_6.append(th["queries"][0])

    live_clips = fetch_pixabay_videos_for_queries(
        queries_6, pixabay_key, OUT_DIR / "promo_media", "promo90", target_count=6, slot_seed=slot
    )
    bg_decoder = None
    if live_clips:
        bg_mp4 = OUT_DIR / "promo_live_bg.mp4"
        stitch_live_video_background(live_clips, duration, RW, RH, FPS, bg_mp4)
        bg_decoder = subprocess.Popen(
            ["ffmpeg", "-i", str(bg_mp4), "-f", "rawvideo", "-pix_fmt", "rgb24", "-v", "error", "pipe:1"],
            stdout=subprocess.PIPE,
        )
        img_bull = img_bear = img_inv = img_city = None
    else:
        live_photos = fetch_pixabay_photos_for_queries(
            queries_6, pixabay_key, OUT_DIR / "promo_media", "promo90", target_count=4, slot_seed=slot
        )
        if len(live_photos) >= 4:
            img_bull = load_cinematic_asset(str(live_photos[0]), ((6, 16, 32), (14, 40, 62)))
            img_bear = load_cinematic_asset(str(live_photos[1]), ((26, 10, 24), (48, 18, 38)))
            img_inv = load_cinematic_asset(str(live_photos[2]), ((8, 22, 42), (16, 44, 70)))
            img_city = load_cinematic_asset(str(live_photos[3]), ((6, 18, 34), (12, 44, 62)))
        else:
            img_bull = load_cinematic_asset("ad1_woman_1.jpg", ((6, 16, 32), (14, 40, 62)))
            img_bear = load_cinematic_asset("ad2_worker_2.jpg", ((26, 10, 24), (48, 18, 38)))
            img_inv = load_cinematic_asset("ad3_couple_1.jpg", ((8, 22, 42), (16, 44, 70)))
            img_city = load_cinematic_asset("ad1_woman_2.jpg", ((6, 18, 34), (12, 44, 62)))

    vignette = Image.new("RGBA", (RW, RH), (0, 0, 0, 0))
    vd = ImageDraw.Draw(vignette)
    for y in range(0, 250, 4):
        vd.rectangle([(0, y), (RW, y + 4)], fill=(4, 8, 18, int(170 * (1.0 - y / 250.0))))
    for y in range(RH - 500, RH, 4):
        vd.rectangle([(0, y), (RW, y + 4)], fill=(4, 8, 18, int(225 * ((y - (RH - 500)) / 500.0))))

    caption_chunks = group_caption_chunks(timings, words_per_chunk=3)
    mint = (18, 238, 166)
    cyan = (16, 206, 255)
    gold = (255, 206, 66)
    violet = (186, 120, 255)
    white = (248, 252, 255)
    muted = (192, 210, 232)
    dark = (6, 14, 26)

    # 6 fast-paced chapters for high viewer retention!
    c1 = duration * 0.14  # Hook
    c2 = duration * 0.40  # CapitalMoon Autonomous 24/7 Trading Deep Dive
    c3 = duration * 0.60  # Online Paper Simulation Before Real Money (Both Apps!)
    c4 = duration * 0.76  # CapitalMaker Yield, Quant & Rent Reclaim
    c5 = duration * 0.89  # Zero-KYC Security + 24/7 AI Support Bot
    xfade = 0.42

    # Warm dual-harmonic ambient studio synth bed under loudness-normalized voiceover
    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo", "-vcodec", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{RW}x{RH}", "-r", str(FPS), "-i", "pipe:0",
        "-i", str(audio_path),
        "-f", "lavfi", "-t", f"{duration:.2f}", "-i", "sine=frequency=110:sample_rate=44100",
        "-f", "lavfi", "-t", f"{duration:.2f}", "-i", "sine=frequency=165:sample_rate=44100",
        "-filter_complex",
        "[1:a]loudnorm=I=-15:TP=-1.5:LRA=11[v];"
        "[2:a]volume=0.018,tremolo=f=2.0:d=0.45[b1];"
        "[3:a]volume=0.010,tremolo=f=1.0:d=0.55[b2];"
        "[v][b1][b2]amix=inputs=3:duration=first:dropout_transition=1[aout]",
        "-map", "0:v:0", "-map", "[aout]",
        "-vf", "scale=1080:1920:flags=lanczos,format=yuv420p",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-r", str(FPS),
        "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart",
        str(out_mp4),
    ]

    proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)
    assert proc.stdin is not None
    frame_bytes = RW * RH * 3
    last_live = Image.new("RGB", (RW, RH), (8, 16, 32))
    try:
        for f_idx in range(total_frames):
            t = f_idx / FPS
            pulse = 0.5 + 0.5 * math.sin(t * 6.5)

            # Real moving live-action HD Pixabay video across all 6 chapters (or diverse photorealistic motion fallback)
            if bg_decoder is not None and bg_decoder.stdout is not None:
                raw = bg_decoder.stdout.read(frame_bytes)
                if len(raw) == frame_bytes:
                    last_live = Image.frombytes("RGB", (RW, RH), raw)
                bg = last_live
            elif t < c1:
                bg = sample_camera_frame(img_bull, t / max(c1, 0.1), "zoom_in")
                if t > c1 - xfade:
                    bg = Image.blend(bg, sample_camera_frame(img_city, 0.0, "pan_right"), (t - (c1 - xfade)) / xfade)
            elif t < c2:
                bg = sample_camera_frame(img_city, (t - c1) / max(c2 - c1, 0.1), "pan_right")
                if t > c2 - xfade:
                    bg = Image.blend(bg, sample_camera_frame(img_inv, 0.0, "zoom_in"), (t - (c2 - xfade)) / xfade)
            elif t < c3:
                bg = sample_camera_frame(img_inv, (t - c2) / max(c3 - c2, 0.1), "zoom_in")
                if t > c3 - xfade:
                    bg = Image.blend(bg, sample_camera_frame(img_bear, 0.0, "pan_right"), (t - (c3 - xfade)) / xfade)
            elif t < c4:
                bg = sample_camera_frame(img_bear, (t - c3) / max(c4 - c3, 0.1), "pan_right")
                if t > c4 - xfade:
                    bg = Image.blend(bg, sample_camera_frame(img_bull, 0.0, "zoom_out"), (t - (c4 - xfade)) / xfade)
            elif t < c5:
                bg = sample_camera_frame(img_bull, (t - c4) / max(c5 - c4, 0.1), "zoom_out")
                if t > c5 - xfade:
                    bg = Image.blend(bg, sample_camera_frame(img_city, 0.0, "zoom_in"), (t - (c5 - xfade)) / xfade)
            else:
                bg = sample_camera_frame(img_city, (t - c5) / max(duration - c5, 0.1), "zoom_in")

            canvas = bg.convert("RGBA")
            draw_fluid_ambient_particles(canvas, t, RW, RH, mint, cyan)
            canvas.alpha_composite(vignette)

            # Active speech check for audio-reactive equalizer
            active_chunk = None
            is_speaking = False
            for ch in caption_chunks:
                if ch[0]["start"] - 0.12 <= t <= ch[-1]["end"] + 0.25:
                    active_chunk = ch
                    for w_item in ch:
                        if w_item["start"] - 0.03 <= t <= w_item["end"] + 0.06:
                            is_speaking = True
                            break
                    break

            # Top retention progress bar + live broadcast header
            d = ImageDraw.Draw(canvas)
            prog_w = int(RW * (t / max(duration, 0.1)))
            d.rectangle([(0, 0), (RW, 8)], fill=(20, 34, 58, 220))
            d.rectangle([(0, 0), (prog_w, 8)], fill=mint)

            blend_glass_panel(canvas, (28, 28, RW - 28, 86), (8, 14, 28, 200), (*cyan, 220), radius=18, width=2)
            d = ImageDraw.Draw(canvas)
            dot_r = int(6 + pulse * 3)
            d.ellipse([(54 - dot_r, 57 - dot_r), (54 + dot_r, 57 + dot_r)], fill=mint)
            d.text((74, 44), "CAPITAL ALPHA  //  iOS & ANDROID SUITE", fill=white, font=load_font(20, bold=True))
            for b_i in range(7):
                bh = int((8 + abs(math.sin(t * 17.0 + b_i * 1.1)) * 20) if is_speaking else (4 + abs(math.sin(t * 3.0 + b_i)) * 4))
                bx = RW - 106 + b_i * 10
                d.rounded_rectangle([(bx, 57 - bh // 2), (bx + 6, 57 + bh // 2)], radius=3, fill=mint if b_i % 2 == 0 else gold)

            # ---------------- CHAPTER 1: SCROLL-STOPPING HOOK ----------------
            if t < c1:
                p = ease_out_cubic(min(1.0, t / 0.6))
                ys = int((1.0 - p) * -40)
                blend_glass_panel(canvas, (28, 108 + ys, RW - 28, 290 + ys), (8, 16, 30, 195), (*mint, 230), radius=24, width=3)
                d = ImageDraw.Draw(canvas)
                d.text((52, 126 + ys), "TRADE SOLANA AUTONOMOUSLY", fill=gold, font=load_font(26, bold=True))
                d.text((52, 164 + ys), "EVEN WHILE YOU SLEEP.", fill=white, font=load_font(42, bold=True))
                d.text((52, 228 + ys), "Test in Online Paper Simulation FIRST — Zero Risk!", fill=mint, font=load_font(22, bold=True))

            # ---------------- CHAPTER 2: CAPITALMOON DEEP DIVE (ANIMATED PHONE HUD) ----------------
            elif t < c2:
                lt = t - c1
                blend_glass_panel(canvas, (28, 106, RW - 28, 800), (8, 14, 28, 205), (*mint, 235), radius=28, width=3)
                d = ImageDraw.Draw(canvas)
                d.text((54, 124), "APP #1  •  AUTONOMOUS MEMECOIN TERMINAL", fill=gold, font=load_font(21, bold=True))
                d.text((54, 156), "CAPITALMOON", fill=white, font=load_font(54, bold=True))

                # Animated live breakout curve inside CapitalMoon HUD card
                gx0, gy0, gx1, gy1 = 56, 236, RW - 56, 445
                blend_glass_panel(canvas, (gx0 - 10, gy0 - 10, gx1 + 10, gy1 + 10), (6, 12, 24, 220), (*cyan, 180), radius=18, width=2)
                d = ImageDraw.Draw(canvas)
                draw_f = ease_out_cubic(min(1.0, lt / max((c2 - c1) * 0.45, 1.5)))
                steps = 22
                vis = max(2, int(round(draw_f * steps)))
                pts = []
                for i in range(vis):
                    frac = i / (steps - 1)
                    px = int(gx0 + (gx1 - gx0) * frac)
                    rise = (frac ** 1.45) * 0.72 + math.sin(i * 1.1) * 0.08
                    py = int(gy1 - 24 - rise * (gy1 - gy0 - 44))
                    pts.append((px, py))
                for i in range(len(pts) - 1):
                    d.line([pts[i], pts[i + 1]], fill=(10, 120, 90), width=10)
                    d.line([pts[i], pts[i + 1]], fill=mint, width=5)
                tx, ty = pts[-1]
                d.ellipse([(tx - 11, ty - 11), (tx + 11, ty + 11)], fill=white, outline=mint, width=4)
                d.text((gx0 + 8, gy0 + 4), "24/7 AUTO-TRADER LIVE RADAR SIMULATION", fill=cyan, font=load_font(17, bold=True))

                # Sliding CapitalMoon autonomous feature badges
                feats = [
                    ("1. PRE-RUN SPIKE RADAR", "Spots surging Solana memecoins early 24/7", cyan),
                    ("2. 8-VECTOR RUG SHIELD", "Blocks freeze traps, honeypots & thin rugs", mint),
                    ("3. AUTO SLEEP-TRADING", "Automated entry, trailing TP & stop-loss", gold),
                ]
                for idx, (ft, fsub, fcol) in enumerate(feats):
                    sp = ease_out_cubic(min(1.0, max(0.0, (lt - idx * 0.5) / 0.55)))
                    xs = int((1.0 - sp) * 240)
                    fy = 474 + idx * 102
                    blend_glass_panel(canvas, (50 + xs, fy, RW - 50 + xs, fy + 88), (10, 22, 42, 225), (*fcol, 220), radius=16, width=2)
                    d = ImageDraw.Draw(canvas)
                    d.text((74 + xs, fy + 14), ft, fill=fcol, font=load_font(23, bold=True))
                    d.text((74 + xs, fy + 48), fsub, fill=white, font=load_font(20, bold=False))

            # ---------------- CHAPTER 3: ONLINE PAPER SIMULATION BEFORE REAL MONEY ----------------
            elif t < c3:
                lt = t - c2
                blend_glass_panel(canvas, (28, 112, RW - 28, 560), (8, 18, 36, 210), (*cyan, 235), radius=28, width=3)
                d = ImageDraw.Draw(canvas)
                d.text((54, 134), "ZERO-RISK PRACTICE ON BOTH APPS", fill=gold, font=load_font(22, bold=True))
                d.text((54, 170), "ONLINE PAPER SIMULATION", fill=white, font=load_font(40, bold=True))
                d.text((54, 226), "Test live Solana markets BEFORE real SOL!", fill=cyan, font=load_font(24, bold=True))

                # Animated Mode Toggle Switch (PAPER SIM -> LIVE SOL VAULT)
                sw_phase = min(1.0, max(0.0, (lt - 2.0) / 1.5))
                blend_glass_panel(canvas, (54, 286, RW - 54, 378), (6, 12, 24, 230), (*mint, 220), radius=20, width=2)
                d = ImageDraw.Draw(canvas)
                half_w = (RW - 124) // 2
                pill_x = int(62 + sw_phase * (half_w + 8))
                d.rounded_rectangle([(pill_x, 294), (pill_x + half_w, 370)], radius=16, fill=mint if sw_phase > 0.5 else cyan)
                d.text((86, 318), "1. PAPER SIM ($0 RISK)", fill=dark if sw_phase <= 0.5 else muted, font=load_font(21, bold=True))
                d.text((62 + half_w + 30, 318), "2. LIVE SOL VAULT", fill=dark if sw_phase > 0.5 else muted, font=load_font(21, bold=True))

                d.text((54, 412), "• Real-time live DexScreener & Jupiter market prices", fill=white, font=load_font(22, bold=False))
                d.text((54, 452), "• Watch win rate, drawdown & trailing exits live", fill=white, font=load_font(22, bold=False))
                d.text((54, 492), "• Only switch to Live SOL when YOU feel ready", fill=mint, font=load_font(22, bold=True))

            # ---------------- CHAPTER 4: CAPITALMAKER YIELD, QUANT & RENT RECLAIM ----------------
            elif t < c4:
                lt = t - c3
                blend_glass_panel(canvas, (28, 112, RW - 28, 535), (12, 14, 32, 210), (*violet, 235), radius=28, width=3)
                d = ImageDraw.Draw(canvas)
                d.text((54, 134), "APP #2  •  SOLANA YIELD & QUANT VAULT", fill=violet, font=load_font(21, bold=True))
                d.text((54, 166), "CAPITALMAKER", fill=white, font=load_font(52, bold=True))

                engines = [
                    ("SOL LIQUID STAKING", "JitoSOL • jupSOL • mSOL native validator yield", mint),
                    ("JUPITER QUANT SWAPS", "Deep-liquidity leaders + <=1.4% spread shield", cyan),
                    ("1-TAP RENT RECLAIM", "Closes empty token accounts -> SOL back to you", gold),
                ]
                for i, (et, es, ec) in enumerate(engines):
                    sp = ease_out_cubic(min(1.0, max(0.0, (lt - i * 0.35) / 0.5)))
                    xs = int((1.0 - sp) * -220)
                    ey = 248 + i * 92
                    blend_glass_panel(canvas, (52 + xs, ey, RW - 52 + xs, ey + 78), (8, 14, 28, 225), (*ec, 215), radius=14, width=2)
                    d = ImageDraw.Draw(canvas)
                    d.text((74 + xs, ey + 12), et, fill=ec, font=load_font(22, bold=True))
                    d.text((74 + xs, ey + 43), es, fill=white, font=load_font(19, bold=False))

            # ---------------- CHAPTER 5: ZERO-KYC SECURITY + 24/7 AI SUPPORT ----------------
            elif t < c5:
                blend_glass_panel(canvas, (28, 118, RW - 28, 490), (8, 18, 34, 210), (*mint, 235), radius=28, width=3)
                d = ImageDraw.Draw(canvas)
                d.text((54, 142), "PRIVACY & SECURITY LOCKED DOWN", fill=gold, font=load_font(24, bold=True))
                d.text((54, 182), "ZERO EMAIL. ZERO KYC.", fill=white, font=load_font(44, bold=True))
                d.text((54, 248), "✅ Fingerprint Biometrics + 6-Digit Local PIN", fill=mint, font=load_font(24, bold=True))
                d.text((54, 292), "✅ Available on Apple iPhone (iOS) & Android", fill=white, font=load_font(23, bold=False))
                d.text((54, 336), "✅ Anti-Screenshot Shield (FLAG_SECURE)", fill=white, font=load_font(23, bold=False))
                d.text((54, 380), "🤖 Built-in 24/7 AI Support Bot inside BOTH apps!", fill=cyan, font=load_font(24, bold=True))
                d.text((54, 428), "Transparent 0.75% routing fee (lower than Phantom 0.85%)", fill=muted, font=load_font(20, bold=False))

            # ---------------- CHAPTER 6: EPIC CTA FINALE ----------------
            else:
                grow = int(pulse * 8)
                blend_glass_panel(canvas, (30, 140, RW - 30, 520), (8, 16, 30, 215), (*mint, 240), radius=30, width=3)
                d = ImageDraw.Draw(canvas)
                d.text((58, 174), "START IN PAPER MODE", fill=white, font=load_font(44, bold=True))
                d.text((58, 228), "FREE TODAY.", fill=mint, font=load_font(52, bold=True))
                d.text((58, 304), "Download CapitalMoon & CapitalMaker + Free 24/7 Alerts:", fill=muted, font=load_font(21, bold=True))
                d.rounded_rectangle([(58 - grow, 355 - grow // 2), (RW - 58 + grow, 476 + grow // 2)], radius=22, fill=mint)
                d.text((84, 374), "TAP LINK IN BIO  /  JOIN TELEGRAM", fill=dark, font=load_font(23, bold=True))
                d.text((84, 412), channel_link, fill=dark, font=load_font(36, bold=True))

            # ---------------- BIG BOLD 3-WORD KARAOKE CAPTIONS ----------------
            if active_chunk:
                cap_y = 955
                blend_glass_panel(canvas, (28, cap_y - 18, RW - 28, cap_y + 116), (6, 10, 20, 220), (*mint, 215), radius=22, width=2)
                d = ImageDraw.Draw(canvas)
                cap_font = load_font(38, bold=True)
                widths = [d.textbbox((0, 0), w["word"].upper() + " ", font=cap_font)[2] for w in active_chunk]
                if sum(widths) <= RW - 92:
                    cur_x = max(46, (RW - sum(widths)) // 2)
                    for item, w_px in zip(active_chunk, widths):
                        col = gold if item["start"] - 0.04 <= t <= item["end"] + 0.08 else white
                        d.text((cur_x + 2, cap_y + 24), item["word"].upper(), fill=(0, 0, 0), font=cap_font)
                        d.text((cur_x, cap_y + 22), item["word"].upper(), fill=col, font=cap_font)
                        cur_x += w_px
                else:
                    small_font = load_font(31, bold=True)
                    for r_i, row_w in enumerate([active_chunk[:2], active_chunk[2:]]):
                        if not row_w:
                            continue
                        rw_px = [d.textbbox((0, 0), w["word"].upper() + " ", font=small_font)[2] for w in row_w]
                        cur_x = max(46, (RW - sum(rw_px)) // 2)
                        ry = cap_y + 6 + r_i * 46
                        for item, w_px in zip(row_w, rw_px):
                            col = gold if item["start"] - 0.04 <= t <= item["end"] + 0.08 else white
                            d.text((cur_x + 2, ry + 2), item["word"].upper(), fill=(0, 0, 0), font=small_font)
                            d.text((cur_x, ry), item["word"].upper(), fill=col, font=small_font)
                            cur_x += w_px

            d = ImageDraw.Draw(canvas)
            d.text((34, RH - 50), f"{hub_url}  •  {channel_link}  •  DYOR / NOT FINANCIAL ADVICE", fill=muted, font=load_font(17, bold=True))
            proc.stdin.write(canvas.convert("RGB").tobytes())
    finally:
        proc.stdin.close()
        if bg_decoder is not None:
            bg_decoder.terminate()
            bg_decoder.wait()
        if proc.wait() != 0:
            raise RuntimeError("FFmpeg Director's Cut render failed")


def main() -> int:
    parser = argparse.ArgumentParser(description="Render CAPITAL ALPHA v2 Director's Cut Promo Video")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    raw_chan = normalize_channel_id(os.getenv("TELEGRAM_CHANNEL_ID", ""))
    handle = raw_chan.lstrip("@") if raw_chan.startswith("@") else "MysolAlpha99"
    channel_link = f"t.me/{handle}"
    hub_url = os.getenv("HUB_URL", "https://iridescent-baklava-d93abb.netlify.app").strip() or "https://iridescent-baklava-d93abb.netlify.app"
    slot = get_30min_slot(offset=10)
    rotating_host = get_rotating_voice(slot)
    voice = os.getenv("PROMO_VOICE", "").strip() or rotating_host["voice"]

    script = build_directors_cut_script(channel_link)
    print(f"[PROMO v3 LIVE-30x] Slot {slot + 1}/30 ({THEMES_30[slot]['label']}) | Voice: {voice} ({rotating_host['name']}) | Words: {len(script.split())}")
    if args.dry_run:
        return 0

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    timings = asyncio.run(synthesize_voiceover_with_timings(script, PROMO_AUDIO, voice=voice))
    dur = get_audio_duration_seconds(PROMO_AUDIO)
    if len(timings) < 10:
        timings = build_fallback_word_timings(script, dur)

    render_directors_cut_mp4(hub_url, channel_link, PROMO_AUDIO, timings, PROMO_VIDEO)
    print(f"[OK] Rendered v2 Director's Cut Promo Video ({dur:.1f}s): {PROMO_VIDEO}")

    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if bot_token and raw_chan:
        caption = (
            f"🎬 DIRECTOR'S CUT — CAPITALMOON & CAPITALMAKER\n\n"
            f"🌙 CapitalMoon: 24/7 Autonomous Memecoin Radar, 8-Vector Rug Shield & Auto Sleep-Trading\n"
            f"💎 CapitalMaker: Real Solana Staking Yield (JitoSOL/jupSOL), Jupiter Quant & 1-Tap SOL Rent Reclaim\n"
            f"🧪 Online Paper Simulation BEFORE Real Money on BOTH Apps!\n"
            f"🔐 Zero Email • Zero KYC • Biometrics + 6-Digit PIN + 24/7 AI Support\n\n"
            f"🌐 Get Free Apple iOS & Android Apps: {hub_url}\n"
            f"📡 Live 24/7 Radar: https://{channel_link}\n"
            f"(Always test in Paper Mode first — DYOR, not financial advice.)"
        )
        send_video_to_telegram(bot_token, raw_chan, PROMO_VIDEO, caption)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
