# Oscilloscope CSV Cleaner

A minimal Streamlit app that removes rows containing missing/non-numeric values and lets users download the cleaned CSV. Multiple files can be uploaded at once; each is cleaned and previewed in its own tab, with a ZIP download for all results.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Deploy to Streamlit Community Cloud

1. Create a GitHub repository and upload `app.py` and `requirements.txt`.
2. Sign in to Streamlit Community Cloud with GitHub.
3. Choose **Create app**, select the repository, branch, and `app.py`.
4. Deploy. Streamlit will provide a public URL.

## Expected input format

For the oscilloscope export used in this project:
- 5 columns: time plus Channels 1–4.
- The second CSV row may contain units such as `second` and `Volt`; leave the units-row checkbox enabled in that case.

The app keeps only rows where all columns contain valid numeric values. It does not automatically remove time gaps, outliers, or voltage spikes.
