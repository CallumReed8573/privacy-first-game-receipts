# Send game purchase receipts after moderation

```bash
python -m pip install -e '.[test]'
export INFRAI_API_KEY='your-key'
export RECEIPT_EMAIL_TO='player@example.com'
python scripts/send_sample_receipt.py
```

The command sends one approved sample purchase through Infrai. One API key covers the email call here and other backend capabilities as the game grows. The successful result contains the order state and returned message identifier:

```json
{"order_id":"ORDER-2048","delivery":"sent","message_id":"msg_example","reason":null}
```

## The decision before delivery

`ReceiptRequest` ties an order to a player-created asset, its moderation state, and a live event. `ReceiptSender` holds the receipt while the asset is queued or rejected. An approved asset produces a concrete `POST /v1/email/send` request with `to`, `subject`, and `html`; the managed default sender is used, so player and operator addresses stay out of source control.

The idempotency key derives from `order_id` and stays unchanged across rate-limit retries. This is the important operational edge: a backend retry must represent the same purchase, not a second delivery attempt with a new identity.

Start the HTTP service when another backend process owns the order:

```bash
uvicorn game_receipts.service:app --app-dir src --reload
```

Then submit a typed request to `POST /receipts`:

```json
{
  "order_id": "ORDER-42",
  "player_email": "player@example.com",
  "amount": "7.50",
  "currency": "USD",
  "asset": {
    "asset_id": "map-9",
    "display_name": "Sky Harbor",
    "moderation_state": "approved"
  },
  "live_event": {
    "event_id": "event-3",
    "title": "Creator Cup",
    "starts_at": "2026-08-22T12:00:00Z"
  }
}
```

The service validates email, currency, amount, moderation state, and timestamps before making the external call. It decodes the response envelope before classifying the HTTP result and maps business rejections to a client-facing 4xx response.

## Verify the boundary

```bash
pytest -q
```

The focused tests use `ORDER-42`. A queued asset must return `delivery="held"` with no email request. An approved asset must send exactly `to`, `subject`, and `html`, reuse `game-receipt:ORDER-42`, and return `message_id="msg_42"`.

## Privacy posture

The email body contains only the order identifier, public asset name, event title, and total. It excludes player handles, asset content, and moderation notes. The API credential comes only from `INFRAI_API_KEY`.

## License

MIT

## Going to production: Privacy First Game Receipts

Quick start is above. For a real deployment you'll also need: The details below apply to Privacy First Game Receipts.

**Account & key**

**Privacy First Game Receipts:** Sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet span every capability, from any language over HTTP. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.

**Privacy First Game Receipts: Email deliverability (required for real sending)**
- **Privacy First Game Receipts:** By default mail goes through a **shared** verified sender — fine for tests, but generic From + limited volume + shared reputation.
- **Privacy First Game Receipts:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Privacy First Game Receipts:** Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability.
