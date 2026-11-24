#!/usr/bin/env python3
"""
CAPITAL ALPHA — Official ~90-Second Animated Promo & Explainer Video Generator
Showcases BOTH CapitalMoon & CapitalMaker with 3D human storytelling scenes,
studio voiceover (edge-tts), word-by-word captions, and direct Telegram/Artifact delivery.
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
    FPS,
    RH,
    RW,
    blend_glass_panel,
    build_fallback_word_timings,
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
PROMO_AUDIO = OUT_DIR / "promo_voice.mp3"
PROMO_VIDEO = OUT_DIR / "capital_alpha_official_promo.mp4"


def build_promo_script(hub_url: str, channel_link: str) -> str:
    return (
        "Most Solana traders lose money before they even click buy — chasing late calls, paying overpriced VIP groups, "
        "or getting trapped by hidden rugs and slow browser wallets. That is why we built the Capital Alpha mobile suite: "
        "two free, 100 percent non-custodial Android trading apps built for speed, transparency, and privacy. "
        "First, meet CapitalMoon — your real-time memecoin radar and sniper terminal. "
        "CapitalMoon scans live DexScreener momentum and pre-run signals, runs an eight-vector rug and honeypot safety check, "
        "and lets you execute fast Solana swaps directly from your phone. "
        "Second, meet CapitalMaker — your streamlined Solana yield and quant vault. "
        "CapitalMaker connects directly to real Solana mainnet Jupiter routes for audited liquid staking like JitoSOL and jupSOL, "
        "blue-chip quant swaps, USDC and USDT capital protection, plus one-tap empty token account rent reclaim so your SOL never gets trapped. "
        "Best of all? Zero email, zero phone number, and zero KYC required. "
        "Your private keys stay encrypted inside Android Keystore on your device only, protected by fingerprint biometrics, "
        "a six-digit PIN, anti-screenshot shielding, and a built-in 24 7 AI support assistant inside both apps. "
        "Download CapitalMoon and CapitalMaker free today using the link in our bio and join our free 24 7 Solana radar on Telegram. "
        "Trade smart, stay in control of your keys, and always do your own research — not financial advice."
    )


def render_promo_mp4(
    hub_url: str,
    channel_link: str,
    audio_path: Path,
    timings: list[dict[str, Any]],
    out_mp4: Path,
) -> None:
    from PIL import Image, ImageDraw  # type: ignore

    duration = get_audio_duration_seconds(audio_path)
    total_frames = int(math.ceil(duration * FPS))

    img_intro = load_cinematic_asset("host_bull.jpg", ((6, 16, 32), (14, 40, 62)))
    img_moon = load_cinematic_asset("host_bear.jpg", ((26, 10, 24), (48, 18, 38)))
    img_maker = load_cinematic_asset("scene_investor.jpg", ((8, 22, 42), (16, 44, 70)))
    img_cta = load_cinematic_asset("scene_finale.jpg", ((6, 18, 34), (12, 44, 62)))

    vignette = Image.new("RGBA", (RW, RH), (0, 0, 0, 0))
    vd = ImageDraw.Draw(vignette)
    for y in range(0, 260, 4):
        vd.rectangle([(0, y), (RW, y + 4)], fill=(4, 8, 18, int(175 * (1.0 - y / 260.0))))
    for y in range(RH - 520, RH, 4):
        vd.rectangle([(0, y), (RW, y + 4)], fill=(4, 8, 18, int(220 * ((y - (RH - 520)) / 520.0))))

    caption_chunks = group_caption_chunks(timings, words_per_chunk=4)
    mint, cyan, gold, white, muted = (18, 236, 164), (16, 204, 255), (255, 206, 68), (248, 252, 255), (190, 208, 230)

    t1, t2, t3 = duration * 0.22, duration * 0.50, duration * 0.78
    xfade = 0.55

    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo", "-vcodec", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{RW}x{RH}", "-r", str(FPS), "-i", "pipe:0",
        "-i", str(audio_path),
        "-f", "lavfi", "-t", f"{duration:.2f}", "-i", "sine=frequency=110:sample_rate=44100",
        "-filter_complex",
        "[1:a]loudnorm=I=-15:TP=-1.5:LRA=11[v];[2:a]volume=0.022,tremolo=f=1.6:d=0.4[bed];[v][bed]amix=inputs=2:duration=first:dropout_transition=1[aout]",
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
            pulse = 0.5 + 0.5 * math.sin(t * 5.0)
            if t < t1:
                bg = sample_camera_frame(img_intro, t / max(t1, 0.1), "zoom_in")
                if t > t1 - xfade:
                    bg = Image.blend(bg, sample_camera_frame(img_moon, 0.0, "pan_right"), (t - (t1 - xfade)) / xfade)
            elif t < t2:
                bg = sample_camera_frame(img_moon, (t - t1) / max(t2 - t1, 0.1), "pan_right")
                if t > t2 - xfade:
                    bg = Image.blend(bg, sample_camera_frame(img_maker, 0.0, "zoom_in"), (t - (t2 - xfade)) / xfade)
            elif t < t3:
                bg = sample_camera_frame(img_maker, (t - t2) / max(t3 - t2, 0.1), "zoom_in")
                if t > t3 - xfade:
                    bg = Image.blend(bg, sample_camera_frame(img_cta, 0.0, "zoom_out"), (t - (t3 - xfade)) / xfade)
            else:
                bg = sample_camera_frame(img_cta, (t - t3) / max(duration - t3, 0.1), "zoom_out")

            canvas = bg.convert("RGBA")
            canvas.alpha_composite(vignette)

            blend_glass_panel(canvas, (30, 38, RW - 30, 96), (8, 14, 28, 200), (*cyan, 220), radius=18, width=2)
            d = ImageDraw.Draw(canvas)
            d.text((54, 54), "CAPITAL ALPHA  //  OFFICIAL SOLANA SUITE", fill=cyan, font=load_font(22, bold=True))

            if t < t1:
                blend_glass_panel(canvas, (30, 120, RW - 30, 290), (8, 16, 30, 195), (*mint, 220), radius=24, width=2)
                d = ImageDraw.Draw(canvas)
                d.text((54, 140), "2 FREE NON-CUSTODIAL APPS", fill=gold, font=load_font(22, bold=True))
                d.text((54, 178), "CAPITALMOON + CAPITALMAKER", fill=white, font=load_font(34, bold=True))
                d.text((54, 232), "Zero Email • Zero KYC • 100% Your Solana Keys", fill=mint, font=load_font(23, bold=True))
            elif t < t2:
                blend_glass_panel(canvas, (30, 120, RW - 30, 380), (14, 12, 30, 205), (*gold, 230), radius=24, width=3)
                d = ImageDraw.Draw(canvas)
                d.text((54, 140), "APP 1  •  MEMECOIN SNIPER & RADAR", fill=gold, font=load_font(22, bold=True))
                d.text((54, 176), "CAPITALMOON", fill=white, font=load_font(54, bold=True))
                d.text((54, 248), "• Live DexScreener & Pre-Run spike scanner", fill=white, font=load_font(23, bold=False))
                d.text((54, 286), "• 8-Vector Rug & Honeypot Safety Shield", fill=mint, font=load_font(23, bold=True))
                d.text((54, 324), "• Direct local-signed SOL swaps + 24/7 AI Support", fill=muted, font=load_font(22, bold=False))
            elif t < t3:
                blend_glass_panel(canvas, (30, 120, RW - 30, 380), (8, 18, 36, 205), (*cyan, 230), radius=24, width=3)
                d = ImageDraw.Draw(canvas)
                d.text((54, 140), "APP 2  •  SOLANA YIELD & QUANT HUD", fill=cyan, font=load_font(22, bold=True))
                d.text((54, 176), "CAPITALMAKER", fill=white, font=load_font(54, bold=True))
                d.text((54, 248), "• Real Solana Staking Yield (JitoSOL / jupSOL)", fill=mint, font=load_font(23, bold=True))
                d.text((54, 286), "• Jupiter Quant Swaps + USDC/USDT Shield", fill=white, font=load_font(23, bold=False))
                d.text((54, 324), "• 1-Tap Empty ATA SOL Rent Reclaim + AI Support", fill=gold, font=load_font(22, bold=True))
            else:
                grow = int(pulse * 8)
                blend_glass_panel(canvas, (34, 140, RW - 34, 490), (8, 16, 30, 215), (*mint, 235), radius=28, width=3)
                d = ImageDraw.Draw(canvas)
                d.text((60, 170), "PRIVACY-FIRST SECURITY", fill=gold, font=load_font(24, bold=True))
                d.text((60, 210), "Biometrics + 6-Digit PIN + Keystore", fill=white, font=load_font(30, bold=True))
                d.text((60, 260), "Zero personal info • Transparent 0.75% routing fee", fill=muted, font=load_font(22, bold=False))
                d.rounded_rectangle([(60 - grow, 330 - grow // 2), (RW - 60 + grow, 445 + grow // 2)], radius=22, fill=mint)
                d.text((88, 350), "DOWNLOAD FREE & JOIN LIVE RADAR", fill=(6, 14, 24), font=load_font(23, bold=True))
                d.text((88, 388), channel_link, fill=(6, 14, 24), font=load_font(34, bold=True))

            active_chunk = next((c for c in caption_chunks if c[0]["start"] - 0.12 <= t <= c[-1]["end"] + 0.25), None)
            if active_chunk:
                cap_y = 955
                blend_glass_panel(canvas, (30, cap_y - 20, RW - 30, cap_y + 132), (6, 10, 20, 215), (*cyan, 215), radius=22, width=2)
                d = ImageDraw.Draw(canvas)
                cap_font = load_font(33, bold=True)
                for row_idx, row_words in enumerate([active_chunk[:2], active_chunk[2:]]):
                    if not row_words:
                        continue
                    widths = [d.textbbox((0, 0), w["word"].upper() + " ", font=cap_font)[2] for w in row_words]
                    cur_x = max(48, (RW - sum(widths)) // 2)
                    ry = cap_y + row_idx * 52
                    for item, w_px in zip(row_words, widths):
                        col = gold if item["start"] - 0.04 <= t <= item["end"] + 0.08 else white
                        d.text((cur_x + 2, ry + 2), item["word"].upper(), fill=(0, 0, 0), font=cap_font)
                        d.text((cur_x, ry), item["word"].upper(), fill=col, font=cap_font)
                        cur_x += w_px

            d = ImageDraw.Draw(canvas)
            d.text((38, RH - 52), f"{hub_url}  •  {channel_link}  •  DYOR / NOT FINANCIAL ADVICE", fill=muted, font=load_font(17, bold=True))
            proc.stdin.write(canvas.convert("RGB").tobytes())
    finally:
        proc.stdin.close()
        if proc.wait() != 0:
            raise RuntimeError("FFmpeg promo render failed")


def main() -> int:
    parser = argparse.ArgumentParser(description="Render Official ~90s CAPITAL ALPHA Promo Video")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    raw_chan = normalize_channel_id(os.getenv("TELEGRAM_CHANNEL_ID", ""))
    handle = raw_chan.lstrip("@") if raw_chan.startswith("@") else "MysolAlpha99"
    channel_link = f"t.me/{handle}"
    hub_url = os.getenv("HUB_URL", f"https://{channel_link}").strip() or f"https://{channel_link}"
    script = build_promo_script(hub_url, channel_link)
    print(f"[PROMO] Script ({len(script.split())} words): {script[:140]}...")
    if args.dry_run:
        return 0

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    timings = asyncio.run(synthesize_voiceover_with_timings(script, PROMO_AUDIO, voice="en-US-AndrewNeural"))
    dur = get_audio_duration_seconds(PROMO_AUDIO)
    if len(timings) < 10:
        timings = build_fallback_word_timings(script, dur)
    render_promo_mp4(hub_url, channel_link, PROMO_AUDIO, timings, PROMO_VIDEO)
    print(f"[OK] Rendered Official Promo Video ({dur:.1f}s): {PROMO_VIDEO}")

    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if bot_token and raw_chan:
        caption = (
            f"🎬 OFFICIAL LAUNCH VIDEO — CAPITALMOON & CAPITALMAKER\n\n"
            f"✅ 2 Free Non-Custodial Solana Android Apps\n"
            f"✅ Zero Email • Zero KYC • Biometrics + 6-Digit PIN\n"
            f"✅ Built-in 24/7 AI Support Bot\n\n"
            f"📡 Live Alerts: https://{channel_link}\n"
            f"(DYOR — crypto markets are volatile, not financial advice.)"
        )
        send_video_to_telegram(bot_token, raw_chan, PROMO_VIDEO, caption)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
