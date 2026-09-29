# POS Billing Software – Textile / Retail

A Point of Sale and billing system with an Admin Portal, a Billing Portal for staff, and a mobile-app-style layout of the complete Admin Portal.

## Live links
- Live app: `<LIVE_URL>`
- Mobile admin (full Admin Portal, phone layout): `<LIVE_URL>/mobile-admin/`
- Source: `<GITHUB_URL>`

## Test credentials
| Role  | Username | Password |
|-------|----------|----------|
| Admin | `<admin_user>` | `<admin_pass>` |
| Staff (billing, discounts up to N%, returns allowed) | `<staff_user>` | `<staff_pass>` |

## Tech stack
- **Backend:** Python, Django, Django REST Framework (token auth for the JSON API)
- **Database:** PostgreSQL by default, with an SQLite option for a quick local try (`DB_ENGINE=sqlite`)
- **Frontend:** Django templates, Bootstrap 5, Bootstrap Icons, vanilla JavaScript for the billing screen
- **Apps:** `accounts` (roles, permissions, business settings), `catalog` (products, categories, suppliers, customers, stock), `billing` (sales, payments, returns, ledger, reports)

## Features

### Admin Portal
- **Products:** create, edit and deactivate products with category, supplier, size, colour, prices, tax %, stock, reorder level and image. Search plus category and low-stock filters.
- **Categories, suppliers, customers:** full management. Each supplier page lists the products it supplies, and each customer page shows purchase history.
- **Staff:** create, edit, deactivate and reset passwords. Per-staff permissions cover discounts (with a maximum %) and returns. Each staff page shows their transaction history and totals.
- **Inventory:** stock-in purchases and manual adjustments, with a full stock movement log and low-stock alerts.
- **Transactions:** search and filter by invoice, customer, date, payment method and staff, with CSV export.
- **Returns:** a staff return is only a request. An admin approves it, which refunds, restocks and writes to the ledger, or rejects it, which changes nothing. Admins process returns directly.
- **Ledger and reports:** a running ledger (sales as credits, refunds as debits). Reports for sales by period, best sellers (net of returns), sales by staff, payments, returned products and low stock, all exportable.
- **Settings:** the business name, address, phone, GSTIN and footer note printed on invoices.

### Billing Portal (staff)
- Select products, set quantities, optionally attach a customer, apply a discount (only if permitted, capped at the staff member's limit), and take payment by cash, card or UPI. Cash shows change due.
- Printable invoice with the business details from Settings.
- Staff see only their own transactions and can raise return requests if permitted.

### Mobile Admin
`/mobile-admin/` switches the whole Admin Portal into a phone layout: bottom tab bar (Home, Products, Sales, Reports, More), a grid of every other section under More, and card lists instead of tables. Every admin page works in this mode. "Desktop view" switches back.

## Access control and transaction handling
- Two roles, admin and staff. Admin pages are protected by an `admin_required` decorator, so staff get a 403 on them.
- Staff can only view their own invoices and transactions.
- Checkout and returns run inside database transactions with row locks (`select_for_update`), so a failed sale leaves nothing half-saved and stock cannot go negative. The database also has a non-negative stock constraint.
- Sales are never edited or deleted. Returns add new records, and each item keeps a price, tax and discount snapshot from the time of sale.
- Discounts are validated on the server, not just in the browser.

## Setup
```bash
python -m venv venv
venv\Scripts\activate          # Windows  (source venv/bin/activate on macOS/Linux)
pip install -r requirements.txt
```

**Database.** Either use PostgreSQL:
```bash
createdb pos
# set the environment variables: DB_NAME, DB_USER, DB_PASSWORD, DB_HOST
```
or, for a quick try, use SQLite by setting the environment variable `DB_ENGINE=sqlite`.
(Windows PowerShell: `$env:DB_ENGINE="sqlite"`)

**Create the tables and run:**
```bash
python manage.py makemigrations accounts catalog billing
python manage.py migrate
python manage.py createsuperuser     # the superuser becomes an Admin automatically
python manage.py runserver
```
Open http://127.0.0.1:8000/ and log in. Create staff accounts under **Staff** in the sidebar, where each person's role, discount limit and return permission are also set.

## Main URLs
| URL | Purpose |
|-----|---------|
| `/login/` | Sign in |
| `/dashboard/` | Admin dashboard |
| `/mobile-admin/` | Admin Portal in mobile layout |
| `/billing/` | Billing Portal for staff |
| `/ledger/`, `/reports/`, `/settings/` | Ledger, reports, invoice settings |
| `/django-admin/` | Raw database admin (superuser) |
| `/api/`, `/api/auth/token/` | REST API and token login |

## Assumptions and limitations
- Tax is a per-product percentage, applied after the discount. A discount is split across items in proportion to their value.
- Refunds are proportional to the line total, including tax and discount.
- Return approval is enforced in the web portal. `<Note here whether the return API also enforces it>`
- Payments are recorded only. There is no real card or UPI gateway.
- Printing uses the browser's print dialog.
- Single store and single currency (INR).
