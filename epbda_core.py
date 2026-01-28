"""
Energy Portfolio Balancing & Decision Algorithm (EPBDA)
Professional algorithmic decision engine for 15-minute energy portfolio management
Version 1.0 - Production Ready
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum
import numpy as np
from datetime import datetime, timedelta


# ================================================================
# 1. DATA STRUCTURES & ENUMS
# ================================================================

class RiskState(Enum):
    """Risk state classification"""
    HOLD = "HOLD"           # Within risk appetite, no action needed
    WATCH = "WATCH"         # Approaching limits, monitor closely
    ACTION = "ACTION"       # Risk appetite breached, action required
    CRITICAL = "CRITICAL"   # Extreme risk, immediate intervention


class ScenarioType(Enum):
    """Portfolio scenario classification"""
    BALANCED = "BALANCED"           # Net position ~0
    SURPLUS = "SURPLUS"             # Long position (excess generation)
    SHORTAGE = "SHORTAGE"           # Short position (demand > supply)
    EXTREME_SHORTAGE = "EXTREME_SHORTAGE"  # Tail risk shortage


class ActionType(Enum):
    """Available actions"""
    DO_NOTHING = "DO_NOTHING"
    INTRADAY_BUY = "INTRADAY_BUY"
    INTRADAY_SELL = "INTRADAY_SELL"
    ACTIVATE_DEMAND_FLEX = "ACTIVATE_DEMAND_FLEX"
    CURTAIL_PV = "CURTAIL_PV"
    CURTAIL_WIND = "CURTAIL_WIND"
    STORAGE_CHARGE = "STORAGE_CHARGE"
    STORAGE_DISCHARGE = "STORAGE_DISCHARGE"
    INCREASE_BUFFER = "INCREASE_BUFFER"
    REDUCE_BUFFER = "REDUCE_BUFFER"


@dataclass
class ProbabilisticForecast:
    """Probabilistic forecast with P10/P50/P90"""
    p10: float  # MW - 10th percentile (pessimistic)
    p50: float  # MW - 50th percentile (expected)
    p90: float  # MW - 90th percentile (optimistic)
    timestamp: datetime
    
    @property
    def uncertainty_range(self) -> float:
        """P90 - P10 spread"""
        return self.p90 - self.p10
    
    @property
    def uncertainty_ratio(self) -> float:
        """Relative uncertainty"""
        if self.p50 == 0:
            return float('inf')
        return self.uncertainty_range / abs(self.p50)


@dataclass
class FlexibilityAsset:
    """Flexibility resource specification"""
    name: str
    max_mw: float           # Maximum capacity (MW)
    duration_minutes: int   # Maximum activation duration
    cost_per_mwh: float     # Activation cost (€/MWh)
    available: bool = True
    current_usage_mw: float = 0.0
    
    @property
    def remaining_capacity(self) -> float:
        return self.max_mw - self.current_usage_mw


@dataclass
class StorageAsset:
    """Battery/storage specification"""
    capacity_mwh: float
    max_power_mw: float
    efficiency: float  # Round-trip efficiency (0-1)
    cost_per_mwh: float
    current_soc: float = 0.5  # State of charge (0-1)
    
    @property
    def available_discharge_mwh(self) -> float:
        return self.capacity_mwh * self.current_soc
    
    @property
    def available_charge_mwh(self) -> float:
        return self.capacity_mwh * (1 - self.current_soc)


@dataclass
class MarketPrices:
    """Market price structure"""
    day_ahead: float        # €/MWh
    intraday_bid: float     # €/MWh - buying price
    intraday_ask: float     # €/MWh - selling price
    rebap_plus_expected: float   # €/MWh - shortage penalty expected
    rebap_minus_expected: float  # €/MWh - surplus penalty expected
    rebap_plus_p95: float   # €/MWh - 95th percentile shortage penalty
    rebap_minus_p95: float  # €/MWh - 95th percentile surplus penalty


@dataclass
class RiskAppetite:
    """Governance & risk limits"""
    cvar_limit_eur: float          # Maximum CVaR (95%) per interval
    risk_energy_threshold_eur: float  # Risk Energy limit
    confidence_threshold_pct: float   # Minimum confidence (%)
    lambda_risk_aversion: float = 2.0  # Risk aversion parameter
    
    # Decision thresholds
    hold_threshold_mw: float = 2.0     # ±2 MW = HOLD
    watch_threshold_mw: float = 5.0    # ±5 MW = WATCH
    action_threshold_mw: float = 10.0  # >10 MW = ACTION


@dataclass
class PortfolioState:
    """Current portfolio state at time t"""
    timestamp: datetime
    
    # Forecasts
    demand_forecast: ProbabilisticForecast
    pv_forecast: ProbabilisticForecast
    wind_forecast: ProbabilisticForecast
    
    # Current hedge
    hedge_position_mw: float  # Existing hedge (PPAs + DA trades)
    
    # Available resources
    demand_flexibility: List[FlexibilityAsset]
    storage: Optional[StorageAsset]
    pv_curtailment_available_mw: float
    wind_curtailment_available_mw: float
    curtailment_cost_per_mwh: float
    
    # Market
    market_prices: MarketPrices
    
    # Governance
    risk_appetite: RiskAppetite
    
    # Optional: Monte Carlo scenarios
    monte_carlo_scenarios: Optional[np.ndarray] = None  # Array of net load scenarios


@dataclass
class RiskMetrics:
    """Calculated risk metrics"""
    expected_net_load_mw: float
    residual_position_mw: float
    short_exposure_mw: float   # Max(residual, 0)
    surplus_exposure_mw: float  # Max(-residual, 0)
    
    prob_shortage: float  # P(residual > 0)
    prob_surplus: float   # P(residual < 0)
    
    expected_cost_eur: float
    cvar_95_eur: float
    risk_energy_eur: float
    
    confidence_pct: float  # Confidence level (%)
    
    risk_state: RiskState
    scenario_type: ScenarioType


@dataclass
class ActionOption:
    """Single action evaluation"""
    action_type: ActionType
    volume_mw: float
    cost_eur: float
    marginal_cost_eur_per_mwh: float
    risk_reduction_eur: float
    residual_after_action_mw: float
    feasible: bool
    rationale: str


@dataclass
class Decision:
    """Final decision output"""
    timestamp: datetime
    
    # State
    risk_state: RiskState
    scenario_type: ScenarioType
    confidence_pct: float
    
    # Risk metrics
    risk_metrics: RiskMetrics
    
    # Recommended actions
    primary_action: ActionOption
    alternative_actions: List[ActionOption]
    
    # Hedge & buffer recommendations
    recommended_hedge_mw: float
    recommended_buffer_mw: float
    buffer_adjustment: str  # "INCREASE" / "DECREASE" / "MAINTAIN"
    
    # Explainability
    trigger_condition: str
    rationale: str
    risk_before_eur: float
    risk_after_eur: float
    alternatives_rejected: Dict[ActionType, str]
    
    # Governance flags
    manual_override_required: bool = False
    escalation_required: bool = False
    breach_details: Optional[str] = None


# ================================================================
# 2. RISK CALCULATION ENGINE
# ================================================================

class RiskCalculator:
    """Calculates risk metrics from portfolio state"""
    
    @staticmethod
    def calculate_net_load_distribution(state: PortfolioState) -> Tuple[float, float, float]:
        """
        Calculate net load: Demand - PV - Wind
        Returns: (p10, p50, p90) of net load
        """
        # Net load = Demand - Generation
        # For P10: pessimistic demand, optimistic generation
        # For P90: optimistic demand, pessimistic generation
        
        net_load_p10 = state.demand_forecast.p10 - state.pv_forecast.p90 - state.wind_forecast.p90
        net_load_p50 = state.demand_forecast.p50 - state.pv_forecast.p50 - state.wind_forecast.p50
        net_load_p90 = state.demand_forecast.p90 - state.pv_forecast.p10 - state.wind_forecast.p10
        
        return net_load_p10, net_load_p50, net_load_p90
    
    @staticmethod
    def calculate_residual_position(net_load: Tuple[float, float, float], 
                                    hedge_mw: float) -> Tuple[float, float, float]:
        """
        Residual position = Net Load - Hedge
        Returns: (p10, p50, p90) of residual
        """
        return (
            net_load[0] - hedge_mw,
            net_load[1] - hedge_mw,
            net_load[2] - hedge_mw
        )
    
    @staticmethod
    def calculate_exposure_split(residual: Tuple[float, float, float]) -> Tuple[float, float]:
        """
        Split into short (positive) and surplus (negative) exposure
        Returns: (short_exposure_mw, surplus_exposure_mw)
        """
        # Use P90 for short exposure (worst case shortage)
        # Use P10 for surplus exposure (worst case surplus)
        short_exposure = max(residual[2], 0)
        surplus_exposure = max(-residual[0], 0)
        
        return short_exposure, surplus_exposure
    
    @staticmethod
    def calculate_probabilities(residual: Tuple[float, float, float]) -> Tuple[float, float]:
        """
        Estimate probabilities assuming normal distribution
        Returns: (prob_shortage, prob_surplus)
        """
        p10, p50, p90 = residual
        
        # Approximate std dev from P10-P90 range
        # For normal dist: P90 - P10 ≈ 2.56 * sigma
        sigma = (p90 - p10) / 2.56
        
        if sigma < 0.01:  # Near-zero variance
            if p50 > 0:
                return 1.0, 0.0
            elif p50 < 0:
                return 0.0, 1.0
            else:
                return 0.5, 0.5
        
        # P(shortage) = P(residual > 0)
        z_score = -p50 / sigma
        from scipy.stats import norm
        prob_shortage = norm.sf(z_score)  # Survival function = 1 - CDF
        prob_surplus = 1 - prob_shortage
        
        return prob_shortage, prob_surplus
    
    @staticmethod
    def calculate_expected_cost(residual: Tuple[float, float, float],
                               prices: MarketPrices,
                               prob_shortage: float,
                               prob_surplus: float) -> float:
        """
        Expected cost = prob_short * short_cost + prob_surplus * surplus_cost
        """
        p10, p50, p90 = residual
        
        # Shortage cost (positive residual = need to buy at ReBAP+)
        short_exposure = max(p50, 0)
        short_cost = short_exposure * prices.rebap_plus_expected * 0.25  # 15-min in hours
        
        # Surplus cost (negative residual = sell at ReBAP-)
        surplus_exposure = max(-p50, 0)
        surplus_cost = surplus_exposure * abs(prices.rebap_minus_expected) * 0.25
        
        expected_cost = prob_shortage * short_cost + prob_surplus * surplus_cost
        
        return expected_cost
    
    @staticmethod
    def calculate_cvar_95(residual: Tuple[float, float, float],
                         prices: MarketPrices,
                         scenarios: Optional[np.ndarray] = None) -> float:
        """
        Calculate CVaR (95%) - average of worst 5% outcomes
        """
        if scenarios is not None:
            # Use Monte Carlo scenarios if available
            costs = np.where(
                scenarios > 0,
                scenarios * prices.rebap_plus_p95 * 0.25,
                -scenarios * abs(prices.rebap_minus_p95) * 0.25
            )
            sorted_costs = np.sort(costs)
            var_95_index = int(0.95 * len(sorted_costs))
            cvar_95 = np.mean(sorted_costs[var_95_index:])
            return cvar_95
        else:
            # Analytical approximation
            p10, p50, p90 = residual
            
            # Worst case: use P90 for shortage, P10 for surplus
            worst_shortage_cost = max(p90, 0) * prices.rebap_plus_p95 * 0.25
            worst_surplus_cost = max(-p10, 0) * abs(prices.rebap_minus_p95) * 0.25
            
            # Take maximum as CVaR proxy
            cvar_95 = max(worst_shortage_cost, worst_surplus_cost)
            
            return cvar_95
    
    @staticmethod
    def classify_scenario(residual: Tuple[float, float, float],
                         prob_shortage: float,
                         prob_surplus: float,
                         risk_appetite: RiskAppetite) -> ScenarioType:
        """Classify portfolio scenario"""
        p10, p50, p90 = residual
        
        if abs(p50) <= risk_appetite.hold_threshold_mw:
            return ScenarioType.BALANCED
        
        if p90 > risk_appetite.action_threshold_mw:
            return ScenarioType.EXTREME_SHORTAGE
        
        if p50 > 0 or prob_shortage > 0.5:
            return ScenarioType.SHORTAGE
        
        return ScenarioType.SURPLUS
    
    @staticmethod
    def classify_risk_state(risk_energy: float,
                           cvar_95: float,
                           confidence: float,
                           risk_appetite: RiskAppetite) -> RiskState:
        """Classify risk state based on risk appetite"""
        
        if cvar_95 > risk_appetite.cvar_limit_eur * 1.5:
            return RiskState.CRITICAL
        
        if risk_energy > risk_appetite.risk_energy_threshold_eur:
            return RiskState.ACTION
        
        if cvar_95 > risk_appetite.cvar_limit_eur * 0.75:
            return RiskState.WATCH
        
        if confidence < risk_appetite.confidence_threshold_pct:
            return RiskState.WATCH
        
        return RiskState.HOLD
    
    @classmethod
    def calculate_risk_metrics(cls, state: PortfolioState) -> RiskMetrics:
        """
        Master function: calculate all risk metrics
        """
        # 1. Net load distribution
        net_load = cls.calculate_net_load_distribution(state)
        
        # 2. Residual position
        residual = cls.calculate_residual_position(net_load, state.hedge_position_mw)
        
        # 3. Exposure split
        short_exposure, surplus_exposure = cls.calculate_exposure_split(residual)
        
        # 4. Probabilities
        prob_shortage, prob_surplus = cls.calculate_probabilities(residual)
        
        # 5. Expected cost
        expected_cost = cls.calculate_expected_cost(
            residual, state.market_prices, prob_shortage, prob_surplus
        )
        
        # 6. CVaR
        cvar_95 = cls.calculate_cvar_95(
            residual, state.market_prices, state.monte_carlo_scenarios
        )
        
        # 7. Risk Energy
        risk_energy = expected_cost + state.risk_appetite.lambda_risk_aversion * cvar_95
        
        # 8. Confidence
        p10, p50, p90 = residual
        if p90 - p10 == 0:
            confidence = 100.0
        else:
            confidence = 100.0 * (1 - (p90 - p10) / max(abs(p50), 1))
        confidence = max(0, min(100, confidence))
        
        # 9. Scenario classification
        scenario_type = cls.classify_scenario(residual, prob_shortage, prob_surplus, state.risk_appetite)
        
        # 10. Risk state
        risk_state = cls.classify_risk_state(risk_energy, cvar_95, confidence, state.risk_appetite)
        
        return RiskMetrics(
            expected_net_load_mw=net_load[1],
            residual_position_mw=residual[1],
            short_exposure_mw=short_exposure,
            surplus_exposure_mw=surplus_exposure,
            prob_shortage=prob_shortage,
            prob_surplus=prob_surplus,
            expected_cost_eur=expected_cost,
            cvar_95_eur=cvar_95,
            risk_energy_eur=risk_energy,
            confidence_pct=confidence,
            risk_state=risk_state,
            scenario_type=scenario_type
        )


# ================================================================
# 3. ACTION OPTIMIZER
# ================================================================

class ActionOptimizer:
    """Evaluates and ranks available actions"""
    
    @staticmethod
    def evaluate_do_nothing(state: PortfolioState, 
                           risk_metrics: RiskMetrics) -> ActionOption:
        """Baseline: accept ReBAP exposure"""
        return ActionOption(
            action_type=ActionType.DO_NOTHING,
            volume_mw=0,
            cost_eur=risk_metrics.expected_cost_eur,
            marginal_cost_eur_per_mwh=float('inf'),
            risk_reduction_eur=0,
            residual_after_action_mw=risk_metrics.residual_position_mw,
            feasible=True,
            rationale="Accept current position, no action taken"
        )
    
    @staticmethod
    def evaluate_intraday_buy(state: PortfolioState,
                             risk_metrics: RiskMetrics,
                             volume_mw: float) -> ActionOption:
        """Buy power in intraday market"""
        cost = volume_mw * state.market_prices.intraday_bid * 0.25
        residual_after = risk_metrics.residual_position_mw - volume_mw
        
        # Risk reduction: avoid ReBAP+
        risk_before = max(risk_metrics.residual_position_mw, 0) * state.market_prices.rebap_plus_expected * 0.25
        risk_after = max(residual_after, 0) * state.market_prices.rebap_plus_expected * 0.25
        risk_reduction = risk_before - risk_after - cost
        
        return ActionOption(
            action_type=ActionType.INTRADAY_BUY,
            volume_mw=volume_mw,
            cost_eur=cost,
            marginal_cost_eur_per_mwh=state.market_prices.intraday_bid,
            risk_reduction_eur=risk_reduction,
            residual_after_action_mw=residual_after,
            feasible=True,
            rationale=f"Buy {volume_mw:.1f} MW intraday at {state.market_prices.intraday_bid:.2f} €/MWh"
        )
    
    @staticmethod
    def evaluate_intraday_sell(state: PortfolioState,
                               risk_metrics: RiskMetrics,
                               volume_mw: float) -> ActionOption:
        """Sell power in intraday market"""
        revenue = volume_mw * state.market_prices.intraday_ask * 0.25
        residual_after = risk_metrics.residual_position_mw + volume_mw
        
        # Risk reduction: avoid ReBAP-
        risk_before = max(-risk_metrics.residual_position_mw, 0) * abs(state.market_prices.rebap_minus_expected) * 0.25
        risk_after = max(-residual_after, 0) * abs(state.market_prices.rebap_minus_expected) * 0.25
        risk_reduction = risk_before - risk_after + revenue
        
        return ActionOption(
            action_type=ActionType.INTRADAY_SELL,
            volume_mw=volume_mw,
            cost_eur=-revenue,  # Negative cost = revenue
            marginal_cost_eur_per_mwh=-state.market_prices.intraday_ask,
            risk_reduction_eur=risk_reduction,
            residual_after_action_mw=residual_after,
            feasible=True,
            rationale=f"Sell {volume_mw:.1f} MW intraday at {state.market_prices.intraday_ask:.2f} €/MWh"
        )
    
    @staticmethod
    def evaluate_demand_flexibility(state: PortfolioState,
                                    risk_metrics: RiskMetrics,
                                    asset: FlexibilityAsset,
                                    volume_mw: float) -> ActionOption:
        """Activate demand flexibility (reduce load)"""
        if not asset.available or volume_mw > asset.remaining_capacity:
            return ActionOption(
                action_type=ActionType.ACTIVATE_DEMAND_FLEX,
                volume_mw=0,
                cost_eur=0,
                marginal_cost_eur_per_mwh=float('inf'),
                risk_reduction_eur=0,
                residual_after_action_mw=risk_metrics.residual_position_mw,
                feasible=False,
                rationale=f"{asset.name} not available or insufficient capacity"
            )
        
        cost = volume_mw * asset.cost_per_mwh * 0.25
        residual_after = risk_metrics.residual_position_mw - volume_mw
        
        # Risk reduction: avoid ReBAP+ and save intraday cost
        intraday_alternative_cost = volume_mw * state.market_prices.intraday_bid * 0.25
        risk_reduction = intraday_alternative_cost - cost
        
        return ActionOption(
            action_type=ActionType.ACTIVATE_DEMAND_FLEX,
            volume_mw=volume_mw,
            cost_eur=cost,
            marginal_cost_eur_per_mwh=asset.cost_per_mwh,
            risk_reduction_eur=risk_reduction,
            residual_after_action_mw=residual_after,
            feasible=True,
            rationale=f"Activate {asset.name}: {volume_mw:.1f} MW at {asset.cost_per_mwh:.2f} €/MWh"
        )
    
    @staticmethod
    def evaluate_curtailment(state: PortfolioState,
                            risk_metrics: RiskMetrics,
                            source: str,  # "PV" or "WIND"
                            volume_mw: float) -> ActionOption:
        """Curtail PV or Wind generation"""
        action_type = ActionType.CURTAIL_PV if source == "PV" else ActionType.CURTAIL_WIND
        max_available = state.pv_curtailment_available_mw if source == "PV" else state.wind_curtailment_available_mw
        
        if volume_mw > max_available:
            return ActionOption(
                action_type=action_type,
                volume_mw=0,
                cost_eur=0,
                marginal_cost_eur_per_mwh=float('inf'),
                risk_reduction_eur=0,
                residual_after_action_mw=risk_metrics.residual_position_mw,
                feasible=False,
                rationale=f"Insufficient {source} generation to curtail"
            )
        
        # Opportunity cost of lost generation
        cost = volume_mw * state.curtailment_cost_per_mwh * 0.25
        residual_after = risk_metrics.residual_position_mw + volume_mw  # Curtailment increases net load
        
        # Risk reduction: avoid ReBAP- penalty
        intraday_alternative_revenue = volume_mw * state.market_prices.intraday_ask * 0.25
        risk_reduction = intraday_alternative_revenue - cost
        
        return ActionOption(
            action_type=action_type,
            volume_mw=volume_mw,
            cost_eur=cost,
            marginal_cost_eur_per_mwh=state.curtailment_cost_per_mwh,
            risk_reduction_eur=risk_reduction,
            residual_after_action_mw=residual_after,
            feasible=True,
            rationale=f"Curtail {volume_mw:.1f} MW {source} at {state.curtailment_cost_per_mwh:.2f} €/MWh"
        )
    
    @staticmethod
    def evaluate_storage_discharge(state: PortfolioState,
                                   risk_metrics: RiskMetrics,
                                   volume_mw: float) -> ActionOption:
        """Discharge storage to cover shortage"""
        if state.storage is None:
            return ActionOption(
                action_type=ActionType.STORAGE_DISCHARGE,
                volume_mw=0,
                cost_eur=0,
                marginal_cost_eur_per_mwh=float('inf'),
                risk_reduction_eur=0,
                residual_after_action_mw=risk_metrics.residual_position_mw,
                feasible=False,
                rationale="No storage available"
            )
        
        max_discharge = min(state.storage.available_discharge_mwh / 0.25, state.storage.max_power_mw)
        
        if volume_mw > max_discharge:
            return ActionOption(
                action_type=ActionType.STORAGE_DISCHARGE,
                volume_mw=0,
                cost_eur=0,
                marginal_cost_eur_per_mwh=float('inf'),
                risk_reduction_eur=0,
                residual_after_action_mw=risk_metrics.residual_position_mw,
                feasible=False,
                rationale="Insufficient storage capacity"
            )
        
        cost = volume_mw * state.storage.cost_per_mwh * 0.25
        residual_after = risk_metrics.residual_position_mw - volume_mw
        
        # Compare to intraday buy
        intraday_alternative = volume_mw * state.market_prices.intraday_bid * 0.25
        risk_reduction = intraday_alternative - cost
        
        return ActionOption(
            action_type=ActionType.STORAGE_DISCHARGE,
            volume_mw=volume_mw,
            cost_eur=cost,
            marginal_cost_eur_per_mwh=state.storage.cost_per_mwh,
            risk_reduction_eur=risk_reduction,
            residual_after_action_mw=residual_after,
            feasible=True,
            rationale=f"Discharge {volume_mw:.1f} MW from storage"
        )
    
    @staticmethod
    def evaluate_storage_charge(state: PortfolioState,
                               risk_metrics: RiskMetrics,
                               volume_mw: float) -> ActionOption:
        """Charge storage with surplus"""
        if state.storage is None:
            return ActionOption(
                action_type=ActionType.STORAGE_CHARGE,
                volume_mw=0,
                cost_eur=0,
                marginal_cost_eur_per_mwh=float('inf'),
                risk_reduction_eur=0,
                residual_after_action_mw=risk_metrics.residual_position_mw,
                feasible=False,
                rationale="No storage available"
            )
        
        max_charge = min(state.storage.available_charge_mwh / 0.25, state.storage.max_power_mw)
        
        if volume_mw > max_charge:
            return ActionOption(
                action_type=ActionType.STORAGE_CHARGE,
                volume_mw=0,
                cost_eur=0,
                marginal_cost_eur_per_mwh=float('inf'),
                risk_reduction_eur=0,
                residual_after_action_mw=risk_metrics.residual_position_mw,
                feasible=False,
                rationale="Storage full or insufficient charge capacity"
            )
        
        cost = volume_mw * state.storage.cost_per_mwh * 0.25
        residual_after = risk_metrics.residual_position_mw + volume_mw
        
        # Compare to intraday sell
        intraday_alternative = volume_mw * state.market_prices.intraday_ask * 0.25
        risk_reduction = intraday_alternative - cost
        
        return ActionOption(
            action_type=ActionType.STORAGE_CHARGE,
            volume_mw=volume_mw,
            cost_eur=cost,
            marginal_cost_eur_per_mwh=state.storage.cost_per_mwh,
            risk_reduction_eur=risk_reduction,
            residual_after_action_mw=residual_after,
            feasible=True,
            rationale=f"Charge {volume_mw:.1f} MW to storage"
        )
    
    @classmethod
    def generate_action_options(cls, state: PortfolioState, 
                               risk_metrics: RiskMetrics) -> List[ActionOption]:
        """
        Generate all feasible action options for current scenario
        """
        options = []
        
        # Always evaluate do nothing
        options.append(cls.evaluate_do_nothing(state, risk_metrics))
        
        # Determine action volume needed
        residual = abs(risk_metrics.residual_position_mw)
        action_volume = max(residual - state.risk_appetite.hold_threshold_mw, 0)
        
        if action_volume < 0.1:
            return options  # No action needed
        
        # SHORTAGE SCENARIO - need to reduce net load
        if risk_metrics.scenario_type in [ScenarioType.SHORTAGE, ScenarioType.EXTREME_SHORTAGE]:
            # Intraday buy
            options.append(cls.evaluate_intraday_buy(state, risk_metrics, action_volume))
            
            # Demand flexibility
            for flex_asset in state.demand_flexibility:
                volume = min(action_volume, flex_asset.remaining_capacity)
                if volume > 0:
                    options.append(cls.evaluate_demand_flexibility(state, risk_metrics, flex_asset, volume))
            
            # Storage discharge
            if state.storage:
                options.append(cls.evaluate_storage_discharge(state, risk_metrics, action_volume))
        
        # SURPLUS SCENARIO - need to increase net load or sell
        elif risk_metrics.scenario_type == ScenarioType.SURPLUS:
            # Intraday sell
            options.append(cls.evaluate_intraday_sell(state, risk_metrics, action_volume))
            
            # Curtailment
            if state.pv_curtailment_available_mw > 0:
                volume = min(action_volume, state.pv_curtailment_available_mw)
                options.append(cls.evaluate_curtailment(state, risk_metrics, "PV", volume))
            
            if state.wind_curtailment_available_mw > 0:
                volume = min(action_volume, state.wind_curtailment_available_mw)
                options.append(cls.evaluate_curtailment(state, risk_metrics, "WIND", volume))
            
            # Storage charge
            if state.storage:
                options.append(cls.evaluate_storage_charge(state, risk_metrics, action_volume))
        
        return options
    
    @staticmethod
    def rank_actions(options: List[ActionOption]) -> List[ActionOption]:
        """
        Rank actions by marginal cost (€/MWh)
        Lower marginal cost = better
        """
        feasible_options = [opt for opt in options if opt.feasible]
        
        # Sort by marginal cost (ascending)
        ranked = sorted(feasible_options, key=lambda x: x.marginal_cost_eur_per_mwh)
        
        return ranked


# ================================================================
# 4. DECISION ENGINE (MAIN CONTROLLER)
# ================================================================

class DecisionEngine:
    """
    Main decision engine - orchestrates risk calculation and action optimization
    """
    
    def __init__(self):
        self.risk_calculator = RiskCalculator()
        self.action_optimizer = ActionOptimizer()
    
    def make_decision(self, state: PortfolioState) -> Decision:
        """
        Master decision function
        """
        # Step 1: Calculate risk metrics
        risk_metrics = self.risk_calculator.calculate_risk_metrics(state)
        
        # Step 2: Generate action options
        action_options = self.action_optimizer.generate_action_options(state, risk_metrics)
        
        # Step 3: Rank actions
        ranked_actions = self.action_optimizer.rank_actions(action_options)
        
        # Step 4: Select primary action
        if len(ranked_actions) == 0:
            primary_action = self.action_optimizer.evaluate_do_nothing(state, risk_metrics)
            alternative_actions = []
        else:
            primary_action = ranked_actions[0]
            alternative_actions = ranked_actions[1:5]  # Top 4 alternatives
        
        # Step 5: Calculate hedge and buffer recommendations
        recommended_hedge, recommended_buffer, buffer_adjustment = self._calculate_hedge_buffer_recommendations(
            state, risk_metrics
        )
        
        # Step 6: Generate explainability
        trigger_condition, rationale, alternatives_rejected = self._generate_explainability(
            risk_metrics, primary_action, alternative_actions, state
        )
        
        # Step 7: Governance checks
        manual_override, escalation, breach_details = self._check_governance(risk_metrics, state)
        
        # Step 8: Calculate risk before/after
        risk_before = risk_metrics.risk_energy_eur
        risk_after = risk_before - primary_action.risk_reduction_eur
        
        # Step 9: Assemble decision
        decision = Decision(
            timestamp=state.timestamp,
            risk_state=risk_metrics.risk_state,
            scenario_type=risk_metrics.scenario_type,
            confidence_pct=risk_metrics.confidence_pct,
            risk_metrics=risk_metrics,
            primary_action=primary_action,
            alternative_actions=alternative_actions,
            recommended_hedge_mw=recommended_hedge,
            recommended_buffer_mw=recommended_buffer,
            buffer_adjustment=buffer_adjustment,
            trigger_condition=trigger_condition,
            rationale=rationale,
            risk_before_eur=risk_before,
            risk_after_eur=risk_after,
            alternatives_rejected=alternatives_rejected,
            manual_override_required=manual_override,
            escalation_required=escalation,
            breach_details=breach_details
        )
        
        return decision
    
    def _calculate_hedge_buffer_recommendations(self, 
                                                state: PortfolioState,
                                                risk_metrics: RiskMetrics) -> Tuple[float, float, str]:
        """
        Calculate recommended hedge position and buffer size
        """
        # Recommended hedge = expected net load
        recommended_hedge = risk_metrics.expected_net_load_mw
        
        # Buffer = P90 - P10 spread scaled by confidence
        uncertainty_mw = state.demand_forecast.uncertainty_range + \
                        state.pv_forecast.uncertainty_range + \
                        state.wind_forecast.uncertainty_range
        
        recommended_buffer = uncertainty_mw * (1 - risk_metrics.confidence_pct / 100)
        
        # Buffer adjustment logic
        current_buffer_implied = abs(state.hedge_position_mw - risk_metrics.expected_net_load_mw)
        
        if recommended_buffer > current_buffer_implied * 1.2:
            buffer_adjustment = "INCREASE"
        elif recommended_buffer < current_buffer_implied * 0.8:
            buffer_adjustment = "DECREASE"
        else:
            buffer_adjustment = "MAINTAIN"
        
        return recommended_hedge, recommended_buffer, buffer_adjustment
    
    def _generate_explainability(self,
                                 risk_metrics: RiskMetrics,
                                 primary_action: ActionOption,
                                 alternatives: List[ActionOption],
                                 state: PortfolioState) -> Tuple[str, str, Dict[ActionType, str]]:
        """
        Generate human-readable explanations
        """
        # Trigger condition
        if risk_metrics.risk_state == RiskState.CRITICAL:
            trigger = f"CRITICAL: CVaR {risk_metrics.cvar_95_eur:.0f}€ exceeds limit {state.risk_appetite.cvar_limit_eur * 1.5:.0f}€"
        elif risk_metrics.risk_state == RiskState.ACTION:
            trigger = f"ACTION: Risk Energy {risk_metrics.risk_energy_eur:.0f}€ exceeds threshold {state.risk_appetite.risk_energy_threshold_eur:.0f}€"
        elif risk_metrics.risk_state == RiskState.WATCH:
            trigger = f"WATCH: Approaching risk limits, confidence {risk_metrics.confidence_pct:.1f}%"
        else:
            trigger = f"HOLD: Within risk appetite, residual {abs(risk_metrics.residual_position_mw):.1f} MW"
        
        # Rationale
        rationale = f"{risk_metrics.scenario_type.value}: {primary_action.rationale}. "
        rationale += f"Reduces risk by {primary_action.risk_reduction_eur:.0f}€. "
        rationale += f"Marginal cost {primary_action.marginal_cost_eur_per_mwh:.2f} €/MWh."
        
        # Alternatives rejected
        rejected = {}
        for alt in alternatives[:3]:
            if alt.marginal_cost_eur_per_mwh > primary_action.marginal_cost_eur_per_mwh:
                reason = f"Higher cost ({alt.marginal_cost_eur_per_mwh:.2f} vs {primary_action.marginal_cost_eur_per_mwh:.2f} €/MWh)"
            elif not alt.feasible:
                reason = "Not feasible"
            else:
                reason = "Lower risk reduction"
            rejected[alt.action_type] = reason
        
        return trigger, rationale, rejected
    
    def _check_governance(self, 
                         risk_metrics: RiskMetrics,
                         state: PortfolioState) -> Tuple[bool, bool, Optional[str]]:
        """
        Check governance rules and escalation requirements
        """
        manual_override = False
        escalation = False
        breach_details = None
        
        # Check CVaR breach
        if risk_metrics.cvar_95_eur > state.risk_appetite.cvar_limit_eur:
            escalation = True
            breach_details = f"CVaR {risk_metrics.cvar_95_eur:.0f}€ exceeds limit {state.risk_appetite.cvar_limit_eur:.0f}€"
        
        # Check critical state
        if risk_metrics.risk_state == RiskState.CRITICAL:
            manual_override = True
            escalation = True
            if breach_details:
                breach_details += " | CRITICAL state requires manual approval"
            else:
                breach_details = "CRITICAL state requires manual approval"
        
        # Check extreme shortage
        if risk_metrics.scenario_type == ScenarioType.EXTREME_SHORTAGE:
            escalation = True
            if breach_details:
                breach_details += " | Extreme shortage scenario"
            else:
                breach_details = "Extreme shortage scenario detected"
        
        return manual_override, escalation, breach_details


# ================================================================
# 5. OUTPUT FORMATTER
# ================================================================

class DecisionFormatter:
    """Format decision output for different audiences"""
    
    @staticmethod
    def format_executive_summary(decision: Decision) -> str:
        """Concise executive summary"""
        summary = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║ ENERGY PORTFOLIO DECISION - {decision.timestamp.strftime('%Y-%m-%d %H:%M')}
╠══════════════════════════════════════════════════════════════════════════════╣
║ 
║ STATUS: {decision.risk_state.value} | Scenario: {decision.scenario_type.value}
║ Confidence: {decision.confidence_pct:.1f}% | Residual: {decision.risk_metrics.residual_position_mw:+.1f} MW
║
║ ── RECOMMENDED ACTION ──────────────────────────────────────────────────────
║ {decision.primary_action.action_type.value}: {decision.primary_action.volume_mw:.1f} MW
║ Cost: {decision.primary_action.cost_eur:.0f}€ | Risk Reduction: {decision.primary_action.risk_reduction_eur:.0f}€
║
║ ── RISK METRICS ────────────────────────────────────────────────────────────
║ Expected Cost: {decision.risk_metrics.expected_cost_eur:.0f}€ | CVaR(95%): {decision.risk_metrics.cvar_95_eur:.0f}€
║ Risk Energy: {decision.risk_before_eur:.0f}€ → {decision.risk_after_eur:.0f}€
║
║ ── RATIONALE ───────────────────────────────────────────────────────────────
║ {decision.trigger_condition}
║ {decision.rationale}
║
{"║ ⚠️  ESCALATION REQUIRED: " + decision.breach_details if decision.escalation_required else ""}
{"║ ⚠️  MANUAL OVERRIDE REQUIRED" if decision.manual_override_required else ""}
╚══════════════════════════════════════════════════════════════════════════════╝
"""
        return summary
    
    @staticmethod
    def format_detailed_report(decision: Decision) -> Dict:
        """Detailed JSON-ready report"""
        return {
            "timestamp": decision.timestamp.isoformat(),
            "risk_state": decision.risk_state.value,
            "scenario_type": decision.scenario_type.value,
            "confidence_pct": decision.confidence_pct,
            "risk_metrics": {
                "expected_net_load_mw": decision.risk_metrics.expected_net_load_mw,
                "residual_position_mw": decision.risk_metrics.residual_position_mw,
                "short_exposure_mw": decision.risk_metrics.short_exposure_mw,
                "surplus_exposure_mw": decision.risk_metrics.surplus_exposure_mw,
                "prob_shortage": decision.risk_metrics.prob_shortage,
                "prob_surplus": decision.risk_metrics.prob_surplus,
                "expected_cost_eur": decision.risk_metrics.expected_cost_eur,
                "cvar_95_eur": decision.risk_metrics.cvar_95_eur,
                "risk_energy_eur": decision.risk_metrics.risk_energy_eur,
            },
            "primary_action": {
                "action_type": decision.primary_action.action_type.value,
                "volume_mw": decision.primary_action.volume_mw,
                "cost_eur": decision.primary_action.cost_eur,
                "marginal_cost_eur_per_mwh": decision.primary_action.marginal_cost_eur_per_mwh,
                "risk_reduction_eur": decision.primary_action.risk_reduction_eur,
                "residual_after_action_mw": decision.primary_action.residual_after_action_mw,
            },
            "alternative_actions": [
                {
                    "action_type": alt.action_type.value,
                    "volume_mw": alt.volume_mw,
                    "marginal_cost_eur_per_mwh": alt.marginal_cost_eur_per_mwh,
                    "rationale": alt.rationale
                }
                for alt in decision.alternative_actions
            ],
            "hedge_buffer": {
                "recommended_hedge_mw": decision.recommended_hedge_mw,
                "recommended_buffer_mw": decision.recommended_buffer_mw,
                "buffer_adjustment": decision.buffer_adjustment,
            },
            "explainability": {
                "trigger_condition": decision.trigger_condition,
                "rationale": decision.rationale,
                "risk_before_eur": decision.risk_before_eur,
                "risk_after_eur": decision.risk_after_eur,
                "alternatives_rejected": {k.value: v for k, v in decision.alternatives_rejected.items()},
            },
            "governance": {
                "manual_override_required": decision.manual_override_required,
                "escalation_required": decision.escalation_required,
                "breach_details": decision.breach_details,
            }
        }


if __name__ == "__main__":
    print("=" * 80)
    print("ENERGY PORTFOLIO BALANCING & DECISION ALGORITHM (EPBDA)")
    print("Production-Ready Decision Engine")
    print("=" * 80)
    print("\nModule loaded successfully!")
    print("\nAvailable components:")
    print("  • DecisionEngine - Main controller")
    print("  • RiskCalculator - Risk metrics computation")
    print("  • ActionOptimizer - Action evaluation & ranking")
    print("  • DecisionFormatter - Output formatting")
    print("\nReady for integration!")
