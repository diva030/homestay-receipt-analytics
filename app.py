
from pathlib import Path

import pandas as pd
import streamlit as st
import plotly.express as px
import numpy as np

# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------
st.set_page_config(
    page_title="Homestay Receipt Analytics",
    page_icon="🏡",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_FILE = Path("receipt_extraction.csv")
MONTHLY_FILE = Path("monthly_receipt_analysis.csv")

REQUIRED_COLUMNS = {
    "receipt_no",
    "booking_date",
    "amount_rm",
    "payment_status",
}

# --------------------------------------------------
# PREMIUM BLACK & GOLD THEME
# --------------------------------------------------
st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(145deg, #10100F 0%, #191713 100%);
        color: #F5F0E5;
    }

   
.block-container {
    max-width: 100%;
    padding-top: 2rem;
    padding-bottom: 3rem;
    padding-left: 2.5rem;
    padding-right: 2.5rem;
}


    section[data-testid="stSidebar"] {
        background: #141310;
        border-right: 1px solid #4D4025;
    }

    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: #E5C579 !important;
    }

    h1, h2, h3 {
        color: #E5C579 !important;
        letter-spacing: -0.4px;
    }

    p, label {
        color: #E5DFD2;
    }

    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #28241B, #1C1A16);
        border: 1px solid #80662F;
        border-radius: 14px;
        padding: 20px 18px;
        box-shadow: 0 5px 18px rgba(0, 0, 0, 0.20);
    }

    div[data-testid="stMetricLabel"] {
        color: #D1C7B0 !important;
    }

    div[data-testid="stMetricValue"] {
        color: #E5C579 !important;
        font-weight: 700;
    }

    div[data-testid="stMetricDelta"] {
        color: #C6AE73 !important;
    }

    div[data-testid="stDataFrame"],
    div[data-testid="stTable"],
    div[data-testid="stPlotlyChart"] {
        border: 1px solid #403722;
        border-radius: 12px;
        overflow: hidden;
    }

    div[data-baseweb="select"] > div,
    div[data-baseweb="input"] > div {
        background-color: #211F1A;
        border-color: #66552D;
        border-radius: 8px;
    }

    .stButton > button,
    .stDownloadButton > button {
        background: linear-gradient(135deg, #E5C579, #B18A38);
        color: #17130A;
        border: none;
        border-radius: 9px;
        font-weight: 700;
    }

    .stButton > button:hover,
    .stDownloadButton > button:hover {
        background: #F2D995;
        color: #111111;
    }

    hr {
        border-color: #554426;
    }

    a {
        color: #E5C579 !important;
    }

    div[data-testid="stAlert"] {
        border-radius: 10px;
    }
    
/* Clearer dashboard section hierarchy */
div[data-testid="stVerticalBlock"] > div {
    gap: 0.85rem;
}

/* More breathing room around section headings */
h2 {
    margin-top: 1.4rem;
    margin-bottom: 0.7rem;
}

/* Keep the main title prominent */
h1 {
    font-size: 2.4rem !important;
    line-height: 1.2 !important;
}

/* Comfortable chart spacing */
div[data-testid="stPlotlyChart"] {
    margin-top: 0.4rem;
    margin-bottom: 1rem;
}
    </style>
    """,
    unsafe_allow_html=True,
)

# --------------------------------------------------
# HEADER
# --------------------------------------------------
st.title("🏡 Homestay Receipt Analytics")
st.caption(
    "PREMIUM BUSINESS DASHBOARD  |  "
    "Practice project using fictional training receipts only."
)

st.markdown(
    """
    <div style="
        background: linear-gradient(90deg, #282319, #191713);
        border-left: 4px solid #D8B45C;
        border-radius: 8px;
        padding: 14px 18px;
        margin: 12px 0 24px 0;
    ">
        <span style="color:#E5C579; font-weight:600;">
            BUSINESS OVERVIEW
        </span>
        <br>
        <span style="color:#D1C7B0;">
            Monitor receipt values, payment statuses and monthly trends.
        </span>
    </div>
    """,
    unsafe_allow_html=True,
)

st.caption(
    "Fictional training data — not actual AQ Wise or "
    "Astana Ria D'Raja financial records."
)

# --------------------------------------------------
# DATA LOADING
# --------------------------------------------------
@st.cache_data
def load_receipts(path_string: str, modified_time: float):
    data = pd.read_csv(path_string)

    missing = REQUIRED_COLUMNS - set(data.columns)
    if missing:
        raise ValueError(
            f"Missing required columns: {', '.join(sorted(missing))}"
        )

    data["receipt_no"] = data["receipt_no"].astype("string").str.strip()

    data["payment_status"] = (
        data["payment_status"]
        .astype("string")
        .str.strip()
        .str.upper()
    )

    data["booking_date"] = pd.to_datetime(
        data["booking_date"],
        format="%d/%m/%Y",
        errors="coerce",
    )

    data["amount_rm"] = pd.to_numeric(
        data["amount_rm"],
        errors="coerce",
    )

    data["booking_month"] = (
        data["booking_date"].dt.to_period("M").astype("string")
    )

    return data


@st.cache_data
def load_monthly(path_string: str, modified_time: float):
    return pd.read_csv(path_string)


if not DATA_FILE.exists():
    st.error(
        f"Cannot find {DATA_FILE.name}. "
        "Make sure the CSV file is included in the GitHub repository."
    )
    st.stop()

try:
    receipts = load_receipts(
        str(DATA_FILE),
        DATA_FILE.stat().st_mtime,
    )
except Exception as exc:
    st.error(f"Could not load receipt data: {exc}")
    st.stop()

if receipts.empty:
    st.info("The receipt file contains no rows.")
    st.stop()

# --------------------------------------------------
# DATA VALIDATION
# --------------------------------------------------
st.subheader("Data Quality")

validation_issues = []

if (
    receipts["receipt_no"].isna().any()
    or receipts["receipt_no"].eq("").any()
):
    validation_issues.append("One or more receipt numbers are missing.")

duplicate_mask = (
    receipts["receipt_no"].notna()
    & receipts["receipt_no"].ne("")
    & receipts["receipt_no"].duplicated(keep=False)
)

if duplicate_mask.any():
    duplicates = sorted(
        receipts.loc[duplicate_mask, "receipt_no"]
        .dropna()
        .unique()
        .tolist()
    )
    validation_issues.append(
        f"Duplicate receipt numbers found: {', '.join(duplicates)}"
    )

if receipts["booking_date"].isna().any():
    validation_issues.append(
        f"{int(receipts['booking_date'].isna().sum())} "
        "missing or invalid booking date(s)."
    )

if receipts["amount_rm"].isna().any():
    validation_issues.append(
        f"{int(receipts['amount_rm'].isna().sum())} "
        "missing or invalid amount(s)."
    )

if (receipts["amount_rm"].dropna() < 0).any():
    validation_issues.append(
        "Negative amounts found; review refunds or adjustments."
    )

known_statuses = {"PAID", "PENDING", "REFUNDED"}

unknown_statuses = sorted(
    set(receipts["payment_status"].dropna().tolist())
    - known_statuses
)

if receipts["payment_status"].isna().any() or unknown_statuses:
    validation_issues.append(
        f"Missing or unrecognised payment statuses: {unknown_statuses}"
    )

if validation_issues:
    st.warning("Some source data needs review.")
    for issue in validation_issues:
        st.write(f"- {issue}")
else:
    st.success(
        "Basic data checks passed: no missing core fields, duplicate "
        "receipt IDs, invalid dates or unrecognised statuses detected."
    )

# --------------------------------------------------
# SIDEBAR FILTERS
# --------------------------------------------------
st.sidebar.markdown("## ✨ Dashboard Filters")
st.sidebar.caption("Refine the receipt records displayed below.")

valid_dates = receipts["booking_date"].dropna()

if valid_dates.empty:
    st.sidebar.info("No valid booking dates are available.")
    start_date = end_date = None
else:
    min_date = valid_dates.min().date()
    max_date = valid_dates.max().date()

    date_range = st.sidebar.date_input(
        "Booking date range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date = end_date = None

statuses = sorted(
    receipts["payment_status"].dropna().unique().tolist()
)

selected_statuses = st.sidebar.multiselect(
    "Payment status",
    options=statuses,
    default=statuses,
)

search_term = st.sidebar.text_input(
    "Search receipt number",
    placeholder="e.g. AR001",
)

filtered = receipts.copy()

if start_date is not None and end_date is not None:
    filtered = filtered[
        filtered["booking_date"].dt.date.between(
            start_date,
            end_date,
        )
    ]

if selected_statuses:
    filtered = filtered[
        filtered["payment_status"].isin(selected_statuses)
    ]
else:
    filtered = filtered.iloc[0:0]

if search_term.strip():
    filtered = filtered[
        filtered["receipt_no"].str.contains(
            search_term.strip(),
            case=False,
            na=False,
        )
    ]

st.sidebar.divider()
st.sidebar.caption(
    f"Showing {len(filtered):,} of {len(receipts):,} receipts."
)

# --------------------------------------------------
# KPI CALCULATIONS
# --------------------------------------------------
amounts = filtered["amount_rm"].fillna(0)

total_value = amounts.sum()

paid_value = filtered.loc[
    filtered["payment_status"] == "PAID",
    "amount_rm",
].sum()

pending_value = filtered.loc[
    filtered["payment_status"] == "PENDING",
    "amount_rm",
].sum()

refunded_value = filtered.loc[
    filtered["payment_status"] == "REFUNDED",
    "amount_rm",
].sum()

receipt_count = len(filtered)

st.subheader("Financial Overview")

k1, k2, k3, k4 = st.columns(4)

k1.metric(
    "Total Receipt Value",
    f"RM {total_value:,.2f}",
    help=(
        "Sum of amounts in the currently filtered receipts; "
        "not necessarily accounting revenue."
    ),
)

k2.metric(
    "Marked Paid",
    f"RM {paid_value:,.2f}",
)

k3.metric(
    "Marked Pending",
    f"RM {pending_value:,.2f}",
)

k4.metric(
    "Receipt Count",
    f"{receipt_count:,}",
)

if refunded_value > 0:
    st.caption(f"Refunded amount in current selection: RM {refunded_value:,.2f}")

st.divider()

# --------------------------------------------------
# MONTHLY CHART
# --------------------------------------------------
st.subheader("Monthly Receipt Analysis")
st.caption("Receipt amounts grouped by booking month and payment status.")

if filtered.empty:
    st.info("No receipts match the selected filters.")
else:
    monthly_filtered = (
        filtered.dropna(subset=["booking_month"])
        .groupby("booking_month", as_index=False)
        .agg(
            total_receipt_value=("amount_rm", "sum"),
            receipt_count=("receipt_no", "count"),
        )
        .sort_values("booking_month")
    )

    monthly_status = (
        filtered.pivot_table(
            index="booking_month",
            columns="payment_status",
            values="amount_rm",
            aggfunc="sum",
            fill_value=0,
        )
        .reset_index()
    )

    monthly_filtered = monthly_filtered.merge(
        monthly_status,
        on="booking_month",
        how="left",
    )

    chart_cols = [
        col
        for col in ["PAID", "PENDING", "REFUNDED"]
        if col in monthly_filtered.columns
    ]

    if chart_cols:
        long_monthly = monthly_filtered.melt(
            id_vars=["booking_month"],
            value_vars=chart_cols,
            var_name="Payment Status",
            value_name="Amount (RM)",
        )

        gold_colors = {
            "PAID": "#E5C579",
            "PENDING": "#4D90C6",
            "REFUNDED": "#D98282",
        }

        fig = px.bar(
            long_monthly,
            x="booking_month",
            y="Amount (RM)",
            color="Payment Status",
            barmode="stack",
            title="Monthly Amounts by Payment Status",
            labels={
                "booking_month": "Booking Month",
                "Amount (RM)": "Amount (RM)",
            },
            color_discrete_map=gold_colors,
            template="plotly_dark",
        )

        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(
                family="Arial, sans-serif",
                color="#F5F0E5",
                size=12,
            ),
            title_font=dict(
                color="#E5C579",
                size=18,
            ),
            legend_title_font=dict(color="#E5C579"),
            xaxis=dict(
                title="Booking Month",
                showgrid=False,
                linecolor="#554426",
            ),
            yaxis=dict(
                title="Amount (RM)",
                gridcolor="#37332A",
                zerolinecolor="#554426",
                tickprefix="RM ",
                separatethousands=True,
            ),
            legend=dict(
                bgcolor="rgba(0,0,0,0)",
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
            ),
            margin=dict(l=15, r=15, t=80, b=15),
            bargap=0.35,
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
            config={"displayModeBar": False},
        )
    else:
        st.info("No recognised payment statuses are available to chart.")

    # --------------------------------------------------
    # MONTHLY SUMMARY TABLE
    # --------------------------------------------------
    st.subheader("Monthly Summary")

    display_monthly = monthly_filtered.rename(
        columns={
            "booking_month": "Booking Month",
            "receipt_count": "Receipt Count",
            "total_receipt_value": "Total Receipt Value (RM)",
            "PAID": "Paid (RM)",
            "PENDING": "Pending (RM)",
            "REFUNDED": "Refunded (RM)",
        }
    )

    st.dataframe(
        display_monthly,
        use_container_width=True,
        hide_index=True,
    )

# --------------------------------------------------
# FUTURE INSIGHTS & EXPLORATORY OUTLOOK
# --------------------------------------------------
st.divider()
st.subheader("🔮 Future Insights")
st.caption(
    "Exploratory estimates based on available receipt data. "
    "These are not guaranteed forecasts."
)

if filtered.empty:
    st.info("Select receipts using the sidebar filters to generate insights.")
else:
    insight_left, insight_right = st.columns(2)

    # Payment risk insight
    pending_total = filtered.loc[
        filtered["payment_status"] == "PENDING",
        "amount_rm",
    ].sum()

    valid_amounts = filtered["amount_rm"].dropna()
    total_amount = valid_amounts.sum()

    with insight_left:
        st.markdown("### 💳 Payment Outlook")

        if pending_total > 0:
            pending_share = (
                pending_total / total_amount * 100
                if total_amount > 0
                else 0
            )

            st.metric(
                "Amount Still Pending",
                f"RM {pending_total:,.2f}",
            )

            st.write(
                f"Pending amounts represent approximately "
                f"{pending_share:.1f}% of the selected receipt value."
            )

            st.info(
                "Suggested action: review pending receipts and "
                "confirm payment status before taking further action."
            )
        else:
            st.success(
                "No positive pending amount appears in the selected records."
            )

    # Monthly trend and exploratory estimate
    with insight_right:
        st.markdown("### 📈 Revenue Trend")

        monthly_values = (
            filtered.dropna(subset=["booking_month"])
            .groupby("booking_month")["amount_rm"]
            .sum()
            .sort_index()
        )

        if len(monthly_values) >= 2:
            previous_value = float(monthly_values.iloc[-2])
            latest_value = float(monthly_values.iloc[-1])

            if previous_value > 0:
                change_pct = (
                    (latest_value - previous_value)
                    / previous_value
                    * 100
                )

                st.metric(
                    "Latest Month vs Previous Month",
                    f"{change_pct:+.1f}%",
                )
            else:
                st.write(
                    "The previous month had zero or negative value, "
                    "so a percentage comparison is not meaningful."
                )

            if latest_value > previous_value:
                st.write(
                    "Receipt value increased compared with the previous month."
                )
            elif latest_value < previous_value:
                st.write(
                    "Receipt value decreased compared with the previous month."
                )
            else:
                st.write(
                    "Receipt value was unchanged compared with the previous month."
                )
        else:
            st.info(
                "At least two months of receipt data are needed "
                "to compare monthly values."
            )

    st.markdown("### 🗓️ Next-Month Receipt Value Estimate")

    monthly_values = (
        filtered.dropna(subset=["booking_month"])
        .groupby("booking_month")["amount_rm"]
        .sum()
        .sort_index()
    )

    if len(monthly_values) >= 3:
        # Fit a simple straight-line trend to monthly totals.
        # This is an exploratory estimate, not a robust forecast.
        y = monthly_values.to_numpy(dtype=float)
        x = np.arange(len(y), dtype=float)

        slope, intercept = np.polyfit(x, y, 1)
        estimate = max(0.0, float(slope * len(y) + intercept))

        last_month = pd.Period(
            str(monthly_values.index[-1]),
            freq="M",
        )
        next_month = last_month + 1

        st.metric(
            f"Indicative estimate for {next_month}",
            f"RM {estimate:,.2f}",
        )

        st.caption(
            "Method: straight-line trend fitted to monthly receipt totals. "
            "This simple method does not account for seasonality, future "
            "bookings, cancellations, or changes in prices."
        )

        st.warning(
            "Use this estimate for practice and exploration only. "
            "Three or a few monthly observations are not enough to "
            "establish a dependable business forecast."
        )
    else:
        st.info(
            "Collect at least three distinct months of receipt data "
            "to display this exploratory estimate. More historical "
            "data will be needed for a meaningful forecast."
        )

    st.markdown("### 💡 Suggested Next Actions")

    if pending_total > 0:
        st.write(
            "- Review pending receipts and reconcile them with "
            "confirmed payment records."
        )

    if len(monthly_values) >= 2:
        if monthly_values.iloc[-1] < monthly_values.iloc[-2]:
            st.write(
                "- Review recent booking activity and investigate "
                "possible reasons for the monthly decline."
            )
        elif monthly_values.iloc[-1] > monthly_values.iloc[-2]:
            st.write(
                "- Review which bookings or periods contributed to "
                "the increase; do not assume the trend will continue."
            )

    st.write(
        "- Continue checking extracted amounts against source receipts "
        "and collect more months of verified data before relying on forecasts."
    )

# --------------------------------------------------
# HISTORICAL VALUES + NEXT-MONTH ESTIMATE CHART
# --------------------------------------------------
st.markdown("### 📊 Revenue Outlook")
st.caption(
    "Historical receipt values compared with a simple trend estimate."
)

forecast_monthly = (
    filtered.dropna(subset=["booking_month"])
    .groupby("booking_month")["amount_rm"]
    .sum()
    .sort_index()
)

if len(forecast_monthly) >= 3:
    history = forecast_monthly.reset_index()
    history.columns = ["Month", "Amount (RM)"]
    history["Type"] = "Historical"

    values = forecast_monthly.to_numpy(dtype=float)
    x_values = np.arange(len(values), dtype=float)
    slope, intercept = np.polyfit(x_values, values, 1)

    estimate = max(
        0.0,
        float(slope * len(values) + intercept),
    )

    last_month = pd.Period(
        str(forecast_monthly.index[-1]),
        freq="M",
    )
    next_month = str(last_month + 1)

    estimate_row = pd.DataFrame({
        "Month": [next_month],
        "Amount (RM)": [estimate],
        "Type": ["Indicative estimate"],
    })

    chart_data = pd.concat(
        [history, estimate_row],
        ignore_index=True,
    )

    outlook_fig = px.bar(
        chart_data,
        x="Month",
        y="Amount (RM)",
        color="Type",
        color_discrete_map={
            "Historical": "#D8B45C",
            "Indicative estimate": "#6CA6D9",
        },
        template="plotly_dark",
        text="Amount (RM)",
        title="Monthly Receipt Value: History vs Estimate",
    )

    outlook_fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#F5F0E5"),
        title_font=dict(color="#E5C579", size=18),
        xaxis=dict(title="Month", showgrid=False),
        yaxis=dict(
            title="Amount (RM)",
            gridcolor="#37332A",
            tickprefix="RM ",
        ),
        legend_title_text="Data type",
        margin=dict(l=15, r=15, t=70, b=15),
    )

    outlook_fig.update_traces(
        texttemplate="RM %{text:,.0f}",
        textposition="outside",
        cliponaxis=False,
    )

    st.plotly_chart(
        outlook_fig,
        use_container_width=True,
        config={"displayModeBar": False},
    )

    st.caption(
        "The estimate uses a straight-line trend, not confirmed future bookings. "
        "Actual results may differ substantially."
    )
else:
    st.info(
        "At least three distinct months of receipt data are needed "
        "to display this exploratory outlook chart."
    )

# --------------------------------------------------
# EXECUTIVE INSIGHTS
# --------------------------------------------------
st.divider()
st.subheader("💼 Executive Insights")
st.caption(
    "An automatically generated summary of the currently selected "
    "fictional receipt records."
)

if filtered.empty:
    st.info("Select receipts using the sidebar filters to generate insights.")
else:
    insight_total = filtered["amount_rm"].fillna(0).sum()

    insight_paid = filtered.loc[
        filtered["payment_status"] == "PAID",
        "amount_rm",
    ].fillna(0).sum()

    insight_pending = filtered.loc[
        filtered["payment_status"] == "PENDING",
        "amount_rm",
    ].fillna(0).sum()

    insight_refunded = filtered.loc[
        filtered["payment_status"] == "REFUNDED",
        "amount_rm",
    ].fillna(0).sum()

    insight_count = len(filtered)

    paid_share = (
        insight_paid / insight_total * 100
        if insight_total > 0
        else 0
    )

    pending_share = (
        insight_pending / insight_total * 100
        if insight_total > 0
        else 0
    )

    # Premium summary panel
    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, #282319, #191713);
            border: 1px solid #80662F;
            border-left: 5px solid #E5C579;
            border-radius: 12px;
            padding: 22px;
            margin: 10px 0 18px 0;
        ">
            <div style="
                color: #E5C579;
                font-size: 19px;
                font-weight: 700;
                margin-bottom: 12px;
            ">
                Executive Summary
            </div>
            <div style="color: #F5F0E5; line-height: 1.8;">
                The current selection contains
                <b>{insight_count:,} receipt(s)</b> with a combined
                receipt value of <b>RM {insight_total:,.2f}</b>.
                An amount of <b>RM {insight_paid:,.2f}</b> is marked paid,
                while <b>RM {insight_pending:,.2f}</b> is marked pending.
                {f" Refunds recorded in this selection total RM {insight_refunded:,.2f}." if insight_refunded > 0 else ""}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    summary_col1, summary_col2 = st.columns(2)

    with summary_col1:
        st.markdown("### 💰 Payment Performance")

        st.write(
            f"**Paid share of selected receipt value:** "
            f"{paid_share:.1f}%"
        )

        st.write(
            f"**Pending share of selected receipt value:** "
            f"{pending_share:.1f}%"
        )

        if insight_pending > 0:
            st.warning(
                "Action: review pending receipts and verify their "
                "payment status against the source records."
            )
        else:
            st.success(
                "No positive pending amount appears in the current selection."
            )

    with summary_col2:
        st.markdown("### 📊 Monthly Performance")

        executive_monthly = (
            filtered.dropna(subset=["booking_month"])
            .groupby("booking_month")["amount_rm"]
            .sum()
            .sort_index()
        )

        if len(executive_monthly) >= 2:
            previous_total = float(executive_monthly.iloc[-2])
            latest_total = float(executive_monthly.iloc[-1])

            st.write(
                f"**Previous month:** RM {previous_total:,.2f}"
            )

            st.write(
                f"**Latest month:** RM {latest_total:,.2f}"
            )

            if latest_total > previous_total:
                st.success(
                    "The latest month's receipt value is higher "
                    "than the previous month's."
                )
            elif latest_total < previous_total:
                st.warning(
                    "The latest month's receipt value is lower "
                    "than the previous month's. Investigate possible "
                    "changes in booking activity."
                )
            else:
                st.info(
                    "Receipt values are unchanged between these months."
                )
        else:
            st.info(
                "At least two distinct months are needed for a "
                "month-to-month comparison."
            )

    st.caption(
        "These observations describe the selected practice data. "
        "They do not establish the cause of a trend or guarantee future results."
    )

# --------------------------------------------------
# RECEIPT DETAILS
# --------------------------------------------------
st.divider()
st.subheader("Receipt Details")
st.caption("Detailed records based on the filters selected in the sidebar.")

display_cols = [
    col
    for col in [
        "receipt_no",
        "booking_date",
        "check_in",
        "check_out",
        "customer",
        "amount_rm",
        "payment_status",
        "payment_method",
        "review_status",
    ]
    if col in filtered.columns
]

details = filtered[display_cols].copy()

if "booking_date" in details.columns:
    details["booking_date"] = (
        details["booking_date"].dt.strftime("%d/%m/%Y")
    )

if "amount_rm" in details.columns:
    details["amount_rm"] = details["amount_rm"].map(
        lambda value: f"RM {value:,.2f}" if pd.notna(value) else "—"
    )

details = details.rename(
    columns={
        "receipt_no": "Receipt Number",
        "booking_date": "Booking Date",
        "check_in": "Check-in",
        "check_out": "Check-out",
        "customer": "Customer",
        "amount_rm": "Amount",
        "payment_status": "Payment Status",
        "payment_method": "Payment Method",
        "review_status": "Review Status",
    }
)

st.dataframe(
    details,
    use_container_width=True,
    hide_index=True,
)

# --------------------------------------------------
# CSV DOWNLOAD
# --------------------------------------------------
st.download_button(
    label="⬇️ Download Filtered Receipts as CSV",
    data=filtered.to_csv(index=False).encode("utf-8-sig"),
    file_name="filtered_receipts.csv",
    mime="text/csv",
)

# --------------------------------------------------
# VALIDATION AND MONTHLY CROSS-CHECK
# --------------------------------------------------
st.divider()

with st.expander("Data Validation & Monthly Cross-check"):
    if MONTHLY_FILE.exists():
        try:
            monthly_existing = load_monthly(
                str(MONTHLY_FILE),
                MONTHLY_FILE.stat().st_mtime,
            )

            st.write("Found `monthly_receipt_analysis.csv`.")

            st.caption(
                "This compares the original monthly summary with the "
                "receipt-level data. Filtered charts are recalculated "
                "from receipt-level records."
            )

            if {
                "booking_month",
                "total_receipt_value",
            }.issubset(monthly_existing.columns):

                detail_monthly = (
                    receipts.dropna(subset=["booking_month"])
                    .groupby("booking_month", as_index=False)["amount_rm"]
                    .sum()
                    .rename(columns={"amount_rm": "detail_total"})
                )

                summary_check = monthly_existing[
                    ["booking_month", "total_receipt_value"]
                ].copy()

                summary_check["booking_month"] = (
                    summary_check["booking_month"].astype(str)
                )

                comparison = summary_check.merge(
                    detail_monthly,
                    on="booking_month",
                    how="outer",
                )

                comparison["matches"] = (
                    comparison["total_receipt_value"].fillna(0).round(2)
                    == comparison["detail_total"].fillna(0).round(2)
                )

                st.dataframe(
                    comparison,
                    use_container_width=True,
                    hide_index=True,
                )

                if comparison["matches"].all():
                    st.success(
                        "Monthly totals match between the summary "
                        "CSV and receipt-level data."
                    )
                else:
                    st.warning(
                        "Monthly totals differ. Check both files "
                        "before relying on the summary."
                    )
            else:
                st.warning(
                    "The monthly summary file does not contain "
                    "the expected columns."
                )

        except Exception as exc:
            st.warning(
                f"Could not read or cross-check monthly summary: {exc}"
            )
    else:
        st.info(
            "`monthly_receipt_analysis.csv` was not found. "
            "The dashboard continues to work using "
            "`receipt_extraction.csv`."
        )

# --------------------------------------------------
# FOOTER
# --------------------------------------------------
st.divider()

st.markdown(
    """
    <div style="text-align:center; padding:12px 0 4px 0;">
        <div style="color:#E5C579; font-weight:600;">
            HOMESTAY RECEIPT ANALYTICS
        </div>
        <div style="color:#AFA696; font-size:12px; margin-top:6px;">
            Premium Practice Dashboard · Fictional Training Data Only
        </div>
        <div style="color:#807866; font-size:11px; margin-top:4px;">
            Verify all extracted values against source documents.
            Do not upload real customer receipts to unapproved tools.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)
