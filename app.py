from pathlib import Path
import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(
    page_title="Homestay Receipt Analytics",
    page_icon="🏡",
    layout="wide",
)

DATA_FILE = Path("receipt_extraction.csv")
MONTHLY_FILE = Path("monthly_receipt_analysis.csv")

st.title("🏡 Homestay Receipt Analytics")
st.caption("Practice dashboard using fictional training receipts — not real AQ Wise or Astana Ria D'Raja financial data.")

REQUIRED_COLUMNS = {"receipt_no", "booking_date", "amount_rm", "payment_status"}

@st.cache_data
def load_receipts(path_string: str, modified_time: float):
    data = pd.read_csv(path_string)
    missing = REQUIRED_COLUMNS - set(data.columns)
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")

    data["receipt_no"] = data["receipt_no"].astype("string").str.strip()
    data["payment_status"] = (
        data["payment_status"].astype("string").str.strip().str.upper()
    )
    data["booking_date"] = pd.to_datetime(
        data["booking_date"], format="%d/%m/%Y", errors="coerce"
    )
    data["amount_rm"] = pd.to_numeric(data["amount_rm"], errors="coerce")
    data["booking_month"] = data["booking_date"].dt.to_period("M").astype("string")
    return data

@st.cache_data
def load_monthly(path_string: str, modified_time: float):
    return pd.read_csv(path_string)

if not DATA_FILE.exists():
    st.error(f"Can't find {DATA_FILE.name}. Save this app.py in the same folder as your CSV files.")
    st.code("Get-ChildItem")
    st.stop()

try:
    receipts = load_receipts(str(DATA_FILE), DATA_FILE.stat().st_mtime)
except Exception as exc:
    st.error(f"Could not load receipt data: {exc}")
    st.stop()

# Validation of source data
validation_issues = []
if receipts["receipt_no"].isna().any() or receipts["receipt_no"].eq("").any():
    validation_issues.append("One or more receipt numbers are missing.")
duplicate_mask = (
    receipts["receipt_no"].notna()
    & receipts["receipt_no"].ne("")
    & receipts["receipt_no"].duplicated(keep=False)
)
if duplicate_mask.any():
    dupes = sorted(receipts.loc[duplicate_mask, "receipt_no"].dropna().unique().tolist())
    validation_issues.append(f"Duplicate receipt numbers found: {', '.join(dupes)}")
if receipts["booking_date"].isna().any():
    validation_issues.append(f"{int(receipts['booking_date'].isna().sum())} missing/invalid booking date(s).")
if receipts["amount_rm"].isna().any():
    validation_issues.append(f"{int(receipts['amount_rm'].isna().sum())} missing/invalid amount(s).")
if (receipts["amount_rm"].dropna() < 0).any():
    validation_issues.append("Negative amounts found; review refunds/adjustments.")
known_statuses = {"PAID", "PENDING", "REFUNDED"}
unknown_statuses = sorted(set(receipts["payment_status"].dropna().tolist()) - known_statuses)
if receipts["payment_status"].isna().any() or unknown_statuses:
    validation_issues.append(f"Missing/unrecognised payment status(es): {unknown_statuses}")

if validation_issues:
    st.warning("Source data needs review before relying on the results.")
    for issue in validation_issues:
        st.write(f"- {issue}")
else:
    st.success("Basic data checks passed: required columns exist; no missing core fields, duplicate receipt IDs, invalid dates, or unrecognised statuses detected.")

if receipts.empty:
    st.info("The receipt file contains no rows.")
    st.stop()

# Filters
st.sidebar.header("Filters")
valid_dates = receipts["booking_date"].dropna()
if valid_dates.empty:
    st.sidebar.info("No valid booking dates available for date filtering.")
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
        start_date = end_date = date_range

statuses = sorted(receipts["payment_status"].dropna().unique().tolist())
selected_statuses = st.sidebar.multiselect(
    "Payment status",
    options=statuses,
    default=statuses,
)
search_term = st.sidebar.text_input("Search receipt number", placeholder="e.g. AR001")

filtered = receipts.copy()
if start_date is not None and end_date is not None:
    filtered = filtered[
        filtered["booking_date"].dt.date.between(start_date, end_date)
    ]
if selected_statuses:
    filtered = filtered[filtered["payment_status"].isin(selected_statuses)]
else:
    filtered = filtered.iloc[0:0]
if search_term.strip():
    filtered = filtered[
        filtered["receipt_no"].str.contains(search_term.strip(), case=False, na=False)
    ]

# Financial KPIs based on current filters
amounts = filtered["amount_rm"].fillna(0)
total_value = amounts.sum()
paid_value = filtered.loc[filtered["payment_status"] == "PAID", "amount_rm"].sum()
pending_value = filtered.loc[filtered["payment_status"] == "PENDING", "amount_rm"].sum()
refunded_value = filtered.loc[filtered["payment_status"] == "REFUNDED", "amount_rm"].sum()
receipt_count = len(filtered)

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total receipt value", f"RM {total_value:,.2f}", help="Sum of amounts in the currently filtered receipts; not necessarily accounting revenue.")
k2.metric("Marked paid", f"RM {paid_value:,.2f}")
k3.metric("Marked pending", f"RM {pending_value:,.2f}")
k4.metric("Receipts", f"{receipt_count:,}")

st.divider()

# Monthly breakdown from filtered detail records
st.subheader("Monthly receipt value")
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
    monthly_filtered = monthly_filtered.merge(monthly_status, on="booking_month", how="left")

    chart_cols = [c for c in ["PAID", "PENDING", "REFUNDED"] if c in monthly_filtered.columns]
    if chart_cols:
        long_monthly = monthly_filtered.melt(
            id_vars=["booking_month"],
            value_vars=chart_cols,
            var_name="Payment status",
            value_name="Amount (RM)",
        )
        fig = px.bar(
            long_monthly,
            x="booking_month",
            y="Amount (RM)",
            color="Payment status",
            barmode="stack",
            title="Monthly amounts by payment status",
            labels={"booking_month": "Booking month"},
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No recognised payment statuses available to chart.")

    st.subheader("Monthly summary")
    display_monthly = monthly_filtered.rename(columns={
        "booking_month": "Booking month",
        "receipt_count": "Receipt count",
        "total_receipt_value": "Total receipt value (RM)",
        "PAID": "Paid (RM)",
        "PENDING": "Pending (RM)",
        "REFUNDED": "Refunded (RM)",
    })
    st.dataframe(display_monthly, use_container_width=True, hide_index=True)

st.subheader("Receipt details")
display_cols = [
    col for col in [
        "receipt_no", "booking_date", "check_in", "check_out",
        "customer", "amount_rm", "payment_status", "payment_method", "review_status"
    ] if col in filtered.columns
]
details = filtered[display_cols].copy()
if "booking_date" in details.columns:
    details["booking_date"] = details["booking_date"].dt.strftime("%d/%m/%Y")
if "amount_rm" in details.columns:
    details = details.rename(columns={"amount_rm": "amount_rm"})
st.dataframe(details, use_container_width=True, hide_index=True)

st.download_button(
    "Download filtered receipts as CSV",
    data=filtered.to_csv(index=False).encode("utf-8-sig"),
    file_name="filtered_receipts.csv",
    mime="text/csv",
)

# Cross-check against previously generated monthly analysis for the unfiltered dataset
st.divider()
with st.expander("Validation and monthly-file cross-check"):
    if MONTHLY_FILE.exists():
        try:
            monthly_existing = load_monthly(str(MONTHLY_FILE), MONTHLY_FILE.stat().st_mtime)
            st.write("Found `monthly_receipt_analysis.csv`.")
            st.caption("This is a cross-check against the earlier summary. Filtered charts above are recalculated from receipt-level data.")
            if {"booking_month", "total_receipt_value"}.issubset(monthly_existing.columns):
                detail_monthly = (
                    receipts.dropna(subset=["booking_month"])
                    .groupby("booking_month", as_index=False)["amount_rm"]
                    .sum()
                    .rename(columns={"amount_rm": "detail_total"})
                )
                summary_check = monthly_existing[["booking_month", "total_receipt_value"]].copy()
                summary_check["booking_month"] = summary_check["booking_month"].astype(str)
                comparison = summary_check.merge(
                    detail_monthly, on="booking_month", how="outer"
                )
                comparison["matches"] = (
                    comparison["total_receipt_value"].fillna(0).round(2)
                    == comparison["detail_total"].fillna(0).round(2)
                )
                st.dataframe(comparison, use_container_width=True, hide_index=True)
                if comparison["matches"].all():
                    st.success("Monthly totals match between the summary CSV and the receipt-level data.")
                else:
                    st.warning("Monthly totals differ. Check the two files and investigate before relying on the summary.")
            else:
                st.warning("The monthly summary file doesn't contain the expected columns.")
        except Exception as exc:
            st.warning(f"Could not read/cross-check monthly summary: {exc}")
    else:
        st.warning("monthly_receipt_analysis.csv wasn't found. The dashboard still works from receipt_extraction.csv.")

st.caption("Training dashboard only. Always verify extracted amounts against source documents. Do not use real customer receipts in unapproved tools.")
