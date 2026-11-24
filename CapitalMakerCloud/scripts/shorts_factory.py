#!/usr/bin/env python3
"""
CapitalMaker Option #5 (v4 Cinematic 3D Human Storytelling Engine)
Produces true 24fps cinematic animated storytelling Shorts with real 3D-illustrated human presenters:
  - Scene 1: Full-bleed 3D Human Crypto Storyteller (Bull or Bear host) with smooth camera push-in,
    audio-reactive voice equalizer waveform & live glowing breakout pill
  - Scene 2: Smooth cross-dissolve to 3D New Investor Story Scene + live animated drawing price chart
    & floating glassmorphism liquidity/volume/buy-pressure telemetry
  - Scene 3: Cross-dissolve back to 3D Human Host reacting to UP (Bull) vs DOWN (Risk/Dip) playbook
  - Scene 4: Epic futuristic Solana City climax + pulsing CAPITAL ALPHA / Telegram CTA
  - Hormozi-style animated word-by-word karaoke captions synced to Microsoft Neural TTS (4 rotating voices!)
  - 10-minute schedule ready: 2h per-coin anti-repeat + 4h YouTube quota guard (max ~6 free uploads/day)
  - Auto-posts straight to Telegram WITH clickable Trojan SOL / Exchange USDT / Live Chart buttons!
"""

from __future__ import annotations

import argparse
import asyncio
import json
import math
import os
import subprocess
import sys
import time as _time
from pathlib import Path
from typing import Any

from signal_broadcaster import (
    SignalCandidate,
    build_inline_keyboard,
    discover_live_signals,
    format_compact_usd,
    format_price,
    http_json,
    normalize_channel_id,
    normalize_url,
)

SCRIPT_DIR = Path(__file__).resolve().parent
ASSETS_DIR = SCRIPT_DIR.parent / "assets"
OUT_DIR = Path("output")
STATE_DIR = Path("state")
SHORTS_COOLDOWN_FILE = STATE_DIR / "shorts_cooldowns.json"
LAST_YT_FILE = STATE_DIR / "last_yt_upload.txt"
AUDIO_PATH = OUT_DIR / "voiceover.mp3"
VIDEO_PATH = OUT_DIR / "latest_short.mp4"
META_PATH = OUT_DIR / "latest_short_meta.json"

SHORTS_COOLDOWN_SEC = 2 * 3600
YT_MIN_INTERVAL_SEC = 4 * 3600

# Render at 720x1280 @ 24fps for smooth fast animation, then Lanczos-upscale to crisp 1080x1920
RW, RH = 720, 1280
FPS = 24

NARRATORS = [
    {"name": "ALEX", "role": "SOLANA STORYTELLER", "voice": "en-US-AndrewNeural", "prefer_host": "host_bull.jpg"},
    {"name": "MAYA", "role": "ALPHA STRATEGIST", "voice": "en-US-AvaNeural", "prefer_host": "host_bear.jpg"},
    {"name": "LIAM", "role": "MARKET ANALYST", "voice": "en-GB-RyanNeural", "prefer_host": "host_bull.jpg"},
    {"name": "ZARA", "role": "ON-CHAIN REPORTER", "voice": "en-US-EmmaNeural", "prefer_host": "host_bear.jpg"},
]


def is_bullish_move(signal: SignalCandidate) -> bool:
    return signal.change_1h >= 0.0 or (signal.change_1h > -1.5 and signal.change_5m >= 0.5)


def select_narrator(signal: SignalCandidate, bullish: bool) -> dict[str, str]:
    idx = (int(_time.time() // 600) + sum(ord(c) for c in signal.symbol)) % len(NARRATORS)
    chosen = dict(NARRATORS[idx])
    # Match human host visual mood to UP vs DOWN while rotating voices every 10 mins!
    chosen["host_img"] = "host_bull.jpg" if bullish else "host_bear.jpg"
    return chosen


def load_shorts_cooldowns() -> dict[str, float]:
    now = _time.time()
    if not SHORTS_COOLDOWN_FILE.exists():
        return {}
    try:
        raw = json.loads(SHORTS_COOLDOWN_FILE.read_text(encoding="utf-8"))
        return {k: float(v) for k, v in raw.items() if float(v) > now}
    except Exception:
        return {}


def mark_short_cooldown(mint: str) -> None:
    data = load_shorts_cooldowns()
    data[mint] = _time.time() + SHORTS_COOLDOWN_SEC
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    SHORTS_COOLDOWN_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def can_upload_youtube_now() -> bool:
    if not LAST_YT_FILE.exists():
        return True
    try:
        return (_time.time() - float(LAST_YT_FILE.read_text(encoding="utf-8").strip())) >= YT_MIN_INTERVAL_SEC
    except Exception:
        return True


def mark_youtube_uploaded() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    LAST_YT_FILE.write_text(str(_time.time()), encoding="utf-8")


def build_storytelling_script(signal: SignalCandidate, channel_link: str, groq_key: str) -> str:
    bullish = is_bullish_move(signal)
    liq = format_compact_usd(signal.liquidity_usd)
    vol = format_compact_usd(signal.volume_24h_usd)

    if bullish:
        fallback = (
            f"Imagine checking Solana right now and seeing {signal.symbol} surge {signal.change_1h:+.1f} percent in a single hour "
            f"while most new investors completely missed the move. Here is the real story behind the chart. "
            f"Behind {signal.symbol} sits {liq} dollars in real liquidity, {vol} dollars in 24 hour volume, "
            f"and {signal.buy_pressure_pct} percent buyer dominance pushing momentum higher. "
            f"If buyers keep control, breakouts like this can accelerate fast — but if it pulls back down, smart traders protect capital instead of panicking. "
            f"Want live 24 7 Solana radar stories before the crowd arrives? Join our free Capital Alpha Telegram in the bio right now. "
            f"Always do your own research, not financial advice."
        )
    else:
        fallback = (
            f"Picture this: {signal.symbol} just dropped {signal.change_1h:.1f} percent on Solana in one hour, "
            f"and new investors are asking one question — is the run over, or is smart money watching a dip? "
            f"Let us look at the real on-chain story. The pool still holds {liq} dollars in liquidity with {vol} dollars in daily volume "
            f"and {signal.buy_pressure_pct} percent buyers stepping into the action. "
            f"If volume flips green, rebounds happen fast; if sellers stay in charge, patience saves your wallet. "
            f"Join our free 24 7 Capital Alpha Telegram in the bio so you never trade blind. Not financial advice."
        )

    if not groq_key.strip():
        return fallback

    direction = "SURGING UP" if bullish else "PULLING BACK DOWN"
    prompt = (
        f"Write a gripping, conversational 60-to-70 word storytelling narration script (like a charismatic human YouTube Shorts host "
        f"talking directly to new crypto investors) about Solana memecoin {signal.symbol} ({signal.name}), currently {direction}. "
        f"Real stats: price {format_price(signal.price_usd)}, 1h {signal.change_1h:+.1f}%, 24h {signal.change_24h:+.1f}%, "
        f"liquidity ${liq}, 24h volume ${vol}, buy pressure {signal.buy_pressure_pct}%, score {signal.signal_score}/99. "
        f"Story arc: (1) vivid 'Imagine/Picture this' hook about it going UP or DOWN, "
        f"(2) explain simply for new investors why liquidity & buyer flow tell the real story, "
        f"(3) contrast what happens if it goes UP vs dips DOWN, "
        f"(4) end inviting them to our free 24/7 Capital Alpha Telegram ({channel_link}) and say 'not financial advice'. "
        f"Natural spoken English only, no emojis, no stage directions, no guaranteed-profit promises."
    )
    try:
        resp = http_json(
            "https://api.groq.com/openai/v1/chat/completions",
            payload={
                "model": "llama-3.3-70b-versatile",
                "temperature": 0.6,
                "max_tokens": 180,
                "messages": [{"role": "user", "content": prompt}],
            },
            headers={"Authorization": f"Bearer {groq_key.strip()}"},
            timeout=14,
        )
        text = resp["choices"][0]["message"]["content"].strip().replace("\n", " ")
        return text if len(text.split()) >= 28 else fallback
    except Exception:
        return fallback


async def synthesize_voiceover_with_timings(
    script_text: str,
    out_mp3: Path,
    voice: str,
) -> list[dict[str, Any]]:
    import edge_tts  # type: ignore

    communicate = edge_tts.Communicate(script_text, voice=voice, rate="+7%")
    timings: list[dict[str, Any]] = []
    with out_mp3.open("wb") as audio_file:
        async for chunk in communicate.stream():
            ctype = chunk.get("type")
            if ctype == "audio":
                audio_file.write(chunk["data"])
            elif ctype == "WordBoundary":
                start_s = float(chunk.get("offset", 0)) / 10_000_000.0
                dur_s = float(chunk.get("duration", 0)) / 10_000_000.0
                word = str(chunk.get("text", "")).strip()
                if word:
                    timings.append({"word": word, "start": start_s, "end": start_s + max(dur_s, 0.12)})
    return timings


def get_audio_duration_seconds(audio_path: Path) -> float:
    out = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(audio_path)],
        text=True,
    ).strip()
    return max(10.0, float(out))


def build_fallback_word_timings(script_text: str, total_duration: float) -> list[dict[str, Any]]:
    words = [w for w in script_text.split() if w.strip()]
    if not words:
        return []
    step = (total_duration - 0.4) / len(words)
    return [{"word": w, "start": 0.15 + i * step, "end": 0.15 + (i + 1) * step} for i, w in enumerate(words)]


def group_caption_chunks(timings: list[dict[str, Any]], words_per_chunk: int = 4) -> list[list[dict[str, Any]]]:
    return [timings[i : i + words_per_chunk] for i in range(0, len(timings), words_per_chunk)]


_FONT_CACHE: dict[tuple[int, bool], Any] = {}


def load_font(size: int, bold: bool = False):
    key = (size, bold)
    if key in _FONT_CACHE:
        return _FONT_CACHE[key]
    from PIL import ImageFont  # type: ignore

    candidates = (
        [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "C:/Windows/Fonts/segoeuib.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
        ]
        if bold
        else [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "C:/Windows/Fonts/segoeui.ttf",
            "C:/Windows/Fonts/arial.ttf",
        ]
    )
    font = None
    for p in candidates:
        if Path(p).exists():
            font = ImageFont.truetype(p, size=size)
            break
    font = font or ImageFont.load_default()
    _FONT_CACHE[key] = font
    return font


def ease_out_cubic(x: float) -> float:
    x = max(0.0, min(1.0, x))
    return 1.0 - (1.0 - x) ** 3


def build_price_curve(signal: SignalCandidate, count: int = 20) -> list[float]:
    now_p = max(signal.price_usd, 1e-9)

    def back(pct: float) -> float:
        return now_p / max(1.0 + pct / 100.0, 0.15)

    anchors = [back(signal.change_24h), back(signal.change_24h * 0.6), back(signal.change_1h), back(signal.change_5m), now_p]
    pts: list[float] = []
    for i in range(count):
        pos = (i / max(count - 1, 1)) * (len(anchors) - 1)
        lo_i = int(math.floor(pos))
        hi_i = min(len(anchors) - 1, lo_i + 1)
        frac = pos - lo_i
        base_val = anchors[lo_i] + (anchors[hi_i] - anchors[lo_i]) * frac
        wave = math.sin(i * 1.45) * 0.015 * now_p * math.sin((i / max(count - 1, 1)) * math.pi)
        pts.append(max(1e-9, base_val + wave))
    return pts


def load_cinematic_asset(filename: str, fallback_colors: tuple[tuple[int, int, int], tuple[int, int, int]]) -> Any:
    """Loads a 9:16 3D storytelling illustration scaled slightly oversized (840x1493) for silky Ken-Burns camera pans."""
    from PIL import Image, ImageDraw, ImageOps  # type: ignore

    target_w, target_h = int(RW * 1.16), int(RH * 1.16)
    path = ASSETS_DIR / filename
    if path.exists():
        img = Image.open(path).convert("RGB")
        return ImageOps.fit(img, (target_w, target_h), method=Image.Resampling.LANCZOS)

    # Graceful fallback gradient if assets folder wasn't uploaded yet
    bg = Image.new("RGB", (target_w, target_h), fallback_colors[0])
    dr = ImageDraw.Draw(bg)
    c0, c1 = fallback_colors
    for y in range(0, target_h, 6):
        t = y / target_h
        col = (int(c0[0] + (c1[0] - c0[0]) * t), int(c0[1] + (c1[1] - c0[1]) * t), int(c0[2] + (c1[2] - c0[2]) * t))
        dr.rectangle([(0, y), (target_w, y + 6)], fill=col)
    return bg


def sample_camera_frame(oversized_img: Any, progress: float, mode: str = "zoom_in") -> Any:
    """Extracts a smooth 720x1280 cinematic camera crop (push-in zoom, pan-right, or subtle breathing)."""
    from PIL import Image  # type: ignore

    ow, oh = oversized_img.size
    p = max(0.0, min(1.0, progress))
    if mode == "zoom_in":
        scale = 1.0 + 0.11 * p
        cw, ch = int(ow / scale), int(oh / scale)
        x0 = (ow - cw) // 2
        y0 = int((oh - ch) * (0.36 + 0.04 * p))
    elif mode == "pan_right":
        cw, ch = int(ow / 1.08), int(oh / 1.08)
        x0 = int((ow - cw) * p)
        y0 = (oh - ch) // 2
    else:  # zoom_out
        scale = 1.11 - 0.10 * p
        cw, ch = int(ow / scale), int(oh / scale)
        x0 = (ow - cw) // 2
        y0 = (oh - ch) // 2
    cropped = oversized_img.crop((x0, y0, x0 + cw, y0 + ch))
    return cropped.resize((RW, RH), Image.Resampling.BILINEAR)


def blend_glass_panel(base_rgba: Any, box: tuple[int, int, int, int], fill_rgba: tuple[int, int, int, int], outline_rgba: tuple[int, int, int, int], radius: int = 22, width: int = 2) -> None:
    from PIL import Image, ImageDraw  # type: ignore

    overlay = Image.new("RGBA", base_rgba.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.rounded_rectangle([(box[0], box[1]), (box[2], box[3])], radius=radius, fill=fill_rgba, outline=outline_rgba, width=width)
    base_rgba.alpha_composite(overlay)


def render_storytelling_mp4(
    signal: SignalCandidate,
    brand: str,
    channel_link: str,
    narrator: dict[str, str],
    audio_path: Path,
    timings: list[dict[str, Any]],
    out_mp4: Path,
) -> None:
    from PIL import Image, ImageDraw  # type: ignore

    duration = get_audio_duration_seconds(audio_path)
    total_frames = int(math.ceil(duration * FPS))
    bullish = is_bullish_move(signal)

    primary = (18, 236, 164) if bullish else (255, 78, 110)
    secondary = (16, 204, 255) if bullish else (255, 198, 64)
    gold = (255, 206, 68)
    mint = (18, 236, 164)
    crimson = (255, 78, 110)
    white = (248, 252, 255)
    muted = (196, 212, 232)

    # Load all 4 cinematic 3D storytelling scenes
    img_host = load_cinematic_asset(narrator["host_img"], ((8, 20, 38), (14, 42, 64)) if bullish else ((30, 10, 20), (54, 16, 30)))
    img_investor = load_cinematic_asset("scene_investor.jpg", ((10, 18, 36), (18, 38, 66)))
    img_host_alt = load_cinematic_asset("host_bear.jpg" if bullish else "host_bull.jpg", ((24, 12, 26), (48, 20, 40)))
    img_finale = load_cinematic_asset("scene_finale.jpg", ((6, 16, 32), (12, 40, 58)))

    # Pre-build top & bottom dark cinema vignette gradient (makes overlays & captions pop crisply over 3D art!)
    vignette = Image.new("RGBA", (RW, RH), (0, 0, 0, 0))
    vd = ImageDraw.Draw(vignette)
    for y in range(0, 260, 4):
        alpha = int(175 * (1.0 - y / 260.0))
        vd.rectangle([(0, y), (RW, y + 4)], fill=(4, 8, 18, alpha))
    for y in range(RH - 520, RH, 4):
        alpha = int(215 * ((y - (RH - 520)) / 520.0))
        vd.rectangle([(0, y), (RW, y + 4)], fill=(4, 8, 18, alpha))

    curve = build_price_curve(signal, count=20)
    c_min, c_max = min(curve), max(curve)
    c_span = max(c_max - c_min, c_max * 0.02, 1e-9)

    caption_chunks = group_caption_chunks(timings, words_per_chunk=4)
    ticker_text = (
        f"  {brand} LIVE  •  ${signal.symbol} {format_price(signal.price_usd)} ({signal.change_1h:+.1f}% 1H)  •  "
        f"LIQ ${format_compact_usd(signal.liquidity_usd)}  •  VOL ${format_compact_usd(signal.volume_24h_usd)}  •  "
        f"FREE ALERTS: {channel_link}  •  "
    ) * 3

    t1 = duration * 0.28
    t2 = duration * 0.58
    t3 = duration * 0.82
    xfade = 0.45  # smooth 0.45s cross-dissolve between storytelling scenes!

    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo", "-vcodec", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{RW}x{RH}", "-r", str(FPS), "-i", "pipe:0",
        "-i", str(audio_path),
        "-f", "lavfi", "-t", f"{duration:.2f}", "-i", "sine=frequency=98:sample_rate=44100",
        "-filter_complex",
        "[1:a]loudnorm=I=-15:TP=-1.5:LRA=11[v];[2:a]volume=0.024,tremolo=f=1.8:d=0.4[bed];[v][bed]amix=inputs=2:duration=first:dropout_transition=1[aout]",
        "-map", "0:v:0", "-map", "[aout]",
        "-vf", "scale=1080:1920:flags=lanczos,format=yuv420p",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-r", str(FPS),
        "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart",
        str(out_mp4),
    ]

    proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)
    assert proc.stdin is not None

    try:
        for f_idx in range(total_frames):
            t = f_idx / FPS
            pulse = 0.5 + 0.5 * math.sin(t * 6.0)

            # Determine active storytelling scene + smooth cross-dissolve transition!
            if t < t1:
                scene_rgb = sample_camera_frame(img_host, t / max(t1, 0.1), mode="zoom_in")
                if t > t1 - xfade:
                    nxt = sample_camera_frame(img_investor, 0.0, mode="pan_right")
                    scene_rgb = Image.blend(scene_rgb, nxt, (t - (t1 - xfade)) / xfade)
            elif t < t2:
                scene_rgb = sample_camera_frame(img_investor, (t - t1) / max(t2 - t1, 0.1), mode="pan_right")
                if t > t2 - xfade:
                    nxt = sample_camera_frame(img_host_alt, 0.0, mode="zoom_in")
                    scene_rgb = Image.blend(scene_rgb, nxt, (t - (t2 - xfade)) / xfade)
            elif t < t3:
                scene_rgb = sample_camera_frame(img_host_alt, (t - t2) / max(t3 - t2, 0.1), mode="zoom_in")
                if t > t3 - xfade:
                    nxt = sample_camera_frame(img_finale, 0.0, mode="zoom_out")
                    scene_rgb = Image.blend(scene_rgb, nxt, (t - (t3 - xfade)) / xfade)
            else:
                scene_rgb = sample_camera_frame(img_finale, (t - t3) / max(duration - t3, 0.1), mode="zoom_out")

            canvas = scene_rgb.convert("RGBA")
            canvas.alpha_composite(vignette)

            # Active speech check for audio-reactive voice equalizer bars
            active_chunk = None
            is_speaking_now = False
            for chunk in caption_chunks:
                if chunk[0]["start"] - 0.12 <= t <= chunk[-1]["end"] + 0.25:
                    active_chunk = chunk
                    for w_item in chunk:
                        if w_item["start"] - 0.03 <= t <= w_item["end"] + 0.06:
                            is_speaking_now = True
                            break
                    break

            # Top broadcast header pill (sleek translucent glass over 3D scene)
            blend_glass_panel(canvas, (30, 36, RW - 30, 96), (8, 14, 28, 195), (*primary, 220), radius=18, width=2)
            d = ImageDraw.Draw(canvas)
            dot_r = int(7 + pulse * 3)
            d.ellipse([(58 - dot_r, 66 - dot_r), (58 + dot_r, 66 + dot_r)], fill=primary)
            d.text((78, 53), f"{brand}  •  {narrator['name']} ({narrator['role']})", fill=white, font=load_font(19, bold=True))

            # Audio-reactive live voice waveform bars (top right inside header!)
            for b_i in range(7):
                bh = int((8 + abs(math.sin(t * 16.0 + b_i * 1.1)) * 22) if is_speaking_now else (4 + abs(math.sin(t * 3.0 + b_i)) * 4))
                bx = RW - 110 + b_i * 10
                d.rounded_rectangle([(bx, 66 - bh // 2), (bx + 6, 66 + bh // 2)], radius=3, fill=primary if b_i % 2 == 0 else gold)

            # ---------------- SCENE-SPECIFIC FLOATING CINEMATIC OVERLAYS ----------------
            if t < t1:
                # Scene 1: Keep 3D human host front-and-center! Sleek floating coin badge at top & bottom-left
                prog = ease_out_cubic(min(1.0, t / 0.6))
                y_shift = int((1.0 - prog) * -40)
                blend_glass_panel(canvas, (30, 112 + y_shift, RW - 30, 232 + y_shift), (8, 16, 30, 185), (*primary, 210), radius=22, width=2)
                d = ImageDraw.Draw(canvas)
                tag = "🚀 BULLISH BREAKOUT STORY" if bullish else "📉 MEMECOIN DIP STORY"
                d.text((52, 124 + y_shift), tag, fill=gold, font=load_font(20, bold=True))
                d.text((52, 154 + y_shift), f"${signal.symbol}", fill=white, font=load_font(56, bold=True))
                arrow = "▲" if bullish else "▼"
                d.text((385, 134 + y_shift), f"{arrow} {signal.change_1h:+.1f}% 1H", fill=primary, font=load_font(34, bold=True))
                d.text((385, 182 + y_shift), f"{format_price(signal.price_usd)} • {signal.signal_score}/99", fill=muted, font=load_font(22, bold=True))

            elif t < t2:
                # Scene 2: 3D New Investor Story + translucent animated drawing price chart + metrics
                local_t = t - t1
                blend_glass_panel(canvas, (30, 116, RW - 30, 446), (8, 15, 30, 195), (*secondary, 215), radius=24, width=2)
                d = ImageDraw.Draw(canvas)
                d.text((54, 132), f"THE ON-CHAIN STORY: ${signal.symbol}", fill=secondary, font=load_font(24, bold=True))

                # Animated live drawing chart inside glass panel
                gx0, gy0, gx1, gy1 = 56, 178, RW - 56, 404
                for gstep in range(4):
                    gy = int(gy0 + (gy1 - gy0) * (gstep / 3.0))
                    d.line([(gx0, gy), (gx1, gy)], fill=(45, 72, 108, 130), width=1)
                draw_frac = ease_out_cubic(min(1.0, local_t / max((t2 - t1) * 0.65, 1.2)))
                vis_n = max(2, int(round(draw_frac * len(curve))))
                coords = [
                    (int(gx0 + (gx1 - gx0) * (i / max(len(curve) - 1, 1))), int(gy1 - ((curve[i] - c_min) / c_span) * (gy1 - gy0)))
                    for i in range(vis_n)
                ]
                for i in range(len(coords) - 1):
                    seg_col = mint if coords[i + 1][1] <= coords[i][1] else crimson
                    d.line([coords[i], coords[i + 1]], fill=seg_col, width=6)
                tx, ty = coords[-1]
                d.ellipse([(tx - 11, ty - 11), (tx + 11, ty + 11)], fill=white, outline=primary, width=4)

                # Floating glass stat pills
                pills = [
                    ("LIQUIDITY", f"${format_compact_usd(signal.liquidity_usd)}", mint),
                    ("24H VOLUME", f"${format_compact_usd(signal.volume_24h_usd)}", gold),
                    ("BUY FLOW", f"{signal.buy_pressure_pct}% BUYS", secondary),
                ]
                pw = (RW - 84) // 3
                for idx, (lbl, val, col) in enumerate(pills):
                    px0 = 30 + idx * (pw + 12)
                    blend_glass_panel(canvas, (px0, 466, px0 + pw, 560), (8, 15, 30, 200), (*col, 210), radius=16, width=2)
                    d = ImageDraw.Draw(canvas)
                    d.text((px0 + 16, 480), lbl, fill=muted, font=load_font(16, bold=True))
                    d.text((px0 + 16, 508), val, fill=col, font=load_font(26, bold=True))

            elif t < t3:
                # Scene 3: 3D Host + Floating UP vs DOWN Split Playbook Cards
                local_t = t - t2
                up_x = int((1.0 - ease_out_cubic(min(1.0, local_t / 0.5))) * -240)
                dn_x = int((1.0 - ease_out_cubic(min(1.0, max(0.0, (local_t - 0.45) / 0.5)))) * 240)

                blend_glass_panel(canvas, (30 + up_x, 120, RW - 30 + up_x, 265), (8, 38, 30, 205), (*mint, 235), radius=20, width=3)
                d = ImageDraw.Draw(canvas)
                d.text((54 + up_x, 138), f"▲ IF ${signal.symbol} BREAKS HIGHER", fill=mint, font=load_font(25, bold=True))
                d.text((54 + up_x, 178), f"• Strong ${format_compact_usd(signal.volume_24h_usd)} volume + {signal.buy_pressure_pct}% buys fuel momentum", fill=white, font=load_font(20, bold=False))
                d.text((54 + up_x, 214), "• Smart traders scale profits on spikes, never chase blind", fill=muted, font=load_font(19, bold=False))

                blend_glass_panel(canvas, (30 + dn_x, 285, RW - 30 + dn_x, 430), (46, 12, 22, 205), (*crimson, 235), radius=20, width=3)
                d = ImageDraw.Draw(canvas)
                d.text((54 + dn_x, 303), f"▼ IF ${signal.symbol} DIPS LOWER", fill=crimson, font=load_font(25, bold=True))
                d.text((54 + dn_x, 343), f"• Watch ${format_compact_usd(signal.liquidity_usd)} pool support & buyer bounce first", fill=white, font=load_font(20, bold=False))
                d.text((54 + dn_x, 379), "• Protect your SOL — never risk money you cannot lose", fill=muted, font=load_font(19, bold=False))

            else:
                # Scene 4: Epic Cyberpunk-Solana Climax + Pulsing Telegram CTA
                grow = int(pulse * 8)
                blend_glass_panel(canvas, (36, 170, RW - 36, 510), (8, 16, 30, 205), (*mint, 230), radius=28, width=3)
                d = ImageDraw.Draw(canvas)
                d.text((64, 205), "NEVER MISS THE NEXT", fill=white, font=load_font(44, bold=True))
                d.text((64, 260), "SOLANA STORY.", fill=mint, font=load_font(48, bold=True))
                d.text((64, 332), "24/7 Live Alerts • Free iPhone & Android Apps", fill=muted, font=load_font(22, bold=True))

                d.rounded_rectangle([(64 - grow, 385 - grow // 2), (RW - 64 + grow, 482 + grow // 2)], radius=20, fill=mint)
                d.text((92, 400), "JOIN FREE TELEGRAM RADAR", fill=(6, 14, 24), font=load_font(24, bold=True))
                d.text((92, 434), channel_link, fill=(6, 14, 24), font=load_font(34, bold=True))

            # ---------------- VIRAL HORMOZI KARAOKE CAPTIONS (BOTTOM-CENTER) ----------------
            if active_chunk:
                cap_y = 955
                blend_glass_panel(canvas, (30, cap_y - 20, RW - 30, cap_y + 132), (6, 10, 20, 210), (*primary, 210), radius=22, width=2)
                d = ImageDraw.Draw(canvas)
                cap_font = load_font(34, bold=True)
                for row_idx, row_words in enumerate([active_chunk[:2], active_chunk[2:]]):
                    if not row_words:
                        continue
                    widths = []
                    total_w = 0
                    for item in row_words:
                        bbox = d.textbbox((0, 0), item["word"].upper() + " ", font=cap_font)
                        w_px = bbox[2] - bbox[0]
                        widths.append(w_px)
                        total_w += w_px
                    cur_x = max(50, (RW - total_w) // 2)
                    ry = cap_y + row_idx * 52
                    for item, w_px in zip(row_words, widths):
                        txt = item["word"].upper()
                        is_active = item["start"] - 0.04 <= t <= item["end"] + 0.08
                        col = gold if is_active else white
                        d.text((cur_x + 2, ry + 2), txt, fill=(0, 0, 0), font=cap_font)
                        d.text((cur_x, ry), txt, fill=col, font=cap_font)
                        cur_x += w_px

            # ---------------- SCROLLING LIVE BREAKING TICKER ----------------
            d = ImageDraw.Draw(canvas)
            d.rectangle([(0, RH - 116), (RW, RH - 62)], fill=(6, 12, 24, 235))
            d.line([(0, RH - 116), (RW, RH - 116)], fill=primary, width=2)
            scroll_x = -int((t * 145) % 1800)
            d.text((scroll_x, RH - 101), ticker_text, fill=primary, font=load_font(21, bold=True))
            d.text((38, RH - 42), f"FREE ALERTS: {channel_link}  •  DYOR / NOT FINANCIAL ADVICE", fill=muted, font=load_font(17, bold=True))

            proc.stdin.write(canvas.convert("RGB").tobytes())
    finally:
        proc.stdin.close()
        ret = proc.wait()
        if ret != 0:
            raise RuntimeError(f"FFmpeg storytelling render failed with code {ret}")


def send_video_to_telegram(bot_token: str, chat_id: str, video_path: Path, caption: str, reply_markup: dict[str, Any] | None = None) -> None:
    import requests  # type: ignore

    url = f"https://api.telegram.org/bot{bot_token}/sendVideo"
    form_data: dict[str, str] = {"chat_id": chat_id, "caption": caption[:1020], "supports_streaming": "true"}
    if reply_markup:
        form_data["reply_markup"] = json.dumps(reply_markup)
    with video_path.open("rb") as fh:
        resp = requests.post(url, data=form_data, files={"video": (video_path.name, fh, "video/mp4")}, timeout=90)
    data = resp.json()
    if not resp.ok or not data.get("ok"):
        raise RuntimeError(f"Telegram sendVideo failed: {data}")
    print(f"[OK] Delivered 3D Human Storytelling Short + Trade Buttons to Telegram {chat_id}!")


def upload_to_youtube_shorts(video_path: Path, title: str, description: str) -> str | None:
    client_id = os.getenv("YOUTUBE_CLIENT_ID", "").strip()
    client_secret = os.getenv("YOUTUBE_CLIENT_SECRET", "").strip()
    refresh_token = os.getenv("YOUTUBE_REFRESH_TOKEN", "").strip()
    if not (client_id and client_secret and refresh_token):
        print("[INFO] YouTube OAuth secrets not set — skipping direct YouTube upload.")
        return None

    from google.oauth2.credentials import Credentials  # type: ignore
    from googleapiclient.discovery import build  # type: ignore
    from googleapiclient.http import MediaFileUpload  # type: ignore

    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=["https://www.googleapis.com/auth/youtube.upload"],
    )
    youtube = build("youtube", "v3", credentials=creds)
    body = {
        "snippet": {
            "title": title[:95],
            "description": description[:4500],
            "tags": ["Solana", "Memecoin", "CryptoStory", "Shorts", "SolanaMemecoins", "CryptoTrading"],
            "categoryId": "28",
        },
        "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False},
    }
    media = MediaFileUpload(str(video_path), chunksize=-1, resumable=True, mimetype="video/mp4")
    resp = youtube.videos().insert(part="snippet,status", body=body, media_body=media).execute()
    vid_id = resp.get("id")
    print(f"[OK] Uploaded Storytelling YouTube Short: https://youtube.com/shorts/{vid_id}")
    return vid_id


def main() -> int:
    parser = argparse.ArgumentParser(description="CapitalMaker #5 v4 Cinematic 3D Human Storytelling Shorts Factory")
    parser.add_argument("--dry-run", action="store_true", help="Verify assets, signal & storytelling script without FFmpeg")
    args = parser.parse_args()

    brand = os.getenv("BRAND_NAME", "CAPITAL ALPHA").strip() or "CAPITAL ALPHA"
    raw_channel = normalize_channel_id(os.getenv("TELEGRAM_CHANNEL_ID", ""))
    channel_handle = raw_channel.lstrip("@") if raw_channel.startswith("@") else ""
    channel_link = f"t.me/{channel_handle}" if channel_handle else "t.me/MysolAlpha99"
    groq_key = os.getenv("GROQ_API_KEY", "").strip()
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    video_target_chat = normalize_channel_id(os.getenv("TELEGRAM_VIDEO_CHAT_ID", "")) or raw_channel
    sol_bot_url = normalize_url(os.getenv("SOLANA_BOT_REF_URL", ""))
    exchange_url = normalize_url(os.getenv("EXCHANGE_REF_URL", ""))

    signals = discover_live_signals()
    if not signals:
        print("[INFO] No live Solana memecoin signal found right now.")
        return 0
    recent_cd = load_shorts_cooldowns()
    fresh_pool = [s for s in signals if s.mint not in recent_cd] or signals
    top = max(fresh_pool[:6], key=lambda s: abs(s.change_1h) + (15.0 if s.is_boosted else 0.0))

    bullish = is_bullish_move(top)
    narrator = select_narrator(top, bullish)
    direction_tag = "BREAKOUT STORY" if bullish else "DIP WATCH STORY"
    script = build_storytelling_script(top, channel_link, groq_key)
    headline_move = f"{top.change_1h:+.1f}% 1H"
    title = f"${top.symbol} Solana {direction_tag} ({headline_move}) 🚨 #Shorts #Solana"
    caption = (
        f"{'🚀' if bullish else '📉'} ${top.symbol} — {direction_tag} ({top.signal_score}/99)\n"
        f"💵 {format_price(top.price_usd)} | 📈 1H: {headline_move} | 💧 Liq: ${format_compact_usd(top.liquidity_usd)} | ⚖️ {top.buy_pressure_pct}% Buys\n\n"
        f"⚡ Free 24/7 Live Solana Radar + Apple iOS & Android Apps:\n"
        f"👉 https://{channel_link}\n\n"
        f"Would you buy this move or wait? Comment below 👇\n"
        f"#Solana #Memecoin #Crypto #Shorts #SOL\n"
        f"(Automated market data only — DYOR, not financial advice.)"
    )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    META_PATH.write_text(
        json.dumps({"symbol": top.symbol, "narrator": narrator["name"], "title": title, "caption": caption, "script": script}, indent=2),
        encoding="utf-8",
    )

    assets_present = [f for f in ("host_bull.jpg", "host_bear.jpg", "scene_investor.jpg", "scene_finale.jpg") if (ASSETS_DIR / f).exists()]
    print(f"[SHORTS v4 STORY] Assets found ({len(assets_present)}/4): {assets_present}")
    print(f"[SHORTS v4 STORY] Host: {narrator['name']} ({narrator['voice']}) | Coin: ${top.symbol} ({direction_tag})")
    print(f"[SHORTS v4 STORY] Script: {script}")
    if args.dry_run:
        return 0

    timings = asyncio.run(synthesize_voiceover_with_timings(script, AUDIO_PATH, voice=narrator["voice"]))
    duration = get_audio_duration_seconds(AUDIO_PATH)
    if len(timings) < 5:
        timings = build_fallback_word_timings(script, duration)

    render_storytelling_mp4(top, brand, channel_link, narrator, AUDIO_PATH, timings, VIDEO_PATH)
    print(f"[OK] Rendered v4 3D Human Storytelling Short: {VIDEO_PATH} ({VIDEO_PATH.stat().st_size} bytes)")

    if bot_token and video_target_chat:
        try:
            markup = build_inline_keyboard(top, sol_bot_url, exchange_url)
            send_video_to_telegram(bot_token, video_target_chat, VIDEO_PATH, caption, reply_markup=markup)
            mark_short_cooldown(top.mint)
        except Exception as exc:
            print(f"[WARN] Telegram video delivery skipped: {exc}", file=sys.stderr)

    if can_upload_youtube_now():
        vid_id = upload_to_youtube_shorts(VIDEO_PATH, title, caption)
        if vid_id:
            mark_youtube_uploaded()
    else:
        print("[INFO] YouTube 4h quota shield active — delivered to Telegram!")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
