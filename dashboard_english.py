import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# ============================================
# Page config (must be the first Streamlit command)
# ============================================
st.set_page_config(
    page_title="Sales Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# Data cleaning function
# ============================================
@st.cache_data
def clean_data(df):
    df['Order Date'] = pd.to_datetime(df['Order Date'])
    df = df.drop_duplicates()

    df['Region'] = df['Region'].astype(str).str.strip().str.title()
    df['Region'] = df['Region'].replace('Nan', np.nan)
    df = df.dropna(subset=['Region'])

    df['Sales'] = df['Sales'].fillna(df['Sales'].median())
    df['Profit_Status'] = np.where(df['Profit'] < 0, 'Loss', 'Profit')

    return df

# ============================================
# Load data
# ============================================
df = pd.read_csv('sales_data.csv')
df = clean_data(df)

# ============================================
# Title and subtitle
# ============================================
st.markdown("""
    <h1 style='text-align: center; color: #2563EB;'>
        📊 Sales Analytics Dashboard
    </h1>
    <p style='text-align: center; color: gray; font-size: 16px;'>
        Sales performance analysis by region, category, and time period
    </p>
""", unsafe_allow_html=True)
st.divider()

# ============================================
# Sidebar filters
# ============================================
st.sidebar.header("🔎 Filters")

selected_regions = st.sidebar.multiselect(
    "Select Region",
    options=sorted(df['Region'].unique()),
    default=sorted(df['Region'].unique())
)

selected_categories = st.sidebar.multiselect(
    "Select Category",
    options=sorted(df['Category'].unique()),
    default=sorted(df['Category'].unique())
)

min_date = df['Order Date'].min()
max_date = df['Order Date'].max()

selected_date_range = st.sidebar.date_input(
    "Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

# ============================================
# Apply filters
# ============================================
filtered_df = df[
    (df['Region'].isin(selected_regions)) &
    (df['Category'].isin(selected_categories))
]

if len(selected_date_range) == 2:
    start_date, end_date = selected_date_range
    filtered_df = filtered_df[
        (filtered_df['Order Date'] >= pd.to_datetime(start_date)) &
        (filtered_df['Order Date'] <= pd.to_datetime(end_date))
    ]

# ============================================
# Stop early if no data matches the filters
# ============================================
if filtered_df.empty:
    st.warning("⚠️ No data available for the selected filters. Please adjust your filters.")
    st.stop()

# ============================================
# Shared Plotly theme
# ============================================
PLOTLY_TEMPLATE = "plotly_white"

# ============================================
# KPI Cards
# ============================================
col1, col2, col3, col4 = st.columns(4)

total_sales = filtered_df['Sales'].sum()
total_profit = filtered_df['Profit'].sum()
avg_sales = filtered_df['Sales'].mean()
loss_percentage = (filtered_df['Profit'] < 0).mean() * 100

col1.metric("💰 Total Sales", f"${total_sales:,.0f}")
col2.metric("📈 Total Profit", f"${total_profit:,.0f}")
col3.metric("🧾 Avg. Sale per Order", f"${avg_sales:,.0f}")
col4.metric("⚠️ Loss-Making Orders", f"{loss_percentage:.1f}%")

st.divider()

# ============================================
# Chart 1: Monthly sales trend
# ============================================
with st.container(border=True):
    st.subheader("📅 Monthly Sales Trend")
    filtered_df['Month'] = filtered_df['Order Date'].dt.to_period('M').astype(str)
    monthly_sales = filtered_df.groupby('Month')['Sales'].sum().reset_index()

    fig1 = px.line(monthly_sales, x='Month', y='Sales', markers=True,
                    template=PLOTLY_TEMPLATE)
    fig1.update_traces(line_color='#2563EB')
    st.plotly_chart(fig1, use_container_width=True)

# ============================================
# Chart 2 & 3: Category + Region
# ============================================
col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        st.subheader("🏷️ Sales by Category")
        cat_sales = filtered_df.groupby('Category')['Sales'].sum().reset_index()
        cat_sales = cat_sales.sort_values('Sales', ascending=False)

        fig2 = px.bar(cat_sales, x='Category', y='Sales', color='Category',
                       template=PLOTLY_TEMPLATE)
        st.plotly_chart(fig2, use_container_width=True)

with col2:
    with st.container(border=True):
        st.subheader("📦 Profit Distribution by Region")
        fig3 = px.box(filtered_df, x='Region', y='Profit', color='Region',
                       template=PLOTLY_TEMPLATE)
        st.plotly_chart(fig3, use_container_width=True)

# ============================================
# Chart 4 & 5: Pie + Scatter
# ============================================
col3, col4 = st.columns(2)

with col3:
    with st.container(border=True):
        st.subheader("🥧 Sales Share by Region")
        region_sales = filtered_df.groupby('Region')['Sales'].sum().reset_index()

        fig4 = px.pie(region_sales, names='Region', values='Sales',
                       template=PLOTLY_TEMPLATE, hole=0.4)
        st.plotly_chart(fig4, use_container_width=True)

with col4:
    with st.container(border=True):
        st.subheader("🔗 Sales vs. Profit")
        fig5 = px.scatter(
            filtered_df,
            x='Sales',
            y='Profit',
            color='Category',
            hover_data=['Product Name'],
            template=PLOTLY_TEMPLATE
        )
        st.plotly_chart(fig5, use_container_width=True)

# ============================================
# Pivot table
# ============================================
with st.container(border=True):
    st.subheader("📋 Sales Table: Category × Region")
    pivot_table = filtered_df.pivot_table(
        values='Sales',
        index='Category',
        columns='Region',
        aggfunc='sum',
        fill_value=0
    )
    st.dataframe(pivot_table.style.format("{:,.0f}"), use_container_width=True)

# ============================================
# Top products
# ============================================
with st.container(border=True):
    st.subheader("🔥 Top Products")
    top_products_count = filtered_df['Product Name'].value_counts().head(10).reset_index()
    top_products_count.columns = ['Product Name', 'Order Count']

    col1, col2 = st.columns(2)

    with col1:
        st.dataframe(top_products_count, use_container_width=True)

    with col2:
        fig6 = px.bar(
            top_products_count,
            x='Order Count',
            y='Product Name',
            orientation='h',
            template=PLOTLY_TEMPLATE
        )
        fig6.update_layout(yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig6, use_container_width=True)

# ============================================
# Automated insights
# ============================================
st.divider()
st.subheader("🔍 Key Insights")

best_region = filtered_df.groupby('Region')['Profit'].sum().idxmax()
best_region_profit = filtered_df.groupby('Region')['Profit'].sum().max()

worst_category = filtered_df.groupby('Category')['Profit'].mean().idxmin()
worst_category_profit = filtered_df.groupby('Category')['Profit'].mean().min()

best_product = filtered_df.groupby('Product Name')['Sales'].sum().idxmax()

correlation = filtered_df[['Sales', 'Profit']].corr().iloc[0, 1]

col1, col2 = st.columns(2)

with col1:
    st.info(f"📈 **Most Profitable Region:** {best_region} (Total Profit: ${best_region_profit:,.0f})")
    st.info(f"🏆 **Top-Selling Product:** {best_product}")

with col2:
    st.warning(f"⚠️ **Lowest Avg. Profit Category:** {worst_category} (${worst_category_profit:,.0f})")
    st.info(f"🔗 **Sales–Profit Correlation:** {correlation:.2f}")
