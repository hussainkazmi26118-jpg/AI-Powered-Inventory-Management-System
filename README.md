# Stockwise — AI-Powered Inventory Management System

A beginner-friendly inventory dashboard built with **Python, Flask, OOP, HTML, CSS, JavaScript, JSON storage, and optional Groq Generative AI**.

## Features

- Product CRUD: add, view, edit, and delete products.
- Search products by name, product ID, or category.
- Standard `Product` and inherited `PerishableProduct` models.
- Dashboard totals: product count, units, inventory value, low-stock count, and out-of-stock count.
- Stock status calculated from quantity and reorder level.
- JSON persistence for local development and demonstrations.
- Optional Groq AI: inventory analysis, reorder suggestions, inventory Q&A, and product description generation.
- Core inventory functions continue working when the Groq key is not configured.
- Responsive green-and-white dashboard.
- Vercel serverless entry point included.

## Project structure

```text
AI_Powered_Inventory_Management_System/
├── api/
│   └── index.py
├── data/
│   └── products.json
├── static/
│   ├── app.js
│   └── style.css
├── templates/
│   └── index.html
├── .env.example
├── .gitignore
├── ai_helper.py
├── app.py
├── inventory.py
├── models.py
├── requirements.txt
├── vercel.json
└── README.md
```

## Requirements

- Python 3.10 or newer
- pip
- Optional: a Groq API key from [Groq Console](https://console.groq.com/)

## Run on Windows (PowerShell)

1. Extract the project ZIP.
2. Open PowerShell in the extracted project folder. The folder should contain `app.py`.
3. Check Python:

   ```powershell
   py --version
   ```

   If `py` is unavailable, try `python --version`. Install Python from [python.org](https://www.python.org/downloads/) if neither command works. During installation, select **Add Python to PATH**.

4. Create a virtual environment:

   ```powershell
   py -m venv venv
   ```

5. Activate it:

   ```powershell
   .\venv\Scripts\Activate.ps1
   ```

   If PowerShell blocks activation, run this once in the same terminal:

   ```powershell
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   .\venv\Scripts\Activate.ps1
   ```

6. Install dependencies:

   ```powershell
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

7. Create your local environment file:

   ```powershell
   Copy-Item .env.example .env
   ```

8. (Optional) Open `.env` and add your Groq key:

   ```env
   GROQ_API_KEY=your_real_groq_api_key
   GROQ_MODEL=llama-3.3-70b-versatile
   ```

   Keep `.env` private. It is excluded from Git. If you do not add a key, the inventory dashboard and CRUD functions still work; only AI endpoints are disabled.

9. Start the server:

   ```powershell
   python app.py
   ```

10. Open **http://127.0.0.1:5000** in your browser. Stop the server with `Ctrl + C`.

### Run on macOS/Linux

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Optionally edit .env and add GROQ_API_KEY
python app.py
```

## How stock status works

- **Out of stock:** quantity is `0`.
- **Low stock:** quantity is greater than `0` and less than or equal to the product's reorder level.
- **In stock:** quantity is greater than the reorder level.

Inventory value is calculated as `price × quantity` for every product and then summed.

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/products` | List products; optional `?q=search-term` |
| POST | `/api/products` | Create a product |
| PUT | `/api/products/<product_id>` | Update a product |
| DELETE | `/api/products/<product_id>` | Delete a product |
| GET | `/api/stats` | Dashboard statistics |
| POST | `/api/ai/analyze` | AI inventory analysis |
| POST | `/api/ai/reorder` | AI reorder suggestions |
| POST | `/api/ai/ask` | Ask an inventory question |
| POST | `/api/ai/description` | Generate a product description |

### Example product JSON

```json
{
  "name": "Wireless Keyboard",
  "category": "Electronics",
  "price": 25.5,
  "quantity": 12,
  "reorder_level": 5,
  "description": "Compact wireless keyboard.",
  "product_type": "standard"
}
```

For a perishable product, use `"product_type": "perishable"` and provide `"expiry_date": "2027-01-31"`.

## Groq configuration

The application reads:

- `GROQ_API_KEY`: your secret API key.
- `GROQ_MODEL`: model identifier. The default is `llama-3.3-70b-versatile`.

You can change the model in `.env` or your hosting provider's environment-variable settings. Model availability and provider limits may change. The app catches AI errors and displays a helpful message rather than disabling inventory management.

## GitHub upload

1. Create a new empty repository on GitHub.
2. Open a terminal in the project folder.
3. Initialize Git and commit the files:

   ```bash
   git init
   git add .
   git commit -m "Build AI-powered inventory management system"
   git branch -M main
   git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPOSITORY.git
   git push -u origin main
   ```

4. Replace the remote URL with your own repository URL.
5. Confirm `.env` is not in the uploaded files. Never upload your real Groq key.

## Deploy to Vercel

1. Push the project to GitHub.
2. Sign in to [Vercel](https://vercel.com/) and choose **Add New → Project**.
3. Import the GitHub repository.
4. Vercel should detect the included `vercel.json` and `api/index.py` Python function.
5. In **Project Settings → Environment Variables**, add:
   - `GROQ_API_KEY` = your Groq API key (optional)
   - `GROQ_MODEL` = `llama-3.3-70b-versatile` (optional)
6. Deploy, then open the deployment URL.

### Important: JSON storage on Vercel

The included JSON file is suitable for local learning, demos, and a single local process. Vercel serverless deployments use an ephemeral/read-only deployment filesystem for application files, and function instances may be replaced or run separately. Therefore, **do not use this JSON storage as production persistence on Vercel**. For a real business deployment, replace `InventoryManager`'s JSON repository with Supabase or PostgreSQL (for example, using a managed database and environment-based connection string). Add the database URL as a Vercel environment variable and never commit credentials.

## Notes and troubleshooting

- **`python` is not recognized:** On Windows try `py --version`; if unavailable, reinstall Python and enable PATH.
- **PowerShell activation is blocked:** use the process-scoped execution policy command shown above.
- **Port already in use:** stop the other Flask process or set a different `PORT` environment variable.
- **AI buttons show “not configured”:** check `.env`, confirm the key is correct, restart Flask, and verify `GROQ_MODEL`.
- **Data file errors:** ensure the `data` folder is writable and `products.json` contains valid JSON.
- Currency is displayed in USD in this starter version. Change the `money()` function in `static/app.js` if you want another display currency; stored prices are numeric and have no currency conversion.

## Production checklist

Before using this for real business inventory, add authentication and authorization, CSRF protection for cookie-authenticated deployments, audit logs, automated backups, database persistence, rate limiting for AI endpoints, and tests. Do not expose this starter dashboard publicly with sensitive business data until access control is implemented.
