"""
EPBDA Professional Web Dashboard - With Integrated Technical Documentation
Run this to access EPBDA via web browser: streamlit run epbda_dashboard_pro.py
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go
from epbda_core import *
import os

# Page configuration
st.set_page_config(
    page_title="EPBDA Professional - Energy Portfolio Decision Engine",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        padding: 1rem;
        background: linear-gradient(90deg, #3498db, #2ecc71);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'engine' not in st.session_state:
    st.session_state.engine = DecisionEngine()
if 'decision_history' not in st.session_state:
    st.session_state.decision_history = []

# Title
st.markdown('<div class="main-header">⚡ EPBDA Professional - Energy Portfolio Decision Engine</div>', unsafe_allow_html=True)

# Create tabs
tab1, tab2, tab3 = st.tabs(["🎯 Decision Engine", "📊 Technical Report", "📚 Algorithm Details"])

# Sidebar inputs
st.sidebar.header("📊 Portfolio Inputs")
timestamp = st.sidebar.time_input("Timestamp", datetime.now().time())
demand_p10 = st.sidebar.number_input("Demand P10", value=45.0)
demand_p50 = st.sidebar.number_input("Demand P50", value=50.0)
demand_p90 = st.sidebar.number_input("Demand P90", value=55.0)
pv_p10 = st.sidebar.number_input("PV P10", value=0.5, key="pv10")
pv_p50 = st.sidebar.number_input("PV P50", value=1.0, key="pv50")
pv_p90 = st.sidebar.number_input("PV P90", value=2.0, key="pv90")
wind_p10 = st.sidebar.number_input("Wind P10", value=8.0, key="w10")
wind_p50 = st.sidebar.number_input("Wind P50", value=12.0, key="w50")
wind_p90 = st.sidebar.number_input("Wind P90", value=15.0, key="w90")
hedge_mw = st.sidebar.number_input("Hedge (MW)", value=35.0)
intraday_bid = st.sidebar.number_input("Intraday Buy", value=150.0)
rebap_plus = st.sidebar.number_input("ReBAP+", value=300.0)
cvar_limit = st.sidebar.number_input("CVaR Limit", value=500.0)

if st.sidebar.button("🚀 MAKE DECISION", type="primary"):
    portfolio_state = PortfolioState(
        timestamp=datetime.now(),
        demand_forecast=ProbabilisticForecast(demand_p10, demand_p50, demand_p90, datetime.now()),
        pv_forecast=ProbabilisticForecast(pv_p10, pv_p50, pv_p90, datetime.now()),
        wind_forecast=ProbabilisticForecast(wind_p10, wind_p50, wind_p90, datetime.now()),
        hedge_position_mw=hedge_mw,
        demand_flexibility=[FlexibilityAsset("Industrial", 5.0, 60, 80.0)],
        storage=StorageAsset(10.0, 5.0, 0.9, 50.0, 0.6),
        pv_curtailment_available_mw=pv_p50,
        wind_curtailment_available_mw=wind_p50,
        curtailment_cost_per_mwh=30.0,
        market_prices=MarketPrices(120, intraday_bid, 140, rebap_plus, -20, rebap_plus*1.5, -40),
        risk_appetite=RiskAppetite(cvar_limit, 800, 70, 2.0)
    )
    decision = st.session_state.engine.make_decision(portfolio_state)
    st.session_state.current_decision = decision

with tab1:
    if 'current_decision' in st.session_state:
        decision = st.session_state.current_decision
        st.success(f"**Risk State:** {decision.risk_state.value}")
        st.info(f"**Recommendation:** {decision.primary_action.rationale}")
        st.metric("CVaR (95%)", f"€{decision.risk_metrics.cvar_95_eur:.2f}")
        st.metric("Confidence", f"{decision.confidence_pct:.1f}%")
    else:
        st.info("Configure inputs and click MAKE DECISION")

with tab2:
    st.header("📊 EPBDA Technical Report")
    tech_file = "EPBDA_TECHNICAL_REPORT.md"
    if os.path.exists(tech_file):
        with open(tech_file, 'r', encoding='utf-8') as f:
            st.markdown(f.read())
        with open(tech_file, 'rb') as f:
            st.download_button("📥 Download Report", f, "EPBDA_Technical_Report.md")
    else:
        st.error("Technical report not found")

with tab3:
    st.header("📚 Algorithm Workflow")
    st.markdown("""
    ## Three-Stage Process
    
    ### Stage 1: Risk Assessment
    - Calculate net load = Demand - PV - Wind
    - Compute residual = Net Load - Hedge
    - Calculate CVaR(95%), expected cost, confidence
    - Classify risk state (HOLD/WATCH/ACTION/CRITICAL)
    
    ### Stage 2: Action Optimization
    - Evaluate all available actions (buy, sell, flex, storage, curtailment)
    - Calculate marginal cost (€/MWh) for each
    - Rank actions by cost-efficiency
    - Filter infeasible actions
    
    ### Stage 3: Decision Generation
    - Select optimal action based on risk state
    - Recommend hedge adjustments
    - Generate explainability (rationale, alternatives)
    - Flag escalations if needed
    """)

st.sidebar.markdown("---")
st.sidebar.info("EPBDA v1.0 Professional")
