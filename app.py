import io
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Oscilloscope CSV Cleaner", page_icon="🧹")
st.title("Oscilloscope CSV Cleaner")
st.write(
    "Upload an oscilloscope CSV, remove rows with missing values, "
    "and download a clean CSV for KaleidaGraph."
)

uploaded = st.file_uploader("Choose a CSV file", type=["csv"])
has_units_row = st.checkbox(
    "The second row contains units (for example, second, Volt, Volt, ...)",
    value=True,
)
use_scope_columns = st.checkbox(
    "Use oscilloscope column names (time and Channels 1–4)",
    value=True,
)

if uploaded is not None:
    try:
        raw = uploaded.getvalue()
        df = pd.read_csv(io.BytesIO(raw), skiprows=[1] if has_units_row else None)

        if use_scope_columns:
            if len(df.columns) != 5:
                st.error(
                    f"Expected 5 columns (time + 4 channels), but found {len(df.columns)}. "
                    "Uncheck 'Use oscilloscope column names' to retain the original headers."
                )
                st.stop()
            df.columns = ["time_s", "ch1_V", "ch2_V", "ch3_V", "ch4_V"]

        # Convert all fields to numeric; non-numeric values become missing.
        for col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        rows_before = len(df)
        cleaned = df.dropna(axis=0, how="any").copy()
        rows_after = len(cleaned)
        removed = rows_before - rows_after

        c1, c2, c3 = st.columns(3)
        c1.metric("Input data rows", f"{rows_before:,}")
        c2.metric("Rows kept", f"{rows_after:,}")
        c3.metric("Rows removed", f"{removed:,}")

        st.subheader("Preview of cleaned data")
        st.dataframe(cleaned.head(20), use_container_width=True)

        output = cleaned.to_csv(index=False).encode("utf-8")
        original_name = uploaded.name.rsplit(".", 1)[0]
        st.download_button(
            label="Download cleaned CSV",
            data=output,
            file_name=f"{original_name}_cleaned.csv",
            mime="text/csv",
            type="primary",
        )

        st.caption(
            "Cleaning rule: retain a row only when every column has a valid numeric value. "
            "This removes rows with missing values; it does not remove time gaps or signal spikes."
        )
    except Exception as exc:
        st.error(f"Could not process this CSV: {exc}")

st.divider()
st.caption("Files are processed in this app session; do not upload confidential data.")
