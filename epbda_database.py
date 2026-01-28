"""
EPBDA Database Module
Records all calculations, decisions, and portfolio states
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional
import pandas as pd
from epbda_core import *


class EPBDADatabase:
    """Database manager for EPBDA decision engine"""
    
    def __init__(self, db_path: str = "epbda_data.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Portfolio States table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS portfolio_states (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP NOT NULL,
                demand_p10 REAL,
                demand_p50 REAL,
                demand_p90 REAL,
                pv_p10 REAL,
                pv_p50 REAL,
                pv_p90 REAL,
                wind_p10 REAL,
                wind_p50 REAL,
                wind_p90 REAL,
                hedge_position_mw REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Market Prices table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS market_prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP NOT NULL,
                day_ahead REAL,
                intraday_bid REAL,
                intraday_ask REAL,
                rebap_plus_expected REAL,
                rebap_minus_expected REAL,
                rebap_plus_p95 REAL,
                rebap_minus_p95 REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Risk Metrics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS risk_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                decision_id INTEGER,
                timestamp TIMESTAMP NOT NULL,
                expected_net_load_mw REAL,
                residual_position_mw REAL,
                short_exposure_mw REAL,
                surplus_exposure_mw REAL,
                prob_shortage REAL,
                prob_surplus REAL,
                expected_cost_eur REAL,
                cvar_95_eur REAL,
                risk_energy_eur REAL,
                confidence_pct REAL,
                risk_state TEXT,
                scenario_type TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (decision_id) REFERENCES decisions(id)
            )
        """)
        
        # Decisions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP NOT NULL,
                risk_state TEXT NOT NULL,
                scenario_type TEXT NOT NULL,
                confidence_pct REAL,
                primary_action_type TEXT,
                primary_action_volume_mw REAL,
                primary_action_cost_eur REAL,
                primary_action_marginal_cost REAL,
                primary_action_risk_reduction_eur REAL,
                recommended_hedge_mw REAL,
                recommended_buffer_mw REAL,
                buffer_adjustment TEXT,
                trigger_condition TEXT,
                rationale TEXT,
                risk_before_eur REAL,
                risk_after_eur REAL,
                manual_override_required BOOLEAN,
                escalation_required BOOLEAN,
                breach_details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Alternative Actions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alternative_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                decision_id INTEGER NOT NULL,
                action_type TEXT,
                volume_mw REAL,
                cost_eur REAL,
                marginal_cost_eur_per_mwh REAL,
                risk_reduction_eur REAL,
                rationale TEXT,
                rank INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (decision_id) REFERENCES decisions(id)
            )
        """)
        
        # Performance Tracking table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS performance_tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                decision_id INTEGER NOT NULL,
                execution_time_ms REAL,
                actions_evaluated INTEGER,
                calculation_timestamp TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (decision_id) REFERENCES decisions(id)
            )
        """)
        
        # System Logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP NOT NULL,
                log_level TEXT,
                component TEXT,
                message TEXT,
                details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    def store_portfolio_state(self, state: PortfolioState) -> int:
        """Store portfolio state and return ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO portfolio_states (
                timestamp, demand_p10, demand_p50, demand_p90,
                pv_p10, pv_p50, pv_p90,
                wind_p10, wind_p50, wind_p90,
                hedge_position_mw
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            state.timestamp,
            state.demand_forecast.p10, state.demand_forecast.p50, state.demand_forecast.p90,
            state.pv_forecast.p10, state.pv_forecast.p50, state.pv_forecast.p90,
            state.wind_forecast.p10, state.wind_forecast.p50, state.wind_forecast.p90,
            state.hedge_position_mw
        ))
        
        portfolio_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return portfolio_id
    
    def store_market_prices(self, timestamp: datetime, prices: MarketPrices) -> int:
        """Store market prices and return ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO market_prices (
                timestamp, day_ahead, intraday_bid, intraday_ask,
                rebap_plus_expected, rebap_minus_expected,
                rebap_plus_p95, rebap_minus_p95
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            timestamp,
            prices.day_ahead, prices.intraday_bid, prices.intraday_ask,
            prices.rebap_plus_expected, prices.rebap_minus_expected,
            prices.rebap_plus_p95, prices.rebap_minus_p95
        ))
        
        price_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return price_id
    
    def store_decision(self, decision: Decision, execution_time_ms: float = 0) -> int:
        """Store complete decision with all components"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Store decision
        cursor.execute("""
            INSERT INTO decisions (
                timestamp, risk_state, scenario_type, confidence_pct,
                primary_action_type, primary_action_volume_mw,
                primary_action_cost_eur, primary_action_marginal_cost,
                primary_action_risk_reduction_eur,
                recommended_hedge_mw, recommended_buffer_mw, buffer_adjustment,
                trigger_condition, rationale,
                risk_before_eur, risk_after_eur,
                manual_override_required, escalation_required, breach_details
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            decision.timestamp,
            decision.risk_state.value,
            decision.scenario_type.value,
            decision.confidence_pct,
            decision.primary_action.action_type.value,
            decision.primary_action.volume_mw,
            decision.primary_action.cost_eur,
            decision.primary_action.marginal_cost_eur_per_mwh,
            decision.primary_action.risk_reduction_eur,
            decision.recommended_hedge_mw,
            decision.recommended_buffer_mw,
            decision.buffer_adjustment,
            decision.trigger_condition,
            decision.rationale,
            decision.risk_before_eur,
            decision.risk_after_eur,
            decision.manual_override_required,
            decision.escalation_required,
            decision.breach_details
        ))
        
        decision_id = cursor.lastrowid
        
        # Store risk metrics
        cursor.execute("""
            INSERT INTO risk_metrics (
                decision_id, timestamp,
                expected_net_load_mw, residual_position_mw,
                short_exposure_mw, surplus_exposure_mw,
                prob_shortage, prob_surplus,
                expected_cost_eur, cvar_95_eur, risk_energy_eur,
                confidence_pct, risk_state, scenario_type
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            decision_id, decision.timestamp,
            decision.risk_metrics.expected_net_load_mw,
            decision.risk_metrics.residual_position_mw,
            decision.risk_metrics.short_exposure_mw,
            decision.risk_metrics.surplus_exposure_mw,
            decision.risk_metrics.prob_shortage,
            decision.risk_metrics.prob_surplus,
            decision.risk_metrics.expected_cost_eur,
            decision.risk_metrics.cvar_95_eur,
            decision.risk_metrics.risk_energy_eur,
            decision.risk_metrics.confidence_pct,
            decision.risk_metrics.risk_state.value,
            decision.risk_metrics.scenario_type.value
        ))
        
        # Store alternative actions
        for rank, alt_action in enumerate(decision.alternative_actions, start=1):
            cursor.execute("""
                INSERT INTO alternative_actions (
                    decision_id, action_type, volume_mw, cost_eur,
                    marginal_cost_eur_per_mwh, risk_reduction_eur,
                    rationale, rank
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                decision_id,
                alt_action.action_type.value,
                alt_action.volume_mw,
                alt_action.cost_eur,
                alt_action.marginal_cost_eur_per_mwh,
                alt_action.risk_reduction_eur,
                alt_action.rationale,
                rank
            ))
        
        # Store performance metrics
        cursor.execute("""
            INSERT INTO performance_tracking (
                decision_id, execution_time_ms, actions_evaluated,
                calculation_timestamp
            ) VALUES (?, ?, ?, ?)
        """, (
            decision_id,
            execution_time_ms,
            len(decision.alternative_actions) + 1,
            datetime.now()
        ))
        
        conn.commit()
        conn.close()
        
        self.log_system_event("INFO", "DecisionEngine", 
                             f"Stored decision {decision_id}", 
                             f"Risk State: {decision.risk_state.value}")
        
        return decision_id
    
    def log_system_event(self, level: str, component: str, message: str, details: str = ""):
        """Log system events"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO system_logs (timestamp, log_level, component, message, details)
            VALUES (?, ?, ?, ?, ?)
        """, (datetime.now(), level, component, message, details))
        
        conn.commit()
        conn.close()
    
    def get_recent_decisions(self, limit: int = 100) -> pd.DataFrame:
        """Get recent decisions as DataFrame"""
        conn = sqlite3.connect(self.db_path)
        
        query = """
            SELECT 
                id, timestamp, risk_state, scenario_type,
                primary_action_type, primary_action_volume_mw,
                primary_action_cost_eur, risk_before_eur, risk_after_eur,
                confidence_pct, escalation_required
            FROM decisions
            ORDER BY timestamp DESC
            LIMIT ?
        """
        
        df = pd.read_sql_query(query, conn, params=(limit,))
        conn.close()
        return df
    
    def get_risk_metrics_history(self, hours: int = 24) -> pd.DataFrame:
        """Get risk metrics history"""
        conn = sqlite3.connect(self.db_path)
        
        query = """
            SELECT 
                timestamp, expected_cost_eur, cvar_95_eur, risk_energy_eur,
                confidence_pct, risk_state, scenario_type,
                residual_position_mw, prob_shortage, prob_surplus
            FROM risk_metrics
            WHERE timestamp >= datetime('now', '-{} hours')
            ORDER BY timestamp ASC
        """.format(hours)
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    
    def get_recent_portfolio_states(self, limit: int = 10) -> pd.DataFrame:
        """Get recent portfolio states from database"""
        conn = sqlite3.connect(self.db_path)
        
        query = """
            SELECT 
                id, timestamp, 
                demand_p10, demand_p50, demand_p90,
                pv_p10, pv_p50, pv_p90,
                wind_p10, wind_p50, wind_p90,
                hedge_position_mw
            FROM portfolio_states
            ORDER BY timestamp DESC
            LIMIT ?
        """
        
        df = pd.read_sql_query(query, conn, params=(limit,))
        
        # Also get latest market prices
        price_query = """
            SELECT 
                day_ahead, intraday_bid, intraday_ask,
                rebap_plus_expected, rebap_minus_expected
            FROM market_prices
            ORDER BY timestamp DESC
            LIMIT 1
        """
        
        prices_df = pd.read_sql_query(price_query, conn)
        
        conn.close()
        
        # Add price columns to portfolio states
        if not prices_df.empty and not df.empty:
            df['day_ahead_price'] = prices_df.iloc[0]['day_ahead']
            df['intraday_bid'] = prices_df.iloc[0]['intraday_bid']
            df['intraday_ask'] = prices_df.iloc[0]['intraday_ask']
            df['rebap_plus'] = prices_df.iloc[0]['rebap_plus_expected']
            df['rebap_minus'] = prices_df.iloc[0]['rebap_minus_expected']
        
        return df
    
    def get_action_statistics(self) -> pd.DataFrame:
        """Get action type statistics"""
        conn = sqlite3.connect(self.db_path)
        
        query = """
            SELECT 
                primary_action_type as action_type,
                COUNT(*) as count,
                AVG(primary_action_volume_mw) as avg_volume_mw,
                AVG(primary_action_cost_eur) as avg_cost_eur,
                AVG(primary_action_risk_reduction_eur) as avg_risk_reduction_eur
            FROM decisions
            GROUP BY primary_action_type
            ORDER BY count DESC
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    
    def get_performance_stats(self) -> Dict:
        """Get performance statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Average execution time
        cursor.execute("""
            SELECT AVG(execution_time_ms), MAX(execution_time_ms), MIN(execution_time_ms)
            FROM performance_tracking
        """)
        avg_time, max_time, min_time = cursor.fetchone()
        
        # Total decisions
        cursor.execute("SELECT COUNT(*) FROM decisions")
        total_decisions = cursor.fetchone()[0]
        
        # Risk state distribution
        cursor.execute("""
            SELECT risk_state, COUNT(*) as count
            FROM decisions
            GROUP BY risk_state
        """)
        risk_distribution = dict(cursor.fetchall())
        
        conn.close()
        
        return {
            "avg_execution_time_ms": avg_time or 0,
            "max_execution_time_ms": max_time or 0,
            "min_execution_time_ms": min_time or 0,
            "total_decisions": total_decisions,
            "risk_state_distribution": risk_distribution
        }
    
    def get_escalation_events(self, limit: int = 50) -> pd.DataFrame:
        """Get escalation and critical events"""
        conn = sqlite3.connect(self.db_path)
        
        query = """
            SELECT 
                timestamp, risk_state, scenario_type,
                breach_details, primary_action_type,
                risk_before_eur, confidence_pct
            FROM decisions
            WHERE escalation_required = 1 OR manual_override_required = 1
            ORDER BY timestamp DESC
            LIMIT ?
        """
        
        df = pd.read_sql_query(query, conn, params=(limit,))
        conn.close()
        return df
    
    def get_cvar_compliance(self, cvar_limit: float) -> Dict:
        """Check CVaR compliance statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN cvar_95_eur <= ? THEN 1 ELSE 0 END) as compliant,
                AVG(cvar_95_eur) as avg_cvar,
                MAX(cvar_95_eur) as max_cvar
            FROM risk_metrics
        """, (cvar_limit,))
        
        total, compliant, avg_cvar, max_cvar = cursor.fetchone()
        
        conn.close()
        
        compliance_rate = (compliant / total * 100) if total > 0 else 0
        
        return {
            "total_intervals": total,
            "compliant_intervals": compliant,
            "compliance_rate_pct": compliance_rate,
            "avg_cvar_eur": avg_cvar or 0,
            "max_cvar_eur": max_cvar or 0
        }


if __name__ == "__main__":
    # Initialize database
    db = EPBDADatabase()
    print("Database initialized: epbda_data.db")
    print("Tables created:")
    print("  - portfolio_states")
    print("  - market_prices")
    print("  - risk_metrics")
    print("  - decisions")
    print("  - alternative_actions")
    print("  - performance_tracking")
    print("  - system_logs")
