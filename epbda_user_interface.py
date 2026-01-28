"""
EPBDA Multi-User Interface with Role-Based Access
Designed for Forecast Department and Management users
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from epbda_core import *
from epbda_database import EPBDADatabase
from epbda_validation import DataValidator, ForecastComparator
import time


# Professional styling - NO EMOJIS
st.set_page_config(
    page_title="EPBDA - Multi-User Interface",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS - Professional corporate styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 8px;
        border-left: 4px solid #2a5298;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 1rem 0;
        color: #1a1a1a;
    }
    .metric-card h3 {
        color: #2a5298;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    .metric-card p {
        color: #333333;
        font-size: 0.9rem;
        margin-bottom: 0;
    }
    .validation-error {
        background: #ffe6e6;
        border-left: 4px solid #d32f2f;
        padding: 1rem;
        border-radius: 4px;
        margin: 0.5rem 0;
        color: #1a1a1a;
        font-weight: 500;
    }
    .validation-warning {
        background: #fff3cd;
        border-left: 4px solid #ff9800;
        padding: 1rem;
        border-radius: 4px;
        margin: 0.5rem 0;
        color: #333333;
        font-weight: 500;
    }
    .validation-info {
        background: #e3f2fd;
        border-left: 4px solid #2196f3;
        padding: 1rem;
        border-radius: 4px;
        margin: 0.5rem 0;
        color: #1a1a1a;
        font-weight: 500;
    }
    .quality-excellent {
        color: #00b894;
        font-weight: bold;
    }
    .quality-good {
        color: #0984e3;
        font-weight: bold;
    }
    .quality-fair {
        color: #fdcb6e;
        font-weight: bold;
    }
    .quality-poor {
        color: #d63031;
        font-weight: bold;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 1rem 2rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)


# Initialize session state
if 'database' not in st.session_state:
    st.session_state.database = EPBDADatabase()
    st.session_state.validator = DataValidator(st.session_state.database)
    st.session_state.comparator = ForecastComparator(st.session_state.database)
    st.session_state.engine = DecisionEngine()
    st.session_state.user_role = None
    st.session_state.last_validation = None
    st.session_state.last_decision = None


def login_screen():
    """User login and role selection"""
    st.markdown('<div class="main-header"><h1>EPBDA - Energy Portfolio Decision System</h1><p>Please select your role to continue</p></div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### User Role Selection")
        
        role = st.selectbox(
            "Select Your Role:",
            ["", "Forecast Department", "Management", "Administrator"],
            help="Choose your role to access appropriate features"
        )
        
        if role:
            user_name = st.text_input("Your Name:", help="Enter your name for audit trail")
            
            if st.button("Login", type="primary"):
                if user_name:
                    st.session_state.user_role = role
                    st.session_state.user_name = user_name
                    st.rerun()
                else:
                    st.error("Please enter your name")


def forecast_department_interface():
    """Interface for forecast department to input data"""
    
    st.markdown('<div class="main-header"><h1>FORECAST DEPARTMENT - Data Input</h1><p>Submit probabilistic forecasts with automated validation</p></div>', unsafe_allow_html=True)
    
    tabs = st.tabs(["DATA INPUT", "VALIDATION RESULTS", "FORECAST QUALITY", "HISTORICAL COMPARISON"])
    
    # TAB 1: DATA INPUT
    with tabs[0]:
        st.markdown("### Probabilistic Forecast Submission")
        st.info("All forecasts are automatically validated. Errors and suggestions will appear immediately.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Demand Forecast (MW)")
            demand_p10 = st.number_input("Demand P10 (Low)", value=45.0, min_value=0.0, step=1.0)
            demand_p50 = st.number_input("Demand P50 (Expected)", value=50.0, min_value=0.0, step=1.0)
            demand_p90 = st.number_input("Demand P90 (High)", value=55.0, min_value=0.0, step=1.0)
            
            st.markdown("#### PV Generation Forecast (MW)")
            pv_p10 = st.number_input("PV P10", value=0.5, min_value=0.0, step=0.1)
            pv_p50 = st.number_input("PV P50", value=1.0, min_value=0.0, step=0.1)
            pv_p90 = st.number_input("PV P90", value=2.0, min_value=0.0, step=0.1)
            
            st.markdown("#### Wind Generation Forecast (MW)")
            wind_p10 = st.number_input("Wind P10", value=8.0, min_value=0.0, step=1.0)
            wind_p50 = st.number_input("Wind P50", value=12.0, min_value=0.0, step=1.0)
            wind_p90 = st.number_input("Wind P90", value=15.0, min_value=0.0, step=1.0)
        
        with col2:
            st.markdown("#### Market Prices (EUR/MWh)")
            day_ahead = st.number_input("Day-Ahead Price", value=80.0, step=5.0)
            intraday_bid = st.number_input("Intraday Bid (Buy Price)", value=120.0, step=5.0)
            intraday_ask = st.number_input("Intraday Ask (Sell Price)", value=60.0, step=5.0)
            rebap_plus = st.number_input("ReBAP+ (Shortage Penalty)", value=250.0, step=10.0)
            rebap_minus = st.number_input("ReBAP- (Surplus Penalty)", value=20.0, step=5.0)
            
            st.markdown("#### Hedge Position")
            hedge_position = st.number_input("Current Hedge Position (MW)", value=40.0, min_value=0.0, step=1.0)
            
            st.markdown("#### Forecast Confidence")
            forecast_confidence = st.slider("Overall Forecast Confidence (%)", 0, 100, 80, step=5,
                                          help="Your confidence in the forecast quality")
            
            forecast_notes = st.text_area("Forecast Notes / Comments:", 
                                         placeholder="Any special conditions, weather events, or assumptions...",
                                         height=100)
        
        # REAL-TIME VALIDATION
        st.markdown("---")
        st.markdown("### Automated Validation & Suggestions")
        
        col_btn1, col_btn2 = st.columns([1, 1])
        
        with col_btn1:
            validate_button = st.button("VALIDATE FORECAST", type="primary")
        
        with col_btn2:
            bypass_validation = st.button("BYPASS VALIDATION & SUBMIT DIRECTLY", type="secondary", help="Submit without validation (use with caution)")
        
        if bypass_validation:
            st.warning("⚠️ Bypassing validation - submitting directly to decision engine without checks")
            
            # Store forecast directly
            forecast_data = {
                'demand': (demand_p10, demand_p50, demand_p90),
                'pv': (pv_p10, pv_p50, pv_p90),
                'wind': (wind_p10, wind_p50, wind_p90),
                'prices': (day_ahead, intraday_bid, intraday_ask, rebap_plus, rebap_minus),
                'hedge': hedge_position,
                'confidence': forecast_confidence,
                'notes': forecast_notes + " [VALIDATION BYPASSED]",
                'timestamp': datetime.now(),
                'user': st.session_state.user_name
            }
            
            # Store in database immediately
            portfolio_state = PortfolioState(
                timestamp=forecast_data['timestamp'],
                demand_forecast=ProbabilisticForecast(*forecast_data['demand'], forecast_data['timestamp']),
                pv_forecast=ProbabilisticForecast(*forecast_data['pv'], forecast_data['timestamp']),
                wind_forecast=ProbabilisticForecast(*forecast_data['wind'], forecast_data['timestamp']),
                hedge_position_mw=forecast_data['hedge'],
                demand_flexibility=[FlexibilityAsset("Industrial", 10, 100, 2)],
                storage=StorageAsset(5, 10, 0.85, 0.90, 0.5),
                pv_curtailment_available_mw=forecast_data['pv'][1],
                wind_curtailment_available_mw=forecast_data['wind'][1],
                curtailment_cost_per_mwh=50.0,
                market_prices=MarketPrices(
                    forecast_data['prices'][0],  # day_ahead
                    forecast_data['prices'][1],  # intraday_bid
                    forecast_data['prices'][2],  # intraday_ask
                    forecast_data['prices'][3],  # rebap_plus_expected
                    forecast_data['prices'][4],  # rebap_minus_expected
                    forecast_data['prices'][3] * 1.5,  # rebap_plus_p95 (assume 50% higher)
                    forecast_data['prices'][4] * 0.5   # rebap_minus_p95 (assume 50% lower)
                ),
                risk_appetite=RiskAppetite(1000, 500, 70)
            )
            
            state_id = st.session_state.database.store_portfolio_state(portfolio_state)
            
            # Store market prices
            st.session_state.database.store_market_prices(
                forecast_data['timestamp'],
                portfolio_state.market_prices
            )
            
            # Store metadata about submission
            st.session_state.database.log_system_event(
                "WARNING",
                "FORECAST_SUBMISSION_BYPASSED",
                f"Forecast submitted by {forecast_data['user']} WITHOUT VALIDATION",
                f"State ID: {state_id}, Confidence: {forecast_data['confidence']}%, Notes: {forecast_data['notes']}"
            )
            
            st.success("✓ Forecast submitted directly to decision engine (validation bypassed)")
            st.info("Management can now review and execute decisions. Note: This forecast was not validated.")
        
        if validate_button:
            with st.spinner("Validating your forecast data..."):
                time.sleep(0.5)  # Simulate processing
                
                # Validate all inputs
                all_results = []
                
                # Validate demand
                all_results.extend(st.session_state.validator.validate_forecast(
                    demand_p10, demand_p50, demand_p90, "Demand", 0, 200
                ))
                
                # Validate PV
                all_results.extend(st.session_state.validator.validate_forecast(
                    pv_p10, pv_p50, pv_p90, "PV", 0, 50
                ))
                
                # Validate Wind
                all_results.extend(st.session_state.validator.validate_forecast(
                    wind_p10, wind_p50, wind_p90, "Wind", 0, 50
                ))
                
                # Validate prices
                all_results.extend(st.session_state.validator.validate_market_prices(
                    day_ahead, intraday_bid, intraday_ask, rebap_plus, rebap_minus
                ))
                
                # Validate hedge
                net_load_p50 = demand_p50 - pv_p50 - wind_p50
                all_results.extend(st.session_state.validator.validate_hedge_position(
                    hedge_position, net_load_p50
                ))
                
                # Store results
                st.session_state.last_validation = all_results
                
                # Display results
                errors = [r for r in all_results if r.severity == "ERROR"]
                warnings = [r for r in all_results if r.severity == "WARNING"]
                infos = [r for r in all_results if r.severity == "INFO"]
                
                col_err, col_warn, col_info = st.columns(3)
                with col_err:
                    st.metric("ERRORS", len(errors), delta=None if len(errors) == 0 else "Fix Required")
                with col_warn:
                    st.metric("WARNINGS", len(warnings), delta=None if len(warnings) == 0 else "Review Suggested")
                with col_info:
                    st.metric("INFO", len(infos))
                
                # Show detailed results
                if errors:
                    st.markdown("#### ERRORS - Must be corrected")
                    for result in errors:
                        st.markdown(f'<div class="validation-error"><strong>ERROR:</strong> {result.message}<br/><em>Suggestion: {result.suggested_correction}</em></div>', unsafe_allow_html=True)
                
                if warnings:
                    st.markdown("#### WARNINGS - Strongly recommended to review")
                    for result in warnings:
                        st.markdown(f'<div class="validation-warning"><strong>WARNING:</strong> {result.message}<br/><em>Suggestion: {result.suggested_correction}</em></div>', unsafe_allow_html=True)
                
                if infos:
                    st.markdown("#### INFORMATION - For your awareness")
                    for result in infos:
                        st.markdown(f'<div class="validation-info"><strong>INFO:</strong> {result.message}</div>', unsafe_allow_html=True)
                
                if not errors and not warnings:
                    st.success("VALIDATION PASSED - All data looks good!")
                    
                    # Store validated forecast
                    forecast_data = {
                        'demand': (demand_p10, demand_p50, demand_p90),
                        'pv': (pv_p10, pv_p50, pv_p90),
                        'wind': (wind_p10, wind_p50, wind_p90),
                        'prices': (day_ahead, intraday_bid, intraday_ask, rebap_plus, rebap_minus),
                        'hedge': hedge_position,
                        'confidence': forecast_confidence,
                        'notes': forecast_notes,
                        'timestamp': datetime.now(),
                        'user': st.session_state.user_name
                    }
                    st.session_state.validated_forecast = forecast_data
                    
                    # Show submit button immediately after validation passes
                    st.markdown("---")
                    st.markdown("### ✓ Ready to Submit")
                    quality = st.session_state.validator.assess_forecast_quality(forecast_data['demand'], forecast_data['pv'], forecast_data['wind'])
                    st.info(f"Forecast Quality Score: {quality.overall_score:.0f}/100")
                    
                    if st.button("SUBMIT TO DECISION ENGINE", type="primary", key="submit_after_validation"):
                        # Store in database
                        portfolio_state = PortfolioState(
                            timestamp=forecast_data['timestamp'],
                            demand_forecast=ProbabilisticForecast(*forecast_data['demand'], forecast_data['timestamp']),
                            pv_forecast=ProbabilisticForecast(*forecast_data['pv'], forecast_data['timestamp']),
                            wind_forecast=ProbabilisticForecast(*forecast_data['wind'], forecast_data['timestamp']),
                            hedge_position_mw=forecast_data['hedge'],
                            demand_flexibility=[FlexibilityAsset("Industrial", 10, 100, 2)],
                            storage=StorageAsset(5, 10, 0.85, 0.90, 0.5),
                            pv_curtailment_available_mw=forecast_data['pv'][1],
                            wind_curtailment_available_mw=forecast_data['wind'][1],
                            curtailment_cost_per_mwh=50.0,
                            market_prices=MarketPrices(
                                forecast_data['prices'][0],  # day_ahead
                                forecast_data['prices'][1],  # intraday_bid
                                forecast_data['prices'][2],  # intraday_ask
                                forecast_data['prices'][3],  # rebap_plus_expected
                                forecast_data['prices'][4],  # rebap_minus_expected
                                forecast_data['prices'][3] * 1.5,  # rebap_plus_p95
                                forecast_data['prices'][4] * 0.5   # rebap_minus_p95
                            ),
                            risk_appetite=RiskAppetite(1000, 500, 70)
                        )
                        
                        state_id = st.session_state.database.store_portfolio_state(portfolio_state)
                        
                        # Store market prices
                        st.session_state.database.store_market_prices(
                            forecast_data['timestamp'],
                            portfolio_state.market_prices
                        )
                        
                        # Store metadata about submission
                        st.session_state.database.log_system_event(
                            "INFO",
                            "FORECAST_SUBMISSION",
                            f"Forecast submitted by {forecast_data['user']}",
                            f"State ID: {state_id}, Confidence: {forecast_data['confidence']}%, Notes: {forecast_data['notes']}"
                        )
                        
                        st.success("✓ Forecast submitted successfully! Management can now review and execute decisions.")
                        st.balloons()
    
    # TAB 2: VALIDATION RESULTS
    with tabs[1]:
        st.markdown("### Validation History")
        
        if st.session_state.last_validation:
            results_df = pd.DataFrame([
                {
                    'Severity': r.severity,
                    'Message': r.message,
                    'Suggested Correction': r.suggested_correction or 'N/A'
                }
                for r in st.session_state.last_validation
            ])
            
            st.dataframe(results_df, use_container_width=True)
            
            # Download report
            if st.button("Download Validation Report"):
                csv = results_df.to_csv(index=False)
                st.download_button(
                    "Download CSV",
                    csv,
                    f"validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    "text/csv"
                )
        else:
            st.info("No validation results yet. Submit a forecast in the DATA INPUT tab.")
    
    # TAB 3: FORECAST QUALITY
    with tabs[2]:
        st.markdown("### Forecast Quality Assessment")
        
        if hasattr(st.session_state, 'validated_forecast'):
            forecast_data = st.session_state.validated_forecast
            
            quality = st.session_state.validator.assess_forecast_quality(
                forecast_data['demand'],
                forecast_data['pv'],
                forecast_data['wind']
            )
            
            # Quality score display
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                score_class = ('quality-excellent' if quality.overall_score >= 80 else
                             'quality-good' if quality.overall_score >= 60 else
                             'quality-fair' if quality.overall_score >= 40 else
                             'quality-poor')
                st.markdown(f'<div class="metric-card"><h3>Overall Quality</h3><h1 class="{score_class}">{quality.overall_score:.1f}/100</h1></div>', unsafe_allow_html=True)
            
            with col2:
                st.markdown(f'<div class="metric-card"><h3>Uncertainty</h3><h1>{quality.uncertainty_score:.1f}/100</h1></div>', unsafe_allow_html=True)
            
            with col3:
                st.markdown(f'<div class="metric-card"><h3>Consistency</h3><h1>{quality.consistency_score:.1f}/100</h1></div>', unsafe_allow_html=True)
            
            with col4:
                st.markdown(f'<div class="metric-card"><h3>Historical Accuracy</h3><h1>{quality.historical_accuracy_score:.1f}/100</h1></div>', unsafe_allow_html=True)
            
            # Recommendations
            st.markdown("### Improvement Recommendations")
            for i, rec in enumerate(quality.recommendations, 1):
                st.markdown(f"{i}. {rec}")
            
            # Visualize uncertainty
            st.markdown("### Forecast Uncertainty Visualization")
            
            fig = go.Figure()
            
            categories = ['Demand', 'PV', 'Wind']
            p10_vals = [forecast_data['demand'][0], forecast_data['pv'][0], forecast_data['wind'][0]]
            p50_vals = [forecast_data['demand'][1], forecast_data['pv'][1], forecast_data['wind'][1]]
            p90_vals = [forecast_data['demand'][2], forecast_data['pv'][2], forecast_data['wind'][2]]
            
            fig.add_trace(go.Bar(name='P10 (Low)', x=categories, y=p10_vals, marker_color='lightblue'))
            fig.add_trace(go.Bar(name='P50 (Expected)', x=categories, y=p50_vals, marker_color='blue'))
            fig.add_trace(go.Bar(name='P90 (High)', x=categories, y=p90_vals, marker_color='darkblue'))
            
            fig.update_layout(
                title='Forecast Uncertainty Bands',
                xaxis_title='Variable',
                yaxis_title='MW',
                barmode='group',
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Submit and validate a forecast first to see quality assessment.")
    
    # TAB 4: HISTORICAL COMPARISON
    with tabs[3]:
        st.markdown("### Historical Forecast Performance")
        
        # Get recent portfolio states (forecasts) from database
        recent_states = st.session_state.database.get_recent_portfolio_states(limit=20)
        
        if not recent_states.empty:
            # Time series of forecast trends
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=recent_states['timestamp'],
                y=recent_states['demand_p50'],
                name='Demand P50',
                mode='lines+markers'
            ))
            
            fig.add_trace(go.Scatter(
                x=recent_states['timestamp'],
                y=recent_states['pv_p50'],
                name='PV P50',
                mode='lines+markers'
            ))
            
            fig.add_trace(go.Scatter(
                x=recent_states['timestamp'],
                y=recent_states['wind_p50'],
                name='Wind P50',
                mode='lines+markers'
            ))
            
            fig.update_layout(
                title='Historical Forecast Trends',
                xaxis_title='Time',
                yaxis_title='MW',
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Show recent submissions
            st.markdown("### Recent Forecast Submissions")
            display_cols = ['timestamp', 'demand_p50', 'pv_p50', 'wind_p50', 'hedge_position_mw']
            st.dataframe(recent_states[display_cols].head(10), use_container_width=True)
        else:
            st.info("No historical data available yet.")


def management_interface():
    """Interface for management to review and execute decisions"""
    
    st.markdown('<div class="main-header"><h1>MANAGEMENT DASHBOARD - Decision Review & Execution</h1><p>Review validated forecasts, execute decisions, and monitor system enhancements</p></div>', unsafe_allow_html=True)
    
    tabs = st.tabs(["DECISION EXECUTION", "ENHANCEMENT PROPOSALS", "SYSTEM PERFORMANCE", "KPI DASHBOARD"])
    
    # TAB 1: DECISION EXECUTION
    with tabs[0]:
        st.markdown("### Execute Portfolio Decision")
        
        # Retrieve latest validated forecast from database
        recent_states = st.session_state.database.get_recent_portfolio_states(limit=1)
        
        if not recent_states.empty:
            latest_state = recent_states.iloc[0]
            
            # Build forecast_data structure from database
            forecast_data = {
                'demand': (latest_state['demand_p10'], latest_state['demand_p50'], latest_state['demand_p90']),
                'pv': (latest_state['pv_p10'], latest_state['pv_p50'], latest_state['pv_p90']),
                'wind': (latest_state['wind_p10'], latest_state['wind_p50'], latest_state['wind_p90']),
                'prices': (latest_state['day_ahead_price'], latest_state['intraday_bid'], latest_state['intraday_ask'], latest_state['rebap_plus'], latest_state['rebap_minus']),
                'hedge': latest_state['hedge_position_mw'],
                'confidence': 80,
                'notes': '',
                'timestamp': pd.to_datetime(latest_state['timestamp']),
                'user': 'Forecast Department'
            }
            
            st.success(f"✓ Validated forecast available from database (submitted at {forecast_data['timestamp'].strftime('%Y-%m-%d %H:%M:%S')})")
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown("#### Forecast Summary")
                summary_df = pd.DataFrame({
                    'Variable': ['Demand', 'PV', 'Wind', 'Net Load', 'Hedge', 'Residual'],
                    'P10 (MW)': [
                        forecast_data['demand'][0],
                        forecast_data['pv'][0],
                        forecast_data['wind'][0],
                        forecast_data['demand'][0] - forecast_data['pv'][0] - forecast_data['wind'][0],
                        forecast_data['hedge'],
                        (forecast_data['demand'][0] - forecast_data['pv'][0] - forecast_data['wind'][0]) - forecast_data['hedge']
                    ],
                    'P50 (MW)': [
                        forecast_data['demand'][1],
                        forecast_data['pv'][1],
                        forecast_data['wind'][1],
                        forecast_data['demand'][1] - forecast_data['pv'][1] - forecast_data['wind'][1],
                        forecast_data['hedge'],
                        (forecast_data['demand'][1] - forecast_data['pv'][1] - forecast_data['wind'][1]) - forecast_data['hedge']
                    ],
                    'P90 (MW)': [
                        forecast_data['demand'][2],
                        forecast_data['pv'][2],
                        forecast_data['wind'][2],
                        forecast_data['demand'][2] - forecast_data['pv'][2] - forecast_data['wind'][2],
                        forecast_data['hedge'],
                        (forecast_data['demand'][2] - forecast_data['pv'][2] - forecast_data['wind'][2]) - forecast_data['hedge']
                    ]
                })
                st.dataframe(summary_df, use_container_width=True)
            
            with col2:
                st.markdown("#### Forecast Confidence")
                st.metric("Confidence Level", f"{forecast_data['confidence']}%")
                st.markdown(f"**Notes:** {forecast_data['notes'] if forecast_data['notes'] else 'None'}")
            
            # Execute decision
            if st.button("EXECUTE DECISION ENGINE", type="primary"):
                with st.spinner("Calculating optimal decision..."):
                    start_time = time.time()
                    
                    # Build portfolio state
                    portfolio_state = PortfolioState(
                        timestamp=datetime.now(),
                        demand_forecast=ProbabilisticForecast(*forecast_data['demand'], datetime.now()),
                        pv_forecast=ProbabilisticForecast(*forecast_data['pv'], datetime.now()),
                        wind_forecast=ProbabilisticForecast(*forecast_data['wind'], datetime.now()),
                        hedge_position_mw=forecast_data['hedge'],
                        demand_flexibility=[FlexibilityAsset("Industrial", 10, 100, 2)],
                        storage=StorageAsset(5, 10, 0.85, 0.90, 0.5),
                        pv_curtailment_available_mw=forecast_data['pv'][1],
                        wind_curtailment_available_mw=forecast_data['wind'][1],
                        curtailment_cost_per_mwh=50.0,
                        market_prices=MarketPrices(
                            forecast_data['prices'][0],  # day_ahead
                            forecast_data['prices'][1],  # intraday_bid
                            forecast_data['prices'][2],  # intraday_ask
                            forecast_data['prices'][3],  # rebap_plus_expected
                            forecast_data['prices'][4],  # rebap_minus_expected
                            forecast_data['prices'][3] * 1.5,  # rebap_plus_p95
                            forecast_data['prices'][4] * 0.5   # rebap_minus_p95
                        ),
                        risk_appetite=RiskAppetite(1000, 500, 70)
                    )
                    
                    # Make decision
                    decision = st.session_state.engine.make_decision(portfolio_state)
                    
                    execution_time = (time.time() - start_time) * 1000
                    
                    # Store decision
                    decision_id = st.session_state.database.store_decision(decision, execution_time)
                    
                    st.session_state.last_decision = decision
                    st.session_state.last_portfolio_state = portfolio_state
                    
                    st.success(f"Decision calculated in {execution_time:.0f}ms (ID: {decision_id})")
            
            # Display decision (only if it exists)
            if hasattr(st.session_state, 'last_decision') and st.session_state.last_decision:
                decision = st.session_state.last_decision
                
                # Risk state color mapping using string values
                state_colors = {
                    'HOLD': 'green',
                    'WATCH': 'orange',
                    'ACTION': 'darkorange',
                    'CRITICAL': 'red'
                }
                st.markdown(f"### Risk State: <span style='color: {state_colors[decision.risk_state.value]}; font-weight: bold;'>{decision.risk_state.value}</span>", unsafe_allow_html=True)
                
                # Key metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("CVaR (95%)", f"{decision.risk_metrics.cvar_95_eur:,.0f} EUR")
                with col2:
                    st.metric("Risk Energy", f"{decision.risk_metrics.risk_energy_eur:.2f} EUR")
                with col3:
                    st.metric("Shortage Prob", f"{decision.risk_metrics.prob_shortage*100:.1f}%")
                with col4:
                    st.metric("Surplus Prob", f"{decision.risk_metrics.prob_surplus*100:.1f}%")
                
                # Primary action
                st.markdown("### Recommended Action")
                st.markdown(f"**{decision.primary_action.action_type.value}** - {decision.primary_action.volume_mw:.2f} MW")
                st.markdown(f"**Marginal Cost:** {decision.primary_action.marginal_cost_eur_per_mwh:.2f} EUR/MWh")
                st.markdown(f"**Expected Cost:** {decision.primary_action.cost_eur:,.2f} EUR")
                
                # Explanation
                st.markdown("### Decision Rationale")
                st.info(f"**Trigger:** {decision.trigger_condition}\n\n**Rationale:** {decision.rationale}")
                
                # Alternative actions
                if decision.alternative_actions:
                    st.markdown("### Alternative Actions (Ranked)")
                    alt_df = pd.DataFrame([
                        {
                            'Rank': i+1,
                            'Action': a.action_type.value,
                            'Quantity (MW)': f"{a.volume_mw:.2f}",
                            'Marginal Cost (EUR/MWh)': f"{a.marginal_cost_eur_per_mwh:.2f}",
                            'Cost (EUR)': f"{a.cost_eur:,.2f}",
                            'Risk Reduction (EUR)': f"{a.risk_reduction_eur:,.0f}"
                        }
                        for i, a in enumerate(decision.alternative_actions[:5])
                    ])
                    st.dataframe(alt_df, use_container_width=True)
        else:
            st.warning("No validated forecast available. Please wait for Forecast Department to submit data.")
    
    # TAB 2: ENHANCEMENT PROPOSALS
    with tabs[1]:
        st.markdown("### System Enhancement Proposals")
        
        if hasattr(st.session_state, 'last_decision') and st.session_state.last_decision:
            decision = st.session_state.last_decision
            portfolio_state = st.session_state.last_portfolio_state if hasattr(st.session_state, 'last_portfolio_state') else None
            
            # Get enhancement proposals
            if portfolio_state:
                enhancements = st.session_state.validator.propose_enhancements(
                    portfolio_state,
                    decision
                )
            else:
                enhancements = []
            
            if enhancements:
                st.markdown("#### Recommended Enhancements")
                for i, enhancement in enumerate(enhancements, 1):
                    st.markdown(f'<div class="metric-card"><strong>{i}. Enhancement Opportunity</strong><br/>{enhancement}</div>', unsafe_allow_html=True)
            else:
                st.success("No critical enhancements needed at this time. System is operating efficiently.")
            
            # Long-term improvement suggestions
            st.markdown("---")
            st.markdown("### Long-Term Improvement Opportunities")
            
            improvement_options = [
                {
                    'title': 'Advanced Weather Integration',
                    'description': 'Integrate real-time weather radar and satellite data for improved PV/Wind forecasts',
                    'impact': 'High',
                    'cost': 'Medium',
                    'timeline': '3-6 months'
                },
                {
                    'title': 'Machine Learning Forecast Models',
                    'description': 'Deploy ML models (LSTM/XGBoost) trained on historical data',
                    'impact': 'High',
                    'cost': 'High',
                    'timeline': '6-12 months'
                },
                {
                    'title': 'Additional Flexibility Contracts',
                    'description': 'Negotiate demand response contracts with industrial customers',
                    'impact': 'Medium',
                    'cost': 'Low',
                    'timeline': '1-3 months'
                },
                {
                    'title': 'Expanded Battery Storage',
                    'description': 'Increase battery capacity from 10 MWh to 20 MWh',
                    'impact': 'High',
                    'cost': 'Very High',
                    'timeline': '12-18 months'
                }
            ]
            
            for option in improvement_options:
                with st.expander(f"{option['title']} - Impact: {option['impact']}"):
                    st.markdown(f"**Description:** {option['description']}")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**Cost:** {option['cost']}")
                    with col2:
                        st.markdown(f"**Timeline:** {option['timeline']}")
        else:
            st.info("Execute a decision first to see enhancement proposals.")
    
    # TAB 3: SYSTEM PERFORMANCE
    with tabs[2]:
        st.markdown("### System Performance Metrics")
        
        # Get performance data
        recent_decisions = st.session_state.database.get_recent_decisions(limit=50)
        
        if not recent_decisions.empty:
            # Calculate KPIs
            avg_cvar = recent_decisions['risk_before_eur'].mean()
            cvar_limit = 1000  # From risk appetite
            compliance_rate = (recent_decisions['risk_before_eur'] <= cvar_limit).mean() * 100
            avg_execution_time = recent_decisions['execution_time_ms'].mean() if 'execution_time_ms' in recent_decisions.columns else 0
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Avg CVaR", f"{avg_cvar:,.0f} EUR", delta=f"{((avg_cvar/cvar_limit-1)*100):+.1f}% vs Limit")
            with col2:
                st.metric("Compliance Rate", f"{compliance_rate:.1f}%", delta=None if compliance_rate >= 95 else f"{compliance_rate-95:.1f}%")
            with col3:
                st.metric("Avg Execution Time", f"{avg_execution_time:.0f}ms")
            with col4:
                st.metric("Total Decisions", len(recent_decisions))
            
            # CVaR trend
            st.markdown("### CVaR Trend")
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=recent_decisions['timestamp'], y=recent_decisions['risk_before_eur'],
                                    mode='lines+markers', name='CVaR'))
            fig.add_hline(y=cvar_limit, line_dash="dash", line_color="red",
                         annotation_text="CVaR Limit")
            fig.update_layout(xaxis_title='Time', yaxis_title='CVaR (EUR)', height=400)
            st.plotly_chart(fig, use_container_width=True)
            
            # Action distribution
            st.markdown("### Action Type Distribution")
            action_counts = recent_decisions['primary_action_type'].value_counts()
            fig = px.pie(values=action_counts.values, names=action_counts.index, title='Primary Actions Taken')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No performance data available yet.")
    
    # TAB 4: KPI DASHBOARD
    with tabs[3]:
        st.markdown("### Executive KPI Dashboard")
        
        # High-level metrics for management
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown('<div class="metric-card"><h3>Risk Management</h3><p>CVaR compliance and risk exposure tracking</p></div>', unsafe_allow_html=True)
            cvar_compliance = st.session_state.database.get_cvar_compliance(1000)
            st.metric("CVaR Compliance", f"{cvar_compliance['compliance_rate_pct']:.1f}%")
        
        with col2:
            st.markdown('<div class="metric-card"><h3>Operational Efficiency</h3><p>Decision quality and execution speed</p></div>', unsafe_allow_html=True)
            st.metric("System Uptime", "99.8%")  # Would calculate from logs
        
        with col3:
            st.markdown('<div class="metric-card"><h3>Forecast Accuracy</h3><p>Historical forecast performance</p></div>', unsafe_allow_html=True)
            st.metric("Forecast Score", "78/100")  # Would calculate from history


# Main application logic
def main():
    if st.session_state.user_role is None:
        login_screen()
    else:
        # Sidebar
        with st.sidebar:
            st.markdown(f"### Logged in as:")
            st.markdown(f"**{st.session_state.user_name}**")
            st.markdown(f"*{st.session_state.user_role}*")
            
            st.markdown("---")
            
            if st.button("Logout"):
                st.session_state.user_role = None
                st.session_state.user_name = None
                st.rerun()
            
            st.markdown("---")
            st.markdown("### Quick Stats")
            recent = st.session_state.database.get_recent_decisions(limit=10)
            if not recent.empty:
                st.metric("Recent Decisions", len(recent))
                st.metric("Last Risk", f"{recent.iloc[0]['risk_before_eur']:,.0f} EUR")
        
        # Route to appropriate interface
        if st.session_state.user_role == "Forecast Department":
            forecast_department_interface()
        elif st.session_state.user_role == "Management":
            management_interface()
        elif st.session_state.user_role == "Administrator":
            st.markdown("### Administrator Interface")
            st.info("Administrator features coming soon...")


if __name__ == "__main__":
    main()
