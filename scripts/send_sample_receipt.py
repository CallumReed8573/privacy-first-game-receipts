import os
import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from game_receipts.infrai_client import InfraiClient
from game_receipts.models import LiveEvent, ModerationState, PlayerAsset, ReceiptRequest
from game_receipts.receipt_sender import ReceiptSender


recipient = os.environ.get("RECEIPT_EMAIL_TO")
if not recipient:
    raise SystemExit("RECEIPT_EMAIL_TO is required")

client = InfraiClient()
try:
    result = ReceiptSender(client).send(
        ReceiptRequest(
            order_id="ORDER-2048",
            player_email=recipient,
            amount=Decimal("14.99"),
            currency="USD",
            asset=PlayerAsset(
                asset_id="skin-neon-7",
                display_name="Neon Arena Skin",
                moderation_state=ModerationState.APPROVED,
            ),
            live_event=LiveEvent(
                event_id="arena-finals",
                title="Arena Finals",
                starts_at=datetime(2026, 9, 1, 18, 0, tzinfo=UTC),
            ),
        )
    )
    print(result.model_dump_json())
finally:
    client.close()
