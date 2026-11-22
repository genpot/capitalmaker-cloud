#!/usr/bin/env python3
"""
CapitalMaker Option #2 — 24/7 Cloud Autonomous Solana Signal & SOL/USDT Affiliate Broadcaster.
Runs on GitHub Actions ($0/month) even when your phone is turned off.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

COOLDOWN_SECONDS = 6 * 3600  # 6-hour anti-spam cooldown per token mint
STATE_FILE = Path(os.getenv("STATE_FILE", "state/cooldowns.json"))

CORE_SOLANA_WATCH_MINTS = [
    "JUPyiwrYJFskUPiHa7hkeR8VUtAeFoSYbKedZNsDvCN",  # JUP
    "4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59S5iCNLY3QrkX6R",  # RAY
    "EKpQGSJtjMFqKZ9KQanSqYXRcF8fBopzLHYxdM65zcjm",  # WIF
    "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",  # BONK
    "HZ1JovNiVvGrGNiiYvEozEVgZ58xaU3RKwX8eACQBCt3",  # PYTH
    "7GCihgDB8fe6KNjn2MYtkzZcRjQy3t9GHdC8uHYmW2hr",  # POPCAT
    "J1toso1uCk3RLmjorhTtrVwY9HJ7X8V9yYac6Y7kGCPn",  # JitoSOL
]


@dataclass
class SignalCandidate:
    mint: str
    symbol: str
    name: str
    price_usd: float
    change_5m: float
    change_1h: float
    change_24h: float
    liquidity_usd: float
    volume_24h_usd: float
    buys_1h: int
    sells_1h: int
    signal_score: int
    dex_url: str
    is_boosted: bool = False
    is_on_cooldown: bool = False

    @property
    def buy_pressure_pct(self) -> int:
        total = self.buys_1h + self.sells_1h
        return round((self.buys_1h / total) * 100) if total > 0 else 50


def http_json(url: str, payload: dict[str, Any] | None = None, headers: dict[str, str] | None = None, timeout: int = 14) -> Any:
    hdrs = {"User-Agent": "CapitalMaker-Cloud-Engine/1.2"}
    if headers:
        hdrs.update(headers)
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        hdrs["Content-Type"] = "application/json"
    req = Request(url, data=data, headers=hdrs, method="POST" if data is not None else "GET")
    with urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def normalize_channel_id(raw: str) -> str:
    t = raw.strip()
    if not t:
        return ""
    if t.startswith("-100") or t.lstrip("-").isdigit():
        return t
    for prefix in ("https://t.me/", "http://t.me/", "t.me/"):
        if t.lower().startswith(prefix):
            t = t[len(prefix):]
    t = t.strip("/")
    return t if t.startswith("@") else f"@{t}"


def normalize_url(raw: str) -> str:
    t = raw.strip()
    if not t:
        return ""
    if t.lower().startswith(("https://", "http://")):
        return t
    return f"https://{t}" if "." in t else ""


def format_price(price: float) -> str:
    if price >= 1.0:
        return f"${price:.4f}"
    if price >= 0.01:
        return f"${price:.5f}"
    if price >= 0.0001:
        return f"${price:.6f}"
    return f"${price:.8f}"


def format_compact_usd(amount: float) -> str:
    if amount >= 1_000_000_000:
        return f"{amount / 1e9:.2f}B"
    if amount >= 1_000_000:
        return f"{amount / 1e6:.2f}M"
    if amount >= 1_000:
        return f"{amount / 1e3:.1f}K"
    return f"{amount:.0f}"


def load_cooldowns(now: float | None = None) -> dict[str, float]:
    now = now or time.time()
    if not STATE_FILE.exists():
        return {}
    try:
        raw = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        return {k: float(v) for k, v in raw.items() if float(v) > now}
    except Exception:
        return {}


def save_cooldown(mint: str, now: float | None = None) -> None:
    now = now or time.time()
    cooldowns = load_cooldowns(now)
    cooldowns[mint] = now + COOLDOWN_SECONDS
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(cooldowns, indent=2), encoding="utf-8")


def compute_signal_score(
    change_5m: float,
    change_1h: float,
    change_24h: float,
    liq_usd: float,
    vol_24h_usd: float,
    buys_1h: int,
    sells_1h: int,
    is_boosted: bool,
) -> int:
    total = buys_1h + sells_1h
    buy_ratio = (buys_1h / total) if total > 0 else 0.5
    vol_liq = (vol_24h_usd / liq_usd) if liq_usd > 0 else 0.0
    score = 52
    if buy_ratio >= 0.60:
        score += 14
    elif buy_ratio >= 0.53:
        score += 8
    elif buy_ratio < 0.45:
        score -= 10

    if 2.0 <= change_1h <= 45.0:
        score += 12
    elif change_1h > 45.0:
        score += 6
    elif change_1h < -8.0:
        score -= 12

    if 0.5 <= change_5m <= 12.0:
        score += 8
    elif change_5m < -4.0:
        score -= 8

    if change_24h > 5.0:
        score += 4
    if liq_usd >= 250_000:
        score += 8
    elif liq_usd >= 75_000:
        score += 4
    if vol_liq >= 1.5:
        score += 6
    if is_boosted:
        score += 4
    return max(25, min(99, score))


def fetch_boosted_solana_mints() -> list[str]:
    try:
        items = http_json("https://api.dexscreener.com/token-boosts/top/v1")
        out: list[str] = []
        if isinstance(items, list):
            for item in items:
                if str(item.get("chainId", "")).lower() != "solana":
                    continue
                addr = str(item.get("tokenAddress", "")).strip()
                if len(addr) >= 32 and addr not in out:
                    out.append(addr)
                if len(out) >= 18:
                    break
        return out
    except Exception as exc:
        print(f"[WARN] Could not fetch boosted mints: {exc}", file=sys.stderr)
        return []


def discover_live_signals() -> list[SignalCandidate]:
    cooldowns = load_cooldowns()
    boosted = fetch_boosted_solana_mints()
    boosted_set = set(boosted)
    pool: list[str] = []
    for m in boosted + CORE_SOLANA_WATCH_MINTS:
        if m not in pool:
            pool.append(m)
    pool = pool[:28]
    if not pool:
        return []

    url = f"https://api.dexscreener.com/latest/dex/tokens/{','.join(pool)}"
    data = http_json(url)
    pairs = data.get("pairs") or []

    best_by_mint: dict[str, dict[str, Any]] = {}
    for pair in pairs:
        if str(pair.get("chainId", "")).lower() != "solana":
            continue
        mint = str((pair.get("baseToken") or {}).get("address", "")).strip()
        if not mint:
            continue
        liq = float((pair.get("liquidity") or {}).get("usd") or 0.0)
        prev_liq = float((best_by_mint.get(mint, {}).get("liquidity") or {}).get("usd") or -1.0)
        if liq > prev_liq:
            best_by_mint[mint] = pair

    candidates: list[SignalCandidate] = []
    for pair in best_by_mint.values():
        base = pair.get("baseToken") or {}
        mint = str(base.get("address", "")).strip()
        symbol = str(base.get("symbol", "")).strip()
        name = str(base.get("name", "")).strip() or symbol
        try:
            price = float(pair.get("priceUsd") or 0.0)
        except ValueError:
            price = 0.0
        liq = float((pair.get("liquidity") or {}).get("usd") or 0.0)
        vol24 = float((pair.get("volume") or {}).get("h24") or 0.0)
        if not symbol or price <= 0.0 or liq < 35_000.0 or vol24 < 50_000.0:
            continue

        changes = pair.get("priceChange") or {}
        m5 = float(changes.get("m5") or 0.0)
        h1 = float(changes.get("h1") or 0.0)
        h24 = float(changes.get("h24") or 0.0)
        tx_h1 = (pair.get("txns") or {}).get("h1") or {}
        buys = int(tx_h1.get("buys") or 0)
        sells = int(tx_h1.get("sells") or 0)
        dex_url = str(pair.get("url") or f"https://dexscreener.com/solana/{mint}")
        is_boosted = mint in boosted_set

        score = compute_signal_score(m5, h1, h24, liq, vol24, buys, sells, is_boosted)
        candidates.append(
            SignalCandidate(
                mint=mint,
                symbol=symbol,
                name=name,
                price_usd=price,
                change_5m=m5,
                change_1h=h1,
                change_24h=h24,
                liquidity_usd=liq,
                volume_24h_usd=vol24,
                buys_1h=buys,
                sells_1h=sells,
                signal_score=score,
                dex_url=dex_url,
                is_boosted=is_boosted,
                is_on_cooldown=mint in cooldowns,
            )
        )

    candidates.sort(key=lambda c: c.signal_score, reverse=True)
    return candidates


def fetch_optional_groq_note(signal: SignalCandidate, groq_api_key: str) -> str | None:
    if not groq_api_key.strip():
        return None
    prompt = (
        f"Write ONE punchy 14-word max crypto trader takeaway (no hashtags, no financial advice claims) "
        f"for Solana token {signal.symbol}: 5m {signal.change_5m:+.1f}%, 1h {signal.change_1h:+.1f}%, "
        f"Liq ${format_compact_usd(signal.liquidity_usd)}, 24h Vol ${format_compact_usd(signal.volume_24h_usd)}, "
        f"{signal.buy_pressure_pct}% buy pressure."
    )
    try:
        resp = http_json(
            "https://api.groq.com/openai/v1/chat/completions",
            payload={
                "model": "llama-3.3-70b-versatile",
                "temperature": 0.3,
                "max_tokens": 50,
                "messages": [{"role": "user", "content": prompt}],
            },
            headers={"Authorization": f"Bearer {groq_api_key.strip()}"},
            timeout=10,
        )
        content = resp["choices"][0]["message"]["content"].strip().replace("\n", " ")
        return content[:150] if content else None
    except Exception:
        return None


def format_telegram_html(signal: SignalCandidate, brand: str, ai_note: str | None) -> str:
    badge = "🔥 TRENDING BREAKOUT" if signal.is_boosted else "⚡ SOLANA MOMENTUM"
    note = html.escape(ai_note) if ai_note else (
        f"Strong {signal.buy_pressure_pct}% buyer dominance with ${format_compact_usd(signal.volume_24h_usd)} 24h flow."
        if signal.buy_pressure_pct >= 60
        else f"Active Solana DEX flow • Liq ${format_compact_usd(signal.liquidity_usd)} • Score {signal.signal_score}/99."
    )
    return "\n".join([
        f"{badge} | <b>{html.escape(brand)}</b>",
        "",
        f"🪙 <b>${html.escape(signal.symbol)}</b> ({html.escape(signal.name)}) • Score <b>{signal.signal_score}/99</b>",
        f"💵 Price: <b>{format_price(signal.price_usd)}</b>",
        f"📈 5m: <b>{signal.change_5m:+.2f}%</b> | 1h: <b>{signal.change_1h:+.2f}%</b> | 24h: <b>{signal.change_24h:+.1f}%</b>",
        f"💧 Liq: <b>${format_compact_usd(signal.liquidity_usd)}</b> | Vol 24h: <b>${format_compact_usd(signal.volume_24h_usd)}</b>",
        f"⚖️ 1h Flow: <b>{signal.buy_pressure_pct}% Buys</b> ({signal.buys_1h}B / {signal.sells_1h}S)",
        f"🧠 <i>{note}</i>",
        "",
        f"CA: <code>{html.escape(signal.mint)}</code>",
        "⚠️ <i>Automated market data only — DYOR, not financial advice.</i>",
    ])


def build_inline_keyboard(signal: SignalCandidate, sol_bot_url: str, exchange_url: str) -> dict[str, Any]:
    rows: list[list[dict[str, str]]] = []
    primary: list[dict[str, str]] = []
    if sol_bot_url:
        primary.append({"text": "⚡ Snipe on Solana Bot (SOL)", "url": sol_bot_url})
    if exchange_url:
        primary.append({"text": "💰 Trade on Exchange (USDT)", "url": exchange_url})
    if primary:
        rows.append(primary)
    rows.append([{"text": f"📊 Live Chart ({signal.symbol})", "url": signal.dex_url}])
    return {"inline_keyboard": rows}


def publish_to_telegram(
    bot_token: str,
    channel_id: str,
    html_text: str,
    reply_markup: dict[str, Any],
) -> dict[str, Any]:
    return http_json(
        f"https://api.telegram.org/bot{bot_token}/sendMessage",
        payload={
            "chat_id": channel_id,
            "text": html_text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
            "reply_markup": reply_markup,
        },
        timeout=14,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="CapitalMaker 24/7 Cloud Solana Signal Broadcaster")
    parser.add_argument("--dry-run", action="store_true", help="Scan live signals and print alert without sending to Telegram")
    args = parser.parse_args()

    brand = os.getenv("BRAND_NAME", "CAPITALMAKER ALPHA").strip() or "CAPITALMAKER ALPHA"
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    channel_id = normalize_channel_id(os.getenv("TELEGRAM_CHANNEL_ID", ""))
    sol_bot_url = normalize_url(os.getenv("SOLANA_BOT_REF_URL", ""))
    exchange_url = normalize_url(os.getenv("EXCHANGE_REF_URL", ""))
    groq_key = os.getenv("GROQ_API_KEY", "").strip()
    min_score = int(os.getenv("MIN_SIGNAL_SCORE", "65"))

    signals = discover_live_signals()
    if not signals:
        print("[INFO] No Solana tokens passed liquidity/volume safety filters right now.")
        return 0

    chosen = next((s for s in signals if not s.is_on_cooldown and s.signal_score >= min_score), None)
    if chosen is None:
        chosen = next((s for s in signals if not s.is_on_cooldown), None)
    if chosen is None:
        print("[INFO] All qualifying tokens are on 6-hour anti-spam cooldown. Skipping post.")
        return 0

    ai_note = fetch_optional_groq_note(chosen, groq_key)
    message_html = format_telegram_html(chosen, brand, ai_note)
    keyboard = build_inline_keyboard(chosen, sol_bot_url, exchange_url)

    print(f"[SCAN] Found {len(signals)} live Solana candidates. Top pick: ${chosen.symbol} (score {chosen.signal_score}/99)")
    if args.dry_run:
        print("\n--- DRY RUN TELEGRAM ALERT ---")
        print(message_html)
        print("\n--- INLINE BUTTONS ---")
        print(json.dumps(keyboard, indent=2))
        return 0

    if not bot_token or not channel_id:
        print("[ERROR] Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHANNEL_ID in GitHub Secrets!", file=sys.stderr)
        return 1

    try:
        res = publish_to_telegram(bot_token, channel_id, message_html, keyboard)
        if res.get("ok"):
            msg_id = (res.get("result") or {}).get("message_id")
            save_cooldown(chosen.mint)
            print(f"[OK] Published ${chosen.symbol} to {channel_id} (msg #{msg_id})")
            return 0
        print(f"[ERROR] Telegram API returned not ok: {res}", file=sys.stderr)
        return 1
    except (HTTPError, URLError) as exc:
        print(f"[ERROR] Telegram request failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
