# Lifecycle Upgrade Dashboard

Interactive Streamlit dashboard built from `Lifecycle_upgrade.xlsx` for publish-ready reporting with a Starbucks-inspired executive theme, logo header, and one-click PDF export.

## Run locally

```powershell
cd C:\Users\PSP1001461\GitHub\lifecycle_dashboard
python -m streamlit run app.py
```

Then open the URL shown in terminal (usually `http://localhost:8501`).

## Data source

- Default file path used by the app:
  `data\Lifecycle_upgrade.xlsx` (for cloud deployment)
- You can also upload a fresh Excel file from the dashboard sidebar.

## Publish options

1. Push this `lifecycle_dashboard` folder to a Git repository.
2. Deploy on Streamlit Community Cloud (or your internal Streamlit server).
3. Set `app.py` as entry point.
4. Include `requirements.txt` during deployment.

## Streamlit Community Cloud deployment

1. Create a new GitHub repository and push the `lifecycle_dashboard` folder contents.
2. Go to `https://share.streamlit.io/` and sign in with GitHub.
3. Click **Create app**.
4. Select your repo and branch.
5. Set **Main file path** to `app.py`.
6. Click **Deploy**.
