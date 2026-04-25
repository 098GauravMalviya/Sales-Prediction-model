import React, { useState, useEffect, useRef } from 'react';
import {
  Search, MapPin, Calendar, Zap, LogOut,
  ChevronRight, BarChart3, DollarSign, Cpu,
  Battery, Package, TrendingUp, AlertTriangle,
  CheckCircle, Loader2, Tag, Globe, Activity
} from 'lucide-react';
import {
  predictSales, getForecast, getHolidayAnalytics,
  getCommodityAnalytics, getMacroAnalytics, getStockAnalytics, checkHealth
} from './api';

// ── Validation constants (mirror your backend) ───────────────────────
const VALID_CATEGORIES = ['Electronics', 'Accessories', 'Office'];
const VALID_REGIONS    = ['North', 'East', 'South', 'West'];
const VALID_TICKERS    = ['NVDA', 'SAMSUNG', 'SONY'];
const MAX_DATE         = '2025-03-31';

export default function CommandCenter({ user, onLogout }) {
  const [isExpanded, setIsExpanded]   = useState(false);
  const [activeTab, setActiveTab]     = useState('predict');  // predict | forecast | holidays | macro | stock | commodity
  const [loading, setLoading]         = useState(false);
  const [apiReady, setApiReady]       = useState(null);       // null=checking, true, false
  const [error, setError]             = useState(null);
  const [result, setResult]           = useState(null);
  const [analyticsData, setAnalyticsData] = useState(null);

  // ── Search bar state ─────────────────────────────────────────────
  const [query, setQuery] = useState({
    category : '',
    region   : '',
    date     : '',
    holiday  : '',
    ticker   : '',
    commodity: '',
    year     : '',
  });

  // ── Validation errors ─────────────────────────────────────────────
  const [validationErrors, setValidationErrors] = useState({});

  // ── Check API health on mount ────────────────────────────────────
  useEffect(() => {
    checkHealth()
      .then((data) => setApiReady(data.model_ready && data.features_ready))
      .catch(() => setApiReady(false));
  }, []);

  // ── Validate inputs ───────────────────────────────────────────────
  const validate = () => {
    const errs = {};
    if (query.category && !VALID_CATEGORIES.includes(query.category))
      errs.category = `Must be one of: ${VALID_CATEGORIES.join(', ')}`;
    if (query.region && !VALID_REGIONS.includes(query.region))
      errs.region = `Must be one of: ${VALID_REGIONS.join(', ')}`;
    if (query.ticker && !VALID_TICKERS.includes(query.ticker.toUpperCase()))
      errs.ticker = `Must be one of: ${VALID_TICKERS.join(', ')}`;
    if (query.date && query.date > MAX_DATE)
      errs.date = `Max reliable date is ${MAX_DATE}`;
    if (query.year && (query.year < 2022 || query.year > 2025))
      errs.year = 'Year must be between 2022 and 2025';
    setValidationErrors(errs);
    return Object.keys(errs).length === 0;
  };

  // ── Main predict call ────────────────────────────────────────────
  const handleGenerate = async () => {
    setError(null);
    setResult(null);
    setAnalyticsData(null);

    if (!validate()) return;

    setLoading(true);
    try {
      const params = {
        category : query.category  || null,
        region   : query.region    || null,
        date     : query.date      || null,
        holiday  : query.holiday   || null,
        ticker   : query.ticker    ? query.ticker.toUpperCase() : null,
        commodity: query.commodity || null,
        year     : query.year      ? parseInt(query.year) : null,
      };
      const data = await predictSales(params);
      setResult(data);
      setActiveTab('predict');
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  // ── Analytics loaders ────────────────────────────────────────────
  const loadAnalytics = async (tab) => {
    setActiveTab(tab);
    setError(null);
    setAnalyticsData(null);
    setLoading(true);
    try {
      let data;
      if (tab === 'forecast')   data = await getForecast(90);
      if (tab === 'holidays')   data = await getHolidayAnalytics();
      if (tab === 'macro')      data = await getMacroAnalytics();
      if (tab === 'stock')      data = await getStockAnalytics(query.ticker || 'NVDA');
      if (tab === 'commodity')  data = await getCommodityAnalytics(query.commodity || 'Copper');
      setAnalyticsData(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0f0f0f] text-white font-sans relative">

      {/* ── Header ─────────────────────────────────────────────────── */}
      <nav className="fixed top-0 w-full z-50 flex justify-between items-center px-10 py-6 backdrop-blur-md border-b border-white/5">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-gradient-to-tr from-orange-500 to-red-600 rounded-lg flex items-center justify-center">
            <BarChart3 size={18} />
          </div>
          <span className="font-black tracking-tighter text-xl uppercase">SalesInsight AI</span>
        </div>
        <div className="flex items-center gap-6">
          {/* API status badge */}
          <div className={`flex items-center gap-2 text-[10px] font-black tracking-widest uppercase px-3 py-1 rounded-full border ${
            apiReady === null ? 'border-yellow-500/30 text-yellow-500' :
            apiReady ? 'border-green-500/30 text-green-500' :
            'border-red-500/30 text-red-500'
          }`}>
            {apiReady === null && <Loader2 size={10} className="animate-spin" />}
            {apiReady === true  && <CheckCircle size={10} />}
            {apiReady === false && <AlertTriangle size={10} />}
            {apiReady === null ? 'Connecting...' : apiReady ? 'API Live' : 'API Offline'}
          </div>
          <span className="text-[10px] font-black tracking-widest text-slate-500 uppercase">
            Pro: {user?.username}
          </span>
          <button
            onClick={onLogout}
            className="text-[10px] font-black tracking-widest uppercase border border-white/10 px-6 py-2 rounded-full hover:bg-red-500/10 hover:text-red-500 transition-all flex items-center gap-2"
          >
            <LogOut size={12} /> Logout
          </button>
        </div>
      </nav>

      {/* ── Main ───────────────────────────────────────────────────── */}
      <main className="relative pt-48 px-10 flex flex-col items-center">
        <div className="absolute top-20 left-1/2 -translate-x-1/2 w-[600px] h-[600px] bg-orange-600/10 blur-[120px] rounded-full pointer-events-none" />

        <h1 className="text-4xl md:text-6xl lg:text-7xl font-black tracking-tighter leading-[1.05] text-center max-w-5xl mb-12 w-full">
          Search{' '}
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-orange-400 to-red-600 font-extrabold whitespace-nowrap">
            Insights...
          </span>
        </h1>

        {/* ── Expanding Search Bar ──────────────────────────────────── */}
        <div
          className={`transition-all duration-500 ease-out bg-[#1a1a1a] border shadow-2xl rounded-[2.5rem] p-2 flex items-center overflow-hidden ${
            isExpanded
              ? 'w-full max-w-5xl border-orange-500/30'
              : 'w-full max-w-2xl cursor-pointer hover:border-orange-500/30 border-white/10'
          }`}
          onClick={() => !isExpanded && setIsExpanded(true)}
        >
          {!isExpanded ? (
            <div className="flex items-center gap-4 px-8 py-4 w-full">
              <Search className="text-orange-500" size={24} />
              <span className="text-slate-500 font-bold tracking-tight text-lg">
                Click to start AI Market Analysis...
              </span>
              <div className="ml-auto bg-white/5 p-2 rounded-full">
                <ChevronRight className="text-slate-500" />
              </div>
            </div>
          ) : (
            <div className="flex flex-col w-full animate-in fade-in zoom-in-95 duration-300">
              {/* Row 1 — main inputs */}
              <div className="flex flex-col md:flex-row items-center w-full">
                {/* Category */}
                <div className="flex-1 flex flex-col px-6 py-3 border-r border-white/5">
                  <div className="flex items-center gap-3">
                    <Tag className="text-orange-500 shrink-0" size={16} />
                    <input
                      autoFocus
                      list="category-options"
                      placeholder="Category (e.g. Electronics)"
                      className="bg-transparent outline-none w-full font-bold placeholder:text-slate-600 text-sm"
                      value={query.category}
                      onChange={(e) => setQuery({ ...query, category: e.target.value })}
                    />
                    <datalist id="category-options">
                      {VALID_CATEGORIES.map(c => <option key={c} value={c} />)}
                    </datalist>
                  </div>
                  {validationErrors.category && (
                    <p className="text-red-400 text-[10px] mt-1 ml-7">{validationErrors.category}</p>
                  )}
                </div>
                {/* Region */}
                <div className="flex-1 flex flex-col px-6 py-3 border-r border-white/5">
                  <div className="flex items-center gap-3">
                    <MapPin className="text-slate-400 shrink-0" size={16} />
                    <input
                      list="region-options"
                      placeholder="Region (North / South...)"
                      className="bg-transparent outline-none w-full font-bold placeholder:text-slate-600 text-sm"
                      value={query.region}
                      onChange={(e) => setQuery({ ...query, region: e.target.value })}
                    />
                    <datalist id="region-options">
                      {VALID_REGIONS.map(r => <option key={r} value={r} />)}
                    </datalist>
                  </div>
                  {validationErrors.region && (
                    <p className="text-red-400 text-[10px] mt-1 ml-7">{validationErrors.region}</p>
                  )}
                </div>
                {/* Date */}
                <div className="flex-1 flex flex-col px-6 py-3 border-r border-white/5">
                  <div className="flex items-center gap-3">
                    <Calendar className="text-slate-400 shrink-0" size={16} />
                    <input
                      type="date"
                      max={MAX_DATE}
                      className="bg-transparent outline-none w-full font-bold text-slate-300 text-sm [color-scheme:dark]"
                      value={query.date}
                      onChange={(e) => setQuery({ ...query, date: e.target.value })}
                    />
                  </div>
                  {validationErrors.date && (
                    <p className="text-red-400 text-[10px] mt-1 ml-7">{validationErrors.date}</p>
                  )}
                </div>
                {/* Generate button */}
                <button
                  onClick={handleGenerate}
                  disabled={loading || !apiReady}
                  className="bg-orange-500 hover:bg-orange-600 disabled:opacity-40 text-white px-8 py-4 rounded-[2rem] font-black uppercase text-xs tracking-widest transition-all flex items-center gap-2 whitespace-nowrap m-1"
                >
                  {loading
                    ? <><Loader2 size={14} className="animate-spin" /> Processing...</>
                    : <><Zap size={14} fill="white" /> Generate</>
                  }
                </button>
              </div>

              {/* Row 2 — optional filters */}
              <div className="flex flex-col md:flex-row border-t border-white/5 mt-1">
                <div className="flex-1 flex items-center gap-3 px-6 py-3 border-r border-white/5">
                  <Calendar className="text-slate-600 shrink-0" size={14} />
                  <input
                    placeholder="Holiday (e.g. Diwali)"
                    className="bg-transparent outline-none w-full font-medium placeholder:text-slate-700 text-sm text-slate-400"
                    value={query.holiday}
                    onChange={(e) => setQuery({ ...query, holiday: e.target.value })}
                  />
                </div>
                <div className="flex-1 flex flex-col px-6 py-3 border-r border-white/5">
                  <div className="flex items-center gap-3">
                    <TrendingUp className="text-slate-600 shrink-0" size={14} />
                    <input
                      list="ticker-options"
                      placeholder="Stock ticker (NVDA / SAMSUNG / SONY)"
                      className="bg-transparent outline-none w-full font-medium placeholder:text-slate-700 text-sm text-slate-400"
                      value={query.ticker}
                      onChange={(e) => setQuery({ ...query, ticker: e.target.value })}
                    />
                    <datalist id="ticker-options">
                      {VALID_TICKERS.map(t => <option key={t} value={t} />)}
                    </datalist>
                  </div>
                  {validationErrors.ticker && (
                    <p className="text-red-400 text-[10px] mt-1 ml-6">{validationErrors.ticker}</p>
                  )}
                </div>
                <div className="flex-1 flex items-center gap-3 px-6 py-3 border-r border-white/5">
                  <Package className="text-slate-600 shrink-0" size={14} />
                  <input
                    placeholder="Commodity (Copper / Aluminum...)"
                    className="bg-transparent outline-none w-full font-medium placeholder:text-slate-700 text-sm text-slate-400"
                    value={query.commodity}
                    onChange={(e) => setQuery({ ...query, commodity: e.target.value })}
                  />
                </div>
                <div className="flex-1 flex items-center gap-3 px-6 py-3">
                  <Activity className="text-slate-600 shrink-0" size={14} />
                  <input
                    type="number"
                    placeholder="Year (2022–2025)"
                    min="2022" max="2025"
                    className="bg-transparent outline-none w-full font-medium placeholder:text-slate-700 text-sm text-slate-400"
                    value={query.year}
                    onChange={(e) => setQuery({ ...query, year: e.target.value })}
                  />
                </div>
              </div>
            </div>
          )}
        </div>

        <p className={`mt-4 text-slate-500 text-xs font-bold tracking-[0.2em] uppercase transition-opacity duration-700 ${isExpanded ? 'opacity-100' : 'opacity-0'}`}>
          AI Engine ready · Data range 2022–2025 · INR currency
        </p>

        {/* ── Error Banner ─────────────────────────────────────────── */}
        {error && (
          <div className="mt-6 w-full max-w-5xl bg-red-500/10 border border-red-500/30 rounded-2xl px-6 py-4 flex items-center gap-3">
            <AlertTriangle className="text-red-400 shrink-0" size={18} />
            <p className="text-red-300 text-sm font-medium">{error}</p>
            <button onClick={() => setError(null)} className="ml-auto text-red-400 hover:text-white text-xs">✕</button>
          </div>
        )}

        {/* ── Results Section ───────────────────────────────────────── */}
        {isExpanded && (
          <div className="mt-12 w-full max-w-6xl animate-in slide-in-from-bottom-10 duration-700">

            {/* Tab navigation */}
            <div className="flex gap-2 mb-8 flex-wrap">
              {[
                { id: 'predict',   label: 'Prediction',  icon: <Zap size={12} /> },
                { id: 'forecast',  label: 'Forecast',    icon: <TrendingUp size={12} /> },
                { id: 'holidays',  label: 'Holidays',    icon: <Calendar size={12} /> },
                { id: 'macro',     label: 'Macro',       icon: <Globe size={12} /> },
                { id: 'stock',     label: 'Stock',       icon: <Activity size={12} /> },
                { id: 'commodity', label: 'Commodity',   icon: <Package size={12} /> },
              ].map(tab => (
                <button
                  key={tab.id}
                  onClick={() => tab.id === 'predict' ? setActiveTab('predict') : loadAnalytics(tab.id)}
                  className={`flex items-center gap-2 px-5 py-2.5 rounded-full text-[10px] font-black tracking-widest uppercase transition-all ${
                    activeTab === tab.id
                      ? 'bg-orange-500 text-white'
                      : 'bg-white/5 text-slate-400 hover:bg-white/10 border border-white/5'
                  }`}
                >
                  {tab.icon}{tab.label}
                </button>
              ))}
            </div>

            {/* Loading spinner */}
            {loading && (
              <div className="flex items-center justify-center py-20">
                <Loader2 className="text-orange-500 animate-spin" size={40} />
              </div>
            )}

            {/* ── PREDICTION RESULT ─────────────────────────────────── */}
            {!loading && activeTab === 'predict' && result && (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Main revenue card */}
                <div className="col-span-1 bg-gradient-to-br from-orange-500/20 to-red-600/10 border border-orange-500/30 rounded-[2.5rem] p-8">
                  <p className="text-orange-400 text-[10px] font-black tracking-widest uppercase mb-2">Estimated Revenue</p>
                  <p className="text-5xl font-black text-white mb-1">
                    ₹{result.prediction_results.estimated_revenue.toLocaleString('en-IN')}
                  </p>
                  <p className="text-slate-500 text-xs mt-2">
                    Based on {result.prediction_results.historical_sample_size} historical records
                  </p>
                  <p className="text-slate-600 text-[10px] mt-1">
                    Basis date: {result.prediction_results.basis_date}
                  </p>
                </div>

                {/* Query context card */}
                <div className="bg-[#1a1a1a] border border-white/5 rounded-[2.5rem] p-8">
                  <p className="text-slate-400 text-[10px] font-black tracking-widest uppercase mb-4">Query Parameters</p>
                  <div className="space-y-2">
                    {Object.entries(result.input_context).map(([k, v]) =>
                      v ? (
                        <div key={k} className="flex justify-between items-center">
                          <span className="text-slate-500 text-xs capitalize">{k}</span>
                          <span className="text-white text-xs font-bold">{String(v)}</span>
                        </div>
                      ) : null
                    )}
                  </div>
                </div>

                {/* Warning card */}
                <div className="bg-yellow-500/5 border border-yellow-500/20 rounded-[2.5rem] p-8">
                  <p className="text-yellow-400 text-[10px] font-black tracking-widest uppercase mb-4">
                    ⚠ Model Notes
                  </p>
                  <p className="text-slate-400 text-sm leading-relaxed">
                    {result.prediction_results.warning}
                  </p>
                  <div className="mt-4 pt-4 border-t border-yellow-500/10">
                    <p className="text-slate-600 text-[10px]">Valid categories: {VALID_CATEGORIES.join(' · ')}</p>
                    <p className="text-slate-600 text-[10px] mt-1">Valid regions: {VALID_REGIONS.join(' · ')}</p>
                  </div>
                </div>
              </div>
            )}

            {/* ── FORECAST ──────────────────────────────────────────── */}
            {!loading && activeTab === 'forecast' && analyticsData && (
              <div className="bg-[#1a1a1a] border border-white/5 rounded-[2.5rem] p-8">
                <p className="text-slate-400 text-[10px] font-black tracking-widest uppercase mb-6">
                  90-Day Prophet Forecast
                </p>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-white/5">
                        <th className="text-left text-slate-500 text-[10px] uppercase tracking-widest pb-3">Date</th>
                        <th className="text-right text-slate-500 text-[10px] uppercase tracking-widest pb-3">Forecast (₹)</th>
                        <th className="text-right text-slate-500 text-[10px] uppercase tracking-widest pb-3">Lower Band</th>
                        <th className="text-right text-slate-500 text-[10px] uppercase tracking-widest pb-3">Upper Band</th>
                      </tr>
                    </thead>
                    <tbody>
                      {analyticsData.forecast?.slice(0, 15).map((row, i) => (
                        <tr key={i} className="border-b border-white/5 hover:bg-white/2">
                          <td className="py-2 text-slate-300">{row.ds}</td>
                          <td className="py-2 text-right font-bold text-orange-400">
                            ₹{Math.round(row.yhat).toLocaleString('en-IN')}
                          </td>
                          <td className="py-2 text-right text-slate-500">
                            ₹{Math.round(row.yhat_lower).toLocaleString('en-IN')}
                          </td>
                          <td className="py-2 text-right text-slate-500">
                            ₹{Math.round(row.yhat_upper).toLocaleString('en-IN')}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  {analyticsData.forecast?.length > 15 && (
                    <p className="text-slate-600 text-xs mt-3 text-center">
                      Showing 15 of {analyticsData.forecast.length} forecast rows
                    </p>
                  )}
                </div>
              </div>
            )}

            {/* ── HOLIDAYS ──────────────────────────────────────────── */}
            {!loading && activeTab === 'holidays' && analyticsData && (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {(Array.isArray(analyticsData) ? analyticsData : []).map((h, i) => (
                  <div key={i} className="bg-[#1a1a1a] border border-white/5 rounded-[2rem] p-6 hover:border-orange-500/20 transition-all">
                    <p className="text-orange-400 font-black text-sm mb-1">{h.holiday}</p>
                    <p className="text-slate-500 text-[10px] mb-4">{h.date} · {h.is_public ? '🟢 Public' : '⚪ Observance'}</p>
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <p className="text-slate-600 text-[10px] uppercase tracking-widest">Revenue</p>
                        <p className="text-white font-black">₹{(h.total_revenue || 0).toLocaleString('en-IN')}</p>
                      </div>
                      <div>
                        <p className="text-slate-600 text-[10px] uppercase tracking-widest">Transactions</p>
                        <p className="text-white font-black">{h.num_transactions || 0}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* ── MACRO ─────────────────────────────────────────────── */}
            {!loading && activeTab === 'macro' && analyticsData && (
              <div className="bg-[#1a1a1a] border border-white/5 rounded-[2.5rem] p-8">
                <p className="text-slate-400 text-[10px] font-black tracking-widest uppercase mb-6">
                  Monthly Sales vs Macro Indicators
                </p>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-white/5">
                        {['Month','Revenue (₹)','USD/INR','Inflation %','Interest %'].map(h => (
                          <th key={h} className="text-left text-slate-500 text-[10px] uppercase tracking-widest pb-3 pr-6">{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {(Array.isArray(analyticsData) ? analyticsData : []).map((row, i) => (
                        <tr key={i} className="border-b border-white/5 hover:bg-white/2">
                          <td className="py-2 text-slate-300 pr-6">{row.month}</td>
                          <td className="py-2 text-orange-400 font-bold pr-6">
                            ₹{Math.round(row.total_revenue || 0).toLocaleString('en-IN')}
                          </td>
                          <td className="py-2 text-slate-400 pr-6">{(row.avg_usd_inr || 0).toFixed(2)}</td>
                          <td className="py-2 text-slate-400 pr-6">{(row.inflation || 0).toFixed(2)}%</td>
                          <td className="py-2 text-slate-400">{(row.interest_rate || 0).toFixed(2)}%</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* ── STOCK ─────────────────────────────────────────────── */}
            {!loading && activeTab === 'stock' && analyticsData && (
              <div className="bg-[#1a1a1a] border border-white/5 rounded-[2.5rem] p-8">
                <p className="text-slate-400 text-[10px] font-black tracking-widest uppercase mb-2">
                  Daily Revenue vs {query.ticker || 'NVDA'} Stock Price
                </p>
                <p className="text-slate-600 text-xs mb-6">
                  Showing last 30 days of overlap between sales data and stock prices
                </p>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-white/5">
                        {['Date','Revenue (₹)','Stock Close','Volume'].map(h => (
                          <th key={h} className="text-left text-slate-500 text-[10px] uppercase tracking-widest pb-3 pr-6">{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {(Array.isArray(analyticsData) ? analyticsData : []).slice(-30).map((row, i) => (
                        <tr key={i} className="border-b border-white/5 hover:bg-white/2">
                          <td className="py-2 text-slate-300 pr-6">{row.date}</td>
                          <td className="py-2 text-orange-400 font-bold pr-6">
                            ₹{Math.round(row.total_revenue || 0).toLocaleString('en-IN')}
                          </td>
                          <td className="py-2 text-slate-400 pr-6">{(row.stock_close || 0).toFixed(2)}</td>
                          <td className="py-2 text-slate-400">{(row.stock_volume || 0).toLocaleString()}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* ── COMMODITY ─────────────────────────────────────────── */}
            {!loading && activeTab === 'commodity' && analyticsData && (
              <div className="bg-[#1a1a1a] border border-white/5 rounded-[2.5rem] p-8">
                <p className="text-slate-400 text-[10px] font-black tracking-widest uppercase mb-6">
                  {query.commodity || 'Copper'} Price vs Sales Revenue
                </p>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-white/5">
                        {['Month','Revenue (₹)','Commodity Price ($/t)','YoY Change %'].map(h => (
                          <th key={h} className="text-left text-slate-500 text-[10px] uppercase tracking-widest pb-3 pr-6">{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {(Array.isArray(analyticsData) ? analyticsData : []).map((row, i) => (
                        <tr key={i} className="border-b border-white/5 hover:bg-white/2">
                          <td className="py-2 text-slate-300 pr-6">{row.month}</td>
                          <td className="py-2 text-orange-400 font-bold pr-6">
                            ₹{Math.round(row.total_revenue || 0).toLocaleString('en-IN')}
                          </td>
                          <td className="py-2 text-slate-400 pr-6">
                            ${(row.avg_commodity_price || 0).toFixed(2)}
                          </td>
                          <td className={`py-2 ${(row.commodity_yoy_pct || 0) > 0 ? 'text-red-400' : 'text-green-400'}`}>
                            {(row.commodity_yoy_pct || 0).toFixed(2)}%
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Empty state */}
            {!loading && !result && !analyticsData && !error && (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {['Fill in the filters above and hit Generate', 'Or click a tab to load analytics data', 'Valid dates: 2022-01-01 to 2025-03-31'].map((msg, i) => (
                  <div key={i} className="h-48 bg-white/5 border border-white/5 rounded-[2.5rem] flex items-center justify-center p-6">
                    <p className="text-slate-700 font-black uppercase tracking-widest text-[10px] text-center">{msg}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* ── Feature Cards ─────────────────────────────────────────── */}
        <div className="w-full max-w-6xl mt-32 space-y-32 pb-32">
          <section>
            <h2 className="text-3xl font-black tracking-tighter mb-12 flex items-center gap-4">
              <div className="w-2 h-8 bg-orange-500 rounded-full" />
              AI-Powered Insights{' '}
              <span className="text-slate-600 ml-2 font-medium text-lg tracking-normal">Unlocked</span>
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              <ActiveFeatureCard
                icon={<MapPin size={24} />}
                title="Regional Analysis"
                desc="Filter by North, East, South, or West region to see localised sales predictions."
                onClick={() => { setIsExpanded(true); }}
              />
              <ActiveFeatureCard
                icon={<Calendar size={24} />}
                title="Festival Correlation"
                desc="Enter a holiday name like Diwali to see how festivals impact your sales forecast."
                onClick={() => loadAnalytics('holidays')}
              />
              <ActiveFeatureCard
                icon={<DollarSign size={24} />}
                title="Macro Intelligence"
                desc="Track how USD/INR, inflation, and interest rates correlate with your revenue."
                onClick={() => loadAnalytics('macro')}
              />
            </div>
          </section>

          {/*--------- CHARTS SECTION--------- */}
      

          <section className="text-center">
            <h2 className="text-3xl font-black tracking-tighter mb-12">Inventory Classification</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              <InventoryCategory title="ICs & Chips"    icon={<Cpu />}      onClick={() => { setQuery({...query, category:'Electronics'}); setIsExpanded(true); }} />
              <InventoryCategory title="Power Systems"  icon={<Battery />}  onClick={() => loadAnalytics('commodity')} />
              <InventoryCategory title="Raw Materials"  icon={<Package />}  onClick={() => loadAnalytics('commodity')} />
              <InventoryCategory title="End Products"   icon={<BarChart3 />} onClick={() => { setQuery({...query, category:'Electronics'}); setIsExpanded(true); }} />
            </div>
          </section>
        </div>
      </main>

      {/* ── Footer ─────────────────────────────────────────────────── */}
      <footer className="w-full bg-[#0a0a0a] px-10 py-16 border-t border-white/5">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row justify-between items-center gap-8">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 bg-orange-500 rounded flex items-center justify-center text-[10px] font-black">AI</div>
            <span className="font-black text-lg tracking-tighter uppercase">SalesInsight AI</span>
          </div>
          <p className="text-[10px] font-black text-slate-600 tracking-[0.4em] uppercase">
            © 2026 PRIVATE LIMITED / ENTERPRISE INTELLIGENCE UNIT
          </p>
          <div className="flex gap-6 text-[10px] font-black text-slate-500 uppercase tracking-widest">
            <span className="hover:text-white cursor-pointer transition-colors">Documentation</span>
            <span className="hover:text-white cursor-pointer transition-colors">API Status</span>
          </div>
        </div>
      </footer>
    </div>
  );
}

// ── Helper components ─────────────────────────────────────────────────
function ActiveFeatureCard({ icon, title, desc, onClick }) {
  return (
    <div
      onClick={onClick}
      className="bg-[#1a1a1a] p-8 rounded-[2.5rem] border border-white/5 hover:border-orange-500/30 transition-all group cursor-pointer"
    >
      <div className="text-orange-500 mb-6 group-hover:scale-110 transition-transform duration-500">{icon}</div>
      <h4 className="font-black text-xl mb-3 tracking-tight">{title}</h4>
      <p className="text-slate-500 text-sm leading-relaxed font-medium">{desc}</p>
    </div>
  );
}

function InventoryCategory({ title, icon, onClick }) {
  return (
    <div
      onClick={onClick}
      className="bg-[#1a1a1a] p-10 rounded-[2.5rem] border border-white/5 hover:bg-orange-500/5 hover:border-orange-500/20 transition-all cursor-pointer group"
    >
      <div className="text-slate-600 group-hover:text-orange-500 transition-colors mb-4 flex justify-center">
        {React.cloneElement(icon, { size: 30 })}
      </div>
      <p className="font-bold text-xs uppercase tracking-widest text-slate-500 group-hover:text-white transition-colors">
        {title}
      </p>
    </div>
  );
}