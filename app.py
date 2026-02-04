import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

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
        padding: 2rem;
        border-radius: 15px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1);
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
        margin-top: 2rem;
        margin-bottom: 1rem;
        border-left: 5px solid #3b82f6;
        padding-left: 10px;
    }
    
    div[data-testid="metric-container"] {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
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
        col_setup1, col_setup2 = st.columns(2)
        
        with col_setup1:
            # Map downtime column - try to find "Equipment Downtime"
            dt_cols = [c for c in df.columns if 'equipment downtime' in str(c).lower()]
            default_dt = dt_cols[0] if dt_cols else df.columns[0]
            downtime_col = st.selectbox("Select Downtime Column (Minutes)", df.columns, index=list(df.columns).index(default_dt))
        
        with col_setup2:
            # Map repair time column
            repair_time_col = st.selectbox("Select Repair Time Column (Minutes)", df.columns, index=list(df.columns).index(downtime_col))
            
            # Map Department column for filtering
            dept_options = [c for c in df.columns if 'department' in str(c).lower()]
            dept_col = st.selectbox("Select Department Column", df.columns, index=list(df.columns).index(dept_options[0]) if dept_options else 0)

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
            st.markdown("<br>", unsafe_allow_html=True)
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

        with st.expander("📄 View Processed Data Table"):
            st.dataframe(df)

    except Exception as e:
        st.error(f"Error: {e}")
        st.info("Sahi column names check karein. Aapne jo image dikhayi hai usme 'Equipment Downtime (Minutes)' column ka use karein.")

else:
    # Instructions
    st.markdown("""
    <div style='background: white; padding: 2rem; border-radius: 12px; border: 1px solid #e2e8f0;'>
        <h3>👋 Suru karne ke liye excel upload karein</h3>
        <p>Aapki file me ye columns hone chahiye:</p>
        <ul>
            <li><b>Equipment Downtime (Minutes)</b> - Failure time calculation ke liye</li>
            <li><b>Reason</b> (Optional) - Breakdown ka reason dekhne ke liye</li>
        </ul>
        <p><i>Note: Hamne default me 24 hours (1440 min) observation period maana hai.</i></p>
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
