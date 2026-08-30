from fastapi import FastAPI, HTTPException

from .infrai_client import InfraiClient, InfraiError
from .models import ReceiptRequest, ReceiptResult
from .receipt_sender import ReceiptSender

app = FastAPI(title="Game receipt service")


@app.post("/receipts", response_model=ReceiptResult)
def send_receipt(order: ReceiptRequest) -> ReceiptResult:
    client = InfraiClient()
    try:
        return ReceiptSender(client).send(order)
    except InfraiError as exc:
        caller_status = exc.status_code if 400 <= exc.status_code < 500 else 502
        raise HTTPException(
            status_code=caller_status,
            detail={"code": exc.code, "detail": exc.detail},
        ) from exc
    finally:
        client.close()
