# JORDAN LUDO HACK AI — UI Demo

A static frontend prototype for a Telegram Mini App-style interface.

## Included
- Dark/gold gaming-style design
- Non-clickable 3D dice with continuous 360-degree rotation
- Analyze Dice button that reveals subscription plans
- Plans: ₹699 / 3 days, ₹999 / 5 days, ₹1,999 / 30 days, ₹4,999 / lifetime
- UPI QR placeholder and UTR field for a future manual-review workflow

## Run locally
Open `index.html` in a browser.

## Before public launch
This is frontend-only. It does not verify payments, contact an admin, or activate/expire subscriptions.
Add a backend, persistent database, authenticated admin approval, and server-side subscription expiry before taking payments.
Keep any secret keys on the server, never in frontend JavaScript.

Dice outcomes in a third-party Ludo game cannot be guaranteed or reliably predicted from prior rolls. The interface therefore avoids claiming guaranteed wins.
