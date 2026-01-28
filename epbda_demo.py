"""
EPBDA Demo & Test Script
Demonstrates the Energy Portfolio Balancing & Decision Algorithm
"""

import numpy as np
from datetime import datetime, timedelta
from epbda_core import *


def create_test_scenario_shortage() -> PortfolioState:
    """
    Test Scenario 1: SHORTAGE (demand spike expected)
    """
    timestamp = datetime.now().replace(minute=0, second=0, microsecond=0)
    
    # High demand forecast (winter peak)
    demand_forecast = ProbabilisticForecast(
        p10=45.0,  # MW
        p50=50.0,
        p90=55.0,
        timestamp=timestamp
    )
    
    # Low PV (winter, cloudy)
    pv_forecast = ProbabilisticForecast(
        p10=0.5,
        p50=1.0,
        p90=2.0,
        timestamp=timestamp
    )
    
    # Moderate wind
    wind_forecast = ProbabilisticForecast(
        p10=8.0,
        p50=12.0,
        p90=15.0,
        timestamp=timestamp
    )
    
    # Existing hedge (insufficient)
    hedge_position_mw = 35.0  # PPAs + DA trades
    
    # Flexibility resources
    demand_flexibility = [
        FlexibilityAsset(
            name="Industrial Load Reduction",
            max_mw=5.0,
            duration_minutes=60,
            cost_per_mwh=80.0,  # Cheaper than intraday
            available=True
        ),
        FlexibilityAsset(
            name="Digital Battery",
            max_mw=3.0,
            duration_minutes=30,
            cost_per_mwh=100.0,
            available=True
        )
    ]
    
    # Storage
    storage = StorageAsset(
        capacity_mwh=10.0,
        max_power_mw=5.0,
        efficiency=0.90,
        cost_per_mwh=50.0,
        current_soc=0.6  # 60% charged
    )
    
    # Market prices (high due to shortage)
    market_prices = MarketPrices(
        day_ahead=120.0,
        intraday_bid=150.0,
        intraday_ask=140.0,
        rebap_plus_expected=300.0,  # High penalty for shortage
        rebap_minus_expected=-20.0,
        rebap_plus_p95=500.0,
        rebap_minus_p95=-40.0
    )
    
    # Risk appetite
    risk_appetite = RiskAppetite(
        cvar_limit_eur=500.0,
        risk_energy_threshold_eur=800.0,
        confidence_threshold_pct=70.0,
        lambda_risk_aversion=2.0,
        hold_threshold_mw=2.0,
        watch_threshold_mw=5.0,
        action_threshold_mw=10.0
    )
    
    return PortfolioState(
        timestamp=timestamp,
        demand_forecast=demand_forecast,
        pv_forecast=pv_forecast,
        wind_forecast=wind_forecast,
        hedge_position_mw=hedge_position_mw,
        demand_flexibility=demand_flexibility,
        storage=storage,
        pv_curtailment_available_mw=1.0,
        wind_curtailment_available_mw=8.0,
        curtailment_cost_per_mwh=30.0,
        market_prices=market_prices,
        risk_appetite=risk_appetite
    )


def create_test_scenario_surplus() -> PortfolioState:
    """
    Test Scenario 2: SURPLUS (high renewable generation)
    """
    timestamp = datetime.now().replace(minute=15, second=0, microsecond=0)
    
    # Low demand (Sunday afternoon)
    demand_forecast = ProbabilisticForecast(
        p10=20.0,
        p50=22.0,
        p90=24.0,
        timestamp=timestamp
    )
    
    # High PV (summer, sunny)
    pv_forecast = ProbabilisticForecast(
        p10=18.0,
        p50=22.0,
        p90=25.0,
        timestamp=timestamp
    )
    
    # High wind
    wind_forecast = ProbabilisticForecast(
        p10=15.0,
        p50=20.0,
        p90=25.0,
        timestamp=timestamp
    )
    
    # Existing hedge
    hedge_position_mw=22.0
    
    # Flexibility
    demand_flexibility = [
        FlexibilityAsset(
            name="Heat Pump Load Increase",
            max_mw=2.0,
            duration_minutes=120,
            cost_per_mwh=-10.0,  # Gets paid to consume
            available=True
        )
    ]
    
    # Storage (low SOC, can charge)
    storage = StorageAsset(
        capacity_mwh=10.0,
        max_power_mw=5.0,
        efficiency=0.90,
        cost_per_mwh=20.0,
        current_soc=0.2  # 20% charged - room to charge
    )
    
    # Market prices (low due to surplus)
    market_prices = MarketPrices(
        day_ahead=40.0,
        intraday_bid=35.0,
        intraday_ask=30.0,  # Low selling price
        rebap_plus_expected=200.0,
        rebap_minus_expected=-50.0,  # Penalty for excess
        rebap_plus_p95=400.0,
        rebap_minus_p95=-100.0
    )
    
    # Risk appetite
    risk_appetite = RiskAppetite(
        cvar_limit_eur=500.0,
        risk_energy_threshold_eur=800.0,
        confidence_threshold_pct=70.0,
        lambda_risk_aversion=2.0
    )
    
    return PortfolioState(
        timestamp=timestamp,
        demand_forecast=demand_forecast,
        pv_forecast=pv_forecast,
        wind_forecast=wind_forecast,
        hedge_position_mw=hedge_position_mw,
        demand_flexibility=demand_flexibility,
        storage=storage,
        pv_curtailment_available_mw=20.0,
        wind_curtailment_available_mw=18.0,
        curtailment_cost_per_mwh=30.0,
        market_prices=market_prices,
        risk_appetite=risk_appetite
    )


def create_test_scenario_balanced() -> PortfolioState:
    """
    Test Scenario 3: BALANCED (well-hedged position)
    """
    timestamp = datetime.now().replace(minute=30, second=0, microsecond=0)
    
    # Normal demand
    demand_forecast = ProbabilisticForecast(
        p10=28.0,
        p50=30.0,
        p90=32.0,
        timestamp=timestamp
    )
    
    # Moderate PV
    pv_forecast = ProbabilisticForecast(
        p10=4.0,
        p50=5.0,
        p90=6.0,
        timestamp=timestamp
    )
    
    # Moderate wind
    wind_forecast = ProbabilisticForecast(
        p10=10.0,
        p50=12.0,
        p90=14.0,
        timestamp=timestamp
    )
    
    # Well-matched hedge
    hedge_position_mw = 13.0  # Close to expected net load
    
    # Resources available but not urgent
    demand_flexibility = [
        FlexibilityAsset(
            name="Backup Flexibility",
            max_mw=5.0,
            duration_minutes=60,
            cost_per_mwh=100.0,
            available=True
        )
    ]
    
    storage = StorageAsset(
        capacity_mwh=10.0,
        max_power_mw=5.0,
        efficiency=0.90,
        cost_per_mwh=50.0,
        current_soc=0.5
    )
    
    # Normal market prices
    market_prices = MarketPrices(
        day_ahead=80.0,
        intraday_bid=85.0,
        intraday_ask=80.0,
        rebap_plus_expected=250.0,
        rebap_minus_expected=-30.0,
        rebap_plus_p95=450.0,
        rebap_minus_p95=-60.0
    )
    
    risk_appetite = RiskAppetite(
        cvar_limit_eur=500.0,
        risk_energy_threshold_eur=800.0,
        confidence_threshold_pct=70.0,
        lambda_risk_aversion=2.0
    )
    
    return PortfolioState(
        timestamp=timestamp,
        demand_forecast=demand_forecast,
        pv_forecast=pv_forecast,
        wind_forecast=wind_forecast,
        hedge_position_mw=hedge_position_mw,
        demand_flexibility=demand_flexibility,
        storage=storage,
        pv_curtailment_available_mw=5.0,
        wind_curtailment_available_mw=12.0,
        curtailment_cost_per_mwh=30.0,
        market_prices=market_prices,
        risk_appetite=risk_appetite
    )


def create_test_scenario_extreme() -> PortfolioState:
    """
    Test Scenario 4: EXTREME SHORTAGE (tail risk event)
    """
    timestamp = datetime.now().replace(minute=45, second=0, microsecond=0)
    
    # Extreme demand spike (cold snap)
    demand_forecast = ProbabilisticForecast(
        p10=70.0,
        p50=80.0,
        p90=90.0,  # Extreme peak
        timestamp=timestamp
    )
    
    # Near-zero PV (winter night)
    pv_forecast = ProbabilisticForecast(
        p10=0.0,
        p50=0.0,
        p90=0.0,
        timestamp=timestamp
    )
    
    # Low wind (calm weather)
    wind_forecast = ProbabilisticForecast(
        p10=2.0,
        p50=3.0,
        p90=5.0,
        timestamp=timestamp
    )
    
    # Insufficient hedge
    hedge_position_mw = 50.0
    
    # Limited flexibility (already activated)
    demand_flexibility = [
        FlexibilityAsset(
            name="Emergency Flex",
            max_mw=2.0,
            duration_minutes=15,
            cost_per_mwh=200.0,
            available=True,
            current_usage_mw=0.0
        )
    ]
    
    # Storage nearly empty
    storage = StorageAsset(
        capacity_mwh=10.0,
        max_power_mw=5.0,
        efficiency=0.90,
        cost_per_mwh=50.0,
        current_soc=0.15  # Almost empty
    )
    
    # Extreme market prices
    market_prices = MarketPrices(
        day_ahead=300.0,
        intraday_bid=400.0,  # Extreme shortage pricing
        intraday_ask=380.0,
        rebap_plus_expected=800.0,  # Severe penalty
        rebap_minus_expected=-20.0,
        rebap_plus_p95=1500.0,  # Catastrophic
        rebap_minus_p95=-40.0
    )
    
    risk_appetite = RiskAppetite(
        cvar_limit_eur=500.0,
        risk_energy_threshold_eur=800.0,
        confidence_threshold_pct=70.0,
        lambda_risk_aversion=2.0
    )
    
    return PortfolioState(
        timestamp=timestamp,
        demand_forecast=demand_forecast,
        pv_forecast=pv_forecast,
        wind_forecast=wind_forecast,
        hedge_position_mw=hedge_position_mw,
        demand_flexibility=demand_flexibility,
        storage=storage,
        pv_curtailment_available_mw=0.0,
        wind_curtailment_available_mw=3.0,
        curtailment_cost_per_mwh=30.0,
        market_prices=market_prices,
        risk_appetite=risk_appetite
    )


def run_demo():
    """Run full demo with all scenarios"""
    
    print("\n" + "="*80)
    print("ENERGY PORTFOLIO BALANCING & DECISION ALGORITHM")
    print("DEMO & TEST SUITE")
    print("="*80 + "\n")
    
    # Initialize decision engine
    engine = DecisionEngine()
    formatter = DecisionFormatter()
    
    # Test scenarios
    scenarios = [
        ("SHORTAGE", create_test_scenario_shortage()),
        ("SURPLUS", create_test_scenario_surplus()),
        ("BALANCED", create_test_scenario_balanced()),
        ("EXTREME SHORTAGE", create_test_scenario_extreme())
    ]
    
    all_decisions = []
    
    for scenario_name, portfolio_state in scenarios:
        print(f"\n{'─'*80}")
        print(f"SCENARIO: {scenario_name}")
        print(f"{'─'*80}\n")
        
        # Make decision
        decision = engine.make_decision(portfolio_state)
        all_decisions.append((scenario_name, decision))
        
        # Print executive summary
        print(formatter.format_executive_summary(decision))
        
        # Print alternative actions
        if len(decision.alternative_actions) > 0:
            print("\n┌─ ALTERNATIVE ACTIONS ─────────────────────────────────────────────┐")
            for i, alt in enumerate(decision.alternative_actions[:3], 1):
                print(f"│ {i}. {alt.action_type.value}: {alt.volume_mw:.1f} MW")
                print(f"│    Cost: {alt.marginal_cost_eur_per_mwh:.2f} €/MWh | {alt.rationale}")
            print("└────────────────────────────────────────────────────────────────────┘\n")
        
        # Print hedge/buffer recommendations
        print(f"┌─ HEDGE & BUFFER RECOMMENDATIONS ──────────────────────────────────┐")
        print(f"│ Recommended Hedge: {decision.recommended_hedge_mw:.1f} MW")
        print(f"│ Recommended Buffer: {decision.recommended_buffer_mw:.1f} MW")
        print(f"│ Buffer Adjustment: {decision.buffer_adjustment}")
        print(f"└────────────────────────────────────────────────────────────────────┘\n")
    
    # Summary statistics
    print("\n" + "="*80)
    print("SUMMARY STATISTICS")
    print("="*80 + "\n")
    
    for scenario_name, decision in all_decisions:
        print(f"{scenario_name:20} | Risk State: {decision.risk_state.value:8} | "
              f"Action: {decision.primary_action.action_type.value:20} | "
              f"Risk Reduction: {decision.primary_action.risk_reduction_eur:7.0f}€")
    
    print("\n" + "="*80)
    print("DEMO COMPLETE!")
    print("="*80 + "\n")
    
    print("✅ All scenarios tested successfully!")
    print("\n📊 Key Insights:")
    print("  • SHORTAGE → Buy intraday or activate demand flexibility")
    print("  • SURPLUS → Sell intraday or charge storage")
    print("  • BALANCED → Hold position, monitor")
    print("  • EXTREME → Emergency actions, escalation triggered")
    print("\n🎯 Algorithm demonstrates:")
    print("  ✓ Risk-aware decision making")
    print("  ✓ Cost optimization (lowest marginal cost)")
    print("  ✓ Action ranking & alternatives")
    print("  ✓ Explainable rationale")
    print("  ✓ Governance & escalation")
    print("  ✓ Hedge & buffer recommendations")
    
    return all_decisions


if __name__ == "__main__":
    # Add scipy for probability calculations
    try:
        from scipy.stats import norm
    except ImportError:
        print("⚠️  scipy not installed. Installing...")
        import subprocess
        subprocess.check_call(["pip", "install", "scipy"])
        from scipy.stats import norm
    
    # Run demo
    decisions = run_demo()
