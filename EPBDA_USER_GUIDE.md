# EPBDA Multi-User System - User Guide

**Energy Portfolio Balancing & Decision Algorithm**  
**Version 1.0 | January 2026**

---

## Table of Contents

1. [Introduction](#introduction)
2. [System Overview](#system-overview)
3. [Getting Started](#getting-started)
4. [Forecast Department Guide](#forecast-department-guide)
5. [Management Guide](#management-guide)
6. [Understanding System Outputs](#understanding-system-outputs)
7. [Data Quality Guidelines](#data-quality-guidelines)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)

---

## Introduction

### What is EPBDA?

The Energy Portfolio Balancing & Decision Algorithm (EPBDA) is an advanced decision support system designed to optimize electricity portfolio management under uncertainty. The system analyzes probabilistic forecasts, market conditions, and risk constraints to recommend optimal hedging and operational actions.

### Who Should Use This System?

**Forecast Department:**
- Energy forecasters
- Demand analysts
- Renewable energy specialists
- Market price analysts

**Management:**
- Portfolio managers
- Risk managers
- Trading desk managers
- Operations directors

### Key Benefits

- **Risk Quantification:** CVaR(95%) risk metrics with confidence intervals
- **Actionable Decisions:** Clear recommendations ranked by cost-efficiency
- **Real-Time Validation:** Immediate feedback on forecast quality
- **Audit Trail:** Complete database logging of all decisions
- **Enhancement Proposals:** Intelligent suggestions for system improvements

---

## System Overview

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    EPBDA MULTI-USER SYSTEM                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  FORECAST DEPARTMENT          →     DATABASE    →    MANAGEMENT │
│  ├── Data Input                    ├── Portfolio States    ├── Decision Execution │
│  ├── Validation                    ├── Market Prices       ├── Risk Analysis      │
│  ├── Quality Scoring               ├── Decisions           ├── Enhancement Review │
│  └── Submission                    └── System Logs         └── Performance KPIs   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Core Components

1. **Probabilistic Forecasting:** P10/P50/P90 quantiles for demand, PV, and wind
2. **Risk Calculator:** CVaR(95%), shortage/surplus probabilities
3. **Action Optimizer:** Ranks 7 action types by marginal cost (EUR/MWh)
4. **Decision Engine:** Determines risk state and optimal actions
5. **Database:** SQLite storage with 7 normalized tables

### Decision States

| State | CVaR Status | Confidence | Action Required |
|-------|------------|-----------|----------------|
| **HOLD** | Within limits | High (>80%) | Monitor only |
| **WATCH** | Approaching limits | Medium (60-80%) | Prepare actions |
| **ACTION** | Limit breached | Low (40-60%) | Execute immediately |
| **CRITICAL** | Extreme breach | Very Low (<40%) | Manual override required |

---

## Getting Started

### Accessing the System

1. **Launch the application:**
   ```
   Open: http://localhost:8503
   ```

2. **Login Screen:**
   - Enter your full name
   - Select your role: "Forecast Department" or "Management"
   - Click **LOGIN**

3. **Interface Overview:**
   - **Header:** System title and current timestamp
   - **Sidebar:** User info, quick stats, logout button
   - **Main Area:** Role-specific tabs and functions
   - **Footer:** Database status and help links

### Navigation

- **Tabs:** Click tab names to switch between functions
- **Forms:** Fill all required fields (marked with *)
- **Buttons:** Primary actions are blue, secondary are gray
- **Metrics:** Color-coded (green=good, red=warning)

---

## Forecast Department Guide

### Your Role

As a forecast department user, you are responsible for:
1. Submitting probabilistic forecasts (demand, PV, wind)
2. Providing market price estimates
3. Ensuring data quality through validation
4. Maintaining forecast confidence levels

### Step-by-Step Workflow

#### STEP 1: DATA INPUT

Navigate to the **DATA INPUT** tab.

##### 1.1 Demand Forecast

Enter three probability quantiles:
- **P10 (10th percentile):** Pessimistic case (90% chance actual > this)
- **P50 (50th percentile):** Most likely case (median forecast)
- **P90 (90th percentile):** Optimistic case (10% chance actual > this)

**Example:**
```
P10: 185.0 MW  (low demand scenario)
P50: 200.0 MW  (expected demand)
P90: 215.0 MW  (high demand scenario)
```

**Important Rules:**
- P10 ≤ P50 ≤ P90 (must be increasing)
- Reasonable spread: (P90-P10)/P50 typically 10-30%
- Use historical data and weather forecasts

##### 1.2 PV Solar Forecast

Same structure as demand:

**Example:**
```
P10: 45.0 MW   (cloudy conditions)
P50: 60.0 MW   (expected generation)
P90: 70.0 MW   (clear sky)
```

**Tips:**
- Check weather forecasts (cloud cover, irradiance)
- Consider seasonal patterns
- Account for panel degradation
- Morning/evening: lower uncertainty, Midday: higher potential

##### 1.3 Wind Forecast

**Example:**
```
P10: 80.0 MW   (low wind scenario)
P50: 100.0 MW  (expected generation)
P90: 120.0 MW  (high wind scenario)
```

**Tips:**
- Wind is typically more uncertain than solar (wider spread)
- Check wind speed forecasts from meteorological services
- Consider turbine availability
- Account for curtailment constraints

##### 1.4 Market Prices

Enter five price points (all in EUR/MWh):

1. **Day-Ahead Price:** Next day spot market clearing price
   - Example: `85.0 EUR/MWh`
   - Source: Day-ahead auction results, price forecasts

2. **Intraday Bid Price:** Price you can sell at (typically lower)
   - Example: `83.0 EUR/MWh`
   - Usually 2-5 EUR below day-ahead

3. **Intraday Ask Price:** Price you must pay to buy (typically higher)
   - Example: `87.0 EUR/MWh`
   - Usually 2-5 EUR above day-ahead

4. **ReBAP Plus (Expected):** Penalty for excess energy delivery
   - Example: `120.0 EUR/MWh`
   - Higher than market prices (penalty)

5. **ReBAP Minus (Expected):** Penalty for shortfall
   - Example: `25.0 EUR/MWh`
   - Lower than market prices (penalty)

**Price Relationships:**
```
Intraday Bid < Day-Ahead < Intraday Ask
ReBAP Minus < Intraday Bid
ReBAP Plus > Intraday Ask
```

##### 1.5 Hedge Position

- **Current Hedge Position:** Existing forward contracts (MW)
- **Positive value:** Already sold energy forward
- **Negative value:** Already bought energy forward
- **Example:** `150.0 MW` (hedged 150 MW of expected load)

##### 1.6 Metadata

- **Confidence Level:** Your subjective confidence (60-100%)
  - 90-100%: High confidence (good weather data, stable patterns)
  - 80-89%: Normal confidence
  - 70-79%: Moderate uncertainty
  - 60-69%: High uncertainty (extreme weather, data gaps)

- **Notes:** Optional comments
  - Example: "Cold front expected, increased demand likely"
  - Example: "Wind turbine #3 under maintenance"

#### STEP 2: VALIDATION

After entering data, click **VALIDATE FORECAST**.

The system performs 15+ validation checks:

##### Error Messages (Red) - Must Fix
- P10/P50/P90 ordering violations
- Price inconsistencies (bid > ask)
- Values outside physical limits (negative generation, >1000 MW)
- Missing required fields

**Action:** Review and correct the flagged fields.

##### Warning Messages (Yellow) - Review Recommended
- High uncertainty (P90-P10 spread > 30%)
- Unusual forecast values vs. historical data
- Low confidence levels (<70%)

**Action:** Double-check data sources, consider revising if error found.

##### Info Messages (Blue) - For Your Information
- Acceptable data quality
- Historical comparisons
- System suggestions

**Action:** No action required, but review for insights.

##### Quality Score

The system calculates an overall quality score (0-100):

- **90-100:** Excellent - Proceed with confidence
- **75-89:** Good - Minor improvements possible
- **60-74:** Fair - Review warnings carefully
- **<60:** Poor - Significant data quality issues, revise forecast

**Score Components:**
- Ordering compliance (P10≤P50≤P90)
- Reasonable uncertainty spread
- Price consistency
- Historical alignment
- Confidence level

#### STEP 3: SUBMISSION

Two options:

##### Option A: Regular Submission (Recommended)
1. Ensure validation passes (Quality Score ≥60)
2. Review and address warnings
3. Click **SUBMIT TO DATABASE**
4. Confirmation message appears
5. Data is now available to Management

##### Option B: Bypass Validation
- Use **BYPASS VALIDATION & SUBMIT DIRECTLY** if:
  - Urgent submission needed
  - You have manual override authority
  - You've validated data externally
- **Warning:** Bypassed submissions are logged and flagged

#### STEP 4: REVIEW HISTORY

Navigate to the **HISTORICAL COMPARISON** tab.

**Historical Forecast Trends:**
- Line chart showing Demand, PV, Wind P50 forecasts over time
- Identifies patterns and anomalies
- Helps assess forecast consistency

**Recent Submissions:**
- Table of last 20 submissions with timestamps
- Review your historical forecasts
- Check for data entry errors

---

## Management Guide

### Your Role

As a management user, you are responsible for:
1. Executing the decision engine on validated forecasts
2. Reviewing risk metrics and recommended actions
3. Approving or overriding system recommendations
4. Monitoring system performance and compliance
5. Implementing enhancement proposals

### Step-by-Step Workflow

#### STEP 1: DECISION EXECUTION

Navigate to the **DECISION EXECUTION** tab.

##### 1.1 Retrieve Latest Forecast

The system automatically loads the most recent validated forecast from the database.

**Forecast Summary Display:**
- Demand P50: Expected demand (MW)
- PV P50: Expected solar generation (MW)
- Wind P50: Expected wind generation (MW)
- Net Position: Demand - PV - Wind (MW)
- Hedge Position: Existing hedge (MW)
- Market Prices: Day-ahead, intraday, ReBAP

**Review Checklist:**
- Is this the correct time interval?
- Do values look reasonable?
- Check Forecast Department notes for special conditions

##### 1.2 Execute Decision Engine

Click **EXECUTE DECISION ENGINE**.

The system performs (in ~100-300ms):
1. Risk calculation (CVaR, shortage/surplus probabilities)
2. Scenario classification (SHORTAGE/SURPLUS/BALANCED/EXTREME)
3. Action optimization (7 action types ranked by cost)
4. Decision synthesis (primary action + alternatives)
5. Database storage (full audit trail)

**Processing Time:**
- Normal: 100-200ms
- Complex: 200-500ms
- If >1000ms, contact IT support

##### 1.3 Review Decision Results

**Risk State Display:**

The system shows the risk state with color coding:
- 🟢 **HOLD:** Within risk appetite, no action needed
- 🟠 **WATCH:** Approaching limits, monitor closely
- 🟠 **ACTION:** Risk appetite breached, action required
- 🔴 **CRITICAL:** Extreme risk, manual override needed

**Key Risk Metrics:**

1. **CVaR (95%):** Conditional Value at Risk at 95% confidence
   - Example: `609 EUR`
   - Interpretation: In worst 5% of scenarios, average loss is 609 EUR
   - Compare to limit (typically 1000 EUR)

2. **Risk Energy:** Expected value of imbalance penalty
   - Example: `45.23 EUR`
   - Lower is better

3. **Shortage Probability:** P(demand > supply + actions)
   - Example: `5.2%`
   - Target: <10%

4. **Surplus Probability:** P(supply > demand + actions)
   - Example: `15.8%`
   - Target: <20%

**Primary Action Recommendation:**

The system recommends the most cost-effective action:

**Example:**
```
Action Type: INTRADAY_SELL
Quantity: 1.00 MW
Marginal Cost: 15.00 EUR/MWh
Expected Cost: -15.00 EUR (revenue)
```

**Action Types (Ranked by Marginal Cost):**

1. **FLEXIBILITY_DOWN:** Reduce demand via demand response
   - Cost: Typically 10-30 EUR/MWh
   - Use: When you have excess generation

2. **INTRADAY_SELL:** Sell excess energy to intraday market
   - Cost: Negative (revenue), typically -50 to -100 EUR/MWh
   - Use: When you have surplus

3. **HOLD:** No action, maintain current position
   - Cost: 0 EUR/MWh
   - Use: When balanced

4. **INTRADAY_BUY:** Buy energy from intraday market
   - Cost: Typically 50-100 EUR/MWh
   - Use: When you have shortage

5. **FLEXIBILITY_UP:** Increase demand via storage charging
   - Cost: Typically 60-90 EUR/MWh
   - Use: When you have excess and cheap prices

6. **STORAGE_DISCHARGE:** Use battery storage
   - Cost: Typically 80-120 EUR/MWh (including degradation)
   - Use: When you have shortage and high prices

7. **CURTAIL_RENEWABLES:** Reduce PV/wind generation
   - Cost: Typically 200-500 EUR/MWh (high cost)
   - Use: Last resort when extreme surplus

**Decision Rationale:**

Read the system's explanation:
- **Trigger:** What condition caused this decision?
- **Rationale:** Why was this action chosen?

**Example:**
```
Trigger: CVaR limit (1000 EUR) breached, current CVaR: 1234 EUR

Rationale: Portfolio shows shortage risk (demand forecast 200 MW exceeds 
supply forecast 185 MW). Intraday buy (1.00 MW @ 85 EUR/MWh) is most 
cost-effective action to reduce CVaR from 1234 EUR to 987 EUR.
```

**Alternative Actions:**

Review ranked alternatives if you want to override the primary action:

| Rank | Action | Quantity | Marginal Cost | Expected Cost |
|------|--------|----------|---------------|---------------|
| 1 | INTRADAY_BUY | 1.00 MW | 85.00 EUR/MWh | 85.00 EUR |
| 2 | STORAGE_DISCHARGE | 0.50 MW | 100.00 EUR/MWh | 50.00 EUR |
| 3 | FLEXIBILITY_UP | 2.00 MW | 120.00 EUR/MWh | 240.00 EUR |

**Decision Guidelines:**

- **HOLD State:** Execute monitoring only, no market action
- **WATCH State:** Prepare for action, notify trading desk
- **ACTION State:** Execute primary action immediately
- **CRITICAL State:** Escalate to senior management, manual override required

#### STEP 2: ENHANCEMENT PROPOSALS

Navigate to the **ENHANCEMENT PROPOSALS** tab.

The system analyzes the last decision and suggests improvements:

**Example Enhancements:**

1. **FLEXIBILITY:** "Current flexibility capacity is low (10.0 MW). Consider adding more demand response resources to reduce reliance on expensive intraday markets."

2. **STORAGE:** "Battery storage capacity (5.0 MW / 10.0 MWh) is limited compared to typical imbalances. Consider expanding storage to 10 MW / 20 MWh for better risk buffering."

3. **HEDGING:** "Current hedge position (150.0 MW) is 25% below expected demand P50 (200.0 MW). Consider increasing forward contracts to reduce ReBAP exposure."

4. **FORECAST:** "Forecast uncertainty is high (P90-P10 spread: 30.0 MW). Consider improving forecasting models or adding more weather data sources."

**How to Use Enhancements:**

1. **Short-Term (1-7 days):**
   - Adjust hedge positions
   - Activate additional flexibility contracts
   - Improve forecast data sources

2. **Medium-Term (1-3 months):**
   - Negotiate new demand response agreements
   - Upgrade forecasting models
   - Optimize storage dispatch strategies

3. **Long-Term (3-12 months):**
   - Invest in additional storage capacity
   - Develop new flexibility partnerships
   - Implement advanced AI/ML forecasting

**Action Items:**
- Document enhancement proposals
- Assign owners and timelines
- Track implementation progress
- Re-evaluate after implementation

#### STEP 3: SYSTEM PERFORMANCE

Navigate to the **SYSTEM PERFORMANCE** tab.

**CVaR Trend Chart:**
- Shows CVaR evolution over last 50 decisions
- Red dashed line: CVaR limit (1000 EUR)
- Monitor for:
  - Frequent limit breaches (>20%)
  - Increasing trend (deteriorating)
  - High volatility (unstable)

**Action Type Distribution:**
- Pie chart showing % of each action type
- Ideal distribution:
  - HOLD: 40-60%
  - WATCH/ACTION: 30-50%
  - CRITICAL: <5%
- If CRITICAL >10%, review risk appetite or capacity

**Performance Insights:**

1. **High CVaR Frequency:** 
   - Increase hedge position
   - Add flexibility capacity
   - Improve forecasts

2. **Frequent INTRADAY_BUY:**
   - Demand forecasts may be biased low
   - Increase base hedge position
   - Check PV/wind forecast accuracy

3. **Frequent CURTAILMENT:**
   - Supply forecasts may be biased high
   - Reduce hedge position
   - Add storage for surplus absorption

#### STEP 4: KPI DASHBOARD

Navigate to the **KPI DASHBOARD** tab.

**Key Performance Indicators:**

1. **CVaR Compliance Rate:**
   - Target: >95%
   - Calculation: % of decisions where CVaR ≤ limit
   - If <90%, escalate to risk committee

2. **System Uptime:**
   - Target: >99.5%
   - Monitors application availability
   - If <99%, contact IT support

3. **Forecast Score:**
   - Target: >75/100
   - Average quality score from Forecast Department
   - If <70, provide feedback to forecasters

**Risk Management KPIs:**
- CVaR Compliance: Percentage of intervals within risk appetite
- Average CVaR: Mean CVaR across all decisions
- Maximum CVaR: Worst-case CVaR observed

**Operational Efficiency KPIs:**
- Average Execution Time: Decision engine speed (target: <300ms)
- Total Decisions: Number of decisions made
- System Uptime: Application availability

**Forecast Accuracy KPIs:**
- Forecast Quality Score: Average validation score
- P50 Accuracy: Mean Absolute Percentage Error (MAPE)
- Uncertainty Calibration: P10-P90 spread appropriateness

---

## Understanding System Outputs

### Risk Metrics Explained

#### CVaR (Conditional Value at Risk)

**Definition:** The average loss in the worst 5% of scenarios.

**Formula:**
```
CVaR(95%) = E[Loss | Loss ≥ VaR(95%)]
```

**Interpretation:**
- CVaR = 500 EUR: In worst 5% of cases, average imbalance cost is 500 EUR
- Lower is better
- More conservative than VaR (considers tail risk severity)

**Example Scenario:**
```
1000 simulations of 15-minute interval:
- 950 simulations: loss <200 EUR (95%)
- 50 simulations: loss >200 EUR (5%)
- Average of those 50 worst cases: 609 EUR ← This is CVaR
```

**Risk Appetite:**
- Typical limit: 1000 EUR per 15-min interval
- Equivalent to: ~267,000 EUR annual risk budget (assuming 8760 hours/year × 4 intervals/hour)

#### Shortage Probability

**Definition:** P(Demand > Supply + Hedge + Actions)

**Interpretation:**
- 5%: In 5 out of 100 intervals, you'll have insufficient energy
- Target: <10% (acceptable risk level)
- If >20%: Serious shortage risk, increase hedge or buy energy

**Drivers:**
- High demand forecast
- Low renewable forecast
- Insufficient hedge position
- Limited flexibility/storage

#### Surplus Probability

**Definition:** P(Supply + Hedge > Demand + Actions)

**Interpretation:**
- 15%: In 15 out of 100 intervals, you'll have excess energy
- Target: <20% (acceptable risk level)
- If >30%: Serious surplus risk, reduce hedge or sell energy

**Drivers:**
- Low demand forecast
- High renewable forecast
- Excessive hedge position
- Limited curtailment capability

### Action Cost Interpretation

#### Marginal Cost

**Definition:** Cost per unit (EUR/MWh) of this action.

**Example:**
- INTRADAY_BUY: 85 EUR/MWh
- Means: Each additional MWh purchased costs 85 EUR

**Use Case:**
- Compare marginal costs to select most efficient action
- Lower marginal cost = more efficient action

#### Expected Cost

**Definition:** Total cost (EUR) for the recommended quantity.

**Example:**
- Action: INTRADAY_BUY 1.5 MW
- Marginal Cost: 85 EUR/MWh
- Expected Cost: 1.5 MW × (15 min / 60 min) × 85 EUR/MWh = 31.875 EUR

**Note:** 15-minute intervals require dividing MW by 4 to get MWh.

**Negative Cost = Revenue:**
- INTRADAY_SELL: -15.00 EUR means you earn 15 EUR

---

## Data Quality Guidelines

### Forecast Quality Standards

#### Demand Forecasts

**Minimum Requirements:**
- P10 ≤ P50 ≤ P90 ordering
- (P90-P10)/P50 ≤ 35% (uncertainty spread)
- Values within 50-500 MW range (adjust for your system)
- Confidence ≥60%

**Best Practices:**
- Use 7-day historical average as baseline
- Adjust for weather (temperature, humidity)
- Consider day-of-week patterns (weekday vs. weekend)
- Account for holidays and special events
- Validate against real-time SCADA data

**Data Sources:**
- Historical load data (1-year minimum)
- Weather forecasts (temperature, wind, solar irradiance)
- Calendar (holidays, weekends)
- Economic indicators (industrial activity)

#### Renewable Forecasts

**PV Solar:**
- Check GHI (Global Horizontal Irradiance) forecasts
- Account for panel efficiency (typically 15-20%)
- Consider soiling, shading, degradation
- Morning/evening: lower uncertainty
- Midday: higher potential variation

**Wind:**
- Wind speed forecasts from 10m and 100m height
- Power curve conversion (cubic relationship: P ∝ v³)
- Account for turbine availability (typically 95%)
- Wake effects in large wind farms
- Curtailment constraints

**Best Practices:**
- Update forecasts every 15-60 minutes
- Use ensemble forecasts (multiple models)
- Validate against real-time generation data
- Seasonal calibration (winter vs. summer)

#### Market Price Forecasts

**Day-Ahead Prices:**
- Use historical averages for similar conditions
- Adjust for fuel prices (gas, coal)
- Consider seasonal patterns
- Account for renewable penetration levels

**Intraday Prices:**
- Typically 2-5 EUR/MWh spread around day-ahead
- Wider spread during high volatility
- Bid < Day-Ahead < Ask

**ReBAP Penalties:**
- Regulatory defined or historically observed
- ReBAP Plus: typically 1.2-1.5× day-ahead price
- ReBAP Minus: typically 0.5-0.8× day-ahead price

### Validation Thresholds

| Metric | Warning | Error |
|--------|---------|-------|
| P10-P50-P90 ordering | N/A | Violation |
| Uncertainty spread | >30% | >50% |
| Demand range | <50 or >500 MW | <0 or >1000 MW |
| PV range | <0 or >100 MW | <-10 or >200 MW |
| Wind range | <0 or >150 MW | <-10 or >300 MW |
| Price spread (bid-ask) | >10 EUR/MWh | >20 EUR/MWh |
| Confidence | <70% | <60% |

---

## Best Practices

### For Forecast Department

1. **Regular Updates:**
   - Submit forecasts every 15-60 minutes
   - Update when material weather changes occur
   - Minimum: hourly updates during peak hours

2. **Quality Over Speed:**
   - Don't bypass validation unless truly urgent
   - Review warnings carefully
   - Aim for Quality Score >80

3. **Document Assumptions:**
   - Use Notes field to explain unusual forecasts
   - Flag extreme weather events
   - Note equipment outages or maintenance

4. **Continuous Improvement:**
   - Review forecast vs. actual data weekly
   - Calibrate P10/P50/P90 spread based on historical accuracy
   - Update models seasonally

5. **Collaboration:**
   - Communicate unusual conditions to Management
   - Share forecast rationale for critical decisions
   - Participate in post-mortem reviews

### For Management

1. **Timely Execution:**
   - Execute decisions within 5 minutes of forecast submission
   - Don't delay in ACTION state
   - Escalate CRITICAL states immediately

2. **Risk Monitoring:**
   - Check CVaR compliance daily
   - Review trend charts weekly
   - Investigate CVaR breaches >10% frequency

3. **Action Implementation:**
   - Document all manual overrides with rationale
   - Verify action execution with trading desk
   - Confirm actions in market systems

4. **Performance Review:**
   - Weekly: Review KPI dashboard
   - Monthly: Analyze action distribution and costs
   - Quarterly: Implement enhancement proposals

5. **Governance:**
   - Escalate CRITICAL states per protocol
   - Maintain audit trail for all decisions
   - Report CVaR breaches to risk committee

### Common Workflows

#### Normal Operation (HOLD State)

**Forecast Department:**
1. Submit forecast (Quality Score >75)
2. Monitor validation results
3. Update if conditions change

**Management:**
1. Execute decision engine
2. Verify HOLD state
3. Monitor risk metrics
4. No market action required

#### Action Required (ACTION State)

**Forecast Department:**
1. Submit high-quality forecast (Score >80)
2. Flag any uncertainties in Notes
3. Stay available for questions

**Management:**
1. Execute decision engine immediately
2. Review primary action recommendation
3. Verify action quantity and cost
4. Implement action via trading desk
5. Document execution confirmation
6. Monitor next interval for status change

#### Critical Escalation (CRITICAL State)

**Forecast Department:**
1. Re-validate forecast data
2. Check for data entry errors
3. Communicate extreme conditions to Management

**Management:**
1. **STOP** - Do not auto-execute
2. Call emergency meeting with:
   - Risk manager
   - Trading desk manager
   - Forecast team lead
3. Review decision rationale and alternatives
4. Consider manual override options:
   - Adjust risk appetite temporarily
   - Execute multiple actions simultaneously
   - Activate emergency contracts
5. Document decision and rationale
6. Execute with dual approval
7. Report to executives and risk committee

---

## Troubleshooting

### Common Issues

#### Issue: "Validation Failed - P10/P50/P90 Ordering Error"

**Cause:** P10, P50, P90 values not in increasing order.

**Solution:**
1. Check that P10 ≤ P50 ≤ P90
2. Common mistake: swapping P10 and P90
3. Re-enter values in correct order

**Example:**
```
❌ Wrong: P10=100, P50=90, P90=80
✅ Correct: P10=80, P50=90, P90=100
```

#### Issue: "Quality Score Too Low (<60)"

**Cause:** Multiple validation warnings or errors.

**Solution:**
1. Review all WARNING and ERROR messages
2. Address errors first (red boxes)
3. Revise data based on suggested corrections
4. Re-validate until score >60
5. If confident data is correct, use bypass option with documentation

#### Issue: "No Validated Forecast Available" (Management)

**Cause:** Forecast Department hasn't submitted forecast yet.

**Solution:**
1. Contact Forecast Department
2. Check if forecast is in progress
3. Verify database connection
4. Wait for forecast submission

#### Issue: "CVaR Limit Breached Frequently"

**Cause:** Insufficient hedge or capacity.

**Solution:**
1. Analyze trend: Is this persistent or temporary?
2. Review enhancement proposals
3. Consider:
   - Increasing base hedge position
   - Adding flexibility contracts
   - Expanding storage capacity
   - Improving forecast accuracy
4. Escalate to risk committee if persistent

#### Issue: "System Slow or Timeout"

**Cause:** Database lock, network issue, or high load.

**Solution:**
1. Wait 30 seconds and retry
2. Check internet connection
3. Refresh browser (F5)
4. If persists >5 minutes, contact IT support
5. Check system status at sidebar

#### Issue: "Decision Results Not Displaying"

**Cause:** Decision execution incomplete or error.

**Solution:**
1. Check for error message after clicking EXECUTE
2. Verify forecast was loaded correctly
3. Re-click EXECUTE DECISION ENGINE
4. Check browser console for errors (F12)
5. Contact IT if error persists

### Error Messages Explained

| Error | Meaning | Action |
|-------|---------|--------|
| `KeyError: 'cvar_eur'` | Database schema mismatch | Contact IT support |
| `AttributeError: 'Decision' object...` | Code version mismatch | Refresh page, contact IT |
| `TypeError: unsupported format...` | Data type error | Re-enter data, check formats |
| `ValidationError: P10 > P50` | Ordering violation | Correct forecast ordering |
| `DatabaseError: cannot commit` | Database locked | Wait and retry |

### Getting Help

**Internal Support:**
- **Technical Issues:** IT Helpdesk (ext. 1234)
- **Forecast Questions:** Forecast Team Lead (ext. 5678)
- **Risk/Trading Questions:** Risk Manager (ext. 9012)
- **System Training:** Contact HR Learning & Development

**Documentation:**
- User Guide: `EPBDA_USER_GUIDE.md`
- Technical Documentation: `EPBDA_Technical_Validation_Document.md`
- Test Report: `EPBDA_TEST_REPORT.md`

**Emergency Contacts:**
- Critical System Failure: IT Manager (mobile: +XX-XXX-XXXX)
- Risk Escalation: Chief Risk Officer (mobile: +XX-XXX-XXXX)

---

## Appendix

### Glossary

- **CVaR (Conditional Value at Risk):** Average loss in worst 5% of scenarios
- **P10/P50/P90:** 10th, 50th, 90th percentile forecasts
- **ReBAP:** Regulatory energy balancing penalty
- **Intraday Market:** Real-time energy trading market
- **Hedge Position:** Forward contracts for future energy delivery/purchase
- **Flexibility Asset:** Demand response or controllable load
- **Storage Asset:** Battery energy storage system (BESS)
- **Curtailment:** Intentional reduction of renewable generation

### Key Formulas

**CVaR Calculation:**
```
CVaR(α) = (1/(1-α)) × ∫[α to 1] VaR(p) dp

Where:
- α = confidence level (0.95 for 95%)
- VaR(p) = Value at Risk at probability p
```

**Risk Energy:**
```
Risk Energy = Σ [P(scenario) × |Imbalance| × ReBAP_cost]

Where:
- P(scenario) = probability of each scenario
- Imbalance = demand - supply - actions
- ReBAP_cost = penalty price (plus or minus)
```

**Action Marginal Cost:**
```
Marginal Cost = ∂(Total Cost) / ∂(Action Quantity)

Ranked: MC₁ ≤ MC₂ ≤ ... ≤ MC₇
```

### System Limits

| Parameter | Minimum | Maximum | Typical |
|-----------|---------|---------|---------|
| Demand Forecast P50 | 50 MW | 500 MW | 150-250 MW |
| PV Forecast P50 | 0 MW | 100 MW | 30-70 MW |
| Wind Forecast P50 | 0 MW | 150 MW | 50-120 MW |
| Day-Ahead Price | 10 EUR/MWh | 300 EUR/MWh | 50-100 EUR/MWh |
| Intraday Spread | 2 EUR/MWh | 10 EUR/MWh | 3-5 EUR/MWh |
| CVaR Limit | 500 EUR | 2000 EUR | 1000 EUR |
| Confidence Level | 60% | 100% | 75-85% |
| Execution Time | <100ms | <1000ms | 150-300ms |

### Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | Jan 2026 | Initial release with multi-user interface |
| 0.9 | Dec 2025 | Beta testing with Forecast Department |
| 0.8 | Nov 2025 | Core engine development |

---

**Document Version:** 1.0  
**Last Updated:** January 28, 2026  
**Contact:** EPBDA System Administrator  
**Feedback:** Please submit feedback to improve this guide

---

© 2026 EPBDA System. All rights reserved.
