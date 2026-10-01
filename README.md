# Lunar Market Research — V10.1 web app

A password-protected Streamlit app adapted from Duncan's supplied Bucholtz / Meridian / McWhirter V10.1 notebook. The original notebook is unchanged. This package contains the extracted strategy engine, a browser interface and Render deployment settings.

## What is included

- Individual ticker entry and Finviz CSV uploads (Ticker or Symbol column).
- Original liquid-stock universe when ticker entry and CSV are both empty.
- Stocks, commodities or both; long-only setting; adjustable shortlist.
- Bucholtz, Meridian, McWhirter, technical confirmation, quantum levels and execution-window evidence.
- Bundled 10,754-record first-trade database; optional session-specific replacement.
- Cached lunar clocks for shortlisted candidates; applying, exact and separating contacts.
- PDF, CSV and HTML downloads; database and 2026–2030 trigger calendar downloads.
- Password gate, isolated browser-session state and market-data diagnostics.

## Deploy using GitHub and Render

1. Extract this ZIP on your computer.
2. In GitHub create a **private** repository named `lunar-market-research`.
3. Upload the **contents** of the extracted `lunar-research-app` folder to the repository root. `app.py`, `service.py`, `engine_core.py`, `requirements.txt` and `render.yaml` must appear directly at the top level. Include `.streamlit/config.toml` if your upload method supports hidden folders; it only controls appearance.
4. In Render choose **New > Web Service**, connect GitHub and select this repository.
5. Select the Python runtime and use these settings:

| Setting | Value |
| --- | --- |
| Build command | `pip install -r requirements.txt` |
| Start command | `streamlit run app.py --server.address 0.0.0.0 --server.port $PORT --server.headless true` |
| Health check path | `/_stcore/health` |
| `PYTHON_VERSION` environment variable | `3.12.8` |
| `APP_PASSWORD` environment variable | A long password you choose; enter it only in Render, never in GitHub |

6. Choose the compute plan in Render, review its displayed charge, then create the service. The included Blueprint selects **Starter**, a paid tier. If you prefer a different tier, select it manually or edit `plan` before using the Blueprint.
7. When deployment succeeds, open the Render URL and sign in with your app password.
8. Scan one familiar ticker first, then test a small Finviz export and download the PDF. Check price-data dates and diagnostics before trusting a result.

Alternative: use **New > Blueprint** and select this repository. Render reads `render.yaml` and prompts for APP_PASSWORD. The Blueprint has the same commands and settings above.

## Local use on Windows

Install Python 3.12, open PowerShell in the extracted app folder, then run:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:APP_PASSWORD = "choose-your-own-password"
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Open the local URL printed by Streamlit. Run checks with:

```powershell
.\.venv\Scripts\python.exe -m unittest test_app.py -v
```

## How to use

Choose a date and market, enter tickers or upload a Finviz export, then **Run scan**. Read the decision and market-data dates. Select **Calculate shortlisted lunar clocks** if you want the full session clock on screen. **Prepare PDF, CSV and HTML reports** calculates those clocks automatically before producing downloads.

The sidebar database upload is for your first-trade/IPO database, **not** your Finviz watchlist. It needs `Ticker` and `Date` columns and usable dates on every row. Database replacement is session-specific and clears old scan results. Restore the bundled database with its dedicated button.

## Conversion notes

The extracted source definitions and patch order retain the notebook's scoring logic. `service.py` supplies session isolation, custom ticker lists, temporary report paths and input validation. It also fixes a notebook performance problem: the V10.1 wrapper called the older eager lunar calculation before removing its result. The app bypasses that eager wrapper and runs the same cached V10.1 calculation only after shortlisting. The original HTML exporter predates the complete PDF, so the app appends the full final evidence to HTML exports.

The original strategy can return NO TRADE rows even with long-only selected. This preserves its evidence/reporting behaviour; long-only does not turn bearish or unconfirmed setups into eligible long trades. A shortlist contains ranked research candidates, not orders or a guarantee of a trade.

## Practical limits

- No broker connection or automatic order execution is included.
- Financial astrology is not scientifically established as a forecasting method. Scores are the notebook's model implementations, not probabilities or published formulas from the authors.
- Yahoo/yfinance daily data can be delayed, unavailable or rate-limited from cloud hosting. Empty market data must not be interpreted as a successful NO TRADE finding.
- The original notebook's daily OHLC date handling and intraday execution model are retained. This is not a point-in-time backtest or live intraday execution feed. Today's daily bar can be provisional.
- The lunar session model excludes weekends but does not implement exchange holiday/early-close calendars. Treat holiday and shortened-session output cautiously.
- First-trade 'verified' labels are inherited from the supplied database, not independently verified in this conversion. Date-only records use modelling assumptions; missing and ambiguous records remain labelled.
- Uploaded databases and scan results live in the browser session. Refreshes, disconnected sessions, restarts and redeploys can clear them. Download reports you want to keep.
- Scans are serialised within the server process to protect shared native astronomy/Yahoo state. Start with small watchlists. This is a personal research app, not a multi-user subscription product.
- The shared password is a personal-use access gate. User accounts, subscriptions and stronger access controls would be a separate addition.
- Swiss Ephemeris/pyswisseph has licence obligations; review the upstream licence before commercial distribution or offering a subscription service.

## Validation performed

Local automated checks verify CSV parsing and ticker normalisation, a deterministic stock scan through all strategy layers, lazy lunar computation, PDF/CSV/HTML generation, session isolation, invalid database rejection, and Streamlit sign-in/control loading. Price data in the scan check is synthetic. Live Yahoo access and deployment on your actual Render account have not been verified.

Official deployment references:
- https://render.com/docs/web-services
- https://render.com/docs/blueprint-spec
- https://docs.streamlit.io/deploy/tutorials/docker
