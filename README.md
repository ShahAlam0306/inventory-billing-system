# 🛒 Inventory & Billing Management System

A modern Inventory & Billing Management System built using **Flask**, **PostgreSQL**, and **Bootstrap**. This application helps grocery stores, retail shops, and small businesses manage inventory, generate bills, track sales, and monitor stock levels through an easy-to-use dashboard.

---

## ✨ Features

- 🔐 Secure Login Authentication
- 📦 Inventory Management (Add, Edit, Delete Products)
- 🏷️ Product Categories
- 💰 Billing / Point of Sale (POS)
- 📉 Automatic Stock Deduction
- 📊 Dashboard Analytics
- ⚠️ Low Stock Alerts
- 🧾 Sales History
- 🖨️ PDF Invoice Generation
- 📱 Responsive User Interface

---

## 🛠 Tech Stack

### Backend
- Python 3
- Flask
- SQLAlchemy
- PostgreSQL

### Frontend
- HTML5
- CSS3
- Bootstrap 5
- JavaScript
- Chart.js

### Libraries
- Flask-Login
- ReportLab
- Gunicorn
- Python Dotenv

---

## 📂 Project Structure

```
inventory-billing-system/
│
├── app.py
├── models.py
├── config.py
├── requirements.txt
├── README.md
├── .gitignore
│
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── dashboard.html
│   ├── inventory.html
│   ├── billing.html
│   ├── bills.html
│   ├── bill_detail.html
│   └── invoice_pdf.html
│
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       ├── billing.js
│       └── dashboard.js
│
└── screenshots/
```

---

# 🚀 Installation

## 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/inventory-billing-system.git

cd inventory-billing-system
```

---

## 2. Create Virtual Environment

### Windows

```bash
python -m venv venv

venv\Scripts\activate
```

### Linux / Mac

```bash
python3 -m venv venv

source venv/bin/activate
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Create PostgreSQL Database

```sql
CREATE DATABASE inventory_billing_db;
```

---

## 5. Configure Database

Open **config.py** and update your local PostgreSQL password.

```python
SQLALCHEMY_DATABASE_URI = os.environ.get(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:YOUR_PASSWORD@localhost/inventory_billing_db"
)
```

---

## 6. Initialize Database

```bash
flask --app app seed
```

This creates:

- Database Tables
- Default Admin Account

---

## 7. Run the Application

```bash
flask --app app run
```

Open:

```
http://127.0.0.1:5000
```

---

# 👤 Default Login

Username

```
admin
```

Password

```
admin123
```

**Change the password before deploying to production.**

---

# 📈 Dashboard

The dashboard provides:

- Today's Sales
- Bills Generated
- Total Revenue
- Low Stock Products
- Sales Charts
- Weekly & Monthly Analytics

---

# 🧾 Billing

The billing module supports:

- Add products to cart
- Quantity management
- Automatic stock deduction
- Bill generation
- PDF Invoice generation

---

# 📦 Inventory

Manage products with:

- Product Name
- Category
- Price
- Stock Quantity
- Reorder Level

Products with low stock are automatically highlighted.

---

# ☁️ Deployment (Render)

## Build Command

```bash
pip install -r requirements.txt
```

## Start Command

```bash
gunicorn app:app
```

## Environment Variables

```
DATABASE_URL=<Render PostgreSQL URL>

SECRET_KEY=<Your Secret Key>
```

After deployment:

```bash
flask --app app seed
```

---

# 📸 Screenshots

Add screenshots inside:

```
screenshots/
```

Example:

```
screenshots/
│
├── login.png
├── dashboard.png
├── inventory.png
├── billing.png
├── invoice.png
```

---

# 🔮 Future Improvements

- Barcode Scanner
- Customer Management
- Supplier Management
- Excel Export
- Sales Reports
- User Roles
- Purchase Management
- GST Support
- Backup & Restore

---

# 📄 License

This project is licensed under the MIT License.

---

# 👨‍💻 Author

**Shahalam Rayeen**

GitHub

https://github.com/ShahAlam0306

LinkedIn

https://www.linkedin.com/in/shahalam-rayeen-104435319

Portfolio

https://shahalam-portfolio.vercel.app
