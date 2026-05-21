# 📦 FMCG Distribution Analytics System

> AI-driven order management and demand forecasting system for a regional FMCG distributor in Goa, India.

**BCA Final Year Major Project — Amity University Online**
**Student:** Hemant Parasmal Borana | **Enrolment:** A9922523001748(EL)
**Programme:** Bachelor of Computer Application (Major: Data Analytics)

---

## 📋 Project Overview

This project addresses the operational inefficiencies of a regional innerwear and apparel distributor by building a complete digital order management and analytics system. The system replaces a manual diary-and-WhatsApp order process with a data-driven platform that provides real-time stock visibility, automated purchase order placement, and SKU-level demand forecasting.

### Key Features
- 📱 **Digital Order Management** — Role-based app replacing manual diary/WhatsApp process
- 🔍 **Real-Time Stock Visibility** — Automated web scraping from company ERP portal
- 📧 **One-Click Order Placement** — Auto-fills and emails purchase orders to parent company
- 📊 **Demand Forecasting** — Python-based Linear Regression + Moving Average models
- 🖥️ **Interactive Dashboard** — 6-page Streamlit analytics app

---

## 🗂️ Repository Structure

```
fmcg-distribution-analytics/
│
├── app.py                          ← Streamlit dashboard (main app)
├── requirements.txt                ← Python dependencies
├── .gitignore                      ← Excludes sensitive data files
│
├── notebooks/
│   ├── major_project_analysis.ipynb  ← Main Jupyter analysis notebook
│   └── cleaning_scripts/             ← All data cleaning scripts (20 files)
│
├── outputs/
│   ├── chart_01_monthly_sales_trend.png
│   ├── chart_02_fy_comparison.png
│   ├── chart_03_top20_skus.png
│   ├── chart_04_top10_styles.png
│   ├── chart_05_category_breakdown.png
│   ├── chart_06_top15_retailers.png
│   ├── chart_07_current_firm_monthly.png
│   ├── chart_08_purchase_vs_sales.png
│   ├── chart_09_size_distribution.png
│   ├── chart_10_seasonal_heatmap.png
│   ├── chart_11_demand_forecast.png
│   ├── chart_12_model_evaluation.png
│   └── chart_13_stock_analysis.png
│
└── chapters/
    ├── FrontMatter.docx
    ├── Chapters_1_2_3.docx
    ├── Chapter4_DataAnalysis.docx
    ├── Chapter5_FindingsConclusion.docx
    ├── Chapter6_RecommendationsLimitations.docx
    ├── Bibliography.docx
    └── Appendix.docx
```

> **Note:** Raw and cleaned data files are excluded from this repository to protect proprietary business information. Only anonymized analysis outputs and code are included.

---

## 📊 Dataset Overview

| Dataset | Period | Records |
|---|---|---|
| Sales Billing Data (ERP) | Jun 2023 – Mar 2026 | 13,290 rows |
| Purchase Data | Nov 2023 – Mar 2026 | 10,071 rows |
| App Order Data | Nov 2025 – Mar 2026 | 2,558 rows |
| Stock Snapshots | Nov 2025 – Mar 2026 | 99,252 rows (132 snapshots) |
| SKU Master | — | 5,363 entries |
| Outlet Master | — | 107 outlets |

All datasets contain anonymized business data. Retailer names, style codes, and supplier identities have been replaced with coded identifiers.

---

## 🔑 Key Findings

- 📈 **+17.8% volume growth** and **+28.3% value growth** (FY 2024-25 → FY 2025-26)
- 🎯 **Top 2 style codes** (D143 + D239) = **44.4%** of total sales volume
- 🏪 **Top 2 retailers** = **54.6%** of total sales volume
- 📅 **December and March peaks** driven by retailer incentive target schemes — not seasonal demand
- 📦 **84.9% overall sell-through rate** with 4 understock events identified
- 🔮 **Linear Regression MAE = 134.8 units/month** at style level

---

## 🛠️ Tech Stack

| Category | Tools |
|---|---|
| Language | Python 3.13 |
| Data Analysis | pandas, numpy |
| Visualization | matplotlib, seaborn, plotly |
| Machine Learning | scikit-learn |
| Dashboard | Streamlit |
| Data Storage | Excel (openpyxl), Google Drive |
| Automation | Google Apps Script |
| IDE | Jupyter Notebook |

---

## 🌐 Live Demo

**The app is live and accessible here:**

👉 **[https://fmcg-distribution-analytics.streamlit.app/](https://fmcg-distribution-analytics.streamlit.app/)**

> Note: The hosted app runs on anonymized sample data. The full analysis uses proprietary operational data stored locally.

---

## 🚀 Running Locally

### Prerequisites
```bash
pip install -r requirements.txt
```

### Run
```bash
streamlit run app.py
```

The app runs on `http://localhost:8501` and includes 6 pages:
1. 🏠 Dashboard — KPIs, monthly trend, category split
2. 📈 Sales Analysis — trends, top products, retailer analysis, size distribution
3. 🔮 Demand Forecast — interactive style selector, actual vs predicted, 3-month forecast
4. 📦 Stock Analysis — inventory level over time, current stock position
5. 🔄 Purchase vs Sales — overstock/understock analysis
6. 🎯 Model Evaluation — MA3 vs Linear Regression comparison

> **Note:** The app requires the `data_cleaned/` folder with cleaned data files to run. Due to data privacy, these files are not included in the repository.

---

## 📓 Running the Jupyter Notebook

```bash
jupyter notebook notebooks/major_project_analysis.ipynb
```

The notebook covers:
- Data loading and validation (Cells 1–4)
- Monthly and FY-level sales analysis (Cells 5–8)
- Product and category analysis (Cells 9–10)
- Retailer analysis (Cell 11)
- Purchase vs sales comparison (Cell 12)
- Size distribution (Cell 13)
- Seasonal heatmap (Cell 14)
- Demand forecasting model (Cells 15–20)
- Stock analysis (Cell 21)

---

## 📁 Data Cleaning Pipeline

All raw data was processed through a systematic cleaning pipeline before analysis:

```
Raw Data → clean_01 (app orders) → clean_02 (sales billing) →
clean_03 (purchase data) → clean_04 (style anonymization) →
clean_05 (SKU master) → clean_06 (category mapping) →
clean_07 (outlet master) → clean_08 (stock snapshots) →
Cleaned Data
```

Scripts are in `notebooks/cleaning_scripts/`. Run in numerical order.

---

## 📄 Report

The full project report is available in the `chapters/` folder as individual Word documents:

| File | Contents |
|---|---|
| `FrontMatter.docx` | Title page, abstract, declaration, certificate, TOC |
| `Chapters_1_2_3.docx` | Introduction, Literature Review, Methodology |
| `Chapter4_DataAnalysis.docx` | Data Analysis, Results and Interpretation |
| `Chapter5_FindingsConclusion.docx` | Findings and Conclusion |
| `Chapter6_RecommendationsLimitations.docx` | Recommendations and Limitations |
| `Bibliography.docx` | APA 7th edition references |
| `Appendix.docx` | Charts, screenshots, code snippets |

---

## ⚠️ Data Privacy Notice

All data used in this project has been anonymized:
- Retailer names → `RETAILER_001`, `RETAILER_002` etc.
- Style codes → randomized alphanumeric codes (e.g., `D143`, `TB17`)
- Supplier name → `Brand Principal`
- MRP values → adjusted by a fixed offset
- Raw and cleaned data files are excluded from this repository

---

## 📜 License

This project is submitted as an academic requirement for the BCA programme at Amity University Online. All rights reserved. Not for commercial use.

---

*Project by **Hemant Parasmal Borana** | Amity University Online | 2024-25*