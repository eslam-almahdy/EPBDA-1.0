"""
EPBDA Database Schema Visualization
Creates professional diagram of database structure
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

def create_database_schema():
    """Create database schema visualization"""
    
    fig = plt.figure(figsize=(20, 14), facecolor='white')
    ax = fig.add_subplot(111)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')
    
    # Title
    ax.text(50, 96, 'EPBDA DATABASE SCHEMA', 
           fontsize=24, weight='bold', ha='center',
           bbox=dict(boxstyle='round,pad=1', facecolor='#1e3c72', 
                    edgecolor='black', linewidth=2, alpha=0.9),
           color='white')
    
    # Color scheme
    color_input = '#4CAF50'
    color_core = '#2196F3'
    color_analytics = '#FF9800'
    color_system = '#9C27B0'
    
    # Table definitions with columns
    tables = {
        'portfolio_states': {
            'color': color_input,
            'pos': (10, 75),
            'columns': [
                'id (PK)',
                'timestamp',
                'demand_p10/p50/p90',
                'pv_p10/p50/p90',
                'wind_p10/p50/p90',
                'hedge_position_mw',
                'created_at'
            ]
        },
        'market_prices': {
            'color': color_input,
            'pos': (35, 75),
            'columns': [
                'id (PK)',
                'timestamp',
                'day_ahead',
                'intraday_bid/ask',
                'rebap_plus/minus',
                'created_at'
            ]
        },
        'decisions': {
            'color': color_core,
            'pos': (10, 50),
            'columns': [
                'id (PK)',
                'timestamp',
                'risk_state',
                'scenario_type',
                'primary_action_type',
                'action_volume_mw',
                'action_cost_eur',
                'recommended_hedge',
                'escalation_required',
                'created_at'
            ]
        },
        'risk_metrics': {
            'color': color_core,
            'pos': (35, 50),
            'columns': [
                'id (PK)',
                'decision_id (FK)',
                'expected_cost_eur',
                'cvar_95_eur',
                'risk_energy_eur',
                'prob_shortage',
                'residual_position',
                'created_at'
            ]
        },
        'alternative_actions': {
            'color': color_analytics,
            'pos': (60, 50),
            'columns': [
                'id (PK)',
                'decision_id (FK)',
                'action_type',
                'volume_mw',
                'marginal_cost',
                'risk_reduction',
                'rank'
            ]
        },
        'performance_tracking': {
            'color': color_analytics,
            'pos': (10, 25),
            'columns': [
                'id (PK)',
                'decision_id (FK)',
                'execution_time_ms',
                'actions_evaluated',
                'created_at'
            ]
        },
        'system_logs': {
            'color': color_system,
            'pos': (35, 25),
            'columns': [
                'id (PK)',
                'timestamp',
                'log_level',
                'component',
                'message',
                'details'
            ]
        }
    }
    
    # Draw tables
    table_boxes = {}
    for table_name, table_info in tables.items():
        x, y = table_info['pos']
        columns = table_info['columns']
        color = table_info['color']
        
        # Calculate box height based on columns
        box_height = 2 + len(columns) * 1.2
        box_width = 20
        
        # Table header
        header_box = FancyBboxPatch((x, y), box_width, 3,
                                   boxstyle='round,pad=0.3',
                                   facecolor=color,
                                   edgecolor='black',
                                   linewidth=2)
        ax.add_patch(header_box)
        
        ax.text(x + box_width/2, y + 1.5, table_name.upper(),
               fontsize=11, weight='bold', ha='center', va='center',
               color='white')
        
        # Table body
        body_box = FancyBboxPatch((x, y - box_height + 3), box_width, box_height - 3,
                                 boxstyle='square,pad=0.1',
                                 facecolor='#f5f5f5',
                                 edgecolor='black',
                                 linewidth=1.5)
        ax.add_patch(body_box)
        
        # Columns
        col_y = y + 1.5
        for col in columns:
            col_y -= 1.2
            if '(PK)' in col:
                ax.text(x + 1, col_y, col, fontsize=8, weight='bold', color='#1565C0')
            elif '(FK)' in col:
                ax.text(x + 1, col_y, col, fontsize=8, weight='bold', color='#E64A19')
            else:
                ax.text(x + 1, col_y, col, fontsize=8, color='#424242')
        
        # Store box position for relationships
        table_boxes[table_name] = (x + box_width/2, y - box_height/2)
    
    # Draw relationships
    relationships = [
        ('decisions', 'risk_metrics', 'decision_id'),
        ('decisions', 'alternative_actions', 'decision_id'),
        ('decisions', 'performance_tracking', 'decision_id')
    ]
    
    for from_table, to_table, fk_field in relationships:
        if from_table in table_boxes and to_table in table_boxes:
            x1, y1 = table_boxes[from_table]
            x2, y2 = table_boxes[to_table]
            
            arrow = FancyArrowPatch(
                (x1, y1), (x2, y2),
                arrowstyle='-|>',
                mutation_scale=20,
                linewidth=2,
                color='#E64A19',
                alpha=0.6,
                connectionstyle="arc3,rad=.2"
            )
            ax.add_patch(arrow)
    
    # Legend
    legend_y = 10
    legend_items = [
        ('Input Data', color_input),
        ('Core Decisions', color_core),
        ('Analytics', color_analytics),
        ('System', color_system)
    ]
    
    ax.text(65, legend_y + 8, 'TABLE CATEGORIES', 
           fontsize=12, weight='bold')
    
    for i, (label, color) in enumerate(legend_items):
        box = FancyBboxPatch((65, legend_y + 5 - i*2), 3, 1.5,
                            boxstyle='round,pad=0.1',
                            facecolor=color,
                            edgecolor='black',
                            linewidth=1)
        ax.add_patch(box)
        ax.text(69, legend_y + 5.75 - i*2, label, fontsize=10, va='center')
    
    # Key information panel
    info_text = """
DATABASE STATISTICS
- 7 normalized tables
- Complete audit trail
- Foreign key relationships
- Timestamp tracking on all records
- Performance metrics captured
    """
    
    ax.text(85, 70, info_text, fontsize=9,
           bbox=dict(boxstyle='round,pad=1', facecolor='#ecf0f1',
                    edgecolor='black', linewidth=1.5),
           verticalalignment='top',
           family='monospace')
    
    # Data flow indicators
    ax.text(50, 90, 'INPUT LAYER', fontsize=10, ha='center', 
           weight='bold', color=color_input)
    ax.text(50, 65, 'CORE DECISION LAYER', fontsize=10, ha='center',
           weight='bold', color=color_core)
    ax.text(50, 40, 'ANALYTICS & SYSTEM LAYER', fontsize=10, ha='center',
           weight='bold', color=color_analytics)
    
    plt.tight_layout()
    return fig

if __name__ == "__main__":
    print("Creating EPBDA Database Schema Diagram...")
    
    fig = create_database_schema()
    
    output_file = "EPBDA_Database_Schema.png"
    fig.savefig(output_file, dpi=300, facecolor='white',
               bbox_inches='tight', pad_inches=0.3)
    
    print(f"Database schema diagram saved: {output_file}")
    print("Resolution: 300 DPI")
    print("Format: PNG")
    
    plt.close()
    
    print("\nDatabase Tables:")
    print("  1. portfolio_states - Forecast inputs")
    print("  2. market_prices - Market data")
    print("  3. decisions - Decision records")
    print("  4. risk_metrics - Risk calculations")
    print("  5. alternative_actions - Action rankings")
    print("  6. performance_tracking - System performance")
    print("  7. system_logs - Event logging")
    print("\nAll tables include automatic timestamping and audit trail!")
