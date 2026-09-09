"""
Generates all 11 Plotly charts from the business analysis notebook
and exports each as PNG (for README embedding) and HTML (interactive).
"""
import pandas as pd
import numpy as np
import plotly.express as px
from scipy import stats as st
import plotly.graph_objects as go
from pathlib import Path

OUT = Path("charts_out")
OUT.mkdir(exist_ok=True)

def export(fig, name: str) -> None:
    fig.write_image(OUT / f"{name}.png", width=1100, height=650, scale=2)
    fig.write_html(OUT / f"{name}.html", include_plotlyjs="cdn")
    print(f"exported: {name}")

# ---------- Load ----------
cost = pd.read_csv('costs_us.csv')
orders = pd.read_csv('orders_log_us.csv')
visit = pd.read_csv('visits_log_us.csv')

# ---------- Prepare ----------
visit.columns = ['device', 'end_ts', 'source_id', 'start_ts', 'uid']
orders.columns = ['buy_ts', 'revenue', 'uid']
cost.columns = ['source_id', 'dt', 'costs']

visit['start_ts'] = pd.to_datetime(visit['start_ts'])
visit['end_ts'] = pd.to_datetime(visit['end_ts'])
orders['buy_ts'] = pd.to_datetime(orders['buy_ts'])
cost['dt'] = pd.to_datetime(cost['dt'])

visit['session_duration_sec'] = (visit['end_ts'] - visit['start_ts']).dt.total_seconds()
visit.loc[visit['session_duration_sec'] < 0, 'session_duration_sec'] = 0

visit['session_date'] = visit['start_ts'].dt.date
visit['session_week'] = visit['start_ts'].dt.to_period('W')
visit['session_month'] = visit['start_ts'].dt.to_period('M')

# ---------- Chart 1: DAU ----------
dau_daily = visit.groupby('session_date')['uid'].nunique().reset_index()
dau_daily.columns = ['date', 'dau']

fig_daily = px.line(
    dau_daily, x='date', y='dau',
    title='Number of Daily Active Users',
    labels={'date': 'Date', 'dau': 'Number of Unique Visitors'}
)
export(fig_daily, "01_daily_active_users")

# ---------- Chart 2: Session duration distribution ----------
fig_session = px.histogram(
    visit[visit['session_duration_sec'] < 1800], x='session_duration_sec',
    nbins=60,
    title='Session Duration Distribution',
    labels={'session_duration_sec': 'Session Length (sec)', 'count': 'Number of Sessions'}
)
export(fig_session, "02_session_duration_distribution")

# ---------- Chart 3: Retention matrix ----------
first_activity = visit.groupby('uid')['session_month'].min().reset_index()
first_activity.columns = ['uid', 'first_activity_month']

visit_cohort = visit.merge(first_activity, on='uid')
visit_cohort['cohort_age'] = (
    (visit_cohort['session_month'].dt.year - visit_cohort['first_activity_month'].dt.year) * 12
    + visit_cohort['session_month'].dt.month - visit_cohort['first_activity_month'].dt.month
).astype('int64')

cohort_sizes = visit_cohort.groupby('first_activity_month')['uid'].nunique()
cohort_sizes.name = 'n_users'

cohort_activity = (
    visit_cohort.groupby(['first_activity_month', 'cohort_age'])['uid']
    .nunique().reset_index(name='n_active')
)
cohort_activity = cohort_activity.merge(
    cohort_sizes.rename('n_users').reset_index(), on='first_activity_month',
    how='left', validate='many_to_one'
)
cohort_activity['retention'] = cohort_activity['n_active'] / cohort_activity['n_users']

retention_pivot = cohort_activity.pivot_table(
    index='first_activity_month', columns='cohort_age', values='retention'
)
retention_pivot_copy = retention_pivot.copy()
retention_pivot_copy.index = retention_pivot_copy.index.astype(str)

retention_fig = px.imshow(
    retention_pivot_copy, text_auto='.0%', aspect='auto', color_continuous_scale='Blues',
    title='User Retention Matrix — Month x Cohort',
    labels={'x': 'Cohort Age (months)', 'y': 'First Activity Month (cohort)', 'color': 'Retention'}
)
export(retention_fig, "03_retention_matrix")

# ---------- Chart 4: Conversion time distribution ----------
first_visit = visit.groupby('uid')['start_ts'].min().reset_index()
first_visit.columns = ['uid', 'first_visit_ts']

first_order = orders.groupby('uid')['buy_ts'].min().reset_index()
first_order.columns = ['uid', 'first_order_ts']

conversion = first_order.merge(first_visit, on='uid', how='left')
conversion['conversion_days'] = (conversion['first_order_ts'] - conversion['first_visit_ts']).dt.days

fig_conv = px.histogram(
    conversion[conversion['conversion_days'] <= 30], x='conversion_days',
    nbins=31,
    title='Distribution of Days from First Visit to First Purchase (0-30 Days)',
    labels={'conversion_days': 'Conversion Days', 'count': 'Number of Users'}
)
export(fig_conv, "04_conversion_time_distribution")

# ---------- Chart 5: Monthly orders ----------
orders['order_month'] = orders['buy_ts'].dt.to_period('M')
order_per_month = orders.groupby('order_month')['uid'].count()

fig_order_per_m = px.bar(
    x=order_per_month.index.astype(str), y=order_per_month.values,
    title='Monthly Sales (Number of Orders)',
    labels={'x': 'Month', 'y': 'Number of Orders'}
)
export(fig_order_per_m, "05_monthly_orders")

# ---------- Chart 6: LTV cohort heatmap ----------
orders_ltv = orders.merge(first_visit, on='uid', how='left')
orders_ltv['cohort_month'] = orders_ltv['first_visit_ts'].dt.to_period('M')
orders_ltv['month_number'] = (orders_ltv['order_month'] - orders_ltv['cohort_month']).apply(lambda x: x.n)

size_of_buyers_cohort = (
    first_visit.assign(cohort_month=first_visit['first_visit_ts'].dt.to_period('M'))
    .groupby('cohort_month')['uid'].nunique().rename('n_buyers')
)

revenue_by_month_num = orders_ltv.groupby(['cohort_month', 'month_number'])['revenue'].sum().reset_index()
revenue_by_month_num = revenue_by_month_num.merge(size_of_buyers_cohort, on='cohort_month')
revenue_by_month_num['lifetime_value'] = (revenue_by_month_num['revenue'] / revenue_by_month_num['n_buyers']).round(5)

ltv_pivot = revenue_by_month_num.pivot_table(index='cohort_month', columns='month_number', values='lifetime_value')
ltv_cumulative = ltv_pivot.cumsum(axis=1)

ltv_heatmap = ltv_cumulative.copy().fillna(0)
ltv_heatmap.index = ltv_heatmap.index.astype(str)
ltv_heatmap.columns = [str(col) for col in ltv_heatmap.columns]

fig_heatmap = px.imshow(
    ltv_heatmap, text_auto=".2f", aspect="auto", color_continuous_scale="Blues",
    title="Cumulative LTV by Cohort and Month",
    labels={"x": "Month Number", "y": "Cohort Month", "color": "Cumulative LTV"}
)
fig_heatmap.update_layout(xaxis_title="Month Number", yaxis_title="Cohort Month",
                           coloraxis_colorbar=dict(title="Cumulative LTV"))
export(fig_heatmap, "06_ltv_cohort_heatmap")

# ---------- Chart 7: Marketing costs by source ----------
cost_by_source_id = cost.groupby('source_id')['costs'].sum().sort_values(ascending=False)

fig_costs = px.bar(
    x=cost_by_source_id.index.astype(str), y=cost_by_source_id.values,
    title='Marketing Costs by Source ID',
    labels={'x': 'Source ID', 'y': 'Costs ($)'}
)
export(fig_costs, "07_marketing_costs_by_source")

# ---------- Chart 8: Marketing costs by month ----------
cost['cost_month'] = cost['dt'].dt.to_period('M')
cost_by_month = cost.groupby('cost_month')['costs'].sum()

fig_costs_month = px.line(
    x=cost_by_month.index.astype(str), y=cost_by_month.values,
    title='Marketing Costs by Month', labels={'x': 'Month', 'y': 'Cost ($)'}, markers=True
)
export(fig_costs_month, "08_marketing_costs_by_month")

# ---------- Chart 9: CAC ----------
buyer_source = visit[['uid', 'source_id']].drop_duplicates(subset='uid')
buyers_with_source = first_order.merge(buyer_source, on='uid', how='left')
n_buyers_by_source = buyers_with_source.groupby('source_id')['uid'].nunique()
cac_by_source = (cost_by_source_id / n_buyers_by_source).dropna().sort_values()

fig_cac = px.bar(
    x=cac_by_source.index.astype(str), y=cac_by_source.values,
    title='Customer Acquisition Cost (CAC) by Source',
    labels={'x': 'Source ID', 'y': 'CAC ($)'}
)
export(fig_cac, "09_customer_acquisition_cost")

# ---------- Chart 10: Cumulative ROI ----------
cost_by_cohort_month = cost.groupby('cost_month')['costs'].sum()
cac_by_cohort_month = cost_by_cohort_month / cohort_sizes
roi = (ltv_cumulative.divide(cac_by_cohort_month, axis=0)).round(5)
roi_plot_data = roi.iloc[:, :6].copy()
roi_plot_data.index = roi_plot_data.index.astype(str)

fig_roi = px.line(
    roi_plot_data.T,
    title='Cumulative ROI by Cohort — First 6 Months (1.0 = Break-Even)',
    labels={'index': 'Cohort Age (months)', 'value': 'ROI', 'variable': 'Cohort (first visit month)'}
)
fig_roi.add_hline(y=1.0, line_dash='dash', line_color='red', annotation_text='Break-even (ROI = 1.0)')
fig_roi.update_xaxes(title='Cohort Age (months)')
fig_roi.update_yaxes(title='ROI')
export(fig_roi, "10_cumulative_roi_by_cohort")

# ---------- Chart 11: Sessions by device ----------
device_summary = visit.groupby('device').agg(
    n_sessions=('uid', 'count'), avg_session_sec=('session_duration_sec', 'mean')
).reset_index()
device_orders = orders.merge(visit[['uid', 'device']].drop_duplicates(subset='uid'), on='uid', how='left')
device_revenue = device_orders.groupby('device')['revenue'].agg(['mean', 'sum']).reset_index()
device_revenue.columns = ['device', 'avg_check', 'total_revenue']
device_summary = device_summary.merge(device_revenue, on='device')

fig_device = px.bar(
    device_summary, x='device', y='n_sessions',
    title='Number of Sessions by Device Type',
    labels={'device': 'Device', 'n_sessions': 'Number of Sessions'}
)
export(fig_device, "11_sessions_by_device")

print("\nAll 11 charts exported successfully.")
