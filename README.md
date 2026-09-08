# Eddoboozi — page-to-voice prototype

Photograph a page → check the text → hear it in English or Luganda → save the audio.

Tested in this build: the app boots and the OCR step (photo → text) works end-to-end
against a real image. The Luganda voice call goes through Sunbird AI's live API, so
plug in your own token and test that leg once — it needs your Sunbird account, which
this environment doesn't have access to.

## Setup (10 minutes)

1. Install Tesseract OCR (if not already on your machine):
   - Mac: `brew install tesseract`
   - Linux: `sudo apt install tesseract-ocr`
   - Windows: https://github.com/UB-Mannheim/tesseract/wiki

2. Install Python packages:
   ```
   pip install -r requirements.txt
   ```

3. Get a Sunbird AI token (free): register at https://api.sunbird.ai/register,
   then grab your token from the tokens page.

4. Set it as an environment variable:
   ```
   export SUNBIRD_TOKEN="your_token_here"      # Mac/Linux
   set SUNBIRD_TOKEN=your_token_here            # Windows
   ```

5. Run it:
   ```
   python app.py
   ```
   Open http://localhost:5000

## Before you pitch

- Take 2-3 real photos of textbook pages ahead of time (not just at demo moment) —
  flat, good light, no glare. OCR is good but not perfect on curled pages or shadows.
- Test the Luganda button once beforehand with your real token, live, so you know the
  Sunbird call actually returns audio before you're standing in front of judges.
- The extracted-text box is editable on purpose — if OCR gets a word wrong, fix it
  live. That's a feature, not a bug: it shows the human-in-the-loop step a real
  deployment would have too.
- "Save for the SD card" downloads the mp3 with a filename pattern
  (`page_lug_<timestamp>.mp3`) — say out loud that in the real version this writes
  straight onto the Orbit Reader's card, so judges connect the dots even though this
  prototype just downloads it to your laptop.

## What's deliberately out of scope for this prototype

- Braille output — not attempted, not claimed.
- Batch/multi-page conversion — one page at a time is enough to prove the concept.
- Any student-facing device — this runs on the demo laptop, standing in for the
  school's shared device.

## Deploying so judges get a live link (optional, ~20 min)

Push this folder to a GitHub repo, then deploy free on Render:
new Web Service → connect the repo → build command `pip install -r requirements.txt`
→ start command `python app.py` → add `SUNBIRD_TOKEN` under Environment.
