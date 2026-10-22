import io
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Oscilloscope CSV Cleaner", page_icon="🧹", layout="wide")
st.title("Oscilloscope CSV Cleaner")
st.write("Upload an oscilloscope CSV, remove incomplete rows, inspect the signals interactively, and download the cleaned data for KaleidaGraph.")

uploaded = st.file_uploader("Choose a CSV file", type=["csv"])
has_units_row = st.checkbox("The second row contains units (for example, second, Volt, Volt, ...)", value=True)
use_scope_columns = st.checkbox("Use oscilloscope column names (time and Channels 1–4)", value=True)

if uploaded is not None:
    try:
        source = pd.read_csv(io.BytesIO(uploaded.getvalue()), skiprows=[1] if has_units_row else None)
        if use_scope_columns:
            if len(source.columns) != 5:
                st.error(f"Expected 5 columns (time + 4 channels), but found {len(source.columns)}. Uncheck the oscilloscope column-naming option to keep the original headers.")
                st.stop()
            source.columns = ["time_s", "ch1_V", "ch2_V", "ch3_V", "ch4_V"]

        df = source.copy()
        for col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        rows_before = len(df)
        cleaned = df.dropna(axis=0, how="any").copy()
        rows_after = len(cleaned)
        removed = rows_before - rows_after

        left, middle, right = st.columns(3)
        left.metric("Input data rows", f"{rows_before:,}")
        middle.metric("Complete rows kept", f"{rows_after:,}")
        right.metric("Rows removed", f"{removed:,}")

        st.subheader("Interactive signal plot")
        numeric_cols = list(cleaned.columns)
        if len(cleaned) and len(numeric_cols) >= 2:
            default_x = "time_s" if "time_s" in numeric_cols else numeric_cols[0]
            x_col = st.selectbox("X-axis", options=numeric_cols, index=numeric_cols.index(default_x))
            y_options = [col for col in numeric_cols if col != x_col]
            default_y = [c for c in y_options if c.startswith("ch")] or y_options[:min(4, len(y_options))]
            y_cols = st.multiselect("Signal columns", options=y_options, default=default_y)

            if y_cols:
                plot_df = cleaned[[x_col] + y_cols].melt(id_vars=x_col, value_vars=y_cols, var_name="Channel", value_name="Value")
                fig = px.line(plot_df, x=x_col, y="Value", color="Channel", render_mode="webgl",
                              title="Oscilloscope signals", labels={x_col: x_col, "Value": "Signal value"})
                fig.update_layout(hovermode="x unified", legend_title_text="Channel", margin=dict(l=20, r=20, t=55, b=20))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Select at least one signal column to display the plot.")

        st.subheader("Preview of cleaned data")
        st.dataframe(cleaned.head(20), use_container_width=True)
        output = cleaned.to_csv(index=False).encode("utf-8")
        original_name = uploaded.name.rsplit(".", 1)[0]
        st.download_button("Download cleaned CSV", data=output, file_name=f"{original_name}_cleaned.csv",
                           mime="text/csv", type="primary")
        st.caption("A row is kept only if every column contains a valid numeric value. Hover for values, zoom, pan, and toggle channels in the legend. Time gaps and unusual signal spikes are not automatically removed.")
    except Exception as exc:
        st.error(f"Could not process this CSV: {exc}")

st.divider()
st.caption("Upload only data you are permitted to process. Files are handled during the app session.")
