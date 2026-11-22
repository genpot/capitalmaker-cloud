#!/usr/bin/env python3
"""
CapitalMaker Option #5 — Autonomous Faceless Short-Form Video Traffic Feeder.
Turns the hottest live Solana breakout into a crisp 1080x1920 vertical YouTube Short / TikTok / Reel:
  1) Live DexScreener Solana breakout data (reuses signal_broadcaster.py)
  2) Punchy 20-25s narration script (Groq Llama 3.3 70B if set, else built-in quant script)
  3) Free Microsoft Neural Voiceover via edge-tts (zero API key needed)
  4) Crisp 1080x1920 HUD frames rendered with Pillow + stitched with FFmpeg
  5) Delivers finished MP4 directly to your Telegram + optionally auto-uploads to YouTube Shorts!
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

from signal_broadcaster import (
    SignalCandidate,
    discover_live_signals,
    format_compact_usd,
    format_price,
    http_json,
    normalize_channel_id,
)

OUT_DIR = Path("output")
SLIDES_DIR = OUT_DIR / "slides"
AUDIO_PATH = OUT_DIR / "voiceover.mp3"
VIDEO_PATH = OUT_DIR / "latest_short.mp4"
META_PATH = OUT_DIR / "latest_short_meta.json"


def build_narration_script(signal: SignalCandidate, channel_link: str, groq_key: str) -> str:
    if signal.change_1h >= 1.0:
        move_phrase = f"just surged {signal.change_1h:+.1f} percent in the last hour"
    elif signal.change_5m >= 0.5:
        move_phrase = f"just jumped {signal.change_5m:+.1f} percent in the last 5 minutes"
    else:
        move_phrase = "is seeing strong Solana DEX buyer flow right now"
    fallback = (
        f"Solana breakout alert! {signal.symbol} {move_phrase}, "
        f"backed by {format_compact_usd(signal.liquidity_usd)} dollars in liquidity and {format_compact_usd(signal.volume_24h_usd)} "
        f"dollars in 24 hour volume. Buyer pressure is sitting at {signal.buy_pressure_pct} percent with a quant score of "
        f"{signal.signal_score} out of 99. Want live 24 7 Solana breakout alerts before the crowd? "
        f"Join our free Telegram radar in the pinned comment and bio right now. Always do your own research."
    )
    if not groq_key.strip():
        return fallback
    prompt = (
        f"Write a high-energy 45-to-55 word voiceover script for a 22-second vertical crypto YouTube Short about "
        f"Solana token {signal.symbol} ({signal.name}): price {format_price(signal.price_usd)}, "
        f"1-hour move {signal.change_1h:+.1f}%, 24-hour move {signal.change_24h:+.1f}%, "
        f"liquidity ${format_compact_usd(signal.liquidity_usd)}, 24h volume ${format_compact_usd(signal.volume_24h_usd)}, "
        f"buy pressure {signal.buy_pressure_pct}%, score {signal.signal_score}/99. "
        f"End with a quick call-to-action to join our free 24/7 Telegram alerts channel ({channel_link}) in bio/pinned comment, "
        f"and say not financial advice. Plain spoken English only, no emojis, no stage directions."
    )
    try:
        resp = http_json(
            "https://api.groq.com/openai/v1/chat/completions",
            payload={
                "model": "llama-3.3-70b-versatile",
                "temperature": 0.45,
                "max_tokens": 130,
                "messages": [{"role": "user", "content": prompt}],
            },
            headers={"Authorization": f"Bearer {groq_key.strip()}"},
            timeout=12,
        )
        text = resp["choices"][0]["message"]["content"].strip().replace("\n", " ")
        return text if len(text.split()) >= 20 else fallback
    except Exception:
        return fallback


async def synthesize_voiceover(script_text: str, out_mp3: Path, voice: str = "en-US-AndrewNeural") -> None:
    import edge_tts  # type: ignore

    communicate = edge_tts.Communicate(script_text, voice=voice, rate="+8%")
    await communicate.save(str(out_mp3))


def get_audio_duration_seconds(audio_path: Path) -> float:
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(audio_path),
    ]
    out = subprocess.check_output(cmd, text=True).strip()
    return max(8.0, float(out))


def load_font(size: int, bold: bool = False):
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
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


def render_hud_slides(signal: SignalCandidate, brand: str, channel_link: str) -> list[Path]:
    from PIL import Image, ImageDraw  # type: ignore

    SLIDES_DIR.mkdir(parents=True, exist_ok=True)
    w, h = 1080, 1920
    bg_top = (10, 16, 30)
    bg_bot = (18, 32, 58)
    cyan = (14, 197, 255)
    mint = (16, 224, 154)
    gold = (255, 196, 61)
    crimson = (255, 86, 112)
    white = (245, 250, 255)
    muted = (160, 178, 204)
    card_bg = (20, 32, 56)

    def new_canvas() -> tuple[Any, Any]:
        img = Image.new("RGB", (w, h), bg_top)
        draw = ImageDraw.Draw(img)
        for y in range(0, h, 8):
            t = y / h
            r = int(bg_top[0] + (bg_bot[0] - bg_top[0]) * t)
            g = int(bg_top[1] + (bg_bot[1] - bg_top[1]) * t)
            b = int(bg_top[2] + (bg_bot[2] - bg_top[2]) * t)
            draw.rectangle([(0, y), (w, y + 8)], fill=(r, g, b))
        # Top brand pill
        draw.rounded_rectangle([(80, 110), (w - 80, 200)], radius=24, fill=card_bg, outline=cyan, width=3)
        draw.text((130, 134), f"{brand}  //  24/7 SOLANA RADAR", fill=cyan, font=load_font(34, bold=True))
        # Bottom ticker footer
        draw.rounded_rectangle([(80, h - 180), (w - 80, h - 90)], radius=20, fill=card_bg, outline=mint, width=2)
        draw.text((120, h - 154), f"FREE LIVE ALERTS: {channel_link}", fill=mint, font=load_font(32, bold=True))
        return img, draw

    # Slide 1: Hook + Hero Breakout Card
    img1, d1 = new_canvas()
    d1.rounded_rectangle([(80, 320), (w - 80, 1480)], radius=38, fill=card_bg, outline=cyan, width=4)
    badge = "TRENDING SOLANA BREAKOUT" if signal.is_boosted else "LIVE SOLANA MOMENTUM"
    d1.rounded_rectangle([(130, 380), (w - 130, 465)], radius=20, fill=(26, 48, 76), outline=gold, width=2)
    d1.text((170, 404), badge, fill=gold, font=load_font(36, bold=True))

    d1.text((130, 540), f"${signal.symbol}", fill=white, font=load_font(128, bold=True))
    d1.text((130, 695), signal.name[:24], fill=muted, font=load_font(46, bold=False))

    move_color = mint if signal.change_1h >= 0 else crimson
    d1.text((130, 820), f"1H MOVE:  {signal.change_1h:+.1f}%", fill=move_color, font=load_font(68, bold=True))
    d1.text((130, 935), f"PRICE:  {format_price(signal.price_usd)}", fill=white, font=load_font(54, bold=True))

    d1.rounded_rectangle([(130, 1080), (w - 130, 1380)], radius=28, fill=(13, 24, 44), outline=mint, width=3)
    d1.text((175, 1125), "QUANT SIGNAL SCORE", fill=muted, font=load_font(36, bold=True))
    d1.text((175, 1190), f"{signal.signal_score} / 99", fill=mint, font=load_font(112, bold=True))

    s1 = SLIDES_DIR / "slide_1.png"
    img1.save(s1)

    # Slide 2: On-Chain Metrics & Buy Pressure Bar
    img2, d2 = new_canvas()
    d2.rounded_rectangle([(80, 300), (w - 80, 1520)], radius=38, fill=card_bg, outline=cyan, width=4)
    d2.text((130, 360), f"${signal.symbol} LIVE METRICS", fill=cyan, font=load_font(58, bold=True))

    rows = [
        ("5-MIN MOVE", f"{signal.change_5m:+.2f}%", mint if signal.change_5m >= 0 else crimson),
        ("1-HOUR MOVE", f"{signal.change_1h:+.2f}%", mint if signal.change_1h >= 0 else crimson),
        ("24-HOUR MOVE", f"{signal.change_24h:+.1f}%", mint if signal.change_24h >= 0 else crimson),
        ("LIQUIDITY", f"${format_compact_usd(signal.liquidity_usd)}", white),
        ("24H VOLUME", f"${format_compact_usd(signal.volume_24h_usd)}", gold),
    ]
    y = 490
    for label, value, color in rows:
        d2.rounded_rectangle([(130, y), (w - 130, y + 125)], radius=20, fill=(13, 24, 44), outline=(45, 70, 105), width=2)
        d2.text((170, y + 40), label, fill=muted, font=load_font(36, bold=True))
        d2.text((540, y + 34), value, fill=color, font=load_font(46, bold=True))
        y += 152

    # Buy pressure bar
    bar_y = 1285
    d2.text((130, bar_y - 58), f"1H BUY PRESSURE: {signal.buy_pressure_pct}% BUYS", fill=mint, font=load_font(38, bold=True))
    bar_w = w - 260
    buy_w = int(bar_w * (signal.buy_pressure_pct / 100.0))
    d2.rounded_rectangle([(130, bar_y), (130 + bar_w, bar_y + 52)], radius=16, fill=crimson)
    if buy_w > 12:
        d2.rounded_rectangle([(130, bar_y), (130 + buy_w, bar_y + 52)], radius=16, fill=mint)
    d2.text((130, bar_y + 82), f"{signal.buys_1h} Buys  vs  {signal.sells_1h} Sells", fill=muted, font=load_font(34, bold=False))

    s2 = SLIDES_DIR / "slide_2.png"
    img2.save(s2)

    # Slide 3: Call-To-Action Funnel -> Telegram Channel
    img3, d3 = new_canvas()
    d3.rounded_rectangle([(80, 340), (w - 80, 1480)], radius=38, fill=card_bg, outline=mint, width=4)
    d3.text((130, 420), "CATCH BREAKOUTS", fill=white, font=load_font(74, bold=True))
    d3.text((130, 520), "24/7 AUTOMATICALLY", fill=mint, font=load_font(74, bold=True))

    bullets = [
        "1. Live Solana breakouts every 30 mins",
        "2. Micro-cap rugs (<$35K liq) filtered",
        "3. 1-tap Fast Trade & Chart buttons",
        "4. 100% Free Public Telegram Radar",
    ]
    by = 680
    for b in bullets:
        for line in textwrap.wrap(b, width=32):
            d3.text((130, by), line, fill=white, font=load_font(42, bold=False))
            by += 60
        by += 28

    d3.rounded_rectangle([(130, 1140), (w - 130, 1340)], radius=26, fill=mint)
    d3.text((170, 1185), "JOIN FREE TELEGRAM", fill=bg_top, font=load_font(46, bold=True))
    d3.text((170, 1255), channel_link, fill=bg_top, font=load_font(40, bold=True))
    d3.text((130, 1385), "Automated market data only. Not financial advice.", fill=muted, font=load_font(28, bold=False))

    s3 = SLIDES_DIR / "slide_3.png"
    img3.save(s3)
    return [s1, s2, s3]


def render_mp4_with_ffmpeg(slides: list[Path], audio_path: Path, out_mp4: Path) -> None:
    duration = get_audio_duration_seconds(audio_path)
    seg = duration / len(slides)
    concat_file = OUT_DIR / "slides.txt"
    lines: list[str] = []
    for slide in slides:
        lines.append(f"file '{slide.resolve().as_posix()}'")
        lines.append(f"duration {seg:.3f}")
    lines.append(f"file '{slides[-1].resolve().as_posix()}'")
    concat_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(concat_file),
        "-i",
        str(audio_path),
        "-vf",
        "scale=1080:1920,format=yuv420p",
        "-c:v",
        "libx264",
        "-r",
        "30",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        "-shortest",
        "-movflags",
        "+faststart",
        str(out_mp4),
    ]
    subprocess.check_call(cmd)


def send_video_to_telegram(bot_token: str, chat_id: str, video_path: Path, caption: str) -> None:
    import requests  # type: ignore

    url = f"https://api.telegram.org/bot{bot_token}/sendVideo"
    with video_path.open("rb") as fh:
        resp = requests.post(
            url,
            data={"chat_id": chat_id, "caption": caption[:1020], "supports_streaming": "true"},
            files={"video": (video_path.name, fh, "video/mp4")},
            timeout=60,
        )
    data = resp.json()
    if not resp.ok or not data.get("ok"):
        raise RuntimeError(f"Telegram sendVideo failed: {data}")
    print(f"[OK] Delivered 1080x1920 Short MP4 to Telegram {chat_id}!")


def upload_to_youtube_shorts(video_path: Path, title: str, description: str) -> str | None:
    client_id = os.getenv("YOUTUBE_CLIENT_ID", "").strip()
    client_secret = os.getenv("YOUTUBE_CLIENT_SECRET", "").strip()
    refresh_token = os.getenv("YOUTUBE_REFRESH_TOKEN", "").strip()
    if not (client_id and client_secret and refresh_token):
        print("[INFO] YouTube OAuth secrets not set — skipping direct YouTube upload (MP4 still saved & sent to Telegram).")
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
            "tags": ["Solana", "Crypto", "Shorts", "DeFi", "TradingSignals", "SOL"],
            "categoryId": "28",
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False,
        },
    }
    media = MediaFileUpload(str(video_path), chunksize=-1, resumable=True, mimetype="video/mp4")
    req = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    resp = req.execute()
    vid_id = resp.get("id")
    print(f"[OK] Uploaded YouTube Short: https://youtube.com/shorts/{vid_id}")
    return vid_id


def main() -> int:
    parser = argparse.ArgumentParser(description="CapitalMaker #5 Autonomous Solana Shorts Video Factory")
    parser.add_argument("--dry-run", action="store_true", help="Generate script & metadata only (skip FFmpeg/upload)")
    args = parser.parse_args()

    brand = os.getenv("BRAND_NAME", "CAPITALMAKER ALPHA").strip() or "CAPITALMAKER ALPHA"
    raw_channel = normalize_channel_id(os.getenv("TELEGRAM_CHANNEL_ID", ""))
    channel_handle = raw_channel.lstrip("@") if raw_channel.startswith("@") else ""
    channel_link = f"t.me/{channel_handle}" if channel_handle else "Link in Bio"
    groq_key = os.getenv("GROQ_API_KEY", "").strip()
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    video_target_chat = normalize_channel_id(os.getenv("TELEGRAM_VIDEO_CHAT_ID", "")) or raw_channel

    signals = discover_live_signals()
    if not signals:
        print("[INFO] No live Solana breakout signal found for Shorts factory.")
        return 0
    top = next((s for s in signals if s.change_1h > 0 or s.change_5m > 0), signals[0])

    script = build_narration_script(top, channel_link, groq_key)
    headline_move = f"{top.change_1h:+.1f}% 1H" if top.change_1h >= 0.5 else f"{top.change_5m:+.1f}% 5M"
    title = f"${top.symbol} Solana Breakout ({headline_move}) #Shorts #Solana"
    caption = (
        f"🔥 ${top.symbol} Solana Breakout Radar ({top.signal_score}/99)\n"
        f"Price: {format_price(top.price_usd)} | 1H: {top.change_1h:+.1f}% | Liq: ${format_compact_usd(top.liquidity_usd)}\n\n"
        f"📡 Free 24/7 Live Alerts: https://{channel_link}\n"
        f"#Solana #Crypto #Shorts #SOL #DeFi\n"
        f"(Automated market data only — DYOR, not financial advice.)"
    )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    META_PATH.write_text(
        json.dumps({"symbol": top.symbol, "title": title, "caption": caption, "script": script}, indent=2),
        encoding="utf-8",
    )

    print(f"[SHORTS] Selected ${top.symbol} (score {top.signal_score}/99)")
    print(f"[SHORTS] Script: {script}")
    if args.dry_run:
        return 0

    asyncio.run(synthesize_voiceover(script, AUDIO_PATH))
    slides = render_hud_slides(top, brand, channel_link)
    render_mp4_with_ffmpeg(slides, AUDIO_PATH, VIDEO_PATH)
    print(f"[OK] Rendered 1080x1920 vertical Short: {VIDEO_PATH} ({VIDEO_PATH.stat().st_size} bytes)")

    if bot_token and video_target_chat:
        try:
            send_video_to_telegram(bot_token, video_target_chat, VIDEO_PATH, caption)
        except Exception as exc:
            print(f"[WARN] Telegram video delivery skipped: {exc}", file=sys.stderr)

    upload_to_youtube_shorts(VIDEO_PATH, title, caption)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
