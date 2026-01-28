"""
Complete EPBDA System Test
Tests all components: validation, database, core engine, and data structures
"""

import sys
from datetime import datetime, timedelta
from epbda_core import *
from epbda_database import EPBDADatabase
from epbda_validation import DataValidator, ForecastComparator

def test_data_structures():
    """Test 1: Data Structure Creation"""
    print("\n" + "="*60)
    print("TEST 1: Data Structures")
    print("="*60)
    
    try:
        # Test ProbabilisticForecast
        forecast = ProbabilisticForecast(45, 50, 55, datetime.now())
        print(f"✓ ProbabilisticForecast: P10={forecast.p10}, P50={forecast.p50}, P90={forecast.p90}")
        
        # Test MarketPrices
        prices = MarketPrices(80, 120, 60, 250, 20, 375, 10)
        print(f"✓ MarketPrices: Day-Ahead={prices.day_ahead}, Intraday Bid={prices.intraday_bid}")
        
        # Test FlexibilityAsset
        flex = FlexibilityAsset("Industrial", 10, 100, 2)
        print(f"✓ FlexibilityAsset: {flex.name}, {flex.max_mw} MW")
        
        # Test StorageAsset
        storage = StorageAsset(5, 10, 0.85, 0.90, 0.5)
        print(f"✓ StorageAsset: {storage.capacity_mwh} MWh, SOC={storage.current_soc*100}%")
        
        # Test RiskAppetite
        risk = RiskAppetite(1000, 500, 70)
        print(f"✓ RiskAppetite: CVaR Limit={risk.cvar_limit_eur} EUR")
        
        # Test PortfolioState
        portfolio = PortfolioState(
            timestamp=datetime.now(),
            demand_forecast=ProbabilisticForecast(45, 50, 55, datetime.now()),
            pv_forecast=ProbabilisticForecast(0.5, 1.0, 2.0, datetime.now()),
            wind_forecast=ProbabilisticForecast(8, 12, 15, datetime.now()),
            hedge_position_mw=40,
            demand_flexibility=[flex],
            storage=storage,
            pv_curtailment_available_mw=1.0,
            wind_curtailment_available_mw=12.0,
            curtailment_cost_per_mwh=50.0,
            market_prices=prices,
            risk_appetite=risk
        )
        print(f"✓ PortfolioState: Created successfully")
        
        return True, portfolio
    except Exception as e:
        print(f"✗ ERROR: {e}")
        return False, None


def test_validation():
    """Test 2: Validation Module"""
    print("\n" + "="*60)
    print("TEST 2: Validation Module")
    print("="*60)
    
    try:
        validator = DataValidator()
        
        # Test forecast validation
        results = validator.validate_forecast(45, 50, 55, "Demand", 0, 200)
        print(f"✓ Forecast validation: {len(results)} checks completed")
        
        # Test price validation
        price_results = validator.validate_market_prices(80, 120, 60, 250, 20)
        print(f"✓ Price validation: {len(price_results)} checks completed")
        
        # Test quality assessment
        quality = validator.assess_forecast_quality(
            (45, 50, 55),
            (0.5, 1.0, 2.0),
            (8, 12, 15)
        )
        print(f"✓ Quality assessment: Score={quality.overall_score:.1f}/100")
        
        return True
    except Exception as e:
        print(f"✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_database():
    """Test 3: Database Operations"""
    print("\n" + "="*60)
    print("TEST 3: Database Operations")
    print("="*60)
    
    try:
        db = EPBDADatabase("test_epbda.db")
        print("✓ Database initialized")
        
        # Test portfolio state storage
        portfolio = PortfolioState(
            timestamp=datetime.now(),
            demand_forecast=ProbabilisticForecast(45, 50, 55, datetime.now()),
            pv_forecast=ProbabilisticForecast(0.5, 1.0, 2.0, datetime.now()),
            wind_forecast=ProbabilisticForecast(8, 12, 15, datetime.now()),
            hedge_position_mw=40,
            demand_flexibility=[FlexibilityAsset("Industrial", 10, 100, 2)],
            storage=StorageAsset(5, 10, 0.85, 0.90, 0.5),
            pv_curtailment_available_mw=1.0,
            wind_curtailment_available_mw=12.0,
            curtailment_cost_per_mwh=50.0,
            market_prices=MarketPrices(80, 120, 60, 250, 20, 375, 10),
            risk_appetite=RiskAppetite(1000, 500, 70)
        )
        
        state_id = db.store_portfolio_state(portfolio)
        print(f"✓ Portfolio state stored: ID={state_id}")
        
        # Test market price storage
        price_id = db.store_market_prices(datetime.now(), portfolio.market_prices)
        print(f"✓ Market prices stored: ID={price_id}")
        
        # Test retrieval
        recent_states = db.get_recent_portfolio_states(limit=5)
        print(f"✓ Retrieved {len(recent_states)} portfolio states")
        
        # Test compliance check
        compliance = db.get_cvar_compliance(1000)
        print(f"✓ CVaR compliance check: {compliance['compliance_rate_pct']:.1f}%")
        
        return True
    except Exception as e:
        print(f"✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_decision_engine():
    """Test 4: Decision Engine"""
    print("\n" + "="*60)
    print("TEST 4: Decision Engine")
    print("="*60)
    
    try:
        engine = DecisionEngine()
        
        # Create portfolio state
        portfolio = PortfolioState(
            timestamp=datetime.now(),
            demand_forecast=ProbabilisticForecast(45, 50, 55, datetime.now()),
            pv_forecast=ProbabilisticForecast(0.5, 1.0, 2.0, datetime.now()),
            wind_forecast=ProbabilisticForecast(8, 12, 15, datetime.now()),
            hedge_position_mw=40,
            demand_flexibility=[FlexibilityAsset("Industrial", 10, 100, 2)],
            storage=StorageAsset(5, 10, 0.85, 0.90, 0.5),
            pv_curtailment_available_mw=1.0,
            wind_curtailment_available_mw=12.0,
            curtailment_cost_per_mwh=50.0,
            market_prices=MarketPrices(80, 120, 60, 250, 20, 375, 10),
            risk_appetite=RiskAppetite(1000, 500, 70)
        )
        
        # Make decision
        decision = engine.make_decision(portfolio)
        
        print(f"✓ Decision calculated successfully")
        print(f"  Risk State: {decision.risk_state.value}")
        print(f"  CVaR (95%): {decision.risk_metrics.cvar_95_eur:.2f} EUR")
        print(f"  Primary Action: {decision.primary_action.action_type.value}")
        print(f"  Action Volume: {decision.primary_action.volume_mw:.2f} MW")
        print(f"  Expected Cost: {decision.primary_action.cost_eur:.2f} EUR")
        
        return True, decision
    except Exception as e:
        print(f"✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False, None


def test_full_workflow():
    """Test 5: Full Workflow"""
    print("\n" + "="*60)
    print("TEST 5: Full Workflow (Forecast → Validation → Decision → Database)")
    print("="*60)
    
    try:
        # Initialize components
        validator = DataValidator()
        db = EPBDADatabase("test_epbda_workflow.db")
        engine = DecisionEngine()
        
        # Step 1: Validate forecast
        print("\nStep 1: Validate Forecast")
        validation_results = validator.validate_forecast(45, 50, 55, "Demand", 0, 200)
        validation_results += validator.validate_market_prices(80, 120, 60, 250, 20)
        
        errors = [r for r in validation_results if r.severity == "ERROR"]
        warnings = [r for r in validation_results if r.severity == "WARNING"]
        
        print(f"  Validation: {len(errors)} errors, {len(warnings)} warnings")
        
        if errors:
            print("  ✗ Validation failed with errors")
            return False
        
        # Step 2: Create portfolio state
        print("\nStep 2: Create Portfolio State")
        portfolio = PortfolioState(
            timestamp=datetime.now(),
            demand_forecast=ProbabilisticForecast(45, 50, 55, datetime.now()),
            pv_forecast=ProbabilisticForecast(0.5, 1.0, 2.0, datetime.now()),
            wind_forecast=ProbabilisticForecast(8, 12, 15, datetime.now()),
            hedge_position_mw=40,
            demand_flexibility=[FlexibilityAsset("Industrial", 10, 100, 2)],
            storage=StorageAsset(5, 10, 0.85, 0.90, 0.5),
            pv_curtailment_available_mw=1.0,
            wind_curtailment_available_mw=12.0,
            curtailment_cost_per_mwh=50.0,
            market_prices=MarketPrices(80, 120, 60, 250, 20, 375, 10),
            risk_appetite=RiskAppetite(1000, 500, 70)
        )
        print("  ✓ Portfolio state created")
        
        # Step 3: Store in database
        print("\nStep 3: Store in Database")
        state_id = db.store_portfolio_state(portfolio)
        db.store_market_prices(datetime.now(), portfolio.market_prices)
        print(f"  ✓ Stored in database (ID={state_id})")
        
        # Step 4: Make decision
        print("\nStep 4: Execute Decision Engine")
        decision = engine.make_decision(portfolio)
        print(f"  ✓ Decision: {decision.risk_state.value}")
        print(f"  ✓ Action: {decision.primary_action.action_type.value} {decision.primary_action.volume_mw:.2f} MW")
        
        # Step 5: Store decision
        print("\nStep 5: Store Decision")
        decision_id = db.store_decision(decision, 150.5)
        print(f"  ✓ Decision stored (ID={decision_id})")
        
        # Step 6: Retrieve and verify
        print("\nStep 6: Retrieve and Verify")
        recent_decisions = db.get_recent_decisions(limit=1)
        if not recent_decisions.empty:
            print(f"  ✓ Retrieved decision from database")
            print(f"  ✓ Risk State: {recent_decisions.iloc[0]['risk_state']}")
        
        print("\n✓ FULL WORKFLOW COMPLETED SUCCESSFULLY")
        return True
        
    except Exception as e:
        print(f"✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("\n" + "="*60)
    print("EPBDA SYSTEM - COMPREHENSIVE TEST SUITE")
    print("="*60)
    
    results = {}
    
    # Run all tests
    results['data_structures'], portfolio = test_data_structures()
    results['validation'] = test_validation()
    results['database'] = test_database()
    results['decision_engine'], decision = test_decision_engine()
    results['full_workflow'] = test_full_workflow()
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name.replace('_', ' ').title()}")
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    print("\n" + "="*60)
    print(f"RESULTS: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("✓ ALL TESTS PASSED - SYSTEM IS READY")
    else:
        print("✗ SOME TESTS FAILED - REVIEW ERRORS ABOVE")
    print("="*60)
    
    return passed_tests == total_tests


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
