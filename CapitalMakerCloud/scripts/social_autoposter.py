#!/usr/bin/env python3
"""
CapitalMaker 100% Hands-Free Social Auto-Poster (X / Twitter + Bluesky).
Zero external pip dependencies — pure Python stdlib OAuth 1.0a for X API v2 + ATProto for Bluesky.
Runs every 2 hours on GitHub Actions ($0/month = ~360 posts/mo, safely inside X's 500/mo free tier).
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import os
import secrets
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from signal_broadcaster import (
    SignalCandidate,
    discover_live_signals,
    fetch_optional_groq_note,
    format_compact_usd,
    format_price,
    normalize_channel_id,
)

SOCIAL_STATE_FILE = Path(os.getenv("SOCIAL_STATE_FILE", "state/social_cooldowns.json"))
SOCIAL_COOLDOWN_SECONDS = 4 * 3600  # 4-hour anti-spam cooldown per coin


def load_social_cooldowns(now: float | None = None) -> dict[str, float]:
    now = now or time.time()
    if not SOCIAL_STATE_FILE.exists():
        return {}
    try:
        raw = json.loads(SOCIAL_STATE_FILE.read_text(encoding="utf-8"))
        return {k: float(v) for k, v in raw.items() if float(v) > now}
    except Exception:
        return {}


def save_social_cooldown(mint: str, now: float | None = None) -> None:
    now = now or time.time()
    data = load_social_cooldowns(now)
    data[mint] = now + SOCIAL_COOLDOWN_SECONDS
    SOCIAL_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    SOCIAL_STATE_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def percent_encode(val: str) -> str:
    return quote(str(val), safe="-._~")


def build_oauth1_header(
    method: str,
    url: str,
    consumer_key: str,
    consumer_secret: str,
    access_token: str,
    access_secret: str,
    timestamp: str | None = None,
    nonce: str | None = None,
) -> str:
    oauth_params = {
        "oauth_consumer_key": consumer_key,
        "oauth_nonce": nonce or secrets.token_hex(16),
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": timestamp or str(int(time.time())),
        "oauth_token": access_token,
        "oauth_version": "1.0",
    }
    param_str = "&".join(
        f"{percent_encode(k)}={percent_encode(v)}"
        for k, v in sorted(oauth_params.items())
    )
    base_str = "&".join([
        method.upper(),
        percent_encode(url),
        percent_encode(param_str),
    ])
    signing_key = f"{percent_encode(consumer_secret)}&{percent_encode(access_secret)}"
    digest = hmac.new(signing_key.encode("utf-8"), base_str.encode("utf-8"), hashlib.sha1).digest()
    oauth_params["oauth_signature"] = base64.b64encode(digest).decode("utf-8")

    header_parts = ", ".join(
        f'{percent_encode(k)}="{percent_encode(v)}"'
        for k, v in sorted(oauth_params.items())
    )
    return f"OAuth {header_parts}"


def build_social_post_text(signal: SignalCandidate, channel_url: str, ai_note: str | None) -> str:
    move_str = f"{signal.change_1h:+.1f}% 1H" if abs(signal.change_1h) >= 0.5 else f"{signal.change_5m:+.2f}% 5M"
    ticker = "".join(ch for ch in signal.symbol.upper() if ch.isalnum())[:12] or "SOL"
    base_lines = [
        f"🚨 ${ticker} Solana Breakout Radar ({signal.signal_score}/99)",
        f"💵 {format_price(signal.price_usd)} | 📈 {move_str} | 💧 Liq ${format_compact_usd(signal.liquidity_usd)} | ⚖️ {signal.buy_pressure_pct}% Buys",
    ]
    footer = f"⚡ Free 24/7 live alerts: {channel_url}\n$SOL #Solana #Crypto"
    if ai_note:
        candidate = "\n".join(base_lines + [f"🧠 {ai_note}", "", footer])
        if len(candidate) <= 275:
            return candidate
    return "\n".join(base_lines + ["", footer])[:278]


def post_to_x(
    text: str,
    api_key: str,
    api_secret: str,
    access_token: str,
    access_secret: str,
) -> dict[str, Any]:
    url = "https://api.x.com/2/tweets"
    auth_header = build_oauth1_header(
        method="POST",
        url=url,
        consumer_key=api_key,
        consumer_secret=api_secret,
        access_token=access_token,
        access_secret=access_secret,
    )
    body = json.dumps({"text": text}).encode("utf-8")
    req = Request(
        url,
        data=body,
        headers={
            "Authorization": auth_header,
            "Content-Type": "application/json",
            "User-Agent": "CapitalMaker-Cloud-Social/1.2",
        },
        method="POST",
    )
    with urlopen(req, timeout=16) as resp:
        return json.loads(resp.read().decode("utf-8"))


def post_to_bluesky(text: str, handle: str, app_password: str, link_url: str) -> dict[str, Any]:
    login_req = Request(
        "https://bsky.social/xrpc/com.atproto.server.createSession",
        data=json.dumps({"identifier": handle, "password": app_password}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(login_req, timeout=14) as resp:
        session = json.loads(resp.read().decode("utf-8"))

    did = session["did"]
    jwt = session["accessJwt"]
    facets: list[dict[str, Any]] = []
    idx = text.find(link_url)
    if idx >= 0:
        b_start = len(text[:idx].encode("utf-8"))
        b_end = b_start + len(link_url.encode("utf-8"))
        facets.append({
            "index": {"byteStart": b_start, "byteEnd": b_end},
            "features": [{"$type": "app.bsky.richtext.facet#link", "uri": link_url}],
        })

    record: dict[str, Any] = {
        "$type": "app.bsky.feed.post",
        "text": text,
        "createdAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    if facets:
        record["facets"] = facets

    post_req = Request(
        "https://bsky.social/xrpc/com.atproto.repo.createRecord",
        data=json.dumps({"repo": did, "collection": "app.bsky.feed.post", "record": record}).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {jwt}"},
        method="POST",
    )
    with urlopen(post_req, timeout=14) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="CapitalMaker 100% Hands-Free X & Bluesky Auto-Poster")
    parser.add_argument("--dry-run", action="store_true", help="Format post and verify without publishing")
    args = parser.parse_args()

    raw_channel = normalize_channel_id(os.getenv("TELEGRAM_CHANNEL_ID", ""))
    handle = raw_channel.lstrip("@") if raw_channel.startswith("@") else ""
    channel_url = f"https://t.me/{handle}" if handle else "https://t.me/MysolAlpha99"
    groq_key = os.getenv("GROQ_API_KEY", "").strip()

    x_api_key = os.getenv("X_API_KEY", "").strip()
    x_api_secret = os.getenv("X_API_SECRET", "").strip()
    x_access_token = os.getenv("X_ACCESS_TOKEN", "").strip()
    x_access_secret = os.getenv("X_ACCESS_SECRET", "").strip()
    x_ready = all([x_api_key, x_api_secret, x_access_token, x_access_secret])

    bsky_handle = os.getenv("BLUESKY_HANDLE", "").strip()
    bsky_pass = os.getenv("BLUESKY_APP_PASSWORD", "").strip()
    bsky_ready = bool(bsky_handle and bsky_pass)

    cooldowns = load_social_cooldowns()
    signals = discover_live_signals()
    if not signals:
        print("[INFO] No live Solana breakout candidates right now.")
        return 0

    chosen = next((s for s in signals if s.mint not in cooldowns and (s.change_1h > 0 or s.change_5m > 0)), None)
    if chosen is None:
        chosen = next((s for s in signals if s.mint not in cooldowns), signals[0])

    ai_note = fetch_optional_groq_note(chosen, groq_key)
    post_text = build_social_post_text(chosen, channel_url, ai_note)
    print(f"[SOCIAL] Picked ${chosen.symbol} (score {chosen.signal_score}/99, {len(post_text)} chars)")

    if args.dry_run:
        print("\n--- DRY RUN SOCIAL POST ---")
        print(post_text)
        sample_hdr = build_oauth1_header("POST", "https://api.x.com/2/tweets", "k", "s", "t", "ts")
        print(f"\n[CHECK] OAuth1 header generated OK: {sample_hdr[:42]}...")
        return 0

    if not x_ready and not bsky_ready:
        print("[ERROR] Add X (Twitter) secrets (X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_SECRET) or Bluesky secrets first!", file=sys.stderr)
        return 1

    any_ok = False
    if x_ready:
        try:
            res = post_to_x(post_text, x_api_key, x_api_secret, x_access_token, x_access_secret)
            tweet_id = (res.get("data") or {}).get("id")
            print(f"[OK] Auto-tweeted ${chosen.symbol} on X! Tweet ID: {tweet_id}")
            any_ok = True
        except HTTPError as exc:
            err_body = exc.read().decode("utf-8", errors="ignore")
            print(f"[ERROR] X API HTTP {exc.code}: {err_body}", file=sys.stderr)
        except URLError as exc:
            print(f"[ERROR] X network error: {exc}", file=sys.stderr)

    if bsky_ready:
        try:
            res = post_to_bluesky(post_text, bsky_handle, bsky_pass, channel_url)
            print(f"[OK] Auto-posted ${chosen.symbol} on Bluesky! URI: {res.get('uri')}")
            any_ok = True
        except Exception as exc:
            print(f"[ERROR] Bluesky post failed: {exc}", file=sys.stderr)

    if any_ok:
        save_social_cooldown(chosen.mint)
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
