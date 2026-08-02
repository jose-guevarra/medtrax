import re

import altair as alt
import pandas as pd
import streamlit as st

from core.auth import get_user_id
from core.config import load_config
from core.s3_upload import list_user_documents

config = load_config()
st.title("Health Graph")

user_id = get_user_id(config)
documents = list_user_documents(config, user_id)

if not documents:
    st.info("You haven't uploaded any documents yet.")
    st.stop()


def _description(doc: dict) -> str:
    provider = doc["provider_name"]
    if provider and doc["provider_type"]:
        provider = f"{provider} ({doc['provider_type']})"
    parts = [part for part in (doc["document_type"], provider) if part]
    return " — ".join(parts) if parts else doc["name"]


def _amount(doc: dict) -> float | None:
    raw = doc["amount_paid"]
    if not raw:
        return None
    match = re.search(r"\d[\d,]*\.?\d*", raw)
    if not match:
        return None
    try:
        return float(match.group().replace(",", ""))
    except ValueError:
        return None


df = pd.DataFrame(documents)
df["date"] = pd.to_datetime(df["visit_date"], errors="coerce", format="mixed")
df["description"] = df.apply(_description, axis=1)
df["amount"] = df.apply(_amount, axis=1)
df["amount_display"] = df["amount"].apply(lambda v: "not recorded" if pd.isna(v) else f"${v:,.2f}")
df["amount_size"] = df["amount"].fillna(0.0)

dated = df[df["date"].notna()].sort_values("date")
undated = df[df["date"].isna()]

if dated.empty:
    st.info("None of your documents have a usable date yet, so a timeline can't be drawn.")
else:
    chart = (
        alt.Chart(dated)
        .mark_circle(opacity=0.75)
        .encode(
            x=alt.X("date:T", title="Date"),
            y=alt.value(0),
            size=alt.Size(
                "amount_size:Q",
                title="Out-of-pocket cost",
                scale=alt.Scale(range=[80, 1200]),
                legend=alt.Legend(format="$.2f"),
            ),
            color=alt.Color("document_type:N", title="Type"),
            tooltip=[
                alt.Tooltip("date:T", title="Date"),
                alt.Tooltip("description:N", title="Description"),
                alt.Tooltip("amount_display:N", title="Cost"),
            ],
        )
        .properties(height=180)
        .interactive()
    )
    st.altair_chart(chart, use_container_width=True)

    st.dataframe(
        dated[["date", "description", "amount_display"]].rename(
            columns={"date": "Date", "description": "Description", "amount_display": "Cost"}
        ),
        hide_index=True,
        use_container_width=True,
    )

if not undated.empty:
    with st.expander(f"{len(undated)} document(s) without a usable date"):
        st.dataframe(
            undated[["name", "description"]].rename(columns={"name": "Name", "description": "Description"}),
            hide_index=True,
            use_container_width=True,
        )
