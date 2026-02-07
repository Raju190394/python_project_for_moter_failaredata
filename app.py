import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
import warnings
warnings.filterwarnings('ignore')
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image as RLImage
from reportlab.lib.units import inch
from io import BytesIO
import tempfile
import os

# Page Configuration
st.set_page_config(
    page_title="Reliability & Failure Analytics",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Premium Custom CSS
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
    
    * {
        font-family: 'Outfit', sans-serif;
    }
    
    .stApp {
        background: #f8fafc;
    }
    
    /* Header Container */
    .main-header {
        background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%);
        padding: 1rem 2rem;
        border-radius: 12px;
        color: white;
        margin-bottom: 1rem;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1);
    }
    .main-header h1 {
        margin: 0 !important;
        padding: 0 !important;
        font-size: 1.75rem !important;
    }
    .main-header p {
        margin: 0 !important;
        padding: 0 !important;
        opacity: 0.9;
    }
    
    /* Card Styling */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        transition: transform 0.2s;
    }
    .metric-card:hover {
        transform: translateY(-5px);
        border-color: #3b82f6;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #f1f5f9;
        padding: 1rem;
    }
    
    /* Custom Headers */
    .section-title {
        color: #1e3a8a;
        font-weight: 700;
        margin-top: 0.75rem !important;
        margin-bottom: 0.5rem !important;
        border-left: 5px solid #3b82f6;
        padding-left: 10px;
        font-size: 1.25rem !important;
    }
    
    div[data-testid="metric-container"] {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        padding: 8px 12px !important;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        min-height: auto !important;
    }

    /* Reduce spacing between streamlit elements */
    .element-container {
        margin-bottom: 0.5rem !important;
    }
    </style>
""", unsafe_allow_html=True)

# App Title and Description
st.markdown("""
<div class="main-header">
    <h1>🏭 Equipment Reliability Dashboard</h1>
    <p>Upload your failure data to calculate Failure Rates, Repair Rates, and Mean Time calculations.</p>
</div>
""", unsafe_allow_html=True)

# Sidebar
st.sidebar.markdown("### 📥 Input Data")
uploaded_file = st.sidebar.file_uploader("Upload 'failure data new' (Excel)", type=["xlsx", "xls"])

# Handle Excel Title Rows
skip_rows = st.sidebar.number_input("Skip empty/title rows at top", value=0, min_value=0, help="If your Excel has a title like 'Electrical failure data' on top, skip those rows until you reach the actual headers.")

# Configuration
st.sidebar.markdown("---")
st.sidebar.markdown("### ⚙️ Settings")
obs_period_type = st.sidebar.radio("Observation Period Type", ["24 Hours (1440 min)", "Custom"])
if obs_period_type == "Custom":
    observation_period = st.sidebar.number_input("Mins per Record", value=1440, min_value=1)
else:
    observation_period = 1440

unit_conv = st.sidebar.selectbox("Display Calculations in:", ["Minutes", "Hours"], index=1)
conv_factor = 60 if unit_conv == "Hours" else 1

if uploaded_file:
    try:
        # Load sheets 
        xls = pd.ExcelFile(uploaded_file)
        sheet_names = xls.sheet_names
        sheet_name = st.sidebar.selectbox("Select Sheet", sheet_names)
        
        # Load data with skip rows
        df = pd.read_excel(uploaded_file, sheet_name=sheet_name, skiprows=skip_rows)
        
        
        # Clean column names
        df.columns = [str(c).strip() for c in df.columns]
        
        # UI for Column Selection
        st.markdown("<h3 class='section-title'>🔍 Data Configuration</h3>", unsafe_allow_html=True)
        col_setup1, col_setup2, col_setup3 = st.columns(3)
        
        with col_setup1:
            # Map downtime column - try to find "Equipment Downtime"
            dt_cols = [c for c in df.columns if 'equipment downtime' in str(c).lower()]
            default_dt = dt_cols[0] if dt_cols else df.columns[0]
            downtime_col = st.selectbox("Select Downtime Column (Minutes)", df.columns, index=list(df.columns).index(default_dt))
        
        with col_setup2:
            # Map repair time column
            repair_time_col = st.selectbox("Select Repair Time Column (Minutes)", df.columns, index=list(df.columns).index(downtime_col))
            
        with col_setup3:
            # Map Department column for filtering
            dept_options = [c for c in df.columns if 'department' in str(c).lower()]
            dept_col = st.selectbox("Select Department Column", df.columns, index=list(df.columns).index(dept_options[0]) if dept_options else 0)

        # Map Repairing Cost column (Global selection for summary)
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 💰 Cost Settings")
        cost_options = [c for c in df.columns if 'cost' in str(c).lower()]
        global_cost_col = st.sidebar.selectbox("Select 'Repairing Cost' Column", df.columns, index=list(df.columns).index(cost_options[0]) if cost_options else 0)

        # Prepare columns - convert to numeric and handle non-numeric values
        df[downtime_col] = pd.to_numeric(df[downtime_col], errors='coerce').fillna(0)
        df[repair_time_col] = pd.to_numeric(df[repair_time_col], errors='coerce').fillna(0)
        
        # VALIDATION: Check if the user selected a proper numeric column
        if df[downtime_col].sum() == 0 and len(df) > 0:
            st.warning(f"⚠️ Warning: The selected column '{downtime_col}' contains only zeros or non-numeric data. Please select the correct column from the dropdown.")

        # Department filtering for Repair Rate
        # Requirement: Exclude 'MAINTENANCE' from repair calculations
        repair_df = df.copy()
        if dept_col in df.columns:
            # Clean department names (remove spaces and case-insensitive check)
            repair_df = df[df[dept_col].astype(str).str.strip().str.upper() != 'MAINTENANCE']
            excluded_count = len(df) - len(repair_df)
            if excluded_count > 0:
                st.sidebar.success(f"✅ Filtered: {excluded_count} rows of 'MAINTENANCE' excluded from Repair Rate.")
            else:
                st.sidebar.info(f"ℹ️ No 'MAINTENANCE' rows found in '{dept_col}'.")

        # --- CALCULATIONS ---
        # 1. Operating Time = Obs Period - Downtime (On full data)
        df['Operating_Time'] = observation_period - df[downtime_col]
        df['Operating_Time'] = df['Operating_Time'].clip(lower=0)
        
        # 2. Aggregates
        total_op_time = df['Operating_Time'].sum() / conv_factor
        num_failures = len(df[df[downtime_col] > 0])
        
        # Repair aggregates (Using filtered data)
        total_repair_time = repair_df[repair_time_col].sum() / conv_factor
        num_repairs = len(repair_df[repair_df[repair_time_col] > 0])
        
        # 3. Metrics with safety checks
        mttf = total_op_time / num_failures if num_failures > 0 else 0
        failure_rate = 1 / mttf if mttf > 0 else 0
        
        mttr = total_repair_time / num_repairs if num_repairs > 0 else 0
        repair_rate = 1 / mttr if mttr > 0 else 0

        # --- DISPLAY ---
        
        # Row 1: Failure Analysis
        st.markdown("<h3 class='section-title'>🛑 Failure Rate Analysis</h3>", unsafe_allow_html=True)
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Failures", f"{num_failures:,}")
        m2.metric(f"Total Op. Time ({unit_conv})", f"{total_op_time:,.2f}")
        m3.metric(f"MTTF ({unit_conv})", f"{mttf:,.2f}")
        m4.metric("Failure Rate (λ)", f"{failure_rate:.6f}")
        
        # Row 2: Repair Analysis
        st.markdown("<h3 class='section-title'>🔧 Repair Rate Analysis</h3>", unsafe_allow_html=True)
        r1, r2, r3, r4 = st.columns(4)
        r1.metric("Total Repairs", f"{num_repairs:,}")
        r2.metric(f"Total Repair Time ({unit_conv})", f"{total_repair_time:,.2f}")
        r3.metric(f"MTTR ({unit_conv})", f"{mttr:,.2f}")
        r4.metric("Repair Rate (μ)", f"{repair_rate:.6f}")


        # Add PDF Button to Top Right Corner (after calculations)
        # Note: PDF will be generated at the end after all charts are created
        # Placeholder for now - actual PDF button will be added after all content is ready
        
        pdf_data_store = {
            'num_failures': num_failures,
            'total_op_time': total_op_time,
            'mttf': mttf,
            'failure_rate': failure_rate,
            'num_repairs': num_repairs,
            'total_repair_time': total_repair_time,
            'mttr': mttr,
            'repair_rate': repair_rate,
            'unit_conv': unit_conv
        }

        # Charts Section
        st.markdown("<h3 class='section-title'>📊 Visualization</h3>", unsafe_allow_html=True)
        
        # 1. Timeline Chart (Full Width for better view)
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(
            name='Operating Time',
            x=df.index,
            y=df['Operating_Time'] / conv_factor,
            marker_color='#10b981',
            hovertemplate="Index %{x}<br>Op Time: %{y:.2f} " + unit_conv
        ))
        fig_bar.add_trace(go.Bar(
            name='Downtime',
            x=df.index,
            y=df[downtime_col] / conv_factor,
            marker_color='#ef4444',
            hovertemplate="Index %{x}<br>Downtime: %{y:.2f} " + unit_conv
        ))
        fig_bar.update_layout(
            barmode='stack', 
            title=dict(text=f"Time Distribution per Event ({unit_conv})", font=dict(size=20)),
            plot_bgcolor='rgba(0,0,0,0)',
            height=450,
            margin=dict(l=20, r=20, t=50, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_bar, use_container_width=True)
            
        # 2. Reason Distribution
        reason_col_list = [c for c in df.columns if 'reason' in c.lower()]
        if reason_col_list:
            reason_df = df[df[downtime_col] > 0][reason_col_list[0]].value_counts().reset_index()
            reason_df.columns = ['Reason', 'Count']
            
            # Group small reasons if too many to avoid overlap
            if len(reason_df) > 10:
                top_10 = reason_df.head(10)
                others_count = reason_df.iloc[10:]['Count'].sum()
                reason_df = pd.concat([top_10, pd.DataFrame([{'Reason': 'OTHERS', 'Count': others_count}])])

            fig_pie = px.pie(reason_df, values='Count', names='Reason', 
                           title='Failure Reasons Distribution (Top 10)',
                           hole=0.4, color_discrete_sequence=px.colors.qualitative.Bold)
            
            fig_pie.update_layout(
                height=600,
                legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.1),
                margin=dict(l=20, r=150, t=50, b=20)
            )
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Add a 'Reason' column to see distribution chart.")

        # --- MULTI-SHEET COST SUMMARY ---
        st.markdown("<h3 class='section-title'>💰 Multi-Sheet Cost Summary</h3>", unsafe_allow_html=True)
        
        summary_data = []
        # Create a normalized version of the target cost column for fuzzy matching
        target_cost_norm = str(global_cost_col).strip().lower()

        with st.spinner("Analyzing all sheets..."):
            for s_name in sheet_names:
                try:
                    # Read each sheet
                    temp_df = pd.read_excel(uploaded_file, sheet_name=s_name, skiprows=skip_rows)
                    temp_df.columns = [str(c).strip() for c in temp_df.columns]
                    
                    # Find the best matching cost column in this specific sheet
                    actual_cost_col = None
                    # 1. Try exact match from sidebar selection
                    if global_cost_col in temp_df.columns:
                        actual_cost_col = global_cost_col
                    else:
                        # 2. Try normalized match (ignore case/extra spaces)
                        for c in temp_df.columns:
                            if c.lower().strip() == target_cost_norm:
                                actual_cost_col = c
                                break
                        
                        # 3. If still not found, search for any column containing 'cost'
                        if not actual_cost_col:
                            for c in temp_df.columns:
                                if 'cost' in c.lower():
                                    actual_cost_col = c
                                    break
                    
                    all_cost = 0
                    exclude_maint_cost = 0
                    
                    if actual_cost_col:
                        temp_df[actual_cost_col] = pd.to_numeric(temp_df[actual_cost_col], errors='coerce').fillna(0)
                        all_cost = temp_df[actual_cost_col].sum()
                        
                        # Find department column for this sheet (fuzzy search)
                        actual_dept_col = None
                        if dept_col in temp_df.columns:
                            actual_dept_col = dept_col
                        else:
                            for c in temp_df.columns:
                                if 'department' in c.lower() or 'dept' in c.lower():
                                    actual_dept_col = c
                                    break
                        
                        # Calculate excluded cost
                        if actual_dept_col:
                            mask = temp_df[actual_dept_col].astype(str).str.strip().str.upper() != 'MAINTENANCE'
                            exclude_maint_cost = temp_df[mask][actual_cost_col].sum()
                        else:
                            exclude_maint_cost = all_cost
                            
                    summary_data.append({
                        "Sheet Name": s_name,
                        "All Repair Cost": round(all_cost, 2),
                        "Exclude MAINTENANCE": round(exclude_maint_cost, 2),
                        "Status": "✅ Success" if actual_cost_col else "⚠️ Cost Column Missing"
                    })
                except Exception as e:
                    summary_data.append({
                        "Sheet Name": s_name,
                        "All Repair Cost": 0,
                        "Exclude MAINTENANCE": 0,
                        "Status": f"❌ Error: {str(e)[:30]}..."
                    })

        if summary_data:
            summary_df = pd.DataFrame(summary_data)
            
            # Calculate Grand Totals
            grand_all = summary_df["All Repair Cost"].sum()
            grand_excl = summary_df["Exclude MAINTENANCE"].sum()
            
            # Display metrics for Grand Total
            gt1, gt2 = st.columns(2)
            gt1.metric("Grand Total (All Sheets)", f"{grand_all:,.2f}")
            gt2.metric("Grand Total (Excl. Maintenance)", f"{grand_excl:,.2f}")
            
            # Add Grand Total Row to table
            total_row = pd.DataFrame([{
                "Sheet Name": "✨ GRAND TOTAL",
                "All Repair Cost": grand_all,
                "Exclude MAINTENANCE": grand_excl,
                "Status": "SUMMARY"
            }])
            summary_display_df = pd.concat([summary_df, total_row], ignore_index=True)
            
            st.markdown("##### Detailed Sheet-wise Breakdown")
            st.table(summary_display_df.style.format({
                "All Repair Cost": "{:,.2f}",
                "Exclude MAINTENANCE": "{:,.2f}"
            }))
        else:
            st.warning("Could not find cost data in sheets. Check your column selection.")

        # --- ML PREDICTIVE ANALYTICS ---
        st.markdown("<h3 class='section-title'>🤖 AI Predictive Analytics</h3>", unsafe_allow_html=True)
        
        if len(df) >= 10:  # Need minimum data for ML
            try:
                # Prepare features for ML
                ml_df = df.copy()
                ml_df['record_index'] = range(len(ml_df))
                
                # Feature engineering
                ml_df['avg_downtime'] = ml_df[downtime_col].rolling(window=3, min_periods=1).mean()
                ml_df['downtime_trend'] = ml_df[downtime_col].diff().fillna(0)
                ml_df['failure_flag'] = (ml_df[downtime_col] > 0).astype(int)
                
                # Calculate failure frequency (failures per 10 records)
                ml_df['failure_frequency'] = ml_df['failure_flag'].rolling(window=10, min_periods=1).sum()
                
                # Risk Score Calculation (0-100)
                risk_factors = [
                    ml_df[downtime_col] / ml_df[downtime_col].max() if ml_df[downtime_col].max() > 0 else 0,
                    ml_df['avg_downtime'] / ml_df['avg_downtime'].max() if ml_df['avg_downtime'].max() > 0 else 0,
                    ml_df['failure_frequency'] / 10  # Normalize to 0-1
                ]
                ml_df['risk_score'] = (sum(risk_factors) / len(risk_factors) * 100).clip(0, 100)
                
                # Current Risk Assessment
                current_risk = ml_df['risk_score'].iloc[-1]
                avg_risk = ml_df['risk_score'].mean()
                recent_failures = ml_df['failure_flag'].tail(10).sum()
                
                # Display Risk Metrics
                risk1, risk2, risk3 = st.columns(3)
                risk1.metric("Current Risk Score", f"{current_risk:.1f}/100", 
                           delta=f"{current_risk - avg_risk:.1f} vs avg",
                           delta_color="inverse")
                risk2.metric("Recent Failures (Last 10)", f"{recent_failures}")
                risk3.metric("Failure Frequency", f"{(recent_failures/10)*100:.0f}%")
                
                # ML Prediction: Next Failure Time Estimation
                if ml_df['failure_flag'].sum() >= 5:  # Need enough failure events
                    # Get indices where failures occurred
                    failure_indices = ml_df[ml_df['failure_flag'] == 1]['record_index'].values
                    
                    if len(failure_indices) > 1:
                        # Calculate intervals between failures
                        failure_intervals = np.diff(failure_indices)
                        avg_interval = failure_intervals.mean()
                        std_interval = failure_intervals.std()
                        
                        # Predict next failure
                        last_failure_index = failure_indices[-1]
                        current_index = len(ml_df) - 1
                        records_since_failure = current_index - last_failure_index
                        
                        estimated_next_failure = max(0, avg_interval - records_since_failure)
                        confidence = max(0, 100 - (std_interval / avg_interval * 100)) if avg_interval > 0 else 0
                        
                        st.markdown("##### 🔮 Next Failure Prediction")
                        pred1, pred2 = st.columns(2)
                        pred1.metric("Estimated Records Until Next Failure", 
                                   f"{int(estimated_next_failure)} records")
                        pred2.metric("Prediction Confidence", f"{confidence:.0f}%")
                        
                        # Warning if high risk
                        if estimated_next_failure < 5 and current_risk > 60:
                            st.warning("⚠️ **High Risk Alert:** Equipment is showing signs of imminent failure. Consider preventive maintenance.")
                        elif current_risk > 75:
                            st.error("🚨 **Critical Risk:** Immediate inspection recommended!")
                        else:
                            st.success("✅ Equipment operating within normal parameters.")
                
                # Risk Trend Visualization
                fig_risk = go.Figure()
                fig_risk.add_trace(go.Scatter(
                    x=ml_df.index,
                    y=ml_df['risk_score'],
                    mode='lines',
                    name='Risk Score',
                    line=dict(color='#ef4444', width=2),
                    fill='tozeroy',
                    fillcolor='rgba(239, 68, 68, 0.1)'
                ))
                fig_risk.add_hline(y=avg_risk, line_dash="dash", 
                                  line_color="gray", 
                                  annotation_text=f"Average Risk: {avg_risk:.1f}")
                fig_risk.update_layout(
                    title="Risk Score Trend Over Time",
                    xaxis_title="Record Index",
                    yaxis_title="Risk Score (0-100)",
                    height=350,
                    plot_bgcolor='rgba(0,0,0,0)',
                    margin=dict(l=20, r=20, t=50, b=20)
                )
                st.plotly_chart(fig_risk, use_container_width=True)
                
                # Key Insights
                with st.expander("📊 ML Model Insights"):
                    st.markdown(f"""
                    **Model Analysis:**
                    - **Total Records Analyzed:** {len(ml_df)}
                    - **Total Failures Detected:** {ml_df['failure_flag'].sum()}
                    - **Average Time Between Failures:** {avg_interval:.1f} records (if applicable)
                    - **Current Equipment Health:** {'Critical' if current_risk > 75 else 'Warning' if current_risk > 50 else 'Good'}
                    
                    **Risk Factors Contributing to Score:**
                    - Recent downtime patterns
                    - Failure frequency trends
                    - Historical breakdown intervals
                    """)
                    
            except Exception as e:
                st.info(f"ML Analysis requires more structured data. Error: {str(e)}")
        else:
            st.info("⚠️ ML Predictions require at least 10 records. Please upload more data for predictive analytics.")

        with st.expander("📄 View Current Sheet Processed Data"):
            st.dataframe(df)

        # === EXPORT BUTTONS IN SIDEBAR ===
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 📥 Export Reports")
        
        # Excel Export
        excel_buffer = BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
            # Summary Sheet
            summary_export_data = {
                'Metric': ['Total Failures', f'Total Operating Time ({unit_conv})', 
                          f'MTTF ({unit_conv})', 'Failure Rate (λ)',
                          'Total Repairs', f'Total Repair Time ({unit_conv})',
                          f'MTTR ({unit_conv})', 'Repair Rate (μ)'],
                'Value': [num_failures, f"{total_op_time:.2f}", f"{mttf:.2f}", f"{failure_rate:.6f}",
                         num_repairs, f"{total_repair_time:.2f}", f"{mttr:.2f}", f"{repair_rate:.6f}"]
            }
            summary_df_export = pd.DataFrame(summary_export_data)
            summary_df_export.to_excel(writer, sheet_name='Summary', index=False)
            
            # Raw Data Sheet
            df.to_excel(writer, sheet_name='Raw Data', index=False)
            
        excel_buffer.seek(0)
        st.sidebar.download_button(
            label="📊 Download Excel Report",
            data=excel_buffer,
            file_name=f"reliability_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        
        # PDF Export
        try:
            pdf_buffer = BytesIO()
            doc = SimpleDocTemplate(pdf_buffer, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
            elements = []
            styles = getSampleStyleSheet()
            
            # Custom Styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=20,
                textColor=colors.HexColor('#1e3a8a'),
                spaceAfter=6,
                alignment=1  # Center
            )
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=14,
                textColor=colors.HexColor('#1e3a8a'),
                spaceBefore=12,
                spaceAfter=6
            )
            
            # Title Page
            elements.append(Paragraph("🏭 Equipment Reliability & Failure Analytics Report", title_style))
            elements.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
            elements.append(Spacer(1, 0.2*inch))
            
            # 1. Failure Rate Analysis
            elements.append(Paragraph("🛑 Failure Rate Analysis", heading_style))
            failure_data = [
                ['Metric', 'Value'],
                ['Total Failures', f"{pdf_data_store['num_failures']:,}"],
                [f"Total Operating Time ({pdf_data_store['unit_conv']})", f"{pdf_data_store['total_op_time']:,.2f}"],
                [f"MTTF ({pdf_data_store['unit_conv']})", f"{pdf_data_store['mttf']:,.2f}"],
                ['Failure Rate (λ)', f"{pdf_data_store['failure_rate']:.6f}"]
            ]
            failure_table = Table(failure_data, colWidths=[3.5*inch, 2*inch])
            failure_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3b82f6')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(failure_table)
            elements.append(Spacer(1, 0.2*inch))
            
            # 2. Repair Rate Analysis
            elements.append(Paragraph("🔧 Repair Rate Analysis", heading_style))
            repair_data = [
                ['Metric', 'Value'],
                ['Total Repairs', f"{pdf_data_store['num_repairs']:,}"],
                [f"Total Repair Time ({pdf_data_store['unit_conv']})", f"{pdf_data_store['total_repair_time']:,.2f}"],
                [f"MTTR ({pdf_data_store['unit_conv']})", f"{pdf_data_store['mttr']:,.2f}"],
                ['Repair Rate (μ)', f"{pdf_data_store['repair_rate']:.6f}"]
            ]
            repair_table = Table(repair_data, colWidths=[3.5*inch, 2*inch])
            repair_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3b82f6')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(repair_table)
            elements.append(Spacer(1, 0.2*inch))
            
            # 3. Charts as Images
            elements.append(Paragraph("📊 Visualizations", heading_style))
            
            # Save bar chart as image
            temp_bar_path = os.path.join(tempfile.gettempdir(), f'bar_chart_{datetime.now().strftime("%Y%m%d%H%M%S")}.png')
            try:
                fig_bar.write_image(temp_bar_path, width=800, height=400, engine='kaleido')
                elements.append(RLImage(temp_bar_path, width=5.5*inch, height=2.75*inch))
                elements.append(Spacer(1, 0.1*inch))
            except Exception as chart_err:
                elements.append(Paragraph(f"Bar chart unavailable: {str(chart_err)[:50]}", styles['Normal']))
            
            # Save pie chart if exists
            if reason_col_list:
                temp_pie_path = os.path.join(tempfile.gettempdir(), f'pie_chart_{datetime.now().strftime("%Y%m%d%H%M%S")}.png')
                try:
                    fig_pie.write_image(temp_pie_path, width=800, height=500, engine='kaleido')
                    elements.append(RLImage(temp_pie_path, width=5.5*inch, height=3.4*inch))
                    elements.append(Spacer(1, 0.1*inch))
                except Exception as pie_err:
                    elements.append(Paragraph(f"Pie chart unavailable: {str(pie_err)[:50]}", styles['Normal']))
            
            # 4. Cost Summary (if available)
            if summary_data:
                elements.append(PageBreak())
                elements.append(Paragraph("💰 Multi-Sheet Cost Summary", heading_style))
                
                cost_table_data = [['Sheet Name', 'All Repair Cost', 'Exclude MAINTENANCE', 'Status']]
                grand_all = 0
                grand_excl = 0
                
                for item in summary_data:
                    cost_table_data.append([
                        item['Sheet Name'],
                        f"{item['All Repair Cost']:,.2f}",
                        f"{item['Exclude MAINTENANCE']:,.2f}",
                        item.get('Status', 'OK')
                    ])
                    if item['Sheet Name'] != '✨ GRAND TOTAL':
                        grand_all += item['All Repair Cost']
                        grand_excl += item['Exclude MAINTENANCE']
                
                # Add Grand Total Row
                cost_table_data.append([
                    '✨ GRAND TOTAL',
                    f"{grand_all:,.2f}",
                    f"{grand_excl:,.2f}",
                    'SUMMARY'
                ])
                
                cost_table = Table(cost_table_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1*inch])
                cost_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3b82f6')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
                    ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#fef3c7')),  # Highlight grand total
                    ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                elements.append(cost_table)
            
            # 5. ML Predictions (if available)
            if len(df) >= 10:
                try:
                    elements.append(PageBreak())
                    elements.append(Paragraph("🤖 AI/ML Predictive Analytics", heading_style))
                    
                    # ML Data preparation
                    ml_df_pdf = df.copy()
                    ml_df_pdf['record_index'] = range(len(ml_df_pdf))
                    ml_df_pdf['avg_downtime'] = ml_df_pdf[downtime_col].rolling(window=3, min_periods=1).mean()
                    ml_df_pdf['downtime_trend'] = ml_df_pdf[downtime_col].diff().fillna(0)
                    ml_df_pdf['failure_flag'] = (ml_df_pdf[downtime_col] > 0).astype(int)
                    ml_df_pdf['failure_frequency'] = ml_df_pdf['failure_flag'].rolling(window=10, min_periods=1).sum()
                    
                    risk_factors_pdf = [
                        ml_df_pdf[downtime_col] / ml_df_pdf[downtime_col].max() if ml_df_pdf[downtime_col].max() > 0 else 0,
                        ml_df_pdf['avg_downtime'] / ml_df_pdf['avg_downtime'].max() if ml_df_pdf['avg_downtime'].max() > 0 else 0,
                        ml_df_pdf['failure_frequency'] / 10
                    ]
                    ml_df_pdf['risk_score'] = (sum(risk_factors_pdf) / len(risk_factors_pdf) * 100).clip(0, 100)
                    
                    current_risk_pdf = ml_df_pdf['risk_score'].iloc[-1]
                    avg_risk_pdf = ml_df_pdf['risk_score'].mean()
                    recent_failures_pdf = ml_df_pdf['failure_flag'].tail(10).sum()
                    
                    ml_metrics_data = [
                        ['Metric', 'Value'],
                        ['Current Risk Score', f"{current_risk_pdf:.1f}/100"],
                        ['Average Risk Score', f"{avg_risk_pdf:.1f}/100"],
                        ['Recent Failures (Last 10)', f"{recent_failures_pdf}"],
                        ['Failure Frequency', f"{(recent_failures_pdf/10)*100:.0f}%"],
                        ['Equipment Health', 'Critical' if current_risk_pdf > 75 else 'Warning' if current_risk_pdf > 50 else 'Good']
                    ]
                    
                    ml_table = Table(ml_metrics_data, colWidths=[3.5*inch, 2*inch])
                    ml_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3b82f6')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, -1), 10),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black)
                    ]))
                    elements.append(ml_table)
                    elements.append(Spacer(1, 0.1*inch))
                    
                    # Add risk trend chart (recreate it for PDF)
                    try:
                        # Create risk chart
                        fig_risk_pdf = go.Figure()
                        fig_risk_pdf.add_trace(go.Scatter(
                            x=ml_df_pdf.index,
                            y=ml_df_pdf['risk_score'],
                            mode='lines',
                            name='Risk Score',
                            line=dict(color='#ef4444', width=2),
                            fill='tozeroy',
                            fillcolor='rgba(239, 68, 68, 0.1)'
                        ))
                        fig_risk_pdf.add_hline(y=avg_risk_pdf, line_dash="dash", 
                                              line_color="gray", 
                                              annotation_text=f"Average Risk: {avg_risk_pdf:.1f}")
                        fig_risk_pdf.update_layout(
                            title="Risk Score Trend Over Time",
                            xaxis_title="Record Index",
                            yaxis_title="Risk Score (0-100)",
                            height=350,
                            plot_bgcolor='rgba(0,0,0,0)',
                            margin=dict(l=20, r=20, t=50, b=20)
                        )
                        
                        temp_risk_path = os.path.join(tempfile.gettempdir(), f'risk_chart_{datetime.now().strftime("%Y%m%d%H%M%S")}.png')
                        fig_risk_pdf.write_image(temp_risk_path, width=800, height=350, engine='kaleido')
                        elements.append(RLImage(temp_risk_path, width=5.5*inch, height=2.4*inch))
                    except Exception as risk_err:
                        elements.append(Paragraph(f"Risk chart unavailable: {str(risk_err)[:50]}", styles['Normal']))
                        
                except Exception as ml_err:
                    elements.append(Paragraph(f"ML section unavailable: {str(ml_err)[:100]}", styles['Normal']))
            
            # Build PDF
            doc.build(elements)
            pdf_buffer.seek(0)
            
            # Cleanup temp files
            cleanup_files = []
            if 'temp_bar_path' in locals(): cleanup_files.append(temp_bar_path)
            if 'temp_pie_path' in locals(): cleanup_files.append(temp_pie_path)
            if 'temp_risk_path' in locals(): cleanup_files.append(temp_risk_path)
            
            for path in cleanup_files:
                try:
                    if os.path.exists(path):
                        os.unlink(path)
                except:
                    pass
            
            st.sidebar.download_button(
                label="📄 Download PDF Report",
                data=pdf_buffer,
                file_name=f"complete_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        except Exception as e:
            st.sidebar.error(f"PDF Error: {str(e)[:50]}...")
            st.sidebar.info("Run: pip install kaleido")

    except Exception as e:
        st.error(f"Error: {e}")
        st.info("Please check the column names. Ensure you select the correct column from the dropdowns.")

else:
    # Instructions
    st.markdown("""
    <div style='background: white; padding: 2rem; border-radius: 12px; border: 1px solid #e2e8f0;'>
        <h3>👋 Please upload an Excel file to get started</h3>
        <p>Your file should ideally contain these columns:</p>
        <ul>
            <li><b>Equipment Downtime (Minutes)</b> - Required for breakdown calculations</li>
            <li><b>Reason</b> (Optional) - For failure reason distribution chart</li>
        </ul>
        <p><i>Note: By default, we use a 24-hour (1440 min) observation period per record.</i></p>
    </div>
    """, unsafe_allow_html=True)

    # Sample Data Button
    st.sidebar.markdown("---")
    if st.sidebar.button("Generate Demo Excel"):
        demo_df = pd.DataFrame({
            "Date": ["13-Aug-22", "01-Jul-22", "01-Jul-22", "02-Jul-22", "03-Jul-22"],
            "Equipment Downtime (Minutes)": [15, 30, 10, 0, 45],
            "Production loss time (Minutes)": [15, 30, 10, 0, 45],
            "Reason": ["COIL SPARKING", "CRANE NO 8 BREAK DOWN", "CRANE NO 10 MAGNATE CABLE CUT", "OK", "MOTOR HEATING"]
        })
        buffer = pd.ExcelWriter("sample_data.xlsx", engine='openpyxl')
        demo_df.to_excel(buffer, index=False)
        buffer.close()
        with open("sample_data.xlsx", "rb") as f:
            st.sidebar.download_button("Download Sample File", f, "sample_data.xlsx")
