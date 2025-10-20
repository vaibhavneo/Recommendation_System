# Recommendation Chatbot (Bot Framework + Python)

A simple **recommendation-system chatbot** that:

* replies to greetings (`hello`) and `/help`
* returns **top-K** recommendations via `/recommend <userId> [k]`
* renders results as a **Hero Card carousel** in the **Bot Framework Emulator**
* can optionally call a tiny local **Recommendation API** (FastAPI) for real IDs

---

## Repo Structure

```
.
├─ bot_app.py        # Bot Framework (aiohttp) bot that handles messages & renders Hero cards
├─ serve.py          # FastAPI app that exposes `/recommend?user=<id>&k=<k>`
├─ app.py            # Minimal API or helper script (kept for compatibility/labs)
├─ apy.py            # Small utilities for the API (helper module used by serve/app)
├─ train.py          # Toy training/precompute script for user→item candidates
├─ requirements.txt  # Python deps (botbuilder, aiohttp, fastapi, uvicorn, etc.)
└─ README.md         # This file
```

> **Note:** If you intended `api.py` instead of `apy.py`, keep the filename users will actually clone/run. This README refers to **`apy.py`** because that’s what’s in your files.

---

## Quick Start (Windows)

### 1) Prereqs

* Python **3.11+** (or your working version)
* **Bot Framework Emulator**
* (Optional) **Anaconda/conda**

### 2) Create & activate an env

```bat
conda create -y -n bf311 python=3.11
conda activate bf311
```

### 3) Install dependencies

```bat
pip install -r requirements.txt
```

### 4) (Optional) Start the Recommendation API (port **8000**)

```bat
:: Either run the consolidated server:
python serve.py

:: or if your class starter split files:
python app.py
```

This exposes:

```
GET http://127.0.0.1:8000/recommend?user=<id>&k=<k>
```

Returns a JSON list of item IDs; used by the bot to build cards.

### 5) Start the Bot (port **3978**)

```bat
set PORT=3978
set MicrosoftAppId=
set MicrosoftAppPassword=
python bot_app.py
```

> For local Emulator testing you **do not** need AppId/Password. Leave them blank.

### 6) Connect the Emulator

* Open **Bot Framework Emulator**
* **Open Bot** → URL: `http://localhost:3978/api/messages`
* In **Emulator Settings**, **disable auth tokens** (unchecked)

### 7) Try these messages

```
hello
/help
/recommend 1
/recommend 1 5   (top-5)
```

If the optional API is running, the bot fetches real IDs; if not, it falls back to a deterministic local sample.

---

## What You’ll See

When you send `/recommend 1 3`, the bot returns a **carousel** with three **Hero Cards**, each with:

* **Image**
* **Title** (e.g., “Recommended item #103”)
* **Subtitle/description**
* A **View** button (opens a placeholder link)

---

## Implementation Summary

### Files You Created & What They Do

**`bot_app.py`**
Main Bot Framework app (Python, `aiohttp`):

* Sets up an **Adapter** and an `/api/messages` **POST** route
* Parses user input (`hello`, `/help`, `/recommend <userId> [k]`)
* Calls the local Recommendation API (if available) or a **local fallback** list
* Builds **Hero Cards** and sends them as a **carousel** using:

```python
from botbuilder.schema import Attachment, HeroCard, CardImage, CardAction, ActionTypes

card = HeroCard(
    title="Recommended item #101",
    text="Sample recommendation",
    images=[CardImage(url="https://picsum.photos/seed/101/400/220")],
    buttons=[CardAction(type=ActionTypes.open_url, title="View", value="https://example.org/items/101")],
)

attachment = Attachment(
    content_type="application/vnd.microsoft.card.hero",
    content=card,
)
# send attachments as a carousel via MessageFactory.carousel([attachment, ...])
```

> **Note:** Python’s `HeroCard` does **not** have `.to_attachment()`. Wrap the `HeroCard` inside an `Attachment` with `content_type='application/vnd.microsoft.card.hero'`.

---

**`serve.py`**
A **FastAPI** service that exposes:

* `GET /recommend?user=<id>&k=<k>` → returns a list of item IDs.
  Uses simple deterministic logic or precomputed results from `train.py`.

---

**`apy.py`**
Small utilities used by the API (e.g., ID normalization, sample catalog, logging helpers). Keeping the logic isolated makes the API endpoints clean and testable.

---

**`train.py`**
A tiny **training/precompute** script demonstrating how you might:

* Build a simple **popularity** or **user-based** candidate list
* Persist lightweight artifacts (e.g., JSON/CSV) consumed by `serve.py`

---

**`app.py`**
Minimal compatibility app (e.g., a tiny HTTP server or a legacy endpoint used in earlier assignments). Kept in the repo to show evolution; **not required** when `serve.py` is running.

---

## Conversation Flow

1. **User** sends `hello` → bot echoes and shows command tips
2. **User** sends `/recommend 1 3` → bot:

   * (If running) calls `GET http://127.0.0.1:8000/recommend?user=1&k=3`
   * Else uses a local fallback list `[101, 102, 103]`
   * Renders a **carousel** of Hero Cards with images and a **View** button

---

## Why the Carousel

* **Scannable** and **touch-friendly** in Emulator or Web Chat
* Reduces cognitive load vs. raw text lists
* Makes it trivial to add actions later (e.g., **Buy**, **Save**, **More info**)

---

## Bot Commands

```
hello                     # quick echo/handshake
/help                     # show this help & examples
/recommend <userId>       # top-3 default
/recommend <userId> <k>   # explicit top-k
```

---

## Configuration

**Environment variables used by `bot_app.py`:**

* `PORT` (default: `3978`)
* `MicrosoftAppId`, `MicrosoftAppPassword` (leave empty for local Emulator)

**Optional API:**

* `serve.py` listens on `8000` by default
* Endpoint: `/recommend?user=<id>&k=<k>`

---

## Troubleshooting

**400 in Emulator**

* In Emulator **Settings**, uncheck **“Use version 1.0 authentication tokens”**
* Ensure the bot URL is `http://localhost:3978/api/messages`

**“service_url can not be None”**

* Use the Emulator **“Open Bot”** flow; don’t POST to `/api/messages` manually

**“HeroCard has no attribute to_attachment”**

* Use the **Attachment + `content_type`** approach shown above (already in `bot_app.py`)

**API timeouts**

* Start the API (`python serve.py`) **before** sending `/recommend ...`
* If it’s down, the bot falls back to local IDs and still replies

---

## How to “Train”

```bat
:: Generates / refreshes small artifacts the API can read
python train.py
```

By default, `train.py` writes simple deterministic outputs (e.g., JSON with top items per user). Replace with your actual model/inference pipeline later.

---

## Testing Notes

**Unit test the API:**

```bat
curl "http://127.0.0.1:8000/recommend?user=1&k=3"
```

**Manual test the bot in Emulator:**

```
/recommend 1 3
```

→ should show a **Hero Card carousel**.

---

## References

* Microsoft **Bot Framework** SDK for Python
* **FastAPI** & **Uvicorn**
* **Bot Framework Emulator**

---

## License

Use your course’s preferred license (e.g., MIT) or leave proprietary if required by your class.

---

## Acknowledgements

Portions of this project are adapted from **Microsoft BotBuilder** samples and classroom starter code. All trademarks belong to their respective owners.
