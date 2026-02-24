"""
BTW Management LLC — Noodles World Kitchen
Daily Sales Dashboard
"""

import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from data_loader import load_all_reports

# ───────────────────────── Page Config ─────────────────────────
st.set_page_config(
    page_title="NWK Daily Sales Dashboard",
    page_icon="🍜",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ───────────────────────── Custom CSS ─────────────────────────
st.markdown("""
<style>
    .kpi-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        color: white;
        border: 1px solid #0f3460;
    }
    .kpi-value {
        font-size: 28px;
        font-weight: 700;
        margin: 5px 0;
    }
    .kpi-label {
        font-size: 13px;
        text-transform: uppercase;
        letter-spacing: 1px;
        opacity: 0.8;
    }
    .kpi-delta-pos { color: #00d26a; font-size: 16px; font-weight: 600; }
    .kpi-delta-neg { color: #ff4757; font-size: 16px; font-weight: 600; }
    .section-header {
        font-size: 22px;
        font-weight: 600;
        margin: 30px 0 15px 0;
        padding-bottom: 8px;
        border-bottom: 2px solid #0f3460;
    }
</style>
""", unsafe_allow_html=True)

# ───────────────────────── Color Palette ─────────────────────────
COLORS = {
    'primary': '#0f3460',
    'accent': '#e94560',
    'positive': '#00d26a',
    'negative': '#ff4757',
    'ty': '#3498db',
    'ly': '#95a5a6',
}

STORE_COLORS = px.colors.qualitative.Set2

# ───────────────────────── Data Loading ─────────────────────────
FOLDER = os.path.dirname(os.path.abspath(__file__))


@st.cache_data(ttl=60)
def get_data():
    return load_all_reports(FOLDER)


data = get_data()
sales_df = data['sales']
brand_df = data['brand_totals']
trans_df = data['transactions']
channel_df = data['channels']
labor_df = data['labor']

if sales_df.empty:
    st.error("No flash report data found. Place Excel files in the same folder as this dashboard.")
    st.stop()

# ───────────────────────── Sidebar ─────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/noodles.png", width=60)
    st.title("🍜 NWK Dashboard")
    st.caption("BTW Management LLC")
    st.divider()

    # Date selector
    available_dates = sorted(sales_df['date'].unique())
    selected_date = st.selectbox(
        "📅 Select Date",
        options=available_dates,
        index=len(available_dates) - 1,
        format_func=lambda d: pd.Timestamp(d).strftime('%A, %b %d, %Y')
    )

    # Store filter
    all_stores = sorted(sales_df['store'].unique())
    selected_stores = st.multiselect(
        "🏪 Filter Stores",
        options=all_stores,
        default=all_stores,
    )

    st.divider()

    # Page navigation
    page = st.radio(
        "📊 Dashboard Pages",
        options=[
            "Overview",
            "Store Comparison",
            "Trends",
            "Channel Mix",
            "Labor & 3rd Party",
        ],
        index=0,
    )

    st.divider()
    st.caption(f"Data covers {len(available_dates)} days")
    st.caption(f"{len(all_stores)} stores reporting")

    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()


# ───────────────────────── Filter Data ─────────────────────────
def filter_df(df):
    """Filter dataframe to selected date and stores."""
    mask = (df['date'] == selected_date) & (df['store'].isin(selected_stores))
    return df[mask].copy()


def filter_stores(df):
    """Filter dataframe to selected stores only (all dates)."""
    return df[df['store'].isin(selected_stores)].copy()


day_sales = filter_df(sales_df)
day_trans = filter_df(trans_df)
day_channel = filter_df(channel_df)
day_labor = filter_df(labor_df)
day_brand = brand_df[brand_df['date'] == selected_date]


# ───────────────────────── Helper: KPI Card ─────────────────────────
def kpi_card(label, value, delta=None, delta_pct=None, prefix="$", suffix=""):
    delta_html = ""
    if delta is not None:
        arrow = "▲" if delta >= 0 else "▼"
        css_class = "kpi-delta-pos" if delta >= 0 else "kpi-delta-neg"
        pct_str = f" ({delta_pct:+.1f}%)" if delta_pct is not None else ""
        delta_html = f'<div class="{css_class}">{arrow} {prefix}{abs(delta):,.0f}{pct_str}</div>'

    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{prefix}{value:,.0f}{suffix}</div>
        {delta_html}
        <div class="kpi-label" style="margin-top:4px;">vs Last Year</div>
    </div>
    """, unsafe_allow_html=True)


def short_store(name):
    """Shorten store name: '9501 - Normal' → 'Normal'"""
    parts = str(name).split(' - ')
    return parts[1] if len(parts) > 1 else name


# ═══════════════════════════════════════════════════════════════
#  PAGE 1: OVERVIEW
# ═══════════════════════════════════════════════════════════════
if page == "Overview":
    st.markdown(f"## 📊 Daily Overview — {pd.Timestamp(selected_date).strftime('%A, %B %d, %Y')}")

    # KPI Cards
    if not day_brand.empty:
        row = day_brand.iloc[0]
        cols = st.columns(4)
        with cols[0]:
            kpi_card("Day Sales", row['day_sales_ty'], row['day_sales_diff'], row['day_sales_pct'])
        with cols[1]:
            kpi_card("WTD Sales", row['wtd_sales_ty'], row['wtd_sales_diff'], row['wtd_sales_pct'])
        with cols[2]:
            kpi_card("PTD Sales", row['ptd_sales_ty'], row['ptd_sales_diff'], row['ptd_sales_pct'])
        with cols[3]:
            kpi_card("YTD Sales", row['ytd_sales_ty'], row['ytd_sales_diff'], row['ytd_sales_pct'])

    st.markdown("")

    # Transaction & Avg Check KPIs
    if not day_trans.empty and not day_channel.empty:
        total_trans_ty = day_trans['day_trans_ty'].sum()
        total_trans_ly = day_trans['day_trans_ly'].sum()
        trans_diff = total_trans_ty - total_trans_ly
        trans_pct = (trans_diff / total_trans_ly * 100) if total_trans_ly else 0

        avg_check_ty = day_sales['day_sales_ty'].sum() / total_trans_ty if total_trans_ty else 0
        avg_check_ly = day_sales['day_sales_ly'].sum() / total_trans_ly if total_trans_ly else 0
        avg_check_diff = avg_check_ty - avg_check_ly
        avg_check_pct = (avg_check_diff / avg_check_ly * 100) if avg_check_ly else 0

        cols2 = st.columns(4)
        with cols2[0]:
            kpi_card("Day Transactions", total_trans_ty, trans_diff, trans_pct, prefix="")
        with cols2[1]:
            kpi_card("Avg Check", avg_check_ty, avg_check_diff, avg_check_pct)
        with cols2[2]:
            ytd_ty = day_brand.iloc[0]['ytd_sales_ty'] if not day_brand.empty else 0
            kpi_card("R13 Sales", day_brand.iloc[0]['r13_sales_ty'] if not day_brand.empty else 0,
                     day_brand.iloc[0]['r13_sales_diff'] if not day_brand.empty else 0,
                     day_brand.iloc[0]['r13_sales_pct'] if not day_brand.empty else 0)
        with cols2[3]:
            total_labor_pct = day_labor['labor_pct'].mean() if not day_labor.empty else 0
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Avg Labor %</div>
                <div class="kpi-value">{total_labor_pct:.1f}%</div>
                <div class="kpi-label" style="margin-top:4px;">across all stores</div>
            </div>
            """, unsafe_allow_html=True)

    # ── Daily Sales Trend ──
    st.markdown('<div class="section-header">📈 Daily Sales Trend (All Dates)</div>', unsafe_allow_html=True)
    trend_df = brand_df.sort_values('date').copy()
    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(
        x=trend_df['date'], y=trend_df['day_sales_ty'],
        mode='lines+markers', name='This Year',
        line=dict(color=COLORS['ty'], width=3),
        marker=dict(size=10),
    ))
    fig_trend.add_trace(go.Scatter(
        x=trend_df['date'], y=trend_df['day_sales_ly'],
        mode='lines+markers', name='Last Year',
        line=dict(color=COLORS['ly'], width=2, dash='dot'),
        marker=dict(size=8),
    ))
    fig_trend.update_layout(
        height=350,
        margin=dict(l=20, r=20, t=30, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        yaxis_title="Total Brand Sales ($)",
        xaxis_title="",
        hovermode="x unified",
    )
    st.plotly_chart(fig_trend, use_container_width=True)

    # ── Store Performance Table ──
    st.markdown('<div class="section-header">🏪 Store Performance</div>', unsafe_allow_html=True)
    if not day_sales.empty:
        table_df = day_sales[['store', 'day_sales_ty', 'day_sales_ly', 'day_sales_diff', 'day_sales_pct']].copy()
        table_df.columns = ['Store', 'Day Sales TY', 'Day Sales LY', '+/-', '% Change']
        table_df = table_df.sort_values('Day Sales TY', ascending=False)
        table_df['% Change'] = table_df['% Change'].map(lambda x: f"{x:+.1f}%")
        table_df['Day Sales TY'] = table_df['Day Sales TY'].map(lambda x: f"${x:,.2f}")
        table_df['Day Sales LY'] = table_df['Day Sales LY'].map(lambda x: f"${x:,.2f}")
        table_df['+/-'] = table_df['+/-'].map(lambda x: f"${x:+,.2f}")
        st.dataframe(table_df, use_container_width=True, hide_index=True)

# ═══════════════════════════════════════════════════════════════
#  PAGE 2: STORE COMPARISON
# ═══════════════════════════════════════════════════════════════
elif page == "Store Comparison":
    st.markdown(f"## 🏪 Store Comparison — {pd.Timestamp(selected_date).strftime('%b %d, %Y')}")

    # TY vs LY bar chart
    st.markdown('<div class="section-header">Day Sales: This Year vs Last Year</div>', unsafe_allow_html=True)
    if not day_sales.empty:
        chart_df = day_sales.copy()
        chart_df['short_store'] = chart_df['store'].apply(short_store)
        chart_df = chart_df.sort_values('day_sales_ty', ascending=True)

        fig_comp = go.Figure()
        fig_comp.add_trace(go.Bar(
            y=chart_df['short_store'], x=chart_df['day_sales_ly'],
            name='Last Year', orientation='h',
            marker_color=COLORS['ly'], text=chart_df['day_sales_ly'].map(lambda x: f"${x:,.0f}"),
            textposition='auto',
        ))
        fig_comp.add_trace(go.Bar(
            y=chart_df['short_store'], x=chart_df['day_sales_ty'],
            name='This Year', orientation='h',
            marker_color=COLORS['ty'], text=chart_df['day_sales_ty'].map(lambda x: f"${x:,.0f}"),
            textposition='auto',
        ))
        fig_comp.update_layout(
            barmode='group', height=400,
            margin=dict(l=20, r=20, t=10, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            xaxis_title="Sales ($)",
        )
        st.plotly_chart(fig_comp, use_container_width=True)

    # ── Heatmap: % change by store across dates ──
    st.markdown('<div class="section-header">📊 Performance Heatmap (% Change vs LY)</div>', unsafe_allow_html=True)
    stores_sales = filter_stores(sales_df)
    if not stores_sales.empty:
        pivot = stores_sales.pivot_table(
            index='store', columns='date', values='day_sales_pct', aggfunc='first'
        )
        pivot.index = pivot.index.map(short_store)
        pivot.columns = [pd.Timestamp(c).strftime('%m/%d') for c in pivot.columns]

        fig_heat = px.imshow(
            pivot.values,
            x=pivot.columns,
            y=pivot.index,
            color_continuous_scale='RdYlGn',
            color_continuous_midpoint=0,
            aspect='auto',
            text_auto='.1f',
        )
        fig_heat.update_layout(
            height=350,
            margin=dict(l=20, r=20, t=10, b=20),
            coloraxis_colorbar_title="% vs LY",
        )
        st.plotly_chart(fig_heat, use_container_width=True)

    # ── Top / Bottom Performers ──
    st.markdown('<div class="section-header">🏆 Top & Bottom Performers</div>', unsafe_allow_html=True)
    if not day_sales.empty:
        sorted_stores = day_sales.sort_values('day_sales_pct', ascending=False)
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### 🥇 Best Performers")
            for _, row in sorted_stores.head(3).iterrows():
                delta_class = "kpi-delta-pos" if row['day_sales_pct'] >= 0 else "kpi-delta-neg"
                st.markdown(f"""
                **{short_store(row['store'])}** — <span class="{delta_class}">{row['day_sales_pct']:+.1f}%</span>
                (${row['day_sales_ty']:,.0f})
                """, unsafe_allow_html=True)
        with col2:
            st.markdown("#### 📉 Needs Attention")
            for _, row in sorted_stores.tail(3).iterrows():
                delta_class = "kpi-delta-pos" if row['day_sales_pct'] >= 0 else "kpi-delta-neg"
                st.markdown(f"""
                **{short_store(row['store'])}** — <span class="{delta_class}">{row['day_sales_pct']:+.1f}%</span>
                (${row['day_sales_ty']:,.0f})
                """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
#  PAGE 3: TRENDS
# ═══════════════════════════════════════════════════════════════
elif page == "Trends":
    st.markdown("## 📈 Sales & Transaction Trends")

    # ── Daily sales per store ──
    st.markdown('<div class="section-header">Daily Sales by Store Over Time</div>', unsafe_allow_html=True)
    stores_sales = filter_stores(sales_df)
    if not stores_sales.empty:
        stores_sales = stores_sales.copy()
        stores_sales['short_store'] = stores_sales['store'].apply(short_store)
        fig_lines = px.line(
            stores_sales.sort_values('date'),
            x='date', y='day_sales_ty', color='short_store',
            markers=True,
            color_discrete_sequence=STORE_COLORS,
        )
        fig_lines.update_layout(
            height=400,
            margin=dict(l=20, r=20, t=10, b=20),
            legend_title="Store",
            yaxis_title="Day Sales ($)",
            xaxis_title="",
            hovermode="x unified",
        )
        st.plotly_chart(fig_lines, use_container_width=True)

    # ── Sales Period Comparison ──
    st.markdown('<div class="section-header">Sales Period Comparison (Selected Date)</div>', unsafe_allow_html=True)
    if not day_sales.empty:
        period_data = []
        for _, row in day_sales.iterrows():
            store_short = short_store(row['store'])
            period_data.append({'Store': store_short, 'Period': 'Day', 'TY': row['day_sales_ty'], 'LY': row['day_sales_ly']})
            period_data.append({'Store': store_short, 'Period': 'WTD', 'TY': row['wtd_sales_ty'], 'LY': row['wtd_sales_ly']})
            period_data.append({'Store': store_short, 'Period': 'PTD', 'TY': row['ptd_sales_ty'], 'LY': row['ptd_sales_ly']})

        period_df = pd.DataFrame(period_data)

        tab1, tab2, tab3 = st.tabs(["Day", "WTD", "PTD"])
        for tab, period in zip([tab1, tab2, tab3], ["Day", "WTD", "PTD"]):
            with tab:
                pdata = period_df[period_df['Period'] == period].sort_values('TY', ascending=True)
                fig_p = go.Figure()
                fig_p.add_trace(go.Bar(y=pdata['Store'], x=pdata['LY'], name='LY', orientation='h', marker_color=COLORS['ly']))
                fig_p.add_trace(go.Bar(y=pdata['Store'], x=pdata['TY'], name='TY', orientation='h', marker_color=COLORS['ty']))
                fig_p.update_layout(barmode='group', height=350, margin=dict(l=20, r=20, t=10, b=20), xaxis_title="Sales ($)")
                st.plotly_chart(fig_p, use_container_width=True)

    # ── Transaction Trends ──
    st.markdown('<div class="section-header">Daily Transactions by Store Over Time</div>', unsafe_allow_html=True)
    stores_trans = filter_stores(trans_df)
    if not stores_trans.empty:
        stores_trans = stores_trans.copy()
        stores_trans['short_store'] = stores_trans['store'].apply(short_store)
        fig_trans = px.line(
            stores_trans.sort_values('date'),
            x='date', y='day_trans_ty', color='short_store',
            markers=True,
            color_discrete_sequence=STORE_COLORS,
        )
        fig_trans.update_layout(
            height=400,
            margin=dict(l=20, r=20, t=10, b=20),
            legend_title="Store",
            yaxis_title="Transactions",
            xaxis_title="",
            hovermode="x unified",
        )
        st.plotly_chart(fig_trans, use_container_width=True)


# ═══════════════════════════════════════════════════════════════
#  PAGE 4: CHANNEL MIX
# ═══════════════════════════════════════════════════════════════
elif page == "Channel Mix":
    st.markdown(f"## 🍽️ Channel Mix — {pd.Timestamp(selected_date).strftime('%b %d, %Y')}")

    if not day_channel.empty:
        # ── Overall Channel Donut ──
        st.markdown('<div class="section-header">Overall Sales by Channel</div>', unsafe_allow_html=True)
        total_dine = day_channel['dine_in_sales'].sum()
        total_carry = day_channel['carry_out_sales'].sum()
        total_delivery = day_channel['delivery_sales'].sum()
        total_drive = day_channel['drive_thru_sales'].sum()

        channel_totals = pd.DataFrame({
            'Channel': ['Dine In', 'Carry Out', 'Delivery', 'Drive Thru'],
            'Sales': [total_dine, total_carry, total_delivery, total_drive],
        })
        channel_totals = channel_totals[channel_totals['Sales'] > 0]

        col1, col2 = st.columns([1, 1])
        with col1:
            fig_donut = px.pie(
                channel_totals, values='Sales', names='Channel',
                hole=0.5,
                color_discrete_sequence=['#3498db', '#2ecc71', '#e74c3c', '#f39c12'],
            )
            fig_donut.update_traces(textinfo='label+percent+value', texttemplate='%{label}<br>%{percent}<br>$%{value:,.0f}')
            fig_donut.update_layout(height=400, margin=dict(l=20, r=20, t=30, b=20), showlegend=False)
            st.plotly_chart(fig_donut, use_container_width=True)

        with col2:
            # Summary metrics
            total_all = total_dine + total_carry + total_delivery + total_drive
            for ch, val, color in [('Dine In', total_dine, '#3498db'), ('Carry Out', total_carry, '#2ecc71'),
                                    ('Delivery', total_delivery, '#e74c3c'), ('Drive Thru', total_drive, '#f39c12')]:
                pct = (val / total_all * 100) if total_all > 0 else 0
                st.markdown(f"""
                <div style="padding: 10px; margin: 8px 0; border-left: 4px solid {color}; background: #f8f9fa; border-radius: 4px;">
                    <strong>{ch}</strong>: ${val:,.2f} ({pct:.1f}%)
                </div>
                """, unsafe_allow_html=True)

        # ── Channel Mix by Store ──
        st.markdown('<div class="section-header">Channel Mix by Store</div>', unsafe_allow_html=True)
        mix_data = []
        for _, row in day_channel.iterrows():
            store_short = short_store(row['store'])
            mix_data.append({'Store': store_short, 'Channel': 'Dine In', 'Sales': row['dine_in_sales']})
            mix_data.append({'Store': store_short, 'Channel': 'Carry Out', 'Sales': row['carry_out_sales']})
            mix_data.append({'Store': store_short, 'Channel': 'Delivery', 'Sales': row['delivery_sales']})
            if row['drive_thru_sales'] > 0:
                mix_data.append({'Store': store_short, 'Channel': 'Drive Thru', 'Sales': row['drive_thru_sales']})

        mix_df = pd.DataFrame(mix_data)
        fig_stack = px.bar(
            mix_df, x='Store', y='Sales', color='Channel',
            color_discrete_map={'Dine In': '#3498db', 'Carry Out': '#2ecc71', 'Delivery': '#e74c3c', 'Drive Thru': '#f39c12'},
        )
        fig_stack.update_layout(
            barmode='stack', height=400,
            margin=dict(l=20, r=20, t=10, b=20),
            yaxis_title="Sales ($)",
        )
        st.plotly_chart(fig_stack, use_container_width=True)

        # ── Average Check by Channel ──
        st.markdown('<div class="section-header">Average Check by Channel & Store</div>', unsafe_allow_html=True)
        avg_data = []
        for _, row in day_channel.iterrows():
            store_short = short_store(row['store'])
            avg_data.append({'Store': store_short, 'Channel': 'Dine In', 'Avg Check': row['dine_in_avg_check']})
            avg_data.append({'Store': store_short, 'Channel': 'Carry Out', 'Avg Check': row['carry_out_avg_check']})
            avg_data.append({'Store': store_short, 'Channel': 'Delivery', 'Avg Check': row['delivery_avg_check']})
            if row['drive_thru_avg_check'] > 0:
                avg_data.append({'Store': store_short, 'Channel': 'Drive Thru', 'Avg Check': row['drive_thru_avg_check']})

        avg_df = pd.DataFrame(avg_data)
        fig_avg = px.bar(
            avg_df, x='Store', y='Avg Check', color='Channel', barmode='group',
            color_discrete_map={'Dine In': '#3498db', 'Carry Out': '#2ecc71', 'Delivery': '#e74c3c', 'Drive Thru': '#f39c12'},
        )
        fig_avg.update_layout(height=400, margin=dict(l=20, r=20, t=10, b=20), yaxis_title="Avg Check ($)")
        st.plotly_chart(fig_avg, use_container_width=True)


# ═══════════════════════════════════════════════════════════════
#  PAGE 5: LABOR & 3RD PARTY
# ═══════════════════════════════════════════════════════════════
elif page == "Labor & 3rd Party":
    st.markdown(f"## 💰 Labor & 3rd Party Delivery — {pd.Timestamp(selected_date).strftime('%b %d, %Y')}")

    if not day_labor.empty:
        # ── Labor % by Store ──
        st.markdown('<div class="section-header">Labor % by Store</div>', unsafe_allow_html=True)
        labor_chart = day_labor.copy()
        labor_chart['short_store'] = labor_chart['store'].apply(short_store)
        labor_chart = labor_chart.sort_values('labor_pct', ascending=True)

        fig_labor = go.Figure()
        fig_labor.add_trace(go.Bar(
            y=labor_chart['short_store'], x=labor_chart['labor_pct'],
            orientation='h',
            marker_color=[COLORS['negative'] if x > 20 else COLORS['ty'] for x in labor_chart['labor_pct']],
            text=labor_chart['labor_pct'].map(lambda x: f"{x:.1f}%"),
            textposition='auto',
        ))
        # Target line at 18%
        fig_labor.add_vline(x=18, line_dash="dash", line_color="red", annotation_text="Target 18%")
        fig_labor.update_layout(
            height=350,
            margin=dict(l=20, r=20, t=10, b=20),
            xaxis_title="Labor %",
        )
        st.plotly_chart(fig_labor, use_container_width=True)

        # ── Labor $ ──
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Labor Summary**")
            labor_summary = labor_chart[['short_store', 'labor_dollars', 'labor_pct']].copy()
            labor_summary.columns = ['Store', 'Labor $', 'Labor %']
            labor_summary['Labor $'] = labor_summary['Labor $'].map(lambda x: f"${x:,.2f}")
            labor_summary['Labor %'] = labor_summary['Labor %'].map(lambda x: f"{x:.1f}%")
            st.dataframe(labor_summary, use_container_width=True, hide_index=True)

        with col2:
            total_labor = day_labor['labor_dollars'].sum()
            total_sales_day = day_sales['day_sales_ty'].sum() if not day_sales.empty else 0
            overall_labor_pct = (total_labor / total_sales_day * 100) if total_sales_day > 0 else 0
            st.markdown(f"""
            <div class="kpi-card" style="margin-top: 30px;">
                <div class="kpi-label">Total Labor</div>
                <div class="kpi-value">${total_labor:,.0f}</div>
                <div class="kpi-label">{overall_labor_pct:.1f}% of day sales</div>
            </div>
            """, unsafe_allow_html=True)

        # ── 3rd Party Delivery Breakdown ──
        st.markdown('<div class="section-header">🚗 3rd Party Delivery Breakdown</div>', unsafe_allow_html=True)

        third_party_data = []
        for _, row in day_labor.iterrows():
            store_short = short_store(row['store'])
            if row['doordash'] > 0:
                third_party_data.append({'Store': store_short, 'Platform': 'DoorDash', 'Sales': row['doordash']})
            if row['ubereats'] > 0:
                third_party_data.append({'Store': store_short, 'Platform': 'UberEats', 'Sales': row['ubereats']})
            if row['grubhub'] > 0:
                third_party_data.append({'Store': store_short, 'Platform': 'GrubHub', 'Sales': row['grubhub']})
            if row['eatstreet'] > 0:
                third_party_data.append({'Store': store_short, 'Platform': 'EatStreet', 'Sales': row['eatstreet']})
            if row['ezcater'] > 0:
                third_party_data.append({'Store': store_short, 'Platform': 'EZ Cater', 'Sales': row['ezcater']})

        if third_party_data:
            tp_df = pd.DataFrame(third_party_data)
            fig_tp = px.bar(
                tp_df, x='Store', y='Sales', color='Platform',
                color_discrete_map={
                    'DoorDash': '#ff3008', 'UberEats': '#06c167',
                    'GrubHub': '#f63440', 'EatStreet': '#ffa500', 'EZ Cater': '#6f42c1',
                },
            )
            fig_tp.update_layout(
                barmode='stack', height=400,
                margin=dict(l=20, r=20, t=10, b=20),
                yaxis_title="Sales ($)",
            )
            st.plotly_chart(fig_tp, use_container_width=True)

        # ── 3rd Party % of Sales ──
        st.markdown('<div class="section-header">3rd Party as % of Daily Sales</div>', unsafe_allow_html=True)
        tp_pct = day_labor[['store', 'total_3rd_party_pct']].copy()
        tp_pct['short_store'] = tp_pct['store'].apply(short_store)
        tp_pct = tp_pct.sort_values('total_3rd_party_pct', ascending=True)

        fig_tp_pct = go.Figure()
        fig_tp_pct.add_trace(go.Bar(
            y=tp_pct['short_store'], x=tp_pct['total_3rd_party_pct'],
            orientation='h',
            marker_color='#e74c3c',
            text=tp_pct['total_3rd_party_pct'].map(lambda x: f"{x:.1f}%"),
            textposition='auto',
        ))
        fig_tp_pct.update_layout(
            height=350,
            margin=dict(l=20, r=20, t=10, b=20),
            xaxis_title="3rd Party Delivery % of Sales",
        )
        st.plotly_chart(fig_tp_pct, use_container_width=True)

        # OLO Summary
        st.markdown('<div class="section-header">📱 Online Ordering (OLO) by Store</div>', unsafe_allow_html=True)
        olo_chart = day_labor.copy()
        olo_chart['short_store'] = olo_chart['store'].apply(short_store)
        olo_chart = olo_chart.sort_values('olo_sales', ascending=True)
        fig_olo = go.Figure()
        fig_olo.add_trace(go.Bar(
            y=olo_chart['short_store'], x=olo_chart['olo_sales'],
            orientation='h', marker_color='#9b59b6',
            text=olo_chart['olo_sales'].map(lambda x: f"${x:,.0f}"),
            textposition='auto',
        ))
        fig_olo.update_layout(height=350, margin=dict(l=20, r=20, t=10, b=20), xaxis_title="OLO Sales ($)")
        st.plotly_chart(fig_olo, use_container_width=True)
