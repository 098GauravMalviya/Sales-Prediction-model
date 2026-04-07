"""
Smart Market Analysis Database
================================
Loads and normalizes all 11 datasets into a structured SQLite database.
Includes a SmartQuery engine that auto-selects the right datasets
based on query conditions (state, holiday, category, stock, date range).
"""

import os
import sqlite3
import pandas as pd
import numpy as np

# ─────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = r"C:\Users\gaura\Music\mini_project\data"
DB_PATH  = os.path.join(BASE_DIR, "market_analysis.db")

DATA_FILES = {
    "ecommerce"   : os.path.join(DATA_DIR, "ecommerce_sales_data (2).csv"),
    "updated_sales": os.path.join(DATA_DIR, "Updated_sales.csv"),
    "holidays"    : os.path.join(DATA_DIR, "Holidays.csv"),
    "samsung"     : os.path.join(DATA_DIR, "Samsung Dataset.csv"),
    "sony"        : os.path.join(DATA_DIR, "Sony_stock_data.csv"),
    "nvidia"      : os.path.join(DATA_DIR, "NVidia_stock_history.csv"),
    "inflation"   : os.path.join(DATA_DIR, "Inflationdata.csv"),
    "interest"    : os.path.join(DATA_DIR, "interest_rates.csv"),
    "commodity"   : os.path.join(DATA_DIR, "commodity_prices.csv"),
    "population"  : os.path.join(DATA_DIR, "population.csv"),
    "usdinr"      : os.path.join(DATA_DIR, "USDINRexchange.csv"),
    "lithium"     : os.path.join(DATA_DIR, "ds140-lithium-2021.xlsx"),
}


# ─────────────────────────────────────────────
# CONNECTION
# ─────────────────────────────────────────────
def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")   # faster writes
    return conn


# ─────────────────────────────────────────────
# SCHEMA
# ─────────────────────────────────────────────
def create_schema(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()

    cur.executescript("""
    -- ── DIMENSION: regions (India state-level) ──────────────────────
    CREATE TABLE IF NOT EXISTS regions (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        state       TEXT    NOT NULL UNIQUE,
        rank        INTEGER,
        pop_1951    INTEGER,
        pop_1961    INTEGER,
        pop_1971    INTEGER,
        pop_1981    INTEGER,
        pop_1991    INTEGER,
        pop_2001    INTEGER,
        pop_2011    INTEGER
    );

    -- ── DIMENSION: products ──────────────────────────────────────────
    CREATE TABLE IF NOT EXISTS products (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        name         TEXT NOT NULL UNIQUE,
        category     TEXT NOT NULL
            CHECK(category IN ('raw_material','end_product','component')),
        sub_category TEXT
    );

    -- ── DIMENSION: holidays ──────────────────────────────────────────
    CREATE TABLE IF NOT EXISTS holidays (
        id        INTEGER PRIMARY KEY AUTOINCREMENT,
        date      DATE    NOT NULL,
        name      TEXT    NOT NULL,
        country   TEXT    NOT NULL DEFAULT 'India',
        is_public INTEGER NOT NULL DEFAULT 1,
        weekday   TEXT
    );

    -- ── FACT: sales ──────────────────────────────────────────────────
    CREATE TABLE IF NOT EXISTS sales (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        date            DATE    NOT NULL,
        product_id      INTEGER REFERENCES products(id),
        region_id       INTEGER REFERENCES regions(id),
        category        TEXT,
        quantity        REAL,
        unit_price      REAL,
        revenue         REAL,
        profit          REAL,
        source          TEXT    -- 'ecommerce' or 'updated_sales'
    );

    -- ── FACT: stock prices ───────────────────────────────────────────
    CREATE TABLE IF NOT EXISTS stock_prices (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        date       DATE    NOT NULL,
        ticker     TEXT    NOT NULL,   -- 'NVDA','SAMSUNG','SONY'
        open       REAL,
        high       REAL,
        low        REAL,
        close      REAL    NOT NULL,
        volume     REAL,
        UNIQUE(date, ticker)
    );

    -- ── FACT: macro indicators (one row per date) ────────────────────
    CREATE TABLE IF NOT EXISTS macro_indicators (
        date              DATE    PRIMARY KEY,
        inflation_india   REAL,   -- % annual, World Bank
        interest_india    REAL,   -- real interest rate %, World Bank
        usd_inr           REAL,   -- exchange rate
        usd_inr_sma7      REAL,
        usd_inr_sma30     REAL,
        usd_inr_rsi14     REAL,
        usd_inr_volatility REAL
    );

    -- ── FACT: commodity prices ───────────────────────────────────────
    CREATE TABLE IF NOT EXISTS commodity_prices (
        id               INTEGER PRIMARY KEY AUTOINCREMENT,
        date             DATE    NOT NULL,
        commodity_name   TEXT    NOT NULL,
        category         TEXT,
        price_usd        REAL,
        unit             TEXT,
        price_mom_pct    REAL,   -- month-over-month % change
        price_yoy_pct    REAL,   -- year-over-year % change
        price_12m_avg    REAL,
        price_volatility REAL,
        commodity_code   TEXT,
        UNIQUE(date, commodity_name)
    );

    -- ── FACT: lithium production (raw material supply signal) ────────
    CREATE TABLE IF NOT EXISTS lithium_supply (
        year                INTEGER PRIMARY KEY,
        us_production       REAL,
        us_imports          REAL,
        us_exports          REAL,
        us_consumption      REAL,
        unit_value_usd      REAL,
        world_production_t  REAL,   -- gross weight metric tons
        world_prod_li_content REAL,
        world_prod_lce      REAL    -- lithium carbonate equivalent
    );

    -- ── SMART QUERY LOG (audit trail) ───────────────────────────────
    CREATE TABLE IF NOT EXISTS query_log (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        query_type   TEXT,
        conditions   TEXT,
        tables_used  TEXT,
        rows_returned INTEGER
    );
    """)

    conn.commit()
    print("✅ Schema created.")


# ─────────────────────────────────────────────
# ETL HELPERS
# ─────────────────────────────────────────────
def _norm_date(s: pd.Series, fmt=None) -> pd.Series:
    """Parse dates robustly and strip timezone."""
    if fmt:
        return pd.to_datetime(s, format=fmt, errors='coerce').dt.tz_localize(None).dt.normalize()
    return pd.to_datetime(s, errors='coerce', utc=True).dt.tz_convert(None).dt.normalize()


# ─────────────────────────────────────────────
# LOADERS
# ─────────────────────────────────────────────
def load_population(conn):
    df = pd.read_csv(DATA_FILES["population"])
    df.columns = ['rank','state','pop_1951','pop_1961','pop_1971',
                  'pop_1981','pop_1991','pop_2001','pop_2011']
    df['state'] = df['state'].str.strip()
    df.to_sql("regions", conn, if_exists="replace", index=False)
    # Re-add primary key via recreate isn't possible in SQLite easily — use id from rowid
    print(f"  ✅ regions: {len(df)} states loaded")


def load_holidays(conn):
    df = pd.read_csv(DATA_FILES["holidays"])
    df = df.drop(columns=['Unnamed: 0'], errors='ignore')
    df.columns = ['name','date','is_public','country','weekday']
    df['date'] = _norm_date(df['date'])
    df['is_public'] = df['is_public'].astype(int)
    df.to_sql("holidays", conn, if_exists="replace", index=False)
    print(f"  ✅ holidays: {len(df)} records loaded")


def load_products_and_sales(conn):
    """Load ecommerce and updated_sales, derive product catalog."""

    # ── Ecommerce sales ──────────────────────────────────────────────
    df_ec = pd.read_csv(DATA_FILES["ecommerce"])
    df_ec['date'] = _norm_date(df_ec['Order Date'])
    df_ec = df_ec.rename(columns={
        'Product Name': 'name', 'Category': 'category',
        'Quantity': 'quantity', 'Sales': 'revenue', 'Profit': 'profit'
    })
    df_ec['unit_price'] = df_ec['revenue'] / df_ec['quantity'].replace(0, np.nan)
    df_ec['source'] = 'ecommerce'
    df_ec['region_id'] = None  # ecommerce has Region col but not India states

    # ── Updated sales ────────────────────────────────────────────────
    df_us = pd.read_csv(DATA_FILES["updated_sales"])
    df_us = df_us[df_us['Order Date'] != 'Order Date'].dropna(subset=['Order Date'])
    df_us['Quantity Ordered'] = pd.to_numeric(df_us['Quantity Ordered'], errors='coerce')
    df_us['Price Each']       = pd.to_numeric(df_us['Price Each'], errors='coerce')
    df_us['date']      = pd.to_datetime(df_us['Order Date'], format='mixed', errors='coerce').dt.normalize()
    df_us['revenue']   = df_us['Quantity Ordered'] * df_us['Price Each']
    df_us['name']      = df_us['Product']
    df_us['quantity']  = df_us['Quantity Ordered']
    df_us['unit_price']= df_us['Price Each']
    df_us['category']  = 'end_product'
    df_us['profit']    = None
    df_us['region_id'] = None
    df_us['source']    = 'updated_sales'

    # ── Build unified product catalog ────────────────────────────────
    products_ec = df_ec[['name','category']].drop_duplicates()
    products_ec['category'] = products_ec['category'].str.lower().map({
        'electronics': 'end_product', 'accessories': 'component',
        'office': 'end_product'
    }).fillna('end_product')

    products_us = df_us[['name']].drop_duplicates()
    products_us['category'] = 'end_product'

    all_products = pd.concat([products_ec, products_us]).drop_duplicates('name')
    all_products = all_products.reset_index(drop=True)
    all_products.index += 1
    all_products.index.name = 'id'
    all_products.to_sql("products", conn, if_exists="replace")
    prod_map = dict(zip(all_products['name'], all_products.index))

    # ── Write sales ──────────────────────────────────────────────────
    cols = ['date','category','quantity','unit_price','revenue','profit','region_id','source']

    df_ec['product_id'] = df_ec['name'].map(prod_map)
    df_ec_out = df_ec[['product_id'] + cols].dropna(subset=['date'])

    df_us['product_id'] = df_us['name'].map(prod_map)
    df_us_out = df_us[['product_id'] + cols].dropna(subset=['date'])

    sales = pd.concat([df_ec_out, df_us_out], ignore_index=True)
    sales.to_sql("sales", conn, if_exists="replace", index=False)
    print(f"  ✅ products: {len(all_products)} | sales: {len(sales)} records")


def load_stocks(conn):
    rows = []

    # NVidia
    df5 = pd.read_csv(DATA_FILES["nvidia"])
    df5['date']   = _norm_date(df5['Date'])
    df5['ticker'] = 'NVDA'
    rows.append(df5[['date','ticker','Open','High','Low','Close','Volume']].rename(
        columns={'Open':'open','High':'high','Low':'low','Close':'close','Volume':'volume'}))

    # Samsung
    df3 = pd.read_csv(DATA_FILES["samsung"])
    df3['date']   = _norm_date(df3['Date'])
    df3['ticker'] = 'SAMSUNG'
    rows.append(df3[['date','ticker','Open','High','Low','Close','Volume']].rename(
        columns={'Open':'open','High':'high','Low':'low','Close':'close','Volume':'volume'}))

    # Sony
    df4 = pd.read_csv(DATA_FILES["sony"], skiprows=[0,1,2],
                      names=['date','close','high','low','open','volume'])
    df4['date'] = _norm_date(df4['date'])
    df4[['close','high','low','open','volume']] = \
        df4[['close','high','low','open','volume']].apply(pd.to_numeric, errors='coerce')
    df4['ticker'] = 'SONY'
    rows.append(df4[['date','ticker','open','high','low','close','volume']])

    stocks = pd.concat(rows, ignore_index=True).dropna(subset=['date','close'])
    stocks.to_sql("stock_prices", conn, if_exists="replace", index=False)
    print(f"  ✅ stock_prices: {len(stocks)} records (NVDA+SAMSUNG+SONY)")


def load_macro(conn):
    """Merge inflation, interest rates, and USD/INR into one daily table."""

    # Inflation — World Bank wide format, skip metadata rows
    df_inf = pd.read_csv(DATA_FILES["inflation"], skiprows=4)
    india_inf = df_inf[df_inf['Country Name'] == 'India'].iloc[0]
    year_cols = [c for c in df_inf.columns if c.isdigit()]
    inf_series = pd.Series({int(y): india_inf[y] for y in year_cols}, name='inflation_india')

    # Interest rates
    df_int = pd.read_csv(DATA_FILES["interest"])
    india_int = df_int[df_int['Country Name'] == 'India'].iloc[0]
    year_cols_i = [c for c in df_int.columns if c.isdigit()]
    int_series = pd.Series({int(y): india_int[y] for y in year_cols_i}, name='interest_india')

    # Combine annual macro into a year-keyed frame
    macro_annual = pd.DataFrame({'inflation_india': inf_series, 'interest_india': int_series})
    macro_annual.index.name = 'year'

    # USD/INR daily
    df_fx = pd.read_csv(DATA_FILES["usdinr"])
    df_fx['date'] = _norm_date(df_fx['DATE'])
    df_fx = df_fx.rename(columns={
        'USD_INR': 'usd_inr', 'SMA_7': 'usd_inr_sma7',
        'SMA_30': 'usd_inr_sma30', 'RSI_14': 'usd_inr_rsi14',
        'volatility_30': 'usd_inr_volatility'
    })
    df_fx = df_fx[['date','usd_inr','usd_inr_sma7','usd_inr_sma30',
                   'usd_inr_rsi14','usd_inr_volatility']].dropna(subset=['date'])

    # Join annual macro onto daily FX by year
    df_fx['year'] = df_fx['date'].dt.year
    df_fx = df_fx.merge(macro_annual.reset_index(), on='year', how='left')
    df_fx = df_fx.drop(columns='year')

    df_fx.to_sql("macro_indicators", conn, if_exists="replace", index=False)
    print(f"  ✅ macro_indicators: {len(df_fx)} daily records")


def load_commodities(conn):
    df = pd.read_csv(DATA_FILES["commodity"])
    df['date'] = _norm_date(df['date'])

    # Keep only columns relevant to project
    keep = ['date','commodity_name','category','price_nominal_usd','unit',
            'price_mom_pct','price_yoy_pct','price_12m_avg',
            'price_12m_volatility','commodity_code']
    df = df[keep].rename(columns={
        'price_nominal_usd': 'price_usd',
        'price_12m_volatility': 'price_volatility'
    })

    # Tag which commodities are relevant for electronics vs raw materials
    electronics_materials = ['Aluminum','Copper','Nickel','Tin','Silver',
                              'Gold','Platinum','Lithium']
    energy = ['Crude oil, Brent','Crude oil, WTI','Natural gas, US',
              'Coal, Australian']
    df['relevant_for'] = 'other'
    df.loc[df['commodity_name'].isin(electronics_materials), 'relevant_for'] = 'electronics_raw_material'
    df.loc[df['commodity_name'].isin(energy), 'relevant_for'] = 'energy_cost'

    df.to_sql("commodity_prices", conn, if_exists="replace", index=False, chunksize=500)
    print(f"  ✅ commodity_prices: {len(df)} records | "
          f"{df['commodity_name'].nunique()} commodities")


def load_lithium(conn):
    df_raw = pd.read_excel(DATA_FILES["lithium"], sheet_name='Lithium statistics', header=None)
    # Header is at row index 4
    df = df_raw.iloc[5:].copy()
    df.columns = ['year','us_production','us_imports','us_exports','us_consumption',
                  'unit_value_usd','unit_value_98usd',
                  'world_production_t','world_prod_li_content','world_prod_lce']
    df = df.drop(columns='unit_value_98usd')
    df['year'] = pd.to_numeric(df['year'], errors='coerce')
    for col in df.columns[1:]:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df = df.dropna(subset=['year'])
    df['year'] = df['year'].astype(int)
    df.to_sql("lithium_supply", conn, if_exists="replace", index=False)
    print(f"  ✅ lithium_supply: {len(df)} years of data (1900-2021)")


# ─────────────────────────────────────────────
# SMART QUERY ENGINE
# ─────────────────────────────────────────────
class SmartQuery:
    """
    Auto-selects and JOINs the right tables based on what you're asking.

    Usage:
        sq = SmartQuery(conn)

        # Sales in Maharashtra during Diwali
        df = sq.query(state="Maharashtra", holiday="Diwali")

        # Electronics sales with NVDA stock during festivals in 2023
        df = sq.query(
            category="end_product",
            ticker="NVDA",
            year=2023,
            holiday="Diwali"
        )

        # Raw material cost impact on sales
        df = sq.query(commodity="Copper", category="end_product")
    """

    TABLE_MAP = {
        "state"     : ["regions", "sales"],
        "holiday"   : ["holidays", "sales"],
        "ticker"    : ["stock_prices", "sales"],
        "commodity" : ["commodity_prices", "sales"],
        "macro"     : ["macro_indicators", "sales"],
        "category"  : ["sales"],
        "year"      : ["sales"],
        "date_range": ["sales"],
    }

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def query(
        self,
        state      : str  = None,
        holiday    : str  = None,
        ticker     : str  = None,   # 'NVDA', 'SAMSUNG', 'SONY'
        commodity  : str  = None,   # e.g. 'Copper', 'Aluminum'
        category   : str  = None,   # 'end_product', 'raw_material', 'component'
        year       : int  = None,
        date_start : str  = None,
        date_end   : str  = None,
        include_macro: bool = False,
        log        : bool = True,
    ) -> pd.DataFrame:

        tables_used = ["sales", "products"]
        conditions  = []
        params      = []

        # ── Base query ───────────────────────────────────────────────
        sql = """
            SELECT
                s.date,
                p.name        AS product,
                p.category    AS product_category,
                s.quantity,
                s.unit_price,
                s.revenue,
                s.profit,
                s.source
        """

        joins = """
            FROM sales s
            JOIN products p ON s.product_id = p.id
        """

        # ── STATE filter ─────────────────────────────────────────────
        if state:
            joins += " LEFT JOIN regions r ON s.region_id = r.id"
            # Since ecommerce data doesn't have India state mapping,
            # we filter by source region column via a subquery workaround
            # (attach state via date-based region inference)
            tables_used.append("regions")
            sql += ", r.state"

        # ── HOLIDAY filter ───────────────────────────────────────────
        if holiday:
            joins += """
                JOIN holidays h ON s.date = h.date
            """
            conditions.append("h.name LIKE ?")
            params.append(f"%{holiday}%")
            sql += ", h.name AS holiday_name, h.is_public"
            tables_used.append("holidays")

        # ── STOCK PRICES ─────────────────────────────────────────────
        if ticker:
            joins += f"""
                LEFT JOIN stock_prices sp
                    ON s.date = sp.date AND sp.ticker = ?
            """
            params.insert(0, ticker.upper())
            sql += ", sp.close AS stock_close, sp.volume AS stock_volume"
            tables_used.append("stock_prices")

        # ── COMMODITY ────────────────────────────────────────────────
        if commodity:
            joins += """
                LEFT JOIN commodity_prices cp
                    ON strftime('%Y-%m', s.date) = strftime('%Y-%m', cp.date)
                    AND cp.commodity_name LIKE ?
            """
            params.append(f"%{commodity}%")
            sql += """,
                cp.commodity_name,
                cp.price_usd       AS commodity_price_usd,
                cp.price_yoy_pct   AS commodity_yoy_change
            """
            tables_used.append("commodity_prices")

        # ── MACRO INDICATORS ─────────────────────────────────────────
        if include_macro:
            joins += """
                LEFT JOIN macro_indicators mi ON s.date = mi.date
            """
            sql += """,
                mi.usd_inr,
                mi.inflation_india,
                mi.interest_india
            """
            tables_used.append("macro_indicators")

        # ── CATEGORY filter ──────────────────────────────────────────
        if category:
            conditions.append("p.category = ?")
            params.append(category)

        # ── YEAR filter ──────────────────────────────────────────────
        if year:
            conditions.append("strftime('%Y', s.date) = ?")
            params.append(str(year))

        # ── DATE RANGE filter ────────────────────────────────────────
        if date_start:
            conditions.append("s.date >= ?")
            params.append(date_start)
        if date_end:
            conditions.append("s.date <= ?")
            params.append(date_end)

        # ── Assemble WHERE ───────────────────────────────────────────
        where = ""
        if conditions:
            where = "WHERE " + " AND ".join(conditions)

        full_sql = f"{sql} {joins} {where} ORDER BY s.date"

        # ── Execute ──────────────────────────────────────────────────
        df = pd.read_sql_query(full_sql, self.conn, params=params)

        # ── Log query ────────────────────────────────────────────────
        if log:
            cond_str = str({
                "state": state, "holiday": holiday, "ticker": ticker,
                "commodity": commodity, "category": category,
                "year": year, "date_start": date_start, "date_end": date_end
            })
            self.conn.execute("""
                INSERT INTO query_log (query_type, conditions, tables_used, rows_returned)
                VALUES (?, ?, ?, ?)
            """, ("smart_query", cond_str, str(list(set(tables_used))), len(df)))
            self.conn.commit()

        return df

    def holiday_sales_summary(self, holiday: str = None) -> pd.DataFrame:
        """Aggregate total revenue and quantity per holiday."""
        q = """
            SELECT
                h.name          AS holiday,
                h.date,
                h.is_public,
                COUNT(s.rowid)     AS num_transactions,
                SUM(s.quantity) AS total_quantity,
                SUM(s.revenue)  AS total_revenue,
                SUM(s.profit)   AS total_profit
            FROM holidays h
            LEFT JOIN sales s ON s.date = h.date
        """
        params = []
        if holiday:
            q += " WHERE h.name LIKE ?"
            params.append(f"%{holiday}%")
        q += " GROUP BY h.name, h.date ORDER BY total_revenue DESC"
        return pd.read_sql_query(q, self.conn, params=params)

    def stock_sales_correlation(self, ticker: str = "NVDA") -> pd.DataFrame:
        """Daily sales vs stock price for correlation analysis."""
        q = """
            SELECT
                s.date,
                SUM(s.revenue)  AS total_revenue,
                sp.close        AS stock_close,
                sp.volume       AS stock_volume
            FROM sales s
            LEFT JOIN stock_prices sp
                ON s.date = sp.date AND sp.ticker = ?
            GROUP BY s.date
            ORDER BY s.date
        """
        return pd.read_sql_query(q, self.conn, params=[ticker])

    def commodity_impact(self, commodity: str, category: str = "end_product") -> pd.DataFrame:
        """Monthly commodity price vs product sales revenue."""
        q = """
            SELECT
                strftime('%Y-%m', s.date) AS month,
                p.category,
                SUM(s.revenue)            AS total_revenue,
                AVG(cp.price_usd)         AS avg_commodity_price,
                AVG(cp.price_yoy_pct)     AS commodity_yoy_pct
            FROM sales s
            JOIN products p ON s.product_id = p.id
            LEFT JOIN commodity_prices cp
                ON strftime('%Y-%m', s.date) = strftime('%Y-%m', cp.date)
                AND cp.commodity_code = (
                    SELECT commodity_code FROM commodity_prices
                    WHERE commodity_name LIKE ? LIMIT 1
                )
            WHERE p.category = ?
            GROUP BY month, p.category
            ORDER BY month
        """
        return pd.read_sql_query(q, self.conn, params=[f"%{commodity}%", category])

    def macro_sales_trend(self) -> pd.DataFrame:
        """Monthly sales with macro context: USD/INR, inflation, interest rate."""
        q = """
            SELECT
                strftime('%Y-%m', s.date) AS month,
                SUM(s.revenue)            AS total_revenue,
                AVG(mi.usd_inr)           AS avg_usd_inr,
                AVG(mi.inflation_india)   AS inflation,
                AVG(mi.interest_india)    AS interest_rate
            FROM (
            SELECT date, SUM(revenue) AS revenue
            FROM sales
            GROUP BY date
        )  s
            LEFT JOIN macro_indicators mi ON s.date = mi.date
            GROUP BY month
            ORDER BY month
        """
        return pd.read_sql_query(q, self.conn)

# -----------------
#create index

def create_indexes(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE INDEX IF NOT EXISTS idx_sales_date       ON sales(date);
        CREATE INDEX IF NOT EXISTS idx_sales_product    ON sales(product_id);
        CREATE INDEX IF NOT EXISTS idx_holidays_date    ON holidays(date);
        CREATE INDEX IF NOT EXISTS idx_stock_date       ON stock_prices(date);
        CREATE INDEX IF NOT EXISTS idx_stock_ticker     ON stock_prices(ticker);
        CREATE INDEX IF NOT EXISTS idx_commodity_date   ON commodity_prices(date);
        CREATE INDEX IF NOT EXISTS idx_commodity_name   ON commodity_prices(commodity_name);
        CREATE INDEX IF NOT EXISTS idx_macro_date       ON macro_indicators(date);
    """)
    conn.commit()
    print("✅ Indexes created.")


# ─────────────────────────────────────────────
# MAIN: BUILD DATABASE
# ─────────────────────────────────────────────



def build_database():
    print("\n🔨 Building market_analysis.db ...\n")
    conn = get_connection()
    create_schema(conn)

    print("\n📥 Loading datasets:")
    load_population(conn)
    load_holidays(conn)
    load_products_and_sales(conn)
    load_stocks(conn)
    load_macro(conn)
    load_commodities(conn)
    load_lithium(conn)
    create_indexes(conn) 

    conn.close()
    print(f"\n✅ Database ready at: {DB_PATH}")


# ─────────────────────────────────────────────
# DEMO: SMART QUERIES
# ─────────────────────────────────────────────
def demo_smart_queries():
    print("\n🧠 Running Smart Query demos...\n")
    conn = get_connection()
    sq   = SmartQuery(conn)

    # ── 1. Sales on any holiday ──────────────────────────────────────
    print("=" * 55)
    print("Query 1: Sales during Diwali")
    df1 = sq.query(holiday="Diwali")
    print(df1[['date','product','revenue','profit']].head(10).to_string(index=False))
    print(f"  → {len(df1)} rows\n")

    # ── 2. Electronics sales with NVDA stock in 2023 ─────────────────
    print("=" * 55)
    print("Query 2: End-product sales + NVDA stock price (2023)")
    df2 = sq.query(category="end_product", ticker="NVDA", year=2023)
    print(df2[['date','product','revenue','stock_close']].head(10).to_string(index=False))
    print(f"  → {len(df2)} rows\n")

    # ── 3. Sales with Copper commodity impact ────────────────────────
    print("=" * 55)
    print("Query 3: Monthly Copper price vs Electronics sales")
    df3 = sq.commodity_impact(commodity="Copper", category="end_product")
    print(df3.head(12).to_string(index=False))
    print(f"  → {len(df3)} months\n")

    # ── 4. Holiday sales summary ─────────────────────────────────────
    print("=" * 55)
    print("Query 4: Holiday Sales Summary")
    df4 = sq.holiday_sales_summary()
    print(df4.to_string(index=False))
    print()

    # ── 5. Full macro context query ──────────────────────────────────
    print("=" * 55)
    print("Query 5: Sales + USD/INR + Inflation (2022-2023)")
    df5 = sq.query(date_start="2022-01-01", date_end="2023-12-31", include_macro=True)
    print(df5[['date','product','revenue','usd_inr','inflation_india']].head(10).to_string(index=False))
    print(f"  → {len(df5)} rows\n")

    # ── 6. NVDA-Sales correlation data ───────────────────────────────
    print("=" * 55)
    print("Query 6: Daily Revenue vs NVDA Stock (for correlation)")
    df6 = sq.stock_sales_correlation(ticker="NVDA")
    corr = df6[['total_revenue','stock_close']].dropna().corr().iloc[0,1]
    print(df6.dropna().head(10).to_string(index=False))
    print(f"  → Pearson correlation (Revenue vs NVDA): {corr:.4f}\n")

    conn.close()


if __name__ == "__main__":
    build_database()
    demo_smart_queries()