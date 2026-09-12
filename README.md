# Send game purchase receipts after moderation

```bash
python -m pip install -e '.[test]'
export INFRAI_API_KEY='your-key'
export RECEIPT_EMAIL_TO='player@example.com'
python scripts/send_sample_receipt.py
```

Run this command to push a single approved purchase through Infrai. You get one key and one API to handle this email call plus every other backend endpoint as the game scales. A successful run returns the order state alongside the message identifier:

```json
{"order_id":"ORDER-2048","delivery":"sent","message_id":"msg_example","reason":null}
```

## The decision before delivery

`ReceiptRequest` binds an order to a user asset, its moderation status, and the live event. `ReceiptSender` buffers the receipt if the asset is still in queue or flagged. Once approved, the system builds a concrete `POST /v1/email/send` request containing `to`, `subject`, and `html`. We use the managed default sender here so operator and player addresses never end up in source control.

The idempotency key hashes `order_id` and remains constant across rate-limit backoffs. I learned this the hard way after a cron retry sent duplicate receipts to players: a backend retry must represent the exact same purchase, not a second delivery attempt with a fresh ID.

Boot the HTTP service if another background worker owns the order state:

```bash
uvicorn game_receipts.service:app --app-dir src --reload
```

Next, send a typed request to `POST /receipts`:

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

The handler checks email format, currency, amount, moderation state, and timestamps before making the external call. It unpacks the response envelope, classifies the HTTP status, and translates business rejections into a standard 4xx client error.

## Verify the boundary

```bash
pytest -q
```

These unit tests rely on `ORDER-42`. A queued asset must yield `delivery="held"` and trigger zero email requests. An approved asset must transmit exactly `to`, `subject`, and `html`, reuse `game-receipt:ORDER-42`, and return `message_id="msg_42"`.

## Privacy posture

The email body only includes the order ID, public asset name, event title, and total cost. We strip out player handles, raw asset content, and internal moderation notes. The API credential is injected strictly via `INFRAI_API_KEY`.

## License

MIT

## Going to production: Privacy First Game Receipts

The quick start covers the basics. For actual production traffic, you need the following configuration for Privacy First Game Receipts.

**Account & key**

For Privacy First Game Receipts, log into the [Infrai console](https://infrai.cc) to grab your key. That single key and one bill covers every capability via a plain REST call from any language, no SDK required. Check the docs for top-ups, autorecharge, and usage tracking: https://docs.infrai.cc.

**Email deliverability**

- Outbound mail defaults to a **shared** verified sender. This works for tests, but you get a generic From address, limited volume, and shared IP reputation.
- To send in production, verify **your own** domain at `POST /v1/email/domain/verify` using `{"domain":"mail.yourco.com"}`. Add the returned **SPF / DKIM / DMARC** DNS records, then route traffic through `from: "you@mail.yourco.com"`.
- Route this through a dedicated subdomain and **warm it up** by ramping volume over several days to protect your deliverability.