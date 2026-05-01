# 🎙️ Editorial Analysis Hub

**An AI-driven strategic dashboard for music industry professionals.**

The Editorial Analysis Hub transforms raw editorial placement data (from Spotify, Amazon, Apple Music, etc.) into actionable insights. It allows record labels and distributors to monitor their digital presence, track growth, and leverage AI to interrogate their own catalog data.

---

## ⚡ What It Does

1. **Strategic Dashboard**: A high-performance UI providing real-time metrics on your editorial placements. Instantly see YoY/MoM growth, DSP (Digital Service Provider) rankings, and monthly performance heatmaps.
2. **AI Strategic Advisor**: Powered by Google's Gemini 1.5 Flash. Instead of manually filtering spreadsheets, you ask natural language questions (e.g., *"What were the top growing DSPs in Q1?"*). The AI autonomously analyzes the database and generates custom Plotly charts and insights on the fly.
3. **Data Explorer**: A deep-dive interface to dynamically filter, search, and export specific slices of your editorial data.

---

## 🛠️ Technology Stack

- **Frontend/Backend**: Streamlit (Python)
- **AI Integration**: Google Generative AI (Gemini Flash & Pro)
- **Data Engine**: Pandas & Plotly (for visualization)

---

## 🚀 Deployment Guide (Streamlit Community Cloud)

This application is ready to be deployed instantly via Streamlit Community Cloud.

**Prerequisites:**
1. A GitHub account with this repository forked or pushed.
2. A free [Streamlit Community Cloud](https://share.streamlit.io/) account.
3. A Google Gemini API Key.

**Steps to Deploy:**
1. Log in to Streamlit Community Cloud and click **"New app"**.
2. Select your repository (`editorial-analysis-hub`), branch (`main`), and main file path (`app.py`).
3. Click on **Advanced settings** before deploying.
4. In the **Secrets** field, paste your Gemini API Key like this:
   ```toml
   GOOGLE_API_KEY = "your-api-key-here"
   ```
5. Click **Deploy!** The app will automatically install dependencies from `requirements.txt` and launch.

---
*Note: This repository includes a generated `Data_Mockup.xlsx` to demonstrate the engine's capabilities while protecting real artist PII.*
