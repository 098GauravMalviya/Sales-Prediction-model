import joblib
import sqlite3
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware  # ← NEW: needed for React
from pydantic import BaseModel
from typing import Optional
from prophet import Prophet
import os
from database.create_database import get_connection, SmartQuery

app = FastAPI(title="Generalized Sales Prediction API")
FRONTEND_URL = os.getenv("https://sales-prediction-model-mu.vercel.app/", "http://localhost:5173")

# ── NEW: CORS — without this your React frontend cannot call this API ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000",
        FRONTEND_URL, "",
        "https://*.vercel.app",],  # your React dev server port
    allow_methods=["*"],
    allow_headers=["*"],
)

#login signup endpoints

class AuthRequest(BaseModel):
    username: str
    password: str
    full_name: Optional[str] = None

@app.post("/login")
def login(data: AuthRequest):
    if data.username and data.password:
        return {"status": "success", "username": data.username}
    raise HTTPException(400, "Invalid credentials")

@app.post("/signup")
def signup(data: AuthRequest):
    if data.username and data.password:
        return {"status": "success", "username": data.username}
    raise HTTPException(400, "Signup failed")

# ── LOAD MODEL ────────────────────────────────────────────────────────
try:
    model = joblib.load('model.pkl')
    print("✅ ML Model loaded successfully.")
except Exception as e:
    model = None
    print(f"❌ Error loading model: {e}")

try:
    feature_columns = joblib.load('model_features.pkl')
    print(f"✅ Feature columns loaded: {len(feature_columns)} features")
except Exception as e:
    feature_columns = None
    print(f"❌ Error loading feature columns: {e}")

# ── VALIDATION CONSTANTS ──────────────────────────────────────────────
VALID_CATEGORIES = ['Electronics', 'Accessories', 'Office']
VALID_REGIONS    = ['North', 'East', 'South', 'West']
VALID_TICKERS    = ['NVDA', 'SAMSUNG', 'SONY']
MAX_DATE         = '2025-03-31'   # 90 days beyond training data end

# ── REQUEST SCHEMA ────────────────────────────────────────────────────
class MarketQuery(BaseModel):
    state    : Optional[str] = None
    region   : Optional[str] = None     # ← NEW: was missing, needed for one-hot
    holiday  : Optional[str] = None
    ticker   : Optional[str] = None
    commodity: Optional[str] = None
    category : Optional[str] = None
    year     : Optional[int] = None
    date     : Optional[str] = None     # ← NEW: needed for macro feature lookup


# ── /predict ─────────────────────────────────────────────────────────
@app.post("/predict")
async def predict_sales(query_params: MarketQuery):

    # ── Input validation ─────────────────────────────────────────────
    if query_params.category and query_params.category not in VALID_CATEGORIES:
        raise HTTPException(400, f"Invalid category. Choose from: {VALID_CATEGORIES}")

    if query_params.region and query_params.region not in VALID_REGIONS:
        raise HTTPException(400, f"Invalid region. Choose from: {VALID_REGIONS}")

    if query_params.ticker and query_params.ticker.upper() not in VALID_TICKERS:
        raise HTTPException(400, f"Invalid ticker. Choose from: {VALID_TICKERS}")

    if query_params.date:
        try:
            pd.to_datetime(query_params.date)
        except Exception:
            raise HTTPException(400, "Invalid date format. Use YYYY-MM-DD")
        if query_params.date > MAX_DATE:
            raise HTTPException(400, f"Date too far ahead — reliable predictions only up to {MAX_DATE}")

    if model is None or feature_columns is None:
        raise HTTPException(503, "Model not loaded. Run sales_analysis.py first.")

    conn = get_connection()
    sq   = SmartQuery(conn)

    try:
        # ── 1. Pull historical context from DB ───────────────────────
        context_df = sq.query(

            holiday=query_params.holiday,
            ticker=query_params.ticker,
            commodity=query_params.commodity,
            category=query_params.category,
            year=query_params.year,
            include_macro=True
        )
        # Attempt 2: drop holiday and ticker
        if context_df.empty:
            context_df = sq.query(
                category=query_params.category,
                year=query_params.year,
                include_macro=True
            )

        # Attempt 3: just category
        if context_df.empty and query_params.category:
            context_df = sq.query(
                category=query_params.category,
                include_macro=True
            )

        # Attempt 4: guaranteed fallback — last 100 records
        if context_df.empty:
            context_df = pd.read_sql("""
                SELECT s.date, s.revenue, s.profit, s.quantity, s.category,
                    mi.usd_inr, mi.inflation_india, mi.interest_india
                FROM sales s
                LEFT JOIN macro_indicators mi ON s.date = mi.date
                ORDER BY s.date DESC
                LIMIT 100
            """, conn)
        

        if context_df.empty:
            raise HTTPException(404, "No matching historical data found.")

        latest_data = context_df.iloc[-1]

        # ── 2. Build feature row with ALL columns model expects ───────
        # Start with zeros for every column the model was trained on
        input_dict = {col: 0 for col in feature_columns}

        # Date-based features
        ref_date = pd.to_datetime(query_params.date) if query_params.date \
                   else pd.to_datetime(str(latest_data.get('date', '2024-01-01')))

        input_dict['month']       = ref_date.month
        input_dict['week']        = ref_date.isocalendar()[1]
        input_dict['day_of_week'] = ref_date.dayofweek
        input_dict['quarter']     = ref_date.quarter
        input_dict['is_holiday']  = 1 if query_params.holiday else 0

        # Lag features from historical context
        input_dict['sales_lag_7']          = float(latest_data.get('revenue') or 0) * 0.95
        input_dict['sales_lag_30']         = float(latest_data.get('revenue') or 0) * 0.90
        input_dict['sales_rolling_7_mean'] = float(latest_data.get('revenue') or 0)

        # Stock prices from context
        input_dict['nvidia_close']  = float(latest_data.get('stock_close') or 0) \
                                      if query_params.ticker == 'NVDA' else 0
        input_dict['samsung_close'] = float(latest_data.get('stock_close') or 0) \
                                      if query_params.ticker == 'SAMSUNG' else 0

        # Macro + commodity from ml_features table by date
        

        # ── NEW: One-hot encode category and region ───────────────────
        # This is what was missing — the model needs these as separate columns
        if query_params.category:
            col = f"Category_{query_params.category}"
            if col in input_dict:
                input_dict[col] = 1

        if query_params.region:
            col = f"Region_{query_params.region}"
            if col in input_dict:
                input_dict[col] = 1

        # ── 3. Predict ────────────────────────────────────────────────
        input_df   = pd.DataFrame([input_dict])[feature_columns]  # enforce column order
        prediction = model.predict(input_df)

        return {
            "input_context": query_params,
            "prediction_results": {
                "estimated_revenue"     : round(float(prediction[0]), 2),
                "currency"              : "INR",
                "historical_sample_size": len(context_df),
                "basis_date"            : ref_date.strftime('%Y-%m-%d'),
                "warning"               : "Prediction based on historical patterns. "
                                          "Accuracy decreases further from training range (2022-2024)."
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))
    finally:
        conn.close()


# ── /forecast ─────────────────────────────────────────────────────────
@app.get("/forecast")
def get_forecast(days: int = 90):
    """Returns Prophet 90-day forecast for the React chart."""
    if days > 365:
        raise HTTPException(400, "Maximum forecast is 365 days.")
    conn = get_connection()
    try:
        daily = pd.read_sql(
            "SELECT date AS ds, SUM(revenue) AS y FROM sales GROUP BY date ORDER BY date",
            conn
        )
        daily['ds'] = pd.to_datetime(daily['ds'])
        daily = daily.dropna(subset=['y'])

        holiday_df = pd.read_sql(
            "SELECT date AS ds, name AS holiday FROM holidays", conn
        )
        holiday_df['ds'] = pd.to_datetime(holiday_df['ds'])

        m = Prophet(holidays=holiday_df, yearly_seasonality=True, weekly_seasonality=True)
        m.fit(daily)
        future   = m.make_future_dataframe(periods=days)
        forecast = m.predict(future)

        result = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(days).copy()
        result['ds'] = result['ds'].astype(str)
        return {"days_ahead": days, "forecast": result.to_dict(orient="records")}
    finally:
        conn.close()


# ── /analytics/holidays ───────────────────────────────────────────────
@app.get("/analytics/holidays")
def holiday_analytics():
    """Total revenue and quantity per holiday — for dashboard cards."""
    conn = get_connection()
    try:
        sq = SmartQuery(conn)
        return sq.holiday_sales_summary().fillna(0).to_dict(orient="records")
    finally:
        conn.close()


# ── /analytics/commodity/{name} ───────────────────────────────────────
@app.get("/analytics/commodity/{commodity_name}")
def commodity_analytics(commodity_name: str):
    """Monthly commodity price vs sales — for impact chart."""
    conn = get_connection()
    try:
        sq = SmartQuery(conn)
        df = sq.commodity_impact(commodity_name)
        if df.empty:
            raise HTTPException(404, f"No data found for commodity: {commodity_name}")
        return df.fillna(0).to_dict(orient="records")
    finally:
        conn.close()


# ── /analytics/macro ─────────────────────────────────────────────────
@app.get("/analytics/macro")
def macro_analytics():
    """Monthly sales with USD/INR, inflation, interest rate."""
    conn = get_connection()
    try:
        sq = SmartQuery(conn)
        return sq.macro_sales_trend().fillna(0).to_dict(orient="records")
    finally:
        conn.close()


# ── /analytics/stock/{ticker} ─────────────────────────────────────────
@app.get("/analytics/stock/{ticker}")
def stock_analytics(ticker: str):
    """Daily revenue vs stock price correlation data."""
    if ticker.upper() not in VALID_TICKERS:
        raise HTTPException(400, f"Invalid ticker. Choose from: {VALID_TICKERS}")
    conn = get_connection()
    try:
        sq = SmartQuery(conn)
        df = sq.stock_sales_correlation(ticker.upper())
        return df.fillna(0).to_dict(orient="records")
    finally:
        conn.close()


# ── /health ───────────────────────────────────────────────────────────
@app.get("/health")
def health_check():
    return {
        "status"        : "active",
        "model_ready"   : model is not None,
        "features_ready": feature_columns is not None,
        "feature_count" : len(feature_columns) if feature_columns else 0,
        "valid_categories": VALID_CATEGORIES,
        "valid_regions"   : VALID_REGIONS,
        "valid_tickers"   : VALID_TICKERS,
        "max_date"        : MAX_DATE,
    }