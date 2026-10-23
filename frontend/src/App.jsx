import { useEffect, useState } from "react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
} from "recharts";
import {
  getSummary, getRegional, getCategories, getModelComparison,
  getAnomalySummary, getTopAnomalies, getGlobalExplanations, getSampleExplanations,
  predictScenario, getBenchmarkGlobal, getBenchmarkCategories,
} from "./api";
import "./App.css";

const COLORS = ["#4f46e5", "#06b6d4", "#f59e0b", "#ef4444", "#10b981", "#8b5cf6"];

const SHIP_MODES = ["Standard Class", "Second Class", "First Class", "Same Day"];
const SEGMENTS = ["Consumer", "Corporate", "Home Office"];
const REGIONS = ["Central", "East", "South", "West"];
const CATEGORIES = ["Furniture", "Office Supplies", "Technology"];
const SUB_CATEGORIES = [
  "Bookcases", "Chairs", "Labels", "Tables", "Storage", "Furnishings", "Art",
  "Phones", "Binders", "Appliances", "Paper", "Accessories", "Envelopes",
  "Fasteners", "Supplies", "Machines", "Copiers",
];

const DEFAULT_SCENARIO = {
  Quantity: 3,
  Discount: 0.2,
  Profit: 25,
  "Ship Mode": "Standard Class",
  Segment: "Consumer",
  Region: "West",
  Category: "Furniture",
  "Sub-Category": "Chairs",
};

function KpiCard({ label, value, color }) {
  return (
    <div className="kpi-card" style={{ "--accent-color": color }}>
      <div className="kpi-label">{label}</div>
      <div className="kpi-value">{value}</div>
    </div>
  );
}

function Section({ title, subtitle, color, children }) {
  return (
    <section className="panel">
      <div className="panel-heading">
        <span className="panel-dot" style={{ "--accent-color": color }} />
        <h2>{title}</h2>
      </div>
      {subtitle && <p className="subtitle">{subtitle}</p>}
      {children}
    </section>
  );
}

function WhatIfSimulator() {
  const [form, setForm] = useState(DEFAULT_SCENARIO);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const update = (field, value) => setForm((f) => ({ ...f, [field]: value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const payload = {
        ...form,
        Quantity: Number(form.Quantity),
        Discount: Number(form.Discount),
        Profit: Number(form.Profit),
      };
      const res = await predictScenario(payload);
      setResult(res);
    } catch (err) {
      setError(
        err.response?.data?.detail || err.message || "Prediction request failed"
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="simulator">
      <div className="simulator-heading">
        <h2>What-If Decision Simulator</h2>
        <span className="simulator-badge">LIVE LAMBDA INFERENCE</span>
      </div>
      <p className="subtitle">
        Change the scenario below and get a real-time sales prediction, computed on demand
        by an AWS Lambda function, with a plain-language explanation of what drove it.
      </p>

      <form className="sim-form" onSubmit={handleSubmit}>
        <div className="sim-field">
          <label>Quantity</label>
          <input
            type="number" min="1" step="1"
            value={form.Quantity}
            onChange={(e) => update("Quantity", e.target.value)}
          />
        </div>
        <div className="sim-field">
          <label>Discount</label>
          <input
            type="number" min="0" max="1" step="0.05"
            value={form.Discount}
            onChange={(e) => update("Discount", e.target.value)}
          />
        </div>
        <div className="sim-field">
          <label>Profit</label>
          <input
            type="number" step="0.01"
            value={form.Profit}
            onChange={(e) => update("Profit", e.target.value)}
          />
        </div>
        <div className="sim-field">
          <label>Ship Mode</label>
          <select value={form["Ship Mode"]} onChange={(e) => update("Ship Mode", e.target.value)}>
            {SHIP_MODES.map((v) => <option key={v} value={v}>{v}</option>)}
          </select>
        </div>
        <div className="sim-field">
          <label>Segment</label>
          <select value={form.Segment} onChange={(e) => update("Segment", e.target.value)}>
            {SEGMENTS.map((v) => <option key={v} value={v}>{v}</option>)}
          </select>
        </div>
        <div className="sim-field">
          <label>Region</label>
          <select value={form.Region} onChange={(e) => update("Region", e.target.value)}>
            {REGIONS.map((v) => <option key={v} value={v}>{v}</option>)}
          </select>
        </div>
        <div className="sim-field">
          <label>Category</label>
          <select value={form.Category} onChange={(e) => update("Category", e.target.value)}>
            {CATEGORIES.map((v) => <option key={v} value={v}>{v}</option>)}
          </select>
        </div>
        <div className="sim-field">
          <label>Sub-Category</label>
          <select value={form["Sub-Category"]} onChange={(e) => update("Sub-Category", e.target.value)}>
            {SUB_CATEGORIES.map((v) => <option key={v} value={v}>{v}</option>)}
          </select>
        </div>

        <div className="sim-actions">
          <button className="sim-button" type="submit" disabled={loading}>
            {loading ? "Running prediction..." : "Run Prediction"}
          </button>
          {error && <span className="sim-error">{error}</span>}
        </div>
      </form>

      {result && (
        <div className="sim-result">
          <div className="sim-result-figure">
            <div className="sim-result-label">Predicted Sales</div>
            <div className="sim-result-value">
              ${Number(result.prediction).toLocaleString(undefined, { maximumFractionDigits: 2 })}
            </div>
            <div className="sim-result-base">
              Baseline: ${Number(result.base_value).toLocaleString(undefined, { maximumFractionDigits: 2 })}
            </div>
          </div>
          <div className="sim-explanation">
            {result.explanation}
          </div>
        </div>
      )}
    </section>
  );
}

function IndustryBenchmark({ categories, globalFactors }) {
  const [selected, setSelected] = useState(categories[0]?.category || "");
  const current = categories.find((c) => c.category === selected) || categories[0];

  if (!current) return null;

  const fundingRatio = current.median_funding_closed_usd
    ? (current.median_funding_survived_usd / current.median_funding_closed_usd).toFixed(1)
    : "n/a";
  const relRatio = current.median_relationships_closed
    ? (current.median_relationships_survived / current.median_relationships_closed).toFixed(1)
    : "n/a";

  const lesson = `In the ${current.category.replace(/_/g, " ")} category, ${current.survival_rate_pct}% of startups in this dataset survived (were acquired) rather than closing. The ones that survived had raised about ${fundingRatio}x more total funding and had about ${relRatio}x more investor relationships than the ones that closed.`;

  const maxImportance = Math.max(...globalFactors.map((f) => f.importance));

  return (
    <>
      <div className="benchmark-controls">
        <label style={{ display: "block", fontSize: 11, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 6 }}>
          Choose an industry
        </label>
        <select className="benchmark-select" value={selected} onChange={(e) => setSelected(e.target.value)}>
          {categories.map((c) => (
            <option key={c.category} value={c.category}>
              {c.category.replace(/_/g, " ")} ({c.n_companies} companies)
            </option>
          ))}
        </select>
      </div>

      <div className="benchmark-stats-row">
        <div className="benchmark-stat">
          <div className="benchmark-stat-label">Survival Rate</div>
          <div className="benchmark-stat-value">{current.survival_rate_pct}%</div>
        </div>
        <div className="benchmark-stat">
          <div className="benchmark-stat-label">Companies in Category</div>
          <div className="benchmark-stat-value">{current.n_companies}</div>
        </div>
      </div>

      <div className="benchmark-compare">
        <div className="benchmark-compare-col survived">
          <div className="benchmark-compare-heading">Companies that survived</div>
          <div className="benchmark-compare-row"><span>Median funding raised</span><strong>${current.median_funding_survived_usd?.toLocaleString()}</strong></div>
          <div className="benchmark-compare-row"><span>Median funding rounds</span><strong>{current.median_funding_rounds_survived}</strong></div>
          <div className="benchmark-compare-row"><span>Median investor relationships</span><strong>{current.median_relationships_survived}</strong></div>
        </div>
        <div className="benchmark-compare-col closed">
          <div className="benchmark-compare-heading">Companies that closed</div>
          <div className="benchmark-compare-row"><span>Median funding raised</span><strong>${current.median_funding_closed_usd?.toLocaleString()}</strong></div>
          <div className="benchmark-compare-row"><span>Median funding rounds</span><strong>{current.median_funding_rounds_closed}</strong></div>
          <div className="benchmark-compare-row"><span>Median investor relationships</span><strong>{current.median_relationships_closed}</strong></div>
        </div>
      </div>

      <div className="benchmark-lesson">{lesson}</div>

      <div className="benchmark-global-list">
        <h3 className="mini-heading">What separates success from failure, overall</h3>
        {globalFactors.slice(0, 6).map((f) => (
          <div className="benchmark-factor-row" key={f.feature}>
            <span className="benchmark-factor-name">{f.feature.replace(/_/g, " ")}</span>
            <div className="benchmark-factor-bar-wrap">
              <div className="benchmark-factor-bar" style={{ width: `${(f.importance / maxImportance) * 100}%` }} />
            </div>
          </div>
        ))}
      </div>

      <p className="benchmark-note">
        Based on a real dataset of 923 Crunchbase-derived startups, circa 2013. Patterns reflect
        that era and should be read as directional lessons, not current market guarantees.
      </p>
    </>
  );
}

export default function App() {
  const [summary, setSummary] = useState(null);
  const [regional, setRegional] = useState([]);
  const [categories, setCategories] = useState([]);
  const [models, setModels] = useState(null);
  const [anomalySummary, setAnomalySummary] = useState(null);
  const [topAnomalies, setTopAnomalies] = useState([]);
  const [globalExplain, setGlobalExplain] = useState([]);
  const [sampleExplain, setSampleExplain] = useState([]);
  const [benchmarkGlobal, setBenchmarkGlobal] = useState(null);
  const [benchmarkCategories, setBenchmarkCategories] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    Promise.all([
      getSummary(), getRegional(), getCategories(), getModelComparison(),
      getAnomalySummary(), getTopAnomalies(), getGlobalExplanations(), getSampleExplanations(),
      getBenchmarkGlobal(), getBenchmarkCategories(),
    ])
      .then(([s, r, c, m, as, ta, ge, se, bg, bc]) => {
        setSummary(s); setRegional(r); setCategories(c); setModels(m);
        setAnomalySummary(as); setTopAnomalies(ta); setGlobalExplain(ge); setSampleExplain(se);
        setBenchmarkGlobal(bg); setBenchmarkCategories(bc);
      })
      .catch((e) => setError(e.message));
  }, []);

  if (error) {
    return (
      <div className="error-banner">
        Could not reach the backend API ({error}). Is it running?
      </div>
    );
  }
  if (!summary) {
    return (
      <div className="loading">
        <div className="spinner" />
        Loading live data from AWS...
      </div>
    );
  }

  const catByCategory = Object.values(
    categories.reduce((acc, row) => {
      acc[row.Category] = acc[row.Category] || { Category: row.Category, total_sales: 0, total_profit: 0 };
      acc[row.Category].total_sales += row.total_sales;
      acc[row.Category].total_profit += row.total_profit;
      return acc;
    }, {})
  );

  return (
    <div className="dashboard">
      <div className="topbar">
        <div className="brand-mark">CS</div>
        <div className="brand-text">
          <h1>Cloud-Native Decision Simulator</h1>
          <p className="subtitle">
            Explainable AI for Business Operations - {summary.total_orders.toLocaleString()} transactions
          </p>
        </div>
        <div className="cloud-badges">
          <span className="cloud-badge">AWS ECS Fargate</span>
          <span className="cloud-badge">RDS</span>
          <span className="cloud-badge">Lambda SHAP</span>
          <span className="cloud-badge">Cognito Auth</span>
        </div>
      </div>

      <WhatIfSimulator />

      <div className="kpi-row">
        <KpiCard label="Total Sales" value={`$${summary.total_sales.toLocaleString()}`} color="#4f46e5" />
        <KpiCard label="Total Profit" value={`$${summary.total_profit.toLocaleString()}`} color="#10b981" />
        <KpiCard label="Avg Order Value" value={`$${summary.avg_order_value}`} color="#06b6d4" />
        <KpiCard label="Overall Margin" value={`${summary.overall_margin_pct}%`} color="#f59e0b" />
        <KpiCard label="Avg Discount" value={`${(summary.avg_discount * 100).toFixed(1)}%`} color="#8b5cf6" />
      </div>

      <Section title="Regional Sales and Profit" color="#4f46e5">
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={regional}>
            <CartesianGrid strokeDasharray="3 3" stroke="#eef0f6" />
            <XAxis dataKey="Region" tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip />
            <Bar dataKey="total_sales" fill="#4f46e5" name="Sales" radius={[4, 4, 0, 0]} />
            <Bar dataKey="total_profit" fill="#10b981" name="Profit" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </Section>

      <Section title="Sales by Category" color="#06b6d4">
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={catByCategory} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" stroke="#eef0f6" />
            <XAxis type="number" tick={{ fontSize: 12 }} />
            <YAxis type="category" dataKey="Category" width={120} tick={{ fontSize: 12 }} />
            <Tooltip />
            <Bar dataKey="total_sales" name="Sales" radius={[0, 4, 4, 0]}>
              {catByCategory.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </Section>

      <Section
        title="Forecasting Model Comparison"
        subtitle={`Target: ${models.target} - Best performing model: ${models.best_model}`}
        color="#f59e0b"
      >
        <div className="table-wrap">
          <table className="metrics-table">
            <thead>
              <tr><th>Model</th><th>MAE</th><th>RMSE</th><th>MAPE (%)</th><th>R-squared</th></tr>
            </thead>
            <tbody>
              {Object.entries(models.results).map(([name, m]) => (
                <tr key={name} className={name === models.best_model ? "best-row" : ""}>
                  <td>
                    {name}
                    {name === models.best_model && <span className="best-badge">BEST</span>}
                  </td>
                  <td>{m.MAE}</td><td>{m.RMSE}</td><td>{m.MAPE}</td><td>{m.R2}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Section>

      <Section
        title="Anomaly Detection"
        subtitle={`${anomalySummary.flagged} of ${anomalySummary.total_transactions} transactions flagged (${anomalySummary.flagged_pct}%)`}
        color="#ef4444"
      >
        <div className="table-wrap">
          <table className="metrics-table">
            <thead>
              <tr><th>Region</th><th>Category</th><th>Sales</th><th>Profit</th><th>Discount</th><th>Anomaly Score</th></tr>
            </thead>
            <tbody>
              {topAnomalies.slice(0, 10).map((row, i) => (
                <tr key={i}>
                  <td>{row.Region}</td><td>{row.Category}</td>
                  <td>${row.Sales?.toFixed(2)}</td><td>${row.Profit?.toFixed(2)}</td>
                  <td>{(row.Discount * 100).toFixed(0)}%</td>
                  <td>{row.anomaly_score?.toFixed(3)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Section>

      <Section
        title="Explainability (SHAP)"
        subtitle="What drives predicted sales, and why individual predictions land where they do"
        color="#8b5cf6"
      >
        <h3 className="mini-heading">Top global drivers</h3>
        <ResponsiveContainer width="100%" height={320}>
          <BarChart data={globalExplain.slice(0, 8)} layout="vertical" margin={{ left: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#eef0f6" />
            <XAxis type="number" tick={{ fontSize: 12 }} />
            <YAxis type="category" dataKey="feature" width={170} tick={{ fontSize: 12 }} />
            <Tooltip />
            <Bar dataKey="mean_abs_shap" fill="#8b5cf6" name="Mean absolute SHAP value" radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>

        <h3 className="mini-heading">Sample explanations</h3>
        <ul className="explanation-list">
          {sampleExplain.slice(0, 5).map((e) => (
            <li key={e.index}>{e.explanation}</li>
          ))}
        </ul>
      </Section>

      {benchmarkGlobal && benchmarkCategories.length > 0 && (
        <Section
          title="Industry Benchmark and Lessons"
          subtitle="Real outcomes from 923 startups - what separated success from failure"
          color="#10b981"
        >
          <IndustryBenchmark categories={benchmarkCategories} globalFactors={benchmarkGlobal.value} />
        </Section>
      )}

      <div className="infra-footer">
        <span>Deployed on AWS</span>
        <span>Terraform / IaC</span>
        <span>ECS Fargate</span>
        <span>RDS PostgreSQL</span>
        <span>S3</span>
        <span>Lambda SHAP Explainer</span>
        <span>Cognito Auth</span>
        <span>CloudWatch Monitoring</span>
      </div>
    </div>
  );
}
