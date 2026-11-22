# CapitalMaker Cloud Engine (#2 + #5) — $0/Month 24/7 Autonomous Stack

Runs **both** of your autonomous traffic & SOL/USDT affiliate engines in the cloud **24/7 for $0/month** — even when your phone is turned off or has no data:

1. **24/7 Autonomous Solana Signal Broadcaster (`autonomous-signals.yml`)**: Scans DexScreener boosted breakouts & Solana DEX liquidity every 30 minutes, filters out `<$35K` liquidity rugs, avoids spam via 6-hour cooldowns, and auto-publishes alerts with your **SOL (Trojan/GMGN)** & **USDT (Bybit/OKX/MEXC)** buttons to Telegram.
2. **Autonomous Short-Form Video Traffic Feeder (`autonomous-shorts.yml`)**: Twice daily, turns the hottest live Solana breakout into a **1080x1920 vertical video** with free neural voiceover (`edge-tts`) + sharp HUD slides + FFmpeg — automatically delivers the finished MP4 to your Telegram (ready to 1-tap share to TikTok/Reels/Shorts) AND optionally auto-uploads straight to **YouTube Shorts**!

---

## 5-Minute Setup (Zero Coding, Works Right in Your Browser)

### Step 1: Create a Free GitHub Repo
1. Go to [github.com](https://github.com) and sign in (or create a free account).
2. Click **+ → New repository** → name it `capitalmaker-cloud`.
   - Choose **Public** for **UNLIMITED free GitHub Actions minutes forever** (safe because all tokens/links go inside encrypted **GitHub Secrets**, never inside your code!).
   - *(Private also works — includes 2,000 free minutes/month, plenty for both workflows.)*
3. Click **Create repository** → click **uploading an existing file** → drag-and-drop all files/folders from `CapitalMakerCloud` (make sure `.github/workflows/` is included!) → click **Commit changes**.

### Step 2: Add Your Encrypted Secrets (3 mins)
In your GitHub repo, go to **Settings → Secrets and variables → Actions → New repository secret** and add:

| Secret Name | Required? | Example / Value |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | **Yes** | Your `@BotFather` token (`7123456:AAH...`) |
| `TELEGRAM_CHANNEL_ID` | **Yes** | `@YourChannelName` |
| `SOLANA_BOT_REF_URL` | **Yes** | `https://t.me/solana_trojanbot?start=r-yourcode` |
| `EXCHANGE_REF_URL` | **Yes** | `https://www.bybit.com/invite?ref=YOURCODE` |
| `BRAND_NAME` | Optional | `CAPITALMAKER ALPHA` |
| `GROQ_API_KEY` | Optional | Free key from `console.groq.com/keys` for AI commentary & scripts |
| `TELEGRAM_VIDEO_CHAT_ID` | Optional | Your personal Telegram Chat ID if you want daily Shorts MP4 sent to your DM instead of your channel |
| `YOUTUBE_CLIENT_ID` / `YOUTUBE_CLIENT_SECRET` / `YOUTUBE_REFRESH_TOKEN` | Optional | Add later for 100% hands-free direct YouTube Shorts auto-upload |

### Step 3: Turn On & Test Immediately (1 min)
1. Click the **Actions** tab at the top of your GitHub repo.
2. Click **CapitalMaker 24/7 Autonomous Signals (#2)** → click **Run workflow** → watch your live alert land in Telegram!
3. Click **CapitalMaker Auto-Shorts Video Factory (#5)** → click **Run workflow** → within ~60 seconds, a brand-new **1080x1920 vertical MP4 video** lands in your Telegram + under the workflow's **Artifacts**!

*(Tip: Once the GitHub Cloud Runner is live, you can turn **OFF** 24/7 Auto-Broadcast inside the phone app so they don't both post at the same time — or keep the phone app for manual `POST TOP NOW` & `COPY X / WA` whenever you want!)*
