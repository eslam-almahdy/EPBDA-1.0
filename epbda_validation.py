"""
EPBDA Data Validation & Intelligence Module
Provides automated data quality checks, anomaly detection, and enhancement suggestions
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from epbda_core import *


@dataclass
class ValidationResult:
    """Result of data validation check"""
    is_valid: bool
    severity: str  # INFO, WARNING, ERROR, CRITICAL
    message: str
    suggested_correction: Optional[str] = None
    corrected_value: Optional[float] = None


@dataclass
class ForecastQualityScore:
    """Forecast quality assessment"""
    overall_score: float  # 0-100
    uncertainty_score: float
    consistency_score: float
    historical_accuracy_score: float
    recommendations: List[str]


class DataValidator:
    """Validates input data and proposes corrections"""
    
    def __init__(self, database=None):
        self.database = database
        self.validation_rules = self._initialize_rules()
    
    def _initialize_rules(self) -> Dict:
        """Initialize validation rules"""
        return {
            'demand_range': (0, 200),  # MW
            'pv_range': (0, 50),  # MW
            'wind_range': (0, 50),  # MW
            'price_range': (-100, 2000),  # EUR/MWh
            'hedge_range': (0, 300),  # MW
            'max_uncertainty_ratio': 0.5,  # P90-P10 / P50 should be < 50%
            'min_confidence': 50.0  # Minimum acceptable confidence %
        }
    
    def validate_forecast(self, p10: float, p50: float, p90: float, 
                         name: str, min_val: float, max_val: float) -> List[ValidationResult]:
        """Validate probabilistic forecast"""
        results = []
        
        # Check 1: P10 <= P50 <= P90
        if not (p10 <= p50 <= p90):
            results.append(ValidationResult(
                is_valid=False,
                severity="ERROR",
                message=f"{name}: Percentiles must satisfy P10 <= P50 <= P90",
                suggested_correction=f"Correct order: P10={min(p10,p50,p90):.2f}, P50={sorted([p10,p50,p90])[1]:.2f}, P90={max(p10,p50,p90):.2f}",
                corrected_value=None
            ))
        
        # Check 2: Values within valid range
        for val, label in [(p10, 'P10'), (p50, 'P50'), (p90, 'P90')]:
            if val < min_val or val > max_val:
                results.append(ValidationResult(
                    is_valid=False,
                    severity="ERROR",
                    message=f"{name} {label}: {val:.2f} MW outside valid range [{min_val}, {max_val}]",
                    suggested_correction=f"Clip to valid range",
                    corrected_value=np.clip(val, min_val, max_val)
                ))
        
        # Check 3: Excessive uncertainty
        if p50 > 0:
            uncertainty_ratio = (p90 - p10) / p50
            if uncertainty_ratio > self.validation_rules['max_uncertainty_ratio']:
                results.append(ValidationResult(
                    is_valid=False,
                    severity="WARNING",
                    message=f"{name}: High uncertainty ({uncertainty_ratio*100:.1f}%). Review forecast model.",
                    suggested_correction="Consider narrowing confidence intervals or improving forecast quality"
                ))
        
        # Check 4: Zero or negative P50
        if p50 <= 0:
            results.append(ValidationResult(
                is_valid=False,
                severity="WARNING",
                message=f"{name}: P50 is {p50:.2f}. Verify if intentional.",
                suggested_correction="For generation forecasts, ensure positive values. For low-load periods, verify expected value."
            ))
        
        # Check 5: Suspiciously flat distribution (P10 ≈ P50 ≈ P90)
        if abs(p90 - p10) < 0.01 * p50:
            results.append(ValidationResult(
                is_valid=True,
                severity="INFO",
                message=f"{name}: Very narrow distribution detected. Is this certainty realistic?",
                suggested_correction="If highly certain, OK. Otherwise, consider adding realistic uncertainty bands."
            ))
        
        return results
    
    def validate_market_prices(self, day_ahead: float, intraday_bid: float, 
                               intraday_ask: float, rebap_plus: float, 
                               rebap_minus: float) -> List[ValidationResult]:
        """Validate market price inputs"""
        results = []
        
        # Check 1: Bid-Ask spread
        if intraday_bid < intraday_ask:
            results.append(ValidationResult(
                is_valid=False,
                severity="ERROR",
                message=f"Intraday bid ({intraday_bid}) < ask ({intraday_ask}). Buy price should be >= sell price.",
                suggested_correction=f"Swap values: Bid={intraday_ask}, Ask={intraday_bid}",
                corrected_value=None
            ))
        
        # Check 2: ReBAP+ should be higher than intraday (penalty)
        if rebap_plus <= intraday_bid:
            results.append(ValidationResult(
                is_valid=False,
                severity="WARNING",
                message=f"ReBAP+ ({rebap_plus}) should be higher than intraday bid ({intraday_bid}) as penalty",
                suggested_correction=f"Set ReBAP+ to at least {intraday_bid * 1.5:.2f} EUR/MWh",
                corrected_value=intraday_bid * 2.0
            ))
        
        # Check 3: ReBAP- should be lower than intraday (penalty for surplus)
        if rebap_minus >= intraday_ask:
            results.append(ValidationResult(
                is_valid=False,
                severity="WARNING",
                message=f"ReBAP- ({rebap_minus}) should be lower than intraday ask ({intraday_ask})",
                suggested_correction=f"Set ReBAP- to {intraday_ask * 0.3:.2f} EUR/MWh or negative",
                corrected_value=intraday_ask * 0.5
            ))
        
        # Check 4: Extreme prices
        if day_ahead < 0 or day_ahead > 500:
            results.append(ValidationResult(
                is_valid=False,
                severity="WARNING",
                message=f"Day-ahead price {day_ahead:.2f} EUR/MWh is unusual. Verify.",
                suggested_correction="Check if this is a special market condition or data error"
            ))
        
        # Check 5: Negative day-ahead (should be rare)
        if day_ahead < 0:
            results.append(ValidationResult(
                is_valid=True,
                severity="INFO",
                message=f"Negative day-ahead price ({day_ahead:.2f}). Rare but possible in high renewable periods.",
                suggested_correction="Verify this is intentional for negative price scenario"
            ))
        
        return results
    
    def validate_hedge_position(self, hedge_mw: float, expected_net_load: float) -> List[ValidationResult]:
        """Validate hedge position against expected net load"""
        results = []
        
        # Check 1: Hedge within reasonable range
        min_hedge, max_hedge = self.validation_rules['hedge_range']
        if hedge_mw < min_hedge or hedge_mw > max_hedge:
            results.append(ValidationResult(
                is_valid=False,
                severity="ERROR",
                message=f"Hedge position {hedge_mw:.2f} MW outside typical range [{min_hedge}, {max_hedge}]",
                suggested_correction=f"Verify hedge position. Typical range: {min_hedge}-{max_hedge} MW",
                corrected_value=np.clip(hedge_mw, min_hedge, max_hedge)
            ))
        
        # Check 2: Large hedge-load mismatch
        if expected_net_load > 0:
            hedge_ratio = hedge_mw / expected_net_load
            if hedge_ratio < 0.5:
                results.append(ValidationResult(
                    is_valid=True,
                    severity="WARNING",
                    message=f"Hedge only covers {hedge_ratio*100:.1f}% of expected net load. High exposure.",
                    suggested_correction=f"Consider increasing hedge to at least {expected_net_load * 0.7:.2f} MW"
                ))
            elif hedge_ratio > 1.5:
                results.append(ValidationResult(
                    is_valid=True,
                    severity="WARNING",
                    message=f"Hedge is {hedge_ratio*100:.1f}% of expected net load. May be over-hedged.",
                    suggested_correction=f"Consider reducing hedge closer to {expected_net_load:.2f} MW"
                ))
        
        return results
    
    def assess_forecast_quality(self, demand: Tuple[float, float, float],
                               pv: Tuple[float, float, float],
                               wind: Tuple[float, float, float]) -> ForecastQualityScore:
        """Assess overall forecast quality"""
        
        scores = []
        recommendations = []
        
        # 1. Uncertainty assessment
        def calc_uncertainty(p10, p50, p90):
            if p50 == 0:
                return 100  # Perfect score if zero (no uncertainty possible)
            return max(0, 100 - ((p90 - p10) / p50 * 100))
        
        demand_uncertainty = calc_uncertainty(*demand)
        pv_uncertainty = calc_uncertainty(*pv)
        wind_uncertainty = calc_uncertainty(*wind)
        
        uncertainty_score = (demand_uncertainty + pv_uncertainty + wind_uncertainty) / 3
        
        if uncertainty_score < 60:
            recommendations.append("HIGH UNCERTAINTY: Forecasts have wide confidence intervals. Consider improving forecast models or adding weather data.")
        
        # 2. Consistency assessment
        consistency_checks = []
        
        # Check if distributions are properly ordered
        for name, (p10, p50, p90) in [('Demand', demand), ('PV', pv), ('Wind', wind)]:
            if p10 <= p50 <= p90:
                consistency_checks.append(100)
            else:
                consistency_checks.append(0)
                recommendations.append(f"{name} forecast percentiles are not properly ordered")
        
        consistency_score = np.mean(consistency_checks)
        
        # 3. Historical accuracy (if database available)
        historical_accuracy = 75.0  # Default score
        if self.database:
            # Could implement actual historical comparison here
            pass
        
        # Overall score
        overall_score = (uncertainty_score * 0.4 + consistency_score * 0.4 + historical_accuracy * 0.2)
        
        # General recommendations based on score
        if overall_score >= 80:
            recommendations.insert(0, "EXCELLENT: Forecast quality is high. Proceed with confidence.")
        elif overall_score >= 60:
            recommendations.insert(0, "GOOD: Forecast quality is acceptable. Minor improvements possible.")
        elif overall_score >= 40:
            recommendations.insert(0, "FAIR: Forecast quality needs improvement. Review methodology.")
        else:
            recommendations.insert(0, "POOR: Forecast quality is low. Significant improvements required.")
        
        return ForecastQualityScore(
            overall_score=overall_score,
            uncertainty_score=uncertainty_score,
            consistency_score=consistency_score,
            historical_accuracy_score=historical_accuracy,
            recommendations=recommendations
        )
    
    def detect_anomalies(self, current_values: Dict, historical_df: Optional[pd.DataFrame] = None) -> List[ValidationResult]:
        """Detect anomalies compared to historical patterns"""
        results = []
        
        if historical_df is None or len(historical_df) < 10:
            return results  # Need historical data
        
        # Check demand anomaly
        if 'demand_p50' in current_values and 'demand_p50' in historical_df.columns:
            hist_mean = historical_df['demand_p50'].mean()
            hist_std = historical_df['demand_p50'].std()
            current = current_values['demand_p50']
            
            z_score = abs((current - hist_mean) / hist_std) if hist_std > 0 else 0
            
            if z_score > 3:
                results.append(ValidationResult(
                    is_valid=True,
                    severity="WARNING",
                    message=f"Demand forecast {current:.2f} MW is {z_score:.1f} std deviations from historical mean ({hist_mean:.2f} MW)",
                    suggested_correction=f"Verify if this unusual demand is expected. Historical range: {hist_mean - 2*hist_std:.2f} - {hist_mean + 2*hist_std:.2f} MW"
                ))
        
        return results
    
    def propose_enhancements(self, portfolio_state: PortfolioState, 
                           decision: Optional[Decision] = None) -> List[str]:
        """Propose enhancements to improve decision quality"""
        enhancements = []
        
        # Check if more flexibility assets could help
        total_flex = sum(asset.max_mw for asset in portfolio_state.demand_flexibility)
        if total_flex < 10:
            enhancements.append(
                "FLEXIBILITY: Current flexibility capacity is low ({:.1f} MW). "
                "Consider adding more demand response resources to reduce reliance on expensive intraday markets.".format(total_flex)
            )
        
        # Check storage utilization
        if portfolio_state.storage:
            if portfolio_state.storage.current_soc < 0.2:
                enhancements.append(
                    "STORAGE: Battery is nearly empty ({:.0f}% SOC). "
                    "Consider charging during low-price periods to have reserves for shortage events.".format(
                        portfolio_state.storage.current_soc * 100
                    )
                )
            elif portfolio_state.storage.current_soc > 0.9:
                enhancements.append(
                    "STORAGE: Battery is nearly full ({:.0f}% SOC). "
                    "Limited capacity to absorb surplus. Consider discharging or selling if prices are favorable.".format(
                        portfolio_state.storage.current_soc * 100
                    )
                )
        
        # Check hedge effectiveness
        net_load = portfolio_state.demand_forecast.p50 - portfolio_state.pv_forecast.p50 - portfolio_state.wind_forecast.p50
        hedge_coverage = portfolio_state.hedge_position_mw / net_load if net_load > 0 else 0
        
        if hedge_coverage < 0.7:
            enhancements.append(
                "HEDGE: Current hedge covers only {:.0f}% of expected net load. "
                "Consider increasing hedge position to reduce exposure to volatile intraday prices.".format(
                    hedge_coverage * 100
                )
            )
        elif hedge_coverage > 1.3:
            enhancements.append(
                "HEDGE: Current hedge is {:.0f}% of expected net load (over-hedged). "
                "Consider reducing hedge to avoid unnecessary costs and increase flexibility.".format(
                    hedge_coverage * 100
                )
            )
        
        # Check forecast quality
        demand_uncertainty = (portfolio_state.demand_forecast.p90 - portfolio_state.demand_forecast.p10) / portfolio_state.demand_forecast.p50
        if demand_uncertainty > 0.3:
            enhancements.append(
                "FORECAST: Demand forecast has high uncertainty ({:.0f}%). "
                "Consider improving forecast models with more granular weather data or machine learning techniques.".format(
                    demand_uncertainty * 100
                )
            )
        
        # Check risk appetite alignment
        if decision and decision.risk_state in [RiskState.ACTION, RiskState.CRITICAL]:
            if decision.risk_metrics.cvar_95_eur > portfolio_state.risk_appetite.cvar_limit_eur:
                enhancements.append(
                    "RISK: CVaR ({:.0f} EUR) exceeds limit ({:.0f} EUR). "
                    "Options: 1) Increase hedge, 2) Add flexibility, 3) Adjust risk appetite if business justifies higher risk.".format(
                        decision.risk_metrics.cvar_95_eur,
                        portfolio_state.risk_appetite.cvar_limit_eur
                    )
                )
        
        return enhancements


class ForecastComparator:
    """Compares forecasts across time and sources"""
    
    def __init__(self, database):
        self.database = database
    
    def compare_with_previous(self, current: ProbabilisticForecast, 
                             forecast_type: str) -> Dict:
        """Compare current forecast with previous submission"""
        # Query previous forecast from database
        # This would query the last forecast of the same type
        
        comparison = {
            'p50_change_mw': 0,
            'p50_change_pct': 0,
            'uncertainty_change': 0,
            'is_significant': False,
            'explanation': "No previous forecast for comparison"
        }
        
        # Placeholder - would implement actual database query
        
        return comparison
    
    def benchmark_against_actual(self, forecast: ProbabilisticForecast, 
                                actual_value: float) -> Dict:
        """Compare forecast against actual realization"""
        
        error = actual_value - forecast.p50
        error_pct = (error / forecast.p50 * 100) if forecast.p50 != 0 else 0
        
        # Check if actual fell within confidence interval
        within_interval = forecast.p10 <= actual_value <= forecast.p90
        
        accuracy_score = 100 - min(100, abs(error_pct))
        
        return {
            'actual_value': actual_value,
            'forecast_p50': forecast.p50,
            'error_mw': error,
            'error_pct': error_pct,
            'within_p10_p90': within_interval,
            'accuracy_score': accuracy_score,
            'grade': 'EXCELLENT' if accuracy_score > 95 else 
                    'GOOD' if accuracy_score > 85 else
                    'FAIR' if accuracy_score > 70 else 'POOR'
        }


if __name__ == "__main__":
    print("EPBDA Data Validation & Intelligence Module")
    print("=" * 60)
    
    validator = DataValidator()
    
    # Test forecast validation
    print("\n1. Testing Forecast Validation:")
    results = validator.validate_forecast(55, 50, 45, "Demand", 0, 200)  # Wrong order
    for result in results:
        print(f"   [{result.severity}] {result.message}")
        if result.suggested_correction:
            print(f"   Suggestion: {result.suggested_correction}")
    
    # Test quality assessment
    print("\n2. Testing Forecast Quality Assessment:")
    quality = validator.assess_forecast_quality(
        (45, 50, 55),  # Demand
        (0.5, 1.0, 2.0),  # PV
        (8, 12, 15)  # Wind
    )
    print(f"   Overall Score: {quality.overall_score:.1f}/100")
    print(f"   Uncertainty Score: {quality.uncertainty_score:.1f}/100")
    print(f"   Consistency Score: {quality.consistency_score:.1f}/100")
    for rec in quality.recommendations:
        print(f"   - {rec}")
    
    print("\n" + "=" * 60)
    print("Validation module ready for integration!")
