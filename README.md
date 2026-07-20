# Inventory & Billing Software for Local Shops

Flask + MySQL starter project.

## Project structure
```
inventory_billing/
├── app.py              # routes: auth, inventory, billing, dashboard
├── models.py            # User, Product, Bill, BillItem
├── config.py             # DB connection config
├── requirements.txt
├── templates/            # Jinja2 + Bootstrap templates
└── static/css/style.css
```

## Setup (each team member runs this once)

1. **Make sure PostgreSQL is installed and running** on your machine (you can check with `psql --version`). On Windows, the PostgreSQL installer includes a tool called **pgAdmin** — a GUI you can use instead of the command line for the next step if you prefer.

2. **Create the database.** Open a terminal and run:
   ```bash
   psql -U postgres
   ```
   It'll ask for the password you set when installing PostgreSQL. Once you're in the `postgres=#` prompt, run:
   ```sql
   CREATE DATABASE inventory_billing_db;
   \q
   ```
   (`\q` quits back to your normal terminal.) If you prefer a GUI, you can instead open pgAdmin, right-click "Databases" → Create → Database, and name it `inventory_billing_db`.

3. **Create a virtual environment and install dependencies:**
   ```bash
   python -m venv venv
   source venv/bin/activate    
  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

4. **Set your DB connection.** Open `config.py` and replace `password` with your actual PostgreSQL password (the same one you used in step 2):
   ```python
   SQLALCHEMY_DATABASE_URI = os.environ.get(
       "DATABASE_URL",
       "postgresql+psycopg2://postgres:YOUR_PASSWORD_HERE@localhost/inventory_billing_db"
   )
   ```
   Every team member edits this to match their own local PostgreSQL password — this file is just for local dev, so it's fine if everyone's is slightly different.

5. **Create tables + a default admin user:**
   ```bash
   flask --app app seed
   ```
   This prints login credentials: `admin` / `admin123` — change this before your final demo.

6. **Run the app:**
   ```bash
   flask --app app run --debug
   ```
   Visit http://127.0.0.1:5000

## Deploying online (so anyone with a link can use it)

We'll use [Render](https://render.com) — it has a free tier for both the web app and a small PostgreSQL database, no credit card needed.

1. **Push this project to GitHub** (create a new repo, upload all these files — an empty `venv` folder should NOT be uploaded, only the code).

2. **Create the database on Render:**
   - Sign up at render.com, click **New → PostgreSQL**
   - Give it a name (e.g. `inventory-billing-db`), choose the free plan, click **Create Database**
   - Once created, copy the **Internal Database URL** shown on its page — you'll need it next

3. **Create the web service:**
   - Click **New → Web Service**, connect your GitHub repo
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
   - Under **Environment Variables**, add:
     - `DATABASE_URL` = (paste the Internal Database URL from step 2)
     - `SECRET_KEY` = any random string (e.g. `my-super-secret-key-123`)
   - Click **Create Web Service**

4. **Create the tables on the live database:**
   - Once deployed, open the **Shell** tab on your web service in Render's dashboard
   - Run: `flask --app app seed`
   - This creates your tables and the default admin login on the live database

5. **Done.** Render gives you a public URL like `https://inventory-billing.onrender.com` — share that link with anyone, including your friend, and they can use the app directly in their browser. No setup needed on their end.

**Note:** Render's free tier "spins down" the app after 15 minutes of inactivity — the first visit after a break takes ~30 seconds to wake up. This is normal and fine for a demo/viva.

- Login/logout with hashed passwords (Flask-Login)
- Inventory CRUD (add/edit/delete products, low-stock highlighting)
- Billing/POS screen — add products to a cart, checkout deducts stock automatically
- Sales history + individual bill/invoice view
- Dashboard with today's totals, low-stock alerts, and a 7-day sales chart (Chart.js)

## Suggested next steps for your team
- Add role-based permissions (only admin can delete products / see all cashiers' sales)
- Add PDF invoice download using WeasyPrint (render `bill_detail.html` to PDF)
- Add a signup/user-management page for admins to create cashier accounts
- Add product search/barcode field on the billing screen
- Write a few unit tests (e.g. checkout fails correctly when stock is insufficient)

## Notes
- Passwords are hashed with Werkzeug's `generate_password_hash` — never store plain text.
- Stock deduction and bill creation happen in a single DB transaction (see `checkout()` in `app.py`) — if anything fails, nothing is saved, so stock numbers can't go wrong.
