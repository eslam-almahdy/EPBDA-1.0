"""
EPBDA Web Dashboard - Local Interface
Run this to access EPBDA via web browser
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go
from epbda_core import *

# Page configuration
st.set_page_config(
    page_title="EPBDA - Energy Portfolio Decision Engine",
    page_icon="⚡",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #2c3e50;
        text-align: center;
        padding: 1rem;
        background: linear-gradient(90deg, #3498db, #2ecc71);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #ecf0f1;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #3498db;
    }
    .critical {
        color: #e74c3c;
        font-weight: bold;
    }
    .action {
        color: #f39c12;
        font-weight: bold;
    }
    .hold {
        color: #2ecc71;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'engine' not in st.session_state:
    st.session_state.engine = DecisionEngine()
if 'decision_history' not in st.session_state:
    st.session_state.decision_history = []

# Title
st.markdown('<div class="main-header">⚡ EPBDA - Energy Portfolio Decision Engine</div>', unsafe_allow_html=True)

# Create tabs for main interface and technical documentation
tab1, tab2, tab3 = st.tabs(["🎯 Decision Engine", "📊 Technical Report", "📚 User Guide"])

# TAB 1: Main Decision Interface
with tab1:
    # Sidebar - Input Configuration (will be visible across all tabs)
    pass  # Placeholder, sidebar content below

# Sidebar - Input Configuration
st.sidebar.header("📊 Portfolio Inputs")

# Timestamp
current_time = datetime.now().replace(second=0, microsecond=0)
st.sidebar.subheader("⏰ Time")
timestamp = st.sidebar.time_input("Timestamp", current_time.time())

# Forecasts
st.sidebar.subheader("📈 Demand Forecast (MW)")
demand_p10 = st.sidebar.number_input("P10 (Pessimistic)", value=45.0, step=1.0)
demand_p50 = st.sidebar.number_input("P50 (Expected)", value=50.0, step=1.0)
demand_p90 = st.sidebar.number_input("P90 (Optimistic)", value=55.0, step=1.0)

st.sidebar.subheader("☀️ PV Forecast (MW)")
pv_p10 = st.sidebar.number_input("P10", value=0.5, step=0.5, key="pv_p10")
pv_p50 = st.sidebar.number_input("P50", value=1.0, step=0.5, key="pv_p50")
pv_p90 = st.sidebar.number_input("P90", value=2.0, step=0.5, key="pv_p90")

st.sidebar.subheader("💨 Wind Forecast (MW)")
wind_p10 = st.sidebar.number_input("P10", value=8.0, step=1.0, key="wind_p10")
wind_p50 = st.sidebar.number_input("P50", value=12.0, step=1.0, key="wind_p50")
wind_p90 = st.sidebar.number_input("P90", value=15.0, step=1.0, key="wind_p90")

st.sidebar.subheader("🔒 Hedge Position")
hedge_mw = st.sidebar.number_input("Current Hedge (MW)", value=35.0, step=1.0)

st.sidebar.subheader("💰 Market Prices (€/MWh)")
day_ahead = st.sidebar.number_input("Day-Ahead", value=120.0, step=5.0)
intraday_bid = st.sidebar.number_input("Intraday Buy", value=150.0, step=5.0)
intraday_ask = st.sidebar.number_input("Intraday Sell", value=140.0, step=5.0)
rebap_plus = st.sidebar.number_input("ReBAP+ (Shortage)", value=300.0, step=10.0)
rebap_minus = st.sidebar.number_input("ReBAP- (Surplus)", value=-20.0, step=5.0)

st.sidebar.subheader("⚖️ Risk Appetite")
cvar_limit = st.sidebar.number_input("CVaR Limit (€)", value=500.0, step=50.0)
risk_threshold = st.sidebar.number_input("Risk Energy Threshold (€)", value=800.0, step=50.0)

# Decision button
if st.sidebar.button("🎯 MAKE DECISION", type="primary", use_container_width=True):
    # Build portfolio state
    portfolio_state = PortfolioState(
        timestamp=datetime.combine(datetime.now().date(), timestamp),
        demand_forecast=ProbabilisticForecast(demand_p10, demand_p50, demand_p90, current_time),
        pv_forecast=ProbabilisticForecast(pv_p10, pv_p50, pv_p90, current_time),
        wind_forecast=ProbabilisticForecast(wind_p10, wind_p50, wind_p90, current_time),
        hedge_position_mw=hedge_mw,
        demand_flexibility=[
            FlexibilityAsset("Industrial Flex", 5.0, 60, 80.0),
            FlexibilityAsset("Digital Battery", 3.0, 30, 100.0)
        ],
        storage=StorageAsset(10.0, 5.0, 0.9, 50.0, 0.6),
        pv_curtailment_available_mw=pv_p50,
        wind_curtailment_available_mw=wind_p50,
        curtailment_cost_per_mwh=30.0,
        market_prices=MarketPrices(
            day_ahead, intraday_bid, intraday_ask,
            rebap_plus, rebap_minus,
            rebap_plus * 1.5, rebap_minus * 2
        ),
        risk_appetite=RiskAppetite(
            cvar_limit, risk_threshold, 70.0, 2.0
        )
    )
    
    # Make decision
    decision = st.session_state.engine.make_decision(portfolio_state)
    st.session_state.decision_history.append(decision)
    st.session_state.current_decision = decision

# Main content
if 'current_decision' in st.session_state:
    decision = st.session_state.current_decision
    
    # Top metrics
    col1, col2, col3, col4 = st.columns(4)
    
    risk_color = {
        RiskState.HOLD: "🟢",
        RiskState.WATCH: "🟡",
        RiskState.ACTION: "🟠",
        RiskState.CRITICAL: "🔴"
    }[decision.risk_state]
    
    with col1:
        st.metric(
            label="Risk State",
            value=f"{risk_color} {decision.risk_state.value}",
            delta="Requires Action" if decision.risk_state in [RiskState.ACTION, RiskState.CRITICAL] else "OK"
        )
    
    with col2:
        st.metric(
            label="Scenario",
            value=decision.scenario_type.value,
            delta=f"{decision.risk_metrics.residual_position_mw:+.1f} MW"
        )
    
    with col3:
        st.metric(
            label="Confidence",
            value=f"{decision.confidence_pct:.1f}%",
            delta="Low" if decision.confidence_pct < 70 else "Good"
        )
    
    with col4:
        st.metric(
            label="Risk Energy",
            value=f"{decision.risk_before_eur:.0f}€",
            delta=f"-{decision.primary_action.risk_reduction_eur:.0f}€" if decision.primary_action.risk_reduction_eur > 0 else "No change"
        )
    
    # Main decision card
    st.markdown("---")
    st.subheader("🎯 Recommended Action")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        action_icon = {
            ActionType.DO_NOTHING: "⏸️",
            ActionType.INTRADAY_BUY: "💰",
            ActionType.INTRADAY_SELL: "💵",
            ActionType.ACTIVATE_DEMAND_FLEX: "🔋",
            ActionType.STORAGE_DISCHARGE: "🔌",
            ActionType.STORAGE_CHARGE: "⚡",
            ActionType.CURTAIL_PV: "☀️",
            ActionType.CURTAIL_WIND: "💨"
        }.get(decision.primary_action.action_type, "🎯")
        
        st.markdown(f"### {action_icon} {decision.primary_action.action_type.value}")
        st.markdown(f"**Volume:** {decision.primary_action.volume_mw:.1f} MW")
        st.markdown(f"**Cost:** {decision.primary_action.cost_eur:.0f}€")
        st.markdown(f"**Marginal Cost:** {decision.primary_action.marginal_cost_eur_per_mwh:.2f} €/MWh")
        st.markdown(f"**Risk Reduction:** {decision.primary_action.risk_reduction_eur:.0f}€")
        
        st.info(f"📝 **Rationale:** {decision.rationale}")
    
    with col2:
        st.markdown("### Risk Metrics")
        st.markdown(f"**Expected Cost:** {decision.risk_metrics.expected_cost_eur:.0f}€")
        st.markdown(f"**CVaR(95%):** {decision.risk_metrics.cvar_95_eur:.0f}€")
        st.markdown(f"**P(Shortage):** {decision.risk_metrics.prob_shortage*100:.1f}%")
        st.markdown(f"**P(Surplus):** {decision.risk_metrics.prob_surplus*100:.1f}%")
        
        if decision.escalation_required:
            st.error("⚠️ **ESCALATION REQUIRED**")
        if decision.manual_override_required:
            st.warning("⚠️ **MANUAL OVERRIDE NEEDED**")
    
    # Alternative actions
    if decision.alternative_actions:
        st.markdown("---")
        st.subheader("🔄 Alternative Actions")
        
        alt_data = []
        for alt in decision.alternative_actions[:3]:
            alt_data.append({
                "Action": alt.action_type.value,
                "Volume (MW)": f"{alt.volume_mw:.1f}",
                "Cost (€)": f"{alt.cost_eur:.0f}",
                "€/MWh": f"{alt.marginal_cost_eur_per_mwh:.2f}",
                "Rationale": alt.rationale
            })
        
        st.dataframe(pd.DataFrame(alt_data), use_container_width=True)
    
    # Hedge & Buffer recommendations
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔒 Hedge Recommendation")
        st.metric("Recommended Hedge", f"{decision.recommended_hedge_mw:.1f} MW")
        st.metric("Current Hedge", f"{hedge_mw:.1f} MW")
        delta_hedge = decision.recommended_hedge_mw - hedge_mw
        st.metric("Adjustment", f"{delta_hedge:+.1f} MW")
    
    with col2:
        st.subheader("🛡️ Buffer Recommendation")
        st.metric("Recommended Buffer", f"{decision.recommended_buffer_mw:.1f} MW")
        st.metric("Buffer Adjustment", decision.buffer_adjustment)
        
        adjustment_color = {
            "INCREASE": "🔺 Widen safety margin",
            "DECREASE": "🔻 Release excess hedge",
            "MAINTAIN": "➡️ Keep current buffer"
        }
        st.info(adjustment_color.get(decision.buffer_adjustment, ""))
    
    # Visualization
    st.markdown("---")
    st.subheader("📊 Portfolio Position")
    
    # Create balance chart
    fig = go.Figure()
    
    net_load = decision.risk_metrics.expected_net_load_mw
    hedge = hedge_mw
    residual = decision.risk_metrics.residual_position_mw
    
    fig.add_trace(go.Bar(
        name="Net Load (Demand - Gen)",
        x=["Expected"],
        y=[net_load],
        marker_color='#e74c3c'
    ))
    
    fig.add_trace(go.Bar(
        name="Hedge Position",
        x=["Expected"],
        y=[hedge],
        marker_color='#2ecc71'
    ))
    
    fig.add_trace(go.Scatter(
        name="Residual",
        x=["Expected"],
        y=[residual],
        mode='markers',
        marker=dict(size=20, color='#f39c12', symbol='diamond'),
        yaxis='y2'
    ))
    
    fig.update_layout(
        title="Portfolio Balance",
        barmode='group',
        yaxis=dict(title="MW"),
        yaxis2=dict(title="Residual (MW)", overlaying='y', side='right'),
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Trigger condition
    st.markdown("---")
    st.subheader("🚨 Trigger Analysis")
    st.info(f"**Condition:** {decision.trigger_condition}")
    
    if decision.breach_details:
        st.error(f"**Breach:** {decision.breach_details}")

else:
    st.info("👈 Configure portfolio inputs in the sidebar and click **MAKE DECISION** to start")
    
    # Show example scenarios
    st.markdown("---")
    st.subheader("📚 Quick Start Examples")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### ⚠️ Shortage Scenario
        - **Demand:** 50 MW (P50)
        - **Generation:** 13 MW total
        - **Hedge:** 35 MW
        - **Expected:** Shortage → Buy or activate flexibility
        """)
    
    with col2:
        st.markdown("""
        ### ✅ Surplus Scenario
        - **Demand:** 22 MW (P50)
        - **Generation:** 42 MW total
        - **Hedge:** 22 MW
        - **Expected:** Surplus → Sell or curtail
        """)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #7f8c8d; padding: 1rem;'>
    <strong>EPBDA v1.0</strong> - Energy Portfolio Balancing & Decision Algorithm<br>
    Professional-grade algorithmic decision engine for 15-minute energy portfolio management<br>
    🔒 All calculations performed locally | 📊 Real-time decision-making
</div>
""", unsafe_allow_html=True)
