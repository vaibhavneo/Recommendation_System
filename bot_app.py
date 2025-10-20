# bot_app.py
# Bot Framework (Python) web bot with:
#   - /help
#   - echo
#   - /recommend <userId> [k]  -> Hero Card carousel
#
# Fixes:
#   - Uses CardFactory.hero_card(...) (no .to_attachment()) to build attachments
#   - Returns HTTP 200 to Emulator (avoids odd 201 handling)
#   - Async fetch with aiohttp.ClientTimeout to avoid "timeout context manager" warning
#
# Optional env:
#   RECOMMENDER_API_URL (default: http://127.0.0.1:8000/recommend)

import os
from typing import List

from aiohttp import web, ClientSession, ClientTimeout
import aiohttp

from botbuilder.core import (
    BotFrameworkAdapter,
    BotFrameworkAdapterSettings,
    TurnContext,
    ActivityHandler,
    MessageFactory,
    CardFactory,   # <-- important
)
from botbuilder.schema import (
    Activity,
    ActivityTypes,
    HeroCard,
    CardImage,
    CardAction,
    ActionTypes,
)

# -----------------------------------------------------------------------------
# Config
# -----------------------------------------------------------------------------
APP_ID = os.environ.get("MicrosoftAppId", "")
APP_PASSWORD = os.environ.get("MicrosoftAppPassword", "")
PORT = int(os.environ.get("PORT", "3978"))

RECOMMENDER_API_URL = os.environ.get("RECOMMENDER_API_URL", "http://127.0.0.1:8000/recommend")

# -----------------------------------------------------------------------------
# Optional external recommender (safe to skip)
# -----------------------------------------------------------------------------
async def fetch_recs(user_id: str, k: int) -> List[int]:
    """
    Optionally call an external recommender API.
    Accepts either a bare list or {"items":[...]}.
    Falls back to a deterministic list if the API is unavailable.
    """
    try:
        timeout = ClientTimeout(total=5)
        async with ClientSession(timeout=timeout) as session:
            async with session.get(RECOMMENDER_API_URL, params={"user": user_id, "k": k}) as r:
                if r.status == 200:
                    data = await r.json()
                    items = data.get("items", data) if isinstance(data, dict) else data
                    recs = [int(x) for x in items][:k]
                    if recs:
                        return recs
    except Exception:
        pass

    # Fallback if API is down or returns junk
    base = 100
    return list(range(base + 1, base + 1 + max(1, min(k, 10))))


def build_recommendation_carousel(item_ids: List[int]):
    """
    Turn a list of item IDs into a carousel of HeroCards.
    IMPORTANT: In Python, use CardFactory.hero_card(...) to create attachments.
    """
    attachments = []
    for iid in item_ids:
        card = HeroCard(
            title=f"Recommended item #{iid}",
            subtitle="Sample recommendation",
            text="Tap 'View' to open a placeholder link.",
            images=[CardImage(url=f"https://picsum.photos/seed/{iid}/400/220")],
            buttons=[
                CardAction(
                    type=ActionTypes.open_url,
                    title="View",
                    value=f"https://example.org/items/{iid}",
                )
            ],
        )
        attachments.append(CardFactory.hero_card(card))

    # Multiple cards -> carousel; single card -> single attachment also works
    if len(attachments) == 1:
        return MessageFactory.attachment(attachments[0])
    return MessageFactory.carousel(attachments)


# -----------------------------------------------------------------------------
# Bot
# -----------------------------------------------------------------------------
class RecBot(ActivityHandler):
    async def on_message_activity(self, turn_context: TurnContext):
        raw = (turn_context.activity.text or "").strip()
        lo = raw.lower()

        if lo in ("/help", "help"):
            help_text = (
                "Commands:\n"
                "• /help — show this help\n"
                "• say anything — I’ll echo it back\n"
                "• /recommend <userId> [k] — show a Hero Card carousel (optionally top k)\n"
                f"(optional API: {RECOMMENDER_API_URL})"
            )
            await turn_context.send_activity(help_text)
            return

        if lo.startswith("/recommend"):
            parts = raw.split()
            user_id = parts[1] if len(parts) >= 2 else "1"
            try:
                k = int(parts[2]) if len(parts) >= 3 else 5
            except ValueError:
                k = 5
            k = max(1, min(k, 10))  # clamp for safety

            try:
                rec_ids = await fetch_recs(user_id, k)
                reply = build_recommendation_carousel(rec_ids)
                await turn_context.send_activity(reply)
            except Exception as e:
                await turn_context.send_activity(
                    f"Oops — something went wrong building your recommendations. ({e})"
                )
            return

        # Default: echo what the user typed
        await turn_context.send_activity(f"you said: {raw}")

    async def on_members_added_activity(self, members_added, turn_context: TurnContext):
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                await turn_context.send_activity("Hi! Type `/help` to see what I can do.")


# -----------------------------------------------------------------------------
# Adapter, error handler, and server
# -----------------------------------------------------------------------------
settings = BotFrameworkAdapterSettings(APP_ID, APP_PASSWORD)
adapter = BotFrameworkAdapter(settings)
bot = RecBot()


async def on_error(context: TurnContext, error: Exception):
    # Global error handler: log and send a friendly message (when possible)
    print("Bot error:", error)
    try:
        await context.send_activity("Sorry, something went wrong on my side.")
    except Exception:
        pass

adapter.on_turn_error = on_error


async def messages(req: web.Request) -> web.Response:
    if req.method != "POST":
        return web.Response(status=405, text="Method Not Allowed")

    body = await req.json()
    activity = Activity().deserialize(body)
    auth_header = req.headers.get("Authorization", "")

    async def aux(turn_context: TurnContext):
        await bot.on_turn(turn_context)

    try:
        await adapter.process_activity(activity, auth_header, aux)
        return web.Response(status=200, text="OK")  # <- 200 keeps Emulator happy
    except Exception as e:
        print("Top-level error:", e)
        return web.Response(status=500, text=str(e))


async def health(req: web.Request) -> web.Response:
    return web.Response(text="Bot is running. POST /api/messages")


def create_app() -> web.Application:
    app = web.Application()
    app.router.add_get("/", health)
    app.router.add_get("/healthz", health)
    app.router.add_post("/api/messages", messages)
    return app


if __name__ == "__main__":
    web.run_app(create_app(), host="0.0.0.0", port=PORT)
