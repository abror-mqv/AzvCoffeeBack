# Free Coffee Redeem Flow

Policy:
- Only 1 active redeem token per client.
- When stamps reach 7 during paid purchase, issue exactly 1 redeem token (8 digits, TTL 7 days) and reduce stamps by 7. Stamps are capped at 6 while a redeem token exists.
- Regular codes are 6 digits (TTL 15 minutes). Redeem tokens are 8 digits.

Client
- GET /api/client/info/
  - Response:
    - redeem_token: string|null  // 8-digit code if active free token exists
    - other profile fields…
  - If redeem_token present, app shows “Возьми свой бесплатный кофе” with QR.

- POST /api/loyalty/code/generate/
  - Generates a 6-digit regular code for barista.

- POST /api/loyalty/code/generate-free/
  - Generates an 8-digit redeem token if business rules allow (typically auto-issued on purchase at 7 stamps).

Barista
- POST /api/loyalty/code/verify/
  - Body: { "code": "string(6|8)" }
  - 200 OK:
    - For 6-digit (regular): { success: true, free_token: false, user: {...} }
    - For 8-digit (redeem): { success: true, free_token: true, instruction: "Выдай бесплатный кофе этому гостю", confirm_required: true, user: {...} }
  - 400/403/404 on errors.

- POST /api/loyalty/free-coffee/confirm/
  - Body: { "code": "string(8)" }
  - 200 OK:
    - { success: true, message: "Бесплатный кофе выдан", transaction_id: <id> }
  - Effect: deactivates the token, creates a zero-amount audit transaction.

Paid Purchase
- POST /api/loyalty/transaction/create/
  - Body: { "code": "string(6)", "amount": intSom, "points_to_use": int, "coffee_quantity": int }
  - Validates: cannot use an 8-digit redeem token here.
  - Effects:
    - Points: accrue (rank-based) on (amount - points_to_use).
    - Stamps: increment by coffee_quantity, then:
      - If no active redeem token and total >= 7 → issue exactly one redeem token, subtract 7, cap residual to 6.
      - If active redeem token exists → cap stamps to 6.
    - Code is deactivated.

Status
- GET /api/loyalty/code/status/?code=string(6|8)
  - Response: { code, status: "active"|"used"|"expired", is_active, is_expired, used, should_redirect }