# SalesTrack — Inventory Management System

> HARVEY DACILLO
> 
> A desktop inventory and sales tracking application built with Python and PyQt5.
> Designed for small businesses with a focus on clean UI, real-time data, and ease of use.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Screenshots](#screenshots)
- [Requirements](#requirements)
- [Installation](#installation)
- [Running the App](#running-the-app)
- [Seeding the Database](#seeding-the-database)
- [Default Credentials](#default-credentials)
- [Project Structure](#project-structure)
- [Navigation](#navigation)
- [Tech Stack](#tech-stack)
- [Demo Data](#demo-data)

---

## Overview

SalesTrack is a fully offline, single-user desktop application that helps small business owners manage their product catalog, record transactions, and monitor sales performance — all from one screen. It runs entirely locally with no internet connection or server required.

The application ships with a pre-seeded SQLite database containing 20 products and over 1,800 realistic sales transactions spread across 180 days, giving you a fully working demo the moment you launch it.

---

## Features

### Dashboard
- **4 live KPI cards** — Total Products, Units in Stock, Total Sales, and Revenue, each with an animated sparkline graph showing 30-day trends
- **Donut chart** — Revenue breakdown by category with live percentage labels
- **Transaction feed** — Scrollable list of the 50 most recent sales with product name, timestamp, and amount
- **Low Stock Alerts table** — Highlights any product with 5 or fewer units remaining
- **Light / Dark theme toggle** — Switch themes at any time from the navigation bar

### Products
- Card grid view of all products with category icon, stock badge, price, and image support
- **Search and filter** by name or category
- **Sort** by newest, oldest, price, or name
- **Edit Product** — inline dialog to update name, category, price, stock, and product image
- **Delete** with confirmation — removes the product and all related sales records
- Right-click context menu on any card for quick access

### Add Product
- Form with product name, category dropdown, sub-category, description, price, and initial stock
- **Drag-and-drop image upload** or file browser (PNG, JPG, WEBP, BMP)
- **Quick-set stock buttons** (0, 10, 50, 100) for fast input
- **Tag system** with preset tags (New Arrival, Best Seller, On Sale, Featured, Imported, Local)

### Record Sale
- **Live product search** — type to filter the dropdown in real time
- **Custom dropdown delegate** — each item shows product name, price, and a color-coded stock pill (green/orange/red)
- **Quick quantity buttons** (1, 2, 5, 10, 20)
- **Order Summary panel** — shows product image, category, unit price, in-stock count, order total, and remaining stock after the sale
- Fully styled success / warning / error dialogs (no OS-native popups)

### Sales History
- Full transaction table with product, category, quantity, unit price, total, and timestamp
- **KPI chips** — total transactions, units sold, total revenue, and average sale
- Filter by category, search by product or date, sort by newest/oldest/amount
- Alternating row colors with amber accent on totals

---

## Requirements

| Dependency | Version |
|---|---|
| Python | 3.9 or higher |
| PyQt5 | 5.15 or higher |
| Pillow | 9.0 or higher (for image processing) |

No web server, no external database, no internet connection required.

---

## Installation

**1. Clone or extract the project**

```
Inventory System/
├── app_manager.py
├── dashboard.py
├── styles.py
├── database/
│   ├── database.py
│   ├── seed_database.py
│   └── sales_inventory.db
└── assets/
    ├── icons/
    └── ui/
```

**2. Install dependencies**

```bash
pip install PyQt5 Pillow
```

Or if you are on a system-managed Python environment:

```bash
pip install PyQt5 Pillow --break-system-packages
```

---

## Running the App

Navigate into the `Inventory System` folder and run:

```bash
python app_manager.py
```

The app opens full screen. Press **F11** to toggle full screen, or **Escape** to exit full screen mode.

---

## Seeding the Database

The repository ships with a pre-seeded `sales_inventory.db` so the app works immediately. If you want to reset to a clean demo state, run the seeder:

```bash
cd "Inventory System"
python database/seed_database.py
```

The seeder will:

- Wipe all existing products and sales (users are kept)
- Insert **20 products** across 5 categories
- Generate **~1,800 sales transactions** over 180 days
- Apply a **wave-shaped volume pattern** so sparklines show visible high/low swings across the dashboard

Seeder output:

```
  ✔  Inserted 20 products
  ✔  Inserted 1,812 sales transactions
  ✔  Total units sold  : 4,291
  ✔  Total revenue     : ₱5,813,759.00

  Revenue by category:
    Electronics          ₱2,261,993.00  (445 tx)
    Sports & Fitness     ₱1,183,888.00  (347 tx)
    Clothing             ₱1,049,815.00  (331 tx)
    Food & Beverage      ₱  757,425.00  (399 tx)
    Home & Garden        ₱  560,638.00  (290 tx)
```

---

## Default Credentials

| Field | Value |
|---|---|
| Username | `admin` |
| Password | `admin123` |

---

## Project Structure

```
Inventory System/
│
├── app_manager.py              Entry point — initializes DB, launches login
├── dashboard.py                Main window, navigation bar, KPI cards, charts
├── styles.py                   Shared theme system (light/dark), color tokens,
│                               combo_style(), input_style(), spinbox_style(),
│                               dialog_style(), msgbox_style()
│
├── database/
│   ├── database.py             SQLite connection, schema init, login verification
│   ├── seed_database.py        Demo data seeder (20 products, 1800+ sales)
│   └── sales_inventory.db      Live SQLite database
│
└── assets/
    ├── icons/                  Dashboard KPI card icons (150×150 transparent PNG)
    │   ├── products.png
    │   ├── stocks.png
    │   ├── sales.png
    │   └── revenue.png
    ├── images/
    │   └── products/           User-uploaded product images (saved on add/edit)
    └── ui/
        ├── login.py            Animated login screen with orb canvas
        ├── add_product.py      Add Product form (two-column layout)
        ├── view_all_products.py  Product card grid + Edit/Delete dialogs
        ├── record_sale.py      Sale recording with custom dropdown delegate
        └── view_all_sales.py   Full sales history table with KPI chips
```

---

## Navigation

The app uses a floating pill navigation bar at the bottom of the screen.

| Tab | Description |
|---|---|
| **Dashboard** | Live overview — KPIs, sparklines, donut chart, transactions |
| **Add Product** | Form to create a new product listing |
| **Products** | Browse, edit, and delete the full product catalog |
| **Record Sale** | Record a new sales transaction |
| **Sales History** | View and filter all past transactions |

Additional controls in the navigation bar:

| Control | Action |
|---|---|
| **D / L** button | Toggle dark / light theme |
| **admin** badge | Shows the logged-in user |
| **LOGOUT** | Returns to the login screen |
| **X** | Exits the application |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.9+ |
| UI framework | PyQt5 (Qt 5.15) |
| Database | SQLite 3 via `sqlite3` stdlib |
| Image processing | Pillow (PIL) |
| Charts | Custom QPainter — SparkLine, DonutChart |
| Theming | Centralized `styles.py` with light/dark token system |
| Dialogs | Fully custom `QDialog` subclasses (no OS-native popups) |

---

## Demo Data

The pre-seeded database contains the following 20 products:

| Category | Product | Price |
|---|---|---|
| Electronics | Mechanical Keyboard RGB | PHP 3,799 |
| Electronics | Wireless Noise-Cancel Earbuds | PHP 2,499 |
| Electronics | Portable Power Bank 20000mAh | PHP 1,899 |
| Electronics | USB-C Hub 7-in-1 | PHP 899 |
| Clothing | Running Shoes Lightweight | PHP 2,199 |
| Clothing | Premium Hoodie Oversized | PHP 1,299 |
| Clothing | Slim Fit Chinos Khaki | PHP 999 |
| Clothing | Compression Leggings Pro | PHP 799 |
| Food & Beverage | Whey Protein Vanilla 1kg | PHP 1,499 |
| Food & Beverage | Single-Origin Coffee Beans 500g | PHP 699 |
| Food & Beverage | Matcha Powder Premium 100g | PHP 549 |
| Food & Beverage | Mixed Nuts Roasted 500g | PHP 449 |
| Sports & Fitness | Adjustable Dumbbell Set 20kg | PHP 3,299 |
| Sports & Fitness | Yoga Mat Premium 6mm | PHP 899 |
| Sports & Fitness | Resistance Band Set Pro | PHP 649 |
| Sports & Fitness | Jump Rope Speed Pro | PHP 399 |
| Home & Garden | Ceramic Pour-Over Coffee Set | PHP 1,199 |
| Home & Garden | Smart LED Strip 5m RGB | PHP 799 |
| Home & Garden | Bamboo Desk Organizer Set | PHP 599 |
| Home & Garden | Scented Soy Candle Set 3pc | PHP 549 |

Sales data uses a **compound sine wave pattern** across 180 days so every sparkline on the dashboard shows dramatic peaks and troughs — making the charts meaningful at a glance.

---

*Built with PyQt5 · SQLite · Python 3 · Harvey Dacillo*
