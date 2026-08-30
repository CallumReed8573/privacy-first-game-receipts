from datetime import UTC, datetime
from decimal import Decimal

import httpx

from game_receipts.infrai_client import InfraiClient
from game_receipts.models import LiveEvent, ModerationState, PlayerAsset, ReceiptRequest
from game_receipts.receipt_sender import ReceiptSender


def order(state: ModerationState) -> ReceiptRequest:
    return ReceiptRequest(
        order_id="ORDER-42",
        player_email="player@example.com",
        amount=Decimal("7.50"),
        currency="USD",
        asset=PlayerAsset(
            asset_id="map-9",
            display_name="Sky Harbor",
            moderation_state=state,
        ),
        live_event=LiveEvent(
            event_id="event-3",
            title="Creator Cup",
            starts_at=datetime(2026, 8, 22, 12, 0, tzinfo=UTC),
        ),
    )


def test_queued_asset_holds_receipt_without_api_call() -> None:
    def fail_if_called(request: httpx.Request) -> httpx.Response:
        raise AssertionError(f"unexpected request: {request.url}")

    client = InfraiClient(api_key="test-key", transport=httpx.MockTransport(fail_if_called))
    try:
        result = ReceiptSender(client).send(order(ModerationState.QUEUED))
    finally:
        client.close()

    assert result.delivery == "held"
    assert result.reason == "asset_moderation_incomplete"


def test_approved_asset_sends_minimal_idempotent_receipt() -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/v1/email/send"
        assert request.headers["Idempotency-Key"] == "game-receipt:ORDER-42"
        body = __import__("json").loads(request.content)
        assert set(body) == {"to", "subject", "html"}
        assert body["to"] == "player@example.com"
        return httpx.Response(200, json={"ok": True, "data": {"message_id": "msg_42"}})

    client = InfraiClient(api_key="test-key", transport=httpx.MockTransport(respond))
    try:
        result = ReceiptSender(client).send(order(ModerationState.APPROVED))
    finally:
        client.close()

    assert result.delivery == "sent"
    assert result.message_id == "msg_42"
