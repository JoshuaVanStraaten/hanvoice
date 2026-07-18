"""Waitlist welcome email — delivers the Seoul Survival Phrase Card via Resend.

Fired as a background task after a *fresh* waitlist insert (duplicates are
deliberately silent: re-emailing would both spam the subscriber and leak
whether an address was already on the list). A delivery failure must never
surface to the visitor — the signup already succeeded — so this service logs
and swallows every error.
"""

import httpx
import structlog

from app.core.config import Settings

logger = structlog.get_logger(__name__)

_RESEND_URL = "https://api.resend.com/emails"
_SEND_TIMEOUT_SECONDS = 15.0

_SUBJECT = "Your Seoul Survival Phrase Card (+ one quick question)"


def _body_html(card_url: str, app_url: str) -> str:
    return f"""\
<div style="font-family:-apple-system,Segoe UI,Roboto,sans-serif;max-width:560px;\
margin:0 auto;color:#1a1a1a;line-height:1.6">
<p>Hey — Joshua here, the person building HanVoice.</p>
<p>Here's the <strong>Seoul Survival Phrase Card</strong> you signed up for:
the trip phrases from our Speak lessons on one printable page — café,
taxi-and-directions, restaurant, market — each with how to <em>actually</em>
say it, not just the spelling.</p>
<p style="margin:24px 0">
<a href="{card_url}" style="background:#c0392b;color:#fff;padding:12px 22px;\
border-radius:8px;text-decoration:none;font-weight:bold">
Open the phrase card</a></p>
<p>Two suggestions from someone who drills these daily:</p>
<ol>
<li>Don't try to learn the whole card. 주세요 + pointing covers half your
trip. Start there.</li>
<li>Reading a phrase 50 times isn't the same as saying it once. The app
scores your pronunciation on every one of these phrases and lets you
rehearse the café / taxi / market conversations out loud with an AI partner:
<a href="{app_url}">hanvoice.app</a> — the free plan is plenty to start.</li>
</ol>
<p><strong>One quick question — when's your trip?</strong> Just hit reply
with the month. I'm shaping what gets built next around how much runway
people actually have before they land.</p>
<p>고마워요 (that one's not on the card — it's the casual "thanks"),<br>Joshua</p>
<p style="color:#555;font-size:14px">P.S. The Founder Pass ($69 once,
everything forever) is $49 for the first 25 people with code
<strong>SEOUL49</strong> at checkout — it expires August 1st, and the cap is
on the discount, not the pass.</p>
</div>"""


async def send_phrase_card_email(settings: Settings, to_email: str) -> None:
    """Send the phrase-card welcome email. Logs and never raises."""
    if not settings.resend_api_key:
        logger.info("waitlist_email_skipped_unconfigured", to=to_email)
        return
    frontend = settings.frontend_url.rstrip("/")
    payload = {
        "from": settings.resend_from,
        "to": [to_email],
        "reply_to": "hello@hanvoice.app",
        "subject": _SUBJECT,
        "html": _body_html(f"{frontend}/phrase-card.html", frontend),
    }
    try:
        async with httpx.AsyncClient(timeout=_SEND_TIMEOUT_SECONDS) as client:
            response = await client.post(
                _RESEND_URL,
                headers={"Authorization": f"Bearer {settings.resend_api_key}"},
                json=payload,
            )
    except httpx.HTTPError as exc:
        logger.error("waitlist_email_unreachable", to=to_email, error=str(exc))
        return
    if response.status_code != 200:
        logger.error(
            "waitlist_email_failed",
            to=to_email,
            status=response.status_code,
            body=response.text[:300],
        )
        return
    logger.info(
        "waitlist_email_sent",
        to=to_email,
        message_id=response.json().get("id"),
    )
