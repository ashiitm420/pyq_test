# Optional Razorpay support

Flask creates and verifies orders; Vue opens Standard Checkout only after a
supporter clicks Continue to payment. Entries appear on About and completed
result pages. No login, subscription, paid access or exam-time popup is added.

## Configuration

Install `requirements.txt`, then set `RAZORPAY_KEY_ID` and
`RAZORPAY_KEY_SECRET` in the server's ignored `.env` (local) or Render environment
variables (deployment). `.env.example` has placeholders only. Never put a secret
in a VITE variable, source, screenshot, commit or browser bundle. The public key
ID is supplied by the create-order response; Vite needs no payment credentials.

Use test keys first. The originally supplied test secret was shared in chat;
regenerate it after testing and update the server. Keys are not interchangeable:
orders created before a key-ID change need attention under their original key.

Run `flask --app backend:create_app db upgrade` before starting the app. Docker's
existing entrypoint already runs migrations. The additive `support_order` table
stores only order/receipt IDs, hashed browser ownership, amount, currency, key ID,
provider payment ID and status; it contains no card, bank, email or phone data.

## Testing

1. Start Flask with `flask --app backend:create_app run` and Vite with
   `cd frontend && npm run dev` (or use the existing Docker deployment).
2. Open `/about`, click Support MauryaHub, choose an amount and continue.
3. Use Razorpay's documented test payment details. Test keys move no real money.
4. Verify cancellation, a failed test payment, success and verification retry.
   The app thanks the supporter only after signature validation and a matching
   captured payment. An authorized payment remains pending, with a status button.
5. Check the Razorpay Test Dashboard. A successful SDK popup alone is not proof
   of captured/settled money. No end-to-end card/UPI payment is performed by tests.

For real support payments, confirm the business use case is approved, configure
automatic capture in Razorpay, set live keys on the server, deploy and test the
complete flow. Public website contact/refund/privacy information should accurately
describe voluntary support. No webhook or automatic reconciliation job is added;
the dashboard remains the record for payments not revisited by the browser.

## API and safeguards

- POST `/api/create-order`: integer `amount` in paise, INR only, 100–1,000,000
  paise. The server generates the receipt and stores the returned order. Response
  includes order_id, amount, currency, public key_id and test_mode.
- POST `/api/verify-payment`: razorpay_order_id, razorpay_payment_id and
  razorpay_signature. Uses the server-stored, browser-owned order ID for
  HMAC-SHA256 and constant-time comparison, then fetches payment amount/currency/
  order/status before marking captured. Repeated callbacks are idempotent.
- Both endpoints retain the app's CSRF protection and no-store policy. Amounts,
  missing/mismatched fields and signatures return 400; provider authentication
  failure returns 401; provider failures return sanitized 500; missing config 503.
- SDK is lazily imported on server payment requests. Its calls have bounded
  network timeouts and no automatic creation retry. No DB connection is held
  across provider I/O. Rate limits bound optional-payment request traffic.
- Checkout JS is downloaded only on a payment click, not on home/exam loads.
  SPA HTML permits the required Razorpay script/frame/connect origins in CSP;
  unrelated public study pages keep their original CSP.

Automated tests use synthetic credentials and a fake provider, never real keys.
