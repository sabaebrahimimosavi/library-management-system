"""
Stands in for a real provider (Stripe, PayPal, etc.) until one is wired
in. Swapping to a real gateway later should only require rewriting
`MockPaymentGateway.charge()` — nothing in FineService or the views
talks to a specific provider directly, they just look at
`{"success": bool, "reference": str}`.

Deterministic test behavior (mirrors common gateway sandboxes): a card
number ending in "0002" always declines; everything else succeeds.
This makes the decline path testable without any randomness or network
calls.
"""

import uuid


class PaymentDeclined(Exception):
    """Raised by FineService when the gateway declines a charge."""


class MockPaymentGateway:
    DECLINE_SUFFIX = "0002"

    @classmethod
    def charge(cls, *, amount, card_number: str) -> dict:
        reference = f"mock_{uuid.uuid4().hex[:16]}"
        declined = bool(card_number) and card_number.strip().endswith(
            cls.DECLINE_SUFFIX
        )
        return {"success": not declined, "reference": reference}
