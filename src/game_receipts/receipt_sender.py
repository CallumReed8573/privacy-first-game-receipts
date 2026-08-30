from html import escape

from .infrai_client import InfraiClient
from .models import ModerationState, ReceiptRequest, ReceiptResult


class ReceiptSender:
    def __init__(self, client: InfraiClient) -> None:
        self._client = client

    def send(self, order: ReceiptRequest) -> ReceiptResult:
        if order.asset.moderation_state is not ModerationState.APPROVED:
            return ReceiptResult(
                order_id=order.order_id,
                delivery="held",
                reason="asset_moderation_incomplete",
            )

        amount = f"{order.amount:.2f} {order.currency}"
        html = (
            "<h1>Purchase receipt</h1>"
            f"<p>Order <strong>{escape(order.order_id)}</strong></p>"
            f"<p>{escape(order.asset.display_name)} for "
            f"{escape(order.live_event.title)}</p>"
            f"<p>Total: {escape(amount)}</p>"
        )
        data = self._client.email_send(
            {
                "to": str(order.player_email),
                "subject": f"Receipt for order {order.order_id}",
                "html": html,
            },
            idempotency_key=f"game-receipt:{order.order_id}",
        )
        return ReceiptResult(
            order_id=order.order_id,
            delivery="sent",
            message_id=str(data["message_id"]),
        )
