import io
import zipfile

import pandas as pd
import plotly.express as px
import streamlit as st

SCOPE_COLUMNS = ["time_s", "ch1_V", "ch2_V", "ch3_V", "ch4_V"]


def clean_csv(uploaded, has_units_row, use_scope_columns):
    source = pd.read_csv(io.BytesIO(uploaded.getvalue()), skiprows=[1] if has_units_row else None)
    if use_scope_columns:
        if len(source.columns) != 5:
            raise ValueError(
                f"Expected 5 columns (time + 4 channels), but found {len(source.columns)}. "
                "Uncheck the oscilloscope column-naming option to keep the original headers."
            )
        source.columns = SCOPE_COLUMNS

    df = source.copy()
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    cleaned = df.dropna(axis=0, how="any").copy()
    return cleaned, len(df), len(cleaned)


def cleaned_file_name(original_name, used_names):
    stem = original_name.rsplit(".", 1)[0]
    candidate = f"{stem}_cleaned.csv"
    counter = 2
    while candidate in used_names:
        candidate = f"{stem}_cleaned_{counter}.csv"
        counter += 1
    used_names.add(candidate)
    return candidate


def render_signal_plot(cleaned, key_prefix):
    st.subheader("Interactive signal plot")
    numeric_cols = list(cleaned.columns)
    if not len(cleaned) or len(numeric_cols) < 2:
        st.info("No complete rows are available to plot.")
        return

    default_x = "time_s" if "time_s" in numeric_cols else numeric_cols[0]
    x_col = st.selectbox("X-axis", options=numeric_cols, index=numeric_cols.index(default_x),
                         key=f"{key_prefix}_x")
    y_options = [col for col in numeric_cols if col != x_col]
    default_y = [c for c in y_options if c.startswith("ch")] or y_options[:min(4, len(y_options))]
    y_cols = st.multiselect("Signal columns", options=y_options, default=default_y,
                            key=f"{key_prefix}_y")

    if not y_cols:
        st.info("Select at least one signal column to display the plot.")
        return

    plot_df = cleaned[[x_col] + y_cols].melt(id_vars=x_col, value_vars=y_cols, var_name="Channel", value_name="Value")
    fig = px.line(plot_df, x=x_col, y="Value", color="Channel", render_mode="webgl",
                  title="Oscilloscope signals", labels={x_col: x_col, "Value": "Signal value"})
    fig.update_layout(hovermode="x unified", legend_title_text="Channel", margin=dict(l=20, r=20, t=55, b=20))
    st.plotly_chart(fig, use_container_width=True, key=f"{key_prefix}_chart")


def build_zip(results):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for result in results:
            archive.writestr(result["download_name"], result["cleaned"].to_csv(index=False))
    return buffer.getvalue()


st.set_page_config(page_title="Oscilloscope CSV Cleaner", page_icon="🧹", layout="wide")
st.title("Oscilloscope CSV Cleaner")
st.write("Upload one or more oscilloscope CSV files, remove incomplete rows, inspect the signals interactively, and download the cleaned data for KaleidaGraph.")

uploaded_files = st.file_uploader("Choose CSV files", type=["csv"], accept_multiple_files=True)
has_units_row = st.checkbox("The second row contains units (for example, second, Volt, Volt, ...)", value=True)
use_scope_columns = st.checkbox("Use oscilloscope column names (time and Channels 1–4)", value=True)

if uploaded_files:
    results = []
    used_names = set()
    for index, uploaded in enumerate(uploaded_files):
        try:
            cleaned, rows_before, rows_after = clean_csv(uploaded, has_units_row, use_scope_columns)
            results.append({
                "name": uploaded.name,
                "cleaned": cleaned,
                "rows_before": rows_before,
                "rows_after": rows_after,
                "rows_removed": rows_before - rows_after,
                "download_name": cleaned_file_name(uploaded.name, used_names),
            })
        except Exception as exc:
            st.error(f"Could not process {uploaded.name}: {exc}")

    if results:
        total_before = sum(result["rows_before"] for result in results)
        total_after = sum(result["rows_after"] for result in results)
        total_removed = sum(result["rows_removed"] for result in results)

        left, middle, right = st.columns(3)
        left.metric("Input data rows", f"{total_before:,}")
        middle.metric("Complete rows kept", f"{total_after:,}")
        right.metric("Rows removed", f"{total_removed:,}")

        if len(uploaded_files) > 1:
            summary = pd.DataFrame([
                {
                    "File": result["name"],
                    "Input rows": result["rows_before"],
                    "Kept": result["rows_after"],
                    "Removed": result["rows_removed"],
                }
                for result in results
            ])
            st.dataframe(summary, hide_index=True, use_container_width=True)

        tabs = st.tabs([f"{index + 1}. {result['name']}" for index, result in enumerate(results)])
        for index, (tab, result) in enumerate(zip(tabs, results)):
            with tab:
                render_signal_plot(result["cleaned"], key_prefix=f"file_{index}")

                st.subheader("Preview of cleaned data")
                st.dataframe(result["cleaned"].head(20), use_container_width=True)

                output = result["cleaned"].to_csv(index=False).encode("utf-8")
                st.download_button("Download cleaned CSV", data=output, file_name=result["download_name"],
                                   mime="text/csv", type="primary", key=f"download_{index}")

        if len(results) > 1:
            st.download_button("Download all cleaned CSVs (ZIP)", data=build_zip(results),
                               file_name="cleaned_csvs.zip", mime="application/zip", key="download_all")

        st.caption("A row is kept only if every column contains a valid numeric value. Hover for values, zoom, pan, and toggle channels in the legend. Time gaps and unusual signal spikes are not automatically removed.")

st.divider()
st.caption("Upload only data you are permitted to process. Files are handled during the app session.")
