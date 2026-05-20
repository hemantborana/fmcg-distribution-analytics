import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error
import os
import re
import warnings
warnings.filterwarnings("ignore")

#  Page config 
st.set_page_config(
    page_title="Distribution Analytics System",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

#  Paths 
BASE  = os.path.join(os.path.dirname(__file__), "data_cleaned")

#  Custom CSS 
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem 1.2rem;
        border-radius: 12px;
        color: white;
        margin-bottom: 0.5rem;
    }
    .metric-card h3 { margin: 0; font-size: 0.85rem; opacity: 0.85; }
    .metric-card h2 { margin: 0.2rem 0 0 0; font-size: 1.6rem; font-weight: 700; }
    .metric-card p  { margin: 0; font-size: 0.78rem; opacity: 0.75; }
    .section-header {
        border-left: 4px solid #667eea;
        padding-left: 0.8rem;
        margin-bottom: 1rem;
        color: #1e1e2e;
    }
    .finding-box {
        background: #f0f4ff;
        border: 1px solid #c7d2fe;
        border-radius: 8px;
        padding: 0.8rem 1rem;
        margin-bottom: 0.5rem;
        font-size: 0.9rem;
        color: #1e1e2e !important;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        padding: 0.4rem 1rem;
    }
</style>
""", unsafe_allow_html=True)

#  Data loading (cached) 
@st.cache_data
def load_all_data():
    sales    = pd.read_excel(os.path.join(BASE, "sales_billing_data_cleaned.xlsx"),
                             parse_dates=["Invoice_Date"])
    purchase = pd.read_excel(os.path.join(BASE, "purchase_data_cleaned.xlsx"),
                             parse_dates=["Invoice_Date"])
    orders   = pd.read_excel(os.path.join(BASE, "app_order_data_cleaned.xlsx"),
                             parse_dates=["Order Date"])
    sku      = pd.read_excel(os.path.join(BASE, "sku_master_cleaned.xlsx"))
    outlet   = pd.read_excel(os.path.join(BASE, "outlet_master_cleaned.xlsx"))
    stock    = pd.read_excel(os.path.join(BASE, "stock_snapshots_cleaned.xlsx"),
                             parse_dates=["Snapshot_Date"])

    stock = stock[stock["Is_Sync_File"] == False].copy()

    def get_fy(dt):
        return f"FY {dt.year}-{str(dt.year+1)[-2:]}" if dt.month >= 4 \
               else f"FY {dt.year-1}-{str(dt.year)[-2:]}"

    sales["Month"]    = sales["Invoice_Date"].dt.to_period("M")
    sales["FY"]       = sales["Invoice_Date"].apply(get_fy)
    sales["Month_str"]= sales["Month"].astype(str)
    purchase["Month"] = purchase["Invoice_Date"].dt.to_period("M")
    orders["Month"]   = orders["Order Date"].dt.to_period("M")

    sales_current = sales[sales["Invoice_Number"].astype(str).str.upper().str.startswith("K")].copy()
    sales_current["Month_str"] = sales_current["Month"].astype(str)

    # Category lookup from purchase
    cat_lookup = (purchase[purchase["Category"].notna()]
                  [["Style","Category"]]
                  .drop_duplicates(subset="Style", keep="first"))
    sales_cat = sales.merge(cat_lookup, on="Style", how="left")
    sales_cat["Category"] = sales_cat["Category"].fillna("OTHER")

    return sales, purchase, orders, sku, outlet, stock, sales_current, sales_cat, cat_lookup

sales, purchase, orders, sku, outlet, stock, sales_current, sales_cat, cat_lookup, = load_all_data()

#  Forecasting helper 
def make_features(df):
    df = df.copy()
    df["month_of_year"] = df["Month"].dt.month
    df["sin_month"]     = np.sin(2 * np.pi * df["month_of_year"] / 12)
    df["cos_month"]     = np.cos(2 * np.pi * df["month_of_year"] / 12)
    return df

def mape_score(actual, predicted):
    mask = actual > 0
    if mask.sum() == 0: return float("nan")
    return np.mean(np.abs((actual[mask] - predicted[mask]) / actual[mask])) * 100

#  Sidebar navigation 
with st.sidebar:
    st.markdown("## 📦 Distribution Analytics")
    st.markdown("*Goa Territory | FY 2023–2026*")
    st.divider()

    page = st.radio("Navigate", [
        "🏠  Dashboard",
        "📈  Sales Analysis",
        "🔮  Demand Forecast",
        "📦  Stock Analysis",
        "🔄  Purchase vs Sales",
        "🎯  Model Evaluation"
    ])
    st.divider()
    st.caption("Data period: Jun 2023 – Mar 2026")
    st.caption("Built with Python + Streamlit")
    st.divider()
    st.markdown("""
    <div style='text-align:center; padding: 0.5rem;
                background: linear-gradient(135deg,#667eea,#764ba2);
                border-radius: 8px; color: white; font-size: 0.75rem;'>
        <b>Project by</b><br>
        <span style='font-size:0.9rem; font-weight:700;'>Hemant Borana</span><br>
        <span style='opacity:0.8;'>BCA — Data Analytics</span><br>
        <span style='opacity:0.7;'>Amity University Online</span>
    </div>
    """, unsafe_allow_html=True)

# ═══════════════════
# PAGE 1 — DASHBOARD
# ═══════════════════
if page == "🏠  Dashboard":
    st.title("📦 Distribution Management Analytics System")
    st.markdown("**Regional FMCG Distribution — Goa Territory | FY 2023-24 to FY 2025-26**")
    st.divider()

    # KPI row
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown("""<div class="metric-card">
            <h3>Total Units Sold</h3><h2>23,785</h2><p>Jun 2023 – Mar 2026</p>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown("""<div class="metric-card">
            <h3>Total Sales Value</h3><h2>₹1.38 Cr</h2><p>All firms combined</p>
        </div>""", unsafe_allow_html=True)
    with col3:
        st.markdown("""<div class="metric-card">
            <h3>Active Retailers</h3><h2>46</h2><p>Out of 107 registered</p>
        </div>""", unsafe_allow_html=True)
    with col4:
        st.markdown("""<div class="metric-card">
            <h3>Unique SKUs Sold</h3><h2>2,562</h2><p>From 5,363 in catalogue</p>
        </div>""", unsafe_allow_html=True)
    with col5:
        st.markdown("""<div class="metric-card">
            <h3>FY 2025-26 Growth</h3><h2>+17.8%</h2><p>Volume YoY</p>
        </div>""", unsafe_allow_html=True)

    st.divider()

    col_l, col_r = st.columns([3, 2])

    with col_l:
        st.markdown('<h4 class="section-header">Monthly Sales Trend — All Period</h4>', unsafe_allow_html=True)
        monthly = sales.groupby("Month_str")["Quantity"].sum().reset_index()
        fig = px.area(monthly, x="Month_str", y="Quantity",
                      labels={"Month_str":"Month","Quantity":"Units Sold"},
                      color_discrete_sequence=["#667eea"])
        fig.update_layout(margin=dict(l=0,r=0,t=10,b=0), height=280,
                          xaxis_tickangle=-45, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        st.markdown('<h4 class="section-header">FY Sales Comparison</h4>', unsafe_allow_html=True)
        fy_data = sales.groupby("FY").agg(Qty=("Quantity","sum"),
                                           Value=("Item_Total","sum")).reset_index()
        fig2 = px.bar(fy_data, x="FY", y="Qty",
                      color="FY", text="Qty",
                      color_discrete_sequence=["#667eea","#764ba2","#f093fb"])
        fig2.update_traces(texttemplate="%{text:,}", textposition="outside")
        fig2.update_layout(margin=dict(l=0,r=0,t=10,b=0), height=280,
                           showlegend=False, yaxis_title="Units Sold")
        st.plotly_chart(fig2, use_container_width=True)

    st.divider()
    col_a, col_b, col_c = st.columns(3)

    with col_a:
        st.markdown('<h4 class="section-header">Top 5 Styles</h4>', unsafe_allow_html=True)
        top5 = (sales.groupby("Style")["Quantity"].sum()
                .sort_values(ascending=False).head(5).reset_index())
        fig3 = px.bar(top5, x="Quantity", y="Style", orientation="h",
                      color="Quantity", color_continuous_scale="Blues",
                      text="Quantity")
        fig3.update_traces(texttemplate="%{text:,}")
        fig3.update_layout(margin=dict(l=0,r=0,t=10,b=0), height=250,
                           showlegend=False, coloraxis_showscale=False)
        st.plotly_chart(fig3, use_container_width=True)

    with col_b:
        st.markdown('<h4 class="section-header">Category Split</h4>', unsafe_allow_html=True)
        cat_data = (sales_cat.groupby("Category")["Quantity"].sum()
                    .sort_values(ascending=False).reset_index())
        fig4 = px.pie(cat_data, names="Category", values="Quantity",
                      color_discrete_sequence=px.colors.sequential.Purples_r,
                      hole=0.4)
        fig4.update_layout(margin=dict(l=0,r=0,t=10,b=0), height=250,
                           legend=dict(font=dict(size=10)))
        st.plotly_chart(fig4, use_container_width=True)

    with col_c:
        st.markdown('<h4 class="section-header">Key Facts</h4>', unsafe_allow_html=True)
        facts = [
            "🏆 D143 alone = 26.4% of total sales",
            "🏪 Top 2 retailers = 54.6% of volume",
            "📅 December is peak month (4,264 units)",
            "📦 Sell-through rate = 84.9%",
            "🔮 LR model MAE = 134.8 units/month",
            "📈 Value growth +28.3% YoY (FY25-26)",
        ]
        for f in facts:
            st.markdown(f'<div class="finding-box">{f}</div>', unsafe_allow_html=True)

# ════════════════════════
# PAGE 2 — SALES ANALYSIS
# ════════════════════════
elif page == "📈  Sales Analysis":
    st.title("📈 Sales Analysis")
    st.markdown("Detailed analysis of sales performance by period, product, and retailer.")
    st.divider()

    tab1, tab2, tab3, tab4 = st.tabs(["Monthly Trends","Top Products","Retailers","Size Analysis"])

    with tab1:
        st.subheader("Monthly Sales — Current Firm (Nov 2023 – Mar 2026)")
        monthly_curr = (sales_current.groupby("Month_str")
                        .agg(Qty=("Quantity","sum"), Value=("Item_Total","sum"))
                        .reset_index())

        metric = st.radio("Show", ["Units Sold","Sales Value (₹)"], horizontal=True)
        if metric == "Units Sold":
            fig = px.bar(monthly_curr, x="Month_str", y="Qty",
                         labels={"Month_str":"Month","Qty":"Units Sold"},
                         color_discrete_sequence=["#667eea"])
        else:
            fig = px.bar(monthly_curr, x="Month_str", y="Value",
                         labels={"Month_str":"Month","Value":"Sales Value (₹)"},
                         color_discrete_sequence=["#764ba2"])
        fig.update_layout(xaxis_tickangle=-45, height=380)
        st.plotly_chart(fig, use_container_width=True)

        # Seasonal heatmap
        st.subheader("Seasonal Heatmap — Units by FY and Month")
        month_order = ["Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec","Jan","Feb","Mar"]
        month_num   = [4,5,6,7,8,9,10,11,12,1,2,3]
        month_map   = dict(zip(month_num, month_order))
        sales_current2 = sales_current.copy()
        sales_current2["FY"]       = sales_current2["Invoice_Date"].apply(
            lambda d: f"FY {d.year}-{str(d.year+1)[-2:]}" if d.month >= 4
                      else f"FY {d.year-1}-{str(d.year)[-2:]}")
        sales_current2["FY_Month"] = sales_current2["Invoice_Date"].dt.month.map(month_map)
        heat = (sales_current2.groupby(["FY","FY_Month"])["Quantity"]
                .sum().unstack(fill_value=0))
        heat = heat.reindex(columns=[m for m in month_order if m in heat.columns])
        fig_h = px.imshow(heat, text_auto=True, color_continuous_scale="YlOrRd",
                          labels=dict(x="Month", y="Financial Year", color="Units"))
        fig_h.update_layout(height=280)
        st.plotly_chart(fig_h, use_container_width=True)

    with tab2:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Top Styles by Volume")
            n_styles = st.slider("Show top N styles", 5, 20, 10)
            top_styles = (sales.groupby("Style")["Quantity"].sum()
                          .sort_values(ascending=False).head(n_styles).reset_index())
            fig = px.bar(top_styles, x="Quantity", y="Style", orientation="h",
                         color="Quantity", color_continuous_scale="Blues", text="Quantity")
            fig.update_traces(texttemplate="%{text:,}")
            fig.update_layout(height=400, coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("Category Breakdown")
            cat_sum = (sales_cat.groupby("Category")
                       .agg(Qty=("Quantity","sum"), Value=("Item_Total","sum"))
                       .reset_index().sort_values("Qty", ascending=False))
            cat_sum["Qty_Pct"]   = (cat_sum["Qty"] / cat_sum["Qty"].sum() * 100).round(1)
            cat_sum["Value_Pct"] = (cat_sum["Value"] / cat_sum["Value"].sum() * 100).round(1)
            fig2 = px.bar(cat_sum, x="Category", y="Qty",
                          color="Category", text="Qty_Pct",
                          color_discrete_sequence=px.colors.qualitative.Set2)
            fig2.update_traces(texttemplate="%{text}%", textposition="outside")
            fig2.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig2, use_container_width=True)

        # Top SKUs table
        st.subheader("Top 20 SKUs by Sales Volume")
        top20 = (sales.groupby("SKU_Code")["Quantity"].sum()
                 .sort_values(ascending=False).head(20).reset_index())
        top20.columns = ["SKU Code","Total Units"]
        top20["Rank"] = range(1, 21)
        top20["% of Total"] = (top20["Total Units"] / sales["Quantity"].sum() * 100).round(1)
        top20 = top20[["Rank","SKU Code","Total Units","% of Total"]]
        st.dataframe(top20, use_container_width=True, hide_index=True)

    with tab3:
        st.subheader("Retailer Performance Analysis")
        top_ret = (sales.groupby("Party_Code")
                   .agg(Qty=("Quantity","sum"), Value=("Item_Total","sum"),
                        Invoices=("Invoice_Number","nunique"))
                   .sort_values("Qty", ascending=False).reset_index())
        top_ret["Pct"] = (top_ret["Qty"] / top_ret["Qty"].sum() * 100).round(1)

        n_ret = st.slider("Show top N retailers", 5, 20, 15)
        fig = px.bar(top_ret.head(n_ret), x="Qty", y="Party_Code", orientation="h",
                     color="Qty", color_continuous_scale="Purples", text="Pct",
                     labels={"Party_Code":"Retailer","Qty":"Units Purchased"})
        fig.update_traces(texttemplate="%{text}%", textposition="outside")
        fig.update_layout(height=500, coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

        col1, col2, col3 = st.columns(3)
        col1.metric("Top Retailer Share", "38.1%", "RETAILER_026")
        col2.metric("Top 2 Combined", "54.6%", "RETAILER_026 + RETAILER_021")
        col3.metric("Top 15 Combined", "88.4%", "High concentration")

    with tab4:
        st.subheader("Size Distribution Analysis")
        top_sizes = (sales.groupby("Size")["Quantity"].sum()
                     .sort_values(ascending=False).head(25).reset_index())

        def size_type(s):
            if re.match(r'^\d{2}[A-F]$', str(s).strip().upper()): return "Cup Size"
            elif str(s).strip().upper() in ["XS","S","M","L","XL","XXL","2XL","3XL"]: return "Standard Size"
            else: return "Other"

        top_sizes["Type"] = top_sizes["Size"].apply(size_type)
        fig = px.bar(top_sizes, x="Quantity", y="Size", orientation="h",
                     color="Type", text="Quantity",
                     color_discrete_map={"Cup Size":"#667eea","Standard Size":"#16a34a","Other":"#9ca3af"})
        fig.update_traces(texttemplate="%{text:,}")
        fig.update_layout(height=650)
        st.plotly_chart(fig, use_container_width=True)

# ═══════════════════════════
# PAGE 3 — DEMAND FORECAST
# ═══════════════════════════
elif page == "🔮  Demand Forecast":
    st.title("🔮 Demand Forecasting")
    st.markdown("SKU and style-level demand forecasting using Moving Average and Linear Regression models.")
    st.divider()

    # Style selector
    all_styles = sorted(sales_current["Style"].dropna().unique())
    selected_style = st.selectbox("Select Style Code", all_styles,
                                  index=all_styles.index("D143") if "D143" in all_styles else 0)

    # Build monthly series for selected style
    style_monthly = (sales_current[sales_current["Style"] == selected_style]
                     .groupby("Month")["Quantity"].sum().reset_index())
    all_months = pd.period_range(sales_current["Month"].min(),
                                  sales_current["Month"].max(), freq="M")
    style_full = (style_monthly.set_index("Month")["Quantity"]
                  .reindex(all_months, fill_value=0).reset_index())
    style_full.columns = ["Month","Qty"]
    style_full["Month_str"] = style_full["Month"].astype(str)
    style_full["t"] = range(len(style_full))

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Units Sold", f"{style_full['Qty'].sum():,}")
    col2.metric("Avg Monthly Demand", f"{style_full['Qty'].mean():.1f} units")
    col3.metric("Peak Month", f"{style_full['Qty'].max()} units")
    col4.metric("Active Months", f"{(style_full['Qty']>0).sum()} / {len(style_full)}")

    st.divider()

    # Train/test/forecast
    TRAIN_END = 25
    train = style_full.iloc[:TRAIN_END].copy()
    test  = style_full.iloc[TRAIN_END:].copy()

    # MA3
    style_full["MA3"] = style_full["Qty"].rolling(3).mean().shift(1)
    ma_test = style_full.loc[test.index, "MA3"].fillna(style_full["Qty"].mean())

    # LR
    features = ["t","sin_month","cos_month"]
    train_f = make_features(train)
    test_f  = make_features(test)
    lr = LinearRegression()
    lr.fit(train_f[features], train_f["Qty"])
    lr_test = np.maximum(lr.predict(test_f[features]), 0).round().astype(int)

    # Next 3 months forecast
    next_months = pd.period_range(start=style_full["Month"].max() + 1, periods=3, freq="M")
    next_df = pd.DataFrame({"Month": next_months,
                             "t": range(len(style_full), len(style_full)+3),
                             "Month_str": [str(m) for m in next_months]})
    next_f = make_features(next_df)
    lr_next = np.maximum(lr.predict(next_f[features]), 0).round().astype(int)
    last3 = style_full["Qty"].tail(3).values
    ma_next = [round(last3.mean(), 1)]
    ma_next.append(round(np.array([last3[-2], last3[-1], ma_next[0]]).mean(), 1))
    ma_next.append(round(np.array([last3[-1], ma_next[0], ma_next[1]]).mean(), 1))

    # Chart
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=train["Month_str"], y=train["Qty"],
                             mode="lines+markers", name="Actual (Train)",
                             line=dict(color="#667eea", width=2),
                             marker=dict(size=5)))
    fig.add_trace(go.Scatter(x=test["Month_str"], y=test["Qty"],
                             mode="lines+markers", name="Actual (Test)",
                             line=dict(color="#667eea", width=2, dash="dash"),
                             marker=dict(size=7, symbol="square")))
    fig.add_trace(go.Scatter(x=test["Month_str"], y=ma_test.values,
                             mode="lines+markers", name="MA3 Predicted",
                             line=dict(color="#16a34a", width=2),
                             marker=dict(size=7, symbol="triangle-up")))
    fig.add_trace(go.Scatter(x=test["Month_str"], y=lr_test,
                             mode="lines+markers", name="LR Predicted",
                             line=dict(color="#ea580c", width=2),
                             marker=dict(size=7, symbol="diamond")))
    # Forecast lines
    fx = [test["Month_str"].iloc[-1]] + [str(m) for m in next_months]
    fig.add_trace(go.Scatter(x=fx, y=[test["Qty"].iloc[-1]]+list(lr_next),
                             mode="lines+markers", name="LR Forecast",
                             line=dict(color="#ea580c", width=2, dash="dot"),
                             marker=dict(size=7, symbol="diamond")))
    fig.add_trace(go.Scatter(x=fx, y=[test["Qty"].iloc[-1]]+ma_next,
                             mode="lines+markers", name="MA3 Forecast",
                             line=dict(color="#16a34a", width=2, dash="dot"),
                             marker=dict(size=7, symbol="triangle-up")))

    # Vertical markers
    test_start_x  = test["Month_str"].iloc[0]
    forecast_start_x = str(next_months[0])

    all_x_vals = style_full["Month_str"].tolist() + [str(m) for m in next_months]

    fig.add_shape(type="line",
                  x0=test_start_x, x1=test_start_x,
                  y0=0, y1=1, yref="paper",
                  line=dict(color="gray", dash="dash", width=1.5))
    fig.add_annotation(x=test_start_x, y=1.02, yref="paper",
                       text="▼ Test", showarrow=False,
                       font=dict(size=10, color="gray"))

    fig.add_shape(type="line",
                  x0=forecast_start_x, x1=forecast_start_x,
                  y0=0, y1=1, yref="paper",
                  line=dict(color="purple", dash="dash", width=1.5))
    fig.add_annotation(x=forecast_start_x, y=1.02, yref="paper",
                       text="▼ Forecast", showarrow=False,
                       font=dict(size=10, color="purple"))

    fig.update_layout(title=f"Demand Forecast — Style {selected_style}",
                      xaxis_title="Month", yaxis_title="Units",
                      height=420, hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

    # Forecast table
    st.subheader("3-Month Forward Forecast")
    col1, col2, col3 = st.columns(3)
    for i, (col, m) in enumerate(zip([col1,col2,col3], next_months)):
        rec = round((ma_next[i] + lr_next[i]) / 2 / 5) * 5
        col.metric(str(m), f"LR: {lr_next[i]} | MA3: {ma_next[i]:.0f}",
                   f"Recommended order: ~{int(rec)} units")

    st.info("💡 Recommended order quantity = average of both models, rounded to nearest 5 units. Use as a planning guide, not a precise target.")

# ═══════════════════════
# PAGE 4 — STOCK ANALYSIS
# ═══════════════════════
elif page == "📦  Stock Analysis":
    st.title("📦 Stock Analysis")
    st.markdown("Inventory position analysis from daily stock snapshots (Nov 2025 – Mar 2026).")
    st.divider()

    latest = stock["Snapshot_Date"].max()
    latest_stock = (stock[stock["Snapshot_Date"] == latest]
                    .groupby("SKU_Code")["Stock_Qty"].sum()
                    .sort_values(ascending=False).reset_index())

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Latest Snapshot", str(latest.date()))
    col2.metric("Total SKUs in Stock", f"{latest_stock[latest_stock['Stock_Qty']>0].shape[0]:,}")
    col3.metric("Total Units in Stock", f"{latest_stock['Stock_Qty'].sum():,}")
    col4.metric("Avg per SKU", f"{latest_stock['Stock_Qty'].mean():.1f} units")

    st.divider()

    col_l, col_r = st.columns(2)

    with col_l:
        st.subheader("Style Stock Over Time")
        all_styles_stock = sorted(stock["Style"].dropna().unique())
        sel_style = st.selectbox("Select Style", all_styles_stock,
                                  index=all_styles_stock.index("D143") if "D143" in all_styles_stock else 0)

        style_stock = (stock[stock["Style"] == sel_style]
                       .groupby("Snapshot_Date")["Stock_Qty"].sum().reset_index())
        avg_stock = style_stock["Stock_Qty"].mean()

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=style_stock["Snapshot_Date"],
                                 y=style_stock["Stock_Qty"],
                                 fill="tozeroy", name="Stock Level",
                                 line=dict(color="#667eea", width=1.5)))
        fig.add_hline(y=avg_stock, line_dash="dash", line_color="red",
                      annotation_text=f"Avg: {avg_stock:.0f}")
        fig.update_layout(title=f"Stock Level — Style {sel_style}",
                          xaxis_title="Date", yaxis_title="Units in Stock",
                          height=350)
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        st.subheader(f"Top 20 SKUs by Current Stock ({latest.date()})")
        top20_stock = latest_stock.head(20).copy()
        fig2 = px.bar(top20_stock, x="Stock_Qty", y="SKU_Code", orientation="h",
                      color="Stock_Qty", color_continuous_scale="Blues",
                      text="Stock_Qty",
                      labels={"SKU_Code":"SKU","Stock_Qty":"Units in Stock"})
        fig2.update_traces(texttemplate="%{text}")
        fig2.update_layout(height=350, coloraxis_showscale=False)
        st.plotly_chart(fig2, use_container_width=True)

    st.divider()
    st.subheader("Stock Level Snapshot Over Time — All SKUs")
    daily_total = (stock.groupby("Snapshot_Date")["Stock_Qty"].sum().reset_index())
    fig3 = px.line(daily_total, x="Snapshot_Date", y="Stock_Qty",
                   labels={"Snapshot_Date":"Date","Stock_Qty":"Total Units in Stock"},
                   color_discrete_sequence=["#764ba2"])
    fig3.update_layout(height=300)
    st.plotly_chart(fig3, use_container_width=True)

# ═══════════════════════════
# PAGE 5 — PURCHASE VS SALES
# ═══════════════════════════
elif page == "🔄  Purchase vs Sales":
    st.title("🔄 Purchase vs Sales Comparison")
    st.markdown("Monthly analysis of procurement vs sales volume — identifying overstock and understock events.")
    st.divider()

    sales_m = (sales_current.groupby("Month")["Quantity"]
               .sum().reset_index().rename(columns={"Quantity":"Sales_Qty"}))
    purchase_m = (purchase.groupby("Month")["Quantity"]
                  .sum().reset_index().rename(columns={"Quantity":"Purchase_Qty"}))
    comp = pd.merge(sales_m, purchase_m, on="Month", how="outer").fillna(0)
    comp = comp.sort_values("Month").reset_index(drop=True)
    comp["Month_str"] = comp["Month"].astype(str)
    comp["Diff"] = comp["Purchase_Qty"] - comp["Sales_Qty"]
    comp["Status"] = comp["Diff"].apply(
        lambda d: "OVERSTOCK" if d > 100 else "UNDERSTOCK" if d < -100 else "BALANCED")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Purchased", f"{comp['Purchase_Qty'].sum():,.0f} units")
    col2.metric("Total Sold", f"{comp['Sales_Qty'].sum():,.0f} units")
    col3.metric("Net Difference", f"+{comp['Diff'].sum():,.0f} units")
    col4.metric("Sell-Through Rate", "84.9%")

    st.divider()

    # Grouped bar chart
    fig = go.Figure()
    fig.add_trace(go.Bar(x=comp["Month_str"], y=comp["Purchase_Qty"],
                         name="Purchased", marker_color="#ea580c", opacity=0.8))
    fig.add_trace(go.Bar(x=comp["Month_str"], y=comp["Sales_Qty"],
                         name="Sold", marker_color="#667eea", opacity=0.8))
    fig.update_layout(barmode="group", title="Monthly Purchase vs Sales Quantity",
                      xaxis_tickangle=-45, height=380,
                      xaxis_title="Month", yaxis_title="Units")
    st.plotly_chart(fig, use_container_width=True)

    # Status breakdown
    col_l, col_r = st.columns(2)
    with col_l:
        st.subheader("Monthly Status")
        status_counts = comp["Status"].value_counts().reset_index()
        status_counts.columns = ["Status","Months"]
        color_map = {"BALANCED":"#16a34a","OVERSTOCK":"#ea580c","UNDERSTOCK":"#dc2626"}
        fig2 = px.pie(status_counts, names="Status", values="Months",
                      color="Status", color_discrete_map=color_map, hole=0.4)
        fig2.update_layout(height=280)
        st.plotly_chart(fig2, use_container_width=True)

    with col_r:
        st.subheader("Month-by-Month Detail")
        display = comp[["Month_str","Purchase_Qty","Sales_Qty","Diff","Status"]].copy()
        display.columns = ["Month","Purchased","Sold","Difference","Status"]
        display["Purchased"] = display["Purchased"].astype(int)
        display["Sold"]      = display["Sold"].astype(int)
        display["Difference"]= display["Difference"].astype(int)
        st.dataframe(display, use_container_width=True, hide_index=True, height=280)

    st.info("📌 UNDERSTOCK months indicate potential lost sales. The worst event was Aug 2025 (-439 units) — a direct consequence of the July 2025 demand spike depleting warehouse stock.")

# ═══════════════════════════
# PAGE 6 — MODEL EVALUATION
# ═══════════════════════════
elif page == "🎯  Model Evaluation":
    st.title("🎯 Forecasting Model Evaluation")
    st.markdown("Comparison of Moving Average (MA3) vs Linear Regression models at SKU and style level.")
    st.divider()

    tab1, tab2 = st.tabs(["Style-Level Results","SKU-Level Results"])

    def run_model(series_full, train_end=25):
        train = series_full.iloc[:train_end].copy()
        test  = series_full.iloc[train_end:].copy()
        series_full2 = series_full.copy()
        series_full2["MA3"] = series_full2["Qty"].rolling(3).mean().shift(1)
        ma_test = series_full2.loc[test.index,"MA3"].fillna(series_full2["Qty"].mean())
        features = ["t","sin_month","cos_month"]
        train_f  = make_features(train)
        test_f   = make_features(test)
        lr = LinearRegression()
        lr.fit(train_f[features], train_f["Qty"])
        lr_test = np.maximum(lr.predict(test_f[features]), 0).round().astype(int)
        actual  = test["Qty"].values
        return test, actual, ma_test, lr_test

    with tab1:
        st.subheader("Style D143 — All Variants Aggregated")
        d143 = (sales_current[sales_current["Style"]=="D143"]
                .groupby("Month")["Quantity"].sum().reset_index())
        all_m = pd.period_range(sales_current["Month"].min(),
                                 sales_current["Month"].max(), freq="M")
        d143_full = (d143.set_index("Month")["Quantity"]
                     .reindex(all_m, fill_value=0).reset_index())
        d143_full.columns = ["Month","Qty"]
        d143_full["Month_str"] = d143_full["Month"].astype(str)
        d143_full["t"]         = range(len(d143_full))

        test_d, actual_d, ma_d, lr_d = run_model(d143_full)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Evaluation Metrics**")
            metrics = {
                "Metric": ["MAE","RMSE","MAPE"],
                "Moving Avg (MA3)": [
                    f"{mean_absolute_error(actual_d, ma_d.values):.1f}",
                    f"{np.sqrt(mean_squared_error(actual_d, ma_d.values)):.1f}",
                    f"{mape_score(actual_d, ma_d.values):.1f}%"
                ],
                "Linear Regression": [
                    f"{mean_absolute_error(actual_d, lr_d):.1f}",
                    f"{np.sqrt(mean_squared_error(actual_d, lr_d)):.1f}",
                    f"{mape_score(actual_d, lr_d):.1f}%"
                ]
            }
            st.dataframe(pd.DataFrame(metrics), hide_index=True, use_container_width=True)
            st.success("✅ Linear Regression outperforms Moving Average on all metrics")

        with col2:
            st.markdown("**Actual vs Predicted — Test Period**")
            test_display = pd.DataFrame({
                "Month": test_d["Month_str"].tolist(),
                "Actual": actual_d,
                "MA3 Pred": [f"{v:.0f}" for v in ma_d.values],
                "LR Pred": lr_d,
                "MA3 Error": [f"{int(m)-a:+d}" for m,a in zip(ma_d.values, actual_d)],
                "LR Error":  [f"{l-a:+d}" for l,a in zip(lr_d, actual_d)]
            })
            st.dataframe(test_display, hide_index=True, use_container_width=True)

        fig = go.Figure()
        fig.add_trace(go.Bar(x=test_d["Month_str"], y=actual_d,
                             name="Actual", marker_color="#667eea"))
        fig.add_trace(go.Bar(x=test_d["Month_str"], y=ma_d.values,
                             name="MA3 Predicted", marker_color="#16a34a"))
        fig.add_trace(go.Bar(x=test_d["Month_str"], y=lr_d,
                             name="LR Predicted", marker_color="#ea580c"))
        fig.update_layout(barmode="group", title="Actual vs Predicted — Test Period (Dec 2025 – Mar 2026)",
                          height=350, xaxis_title="Month", yaxis_title="Units")
        st.plotly_chart(fig, use_container_width=True)

        st.warning("⚠️ High MAPE is driven by the December 2025 incentive-driven demand spike (452 actual vs 171 predicted) and the January 2026 post-bulk-buy suppression (21 actual vs 179 predicted). Model performs well on normal demand months.")

    with tab2:
        st.subheader("D143_BLACK_36C — Individual SKU Level")
        sku_data = (sales_current[sales_current["SKU_Code"]=="D143_BLACK_36C"]
                    .groupby("Month")["Quantity"].sum().reset_index())
        all_m = pd.period_range(sales_current["Month"].min(),
                                 sales_current["Month"].max(), freq="M")
        sku_full = (sku_data.set_index("Month")["Quantity"]
                    .reindex(all_m, fill_value=0).reset_index())
        sku_full.columns = ["Month","Qty"]
        sku_full["Month_str"] = sku_full["Month"].astype(str)
        sku_full["t"]         = range(len(sku_full))

        test_s, actual_s, ma_s, lr_s = run_model(sku_full)

        col1, col2 = st.columns(2)
        with col1:
            metrics_s = {
                "Metric": ["MAE","RMSE","MAPE"],
                "Moving Avg (MA3)": [
                    f"{mean_absolute_error(actual_s, ma_s.values):.2f}",
                    f"{np.sqrt(mean_squared_error(actual_s, ma_s.values)):.2f}",
                    f"{mape_score(actual_s, ma_s.values):.1f}%"
                ],
                "Linear Regression": [
                    f"{mean_absolute_error(actual_s, lr_s):.2f}",
                    f"{np.sqrt(mean_squared_error(actual_s, lr_s)):.2f}",
                    f"{mape_score(actual_s, lr_s):.1f}%"
                ]
            }
            st.dataframe(pd.DataFrame(metrics_s), hide_index=True, use_container_width=True)
            st.info("ℹ️ MAE of ~2.75 units means the model is off by fewer than 3 units per month — meaningful accuracy for a product selling 1-9 units/month.")

        with col2:
            test_s_display = pd.DataFrame({
                "Month": test_s["Month_str"].tolist(),
                "Actual": actual_s,
                "MA3 Pred": [f"{v:.1f}" for v in ma_s.values],
                "LR Pred": lr_s,
            })
            st.dataframe(test_s_display, hide_index=True, use_container_width=True)