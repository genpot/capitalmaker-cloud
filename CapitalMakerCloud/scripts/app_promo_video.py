name: Render Official 90s App Promo Video (CapitalMoon & CapitalMaker)

on:
  workflow_dispatch:
    inputs:
      hub_url:
        description: 'Your Netlify Download Website URL (optional)'
        required: false
        default: 't.me/MysolAlpha99'

jobs:
  render-promo-video:
    runs-on: ubuntu-latest
    timeout-minutes: 15

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Setup Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install FFmpeg & Python Dependencies
        run: |
          sudo apt-get update -qq
          sudo apt-get install -y -qq ffmpeg fonts-dejavu-core
          pip install -q -r CapitalMakerCloud/requirements.txt

      - name: Render 90-Second Official Promo Video
        env:
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHANNEL_ID: ${{ secrets.TELEGRAM_CHANNEL_ID }}
          HUB_URL: ${{ github.event.inputs.hub_url }}
        run: python CapitalMakerCloud/scripts/app_promo_video.py

      - name: Upload Official Promo MP4 Artifact
        uses: actions/upload-artifact@v4
        with:
          name: capital-alpha-official-promo-video
          path: output/capital_alpha_official_promo.mp4
          retention-days: 14
