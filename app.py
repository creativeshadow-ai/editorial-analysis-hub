import streamlit as st
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import google.generativeai as genai
from streamlit_gsheets import GSheetsConnection
import plotly.express as px
import plotly.graph_objects as go
import time
import re
import unicodedata
import io
import base64
import re
from datetime import datetime

# ==============================================================================
# 0. INITIAL CONFIG
# ==============================================================================
st.set_page_config(
    page_title="Editorial Analysis Hub",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================================================================
# 1. THEME & VISUAL CONFIGURATION (AESTHETIC LIGHT MODE)
# ==============================================================================
PRIMARY_COLOR = "#443392"
SECONDARY_COLOR = "#333333"
BG_APP = "#F8FAFC"
TEXT_MAIN = "#0F172A"
TEXT_SUB = "#475569"
CARD_BG = "rgba(255, 255, 255, 0.9)"
CARD_BORDER = "rgba(0, 0, 0, 0.04)"
SIDEBAR_BG = "#FFFFFF"
INPUT_BG = "#FFFFFF"
INPUT_BORDER = "#E2E8F0"

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
    
    :root {{
        --primary: {PRIMARY_COLOR};
        --secondary: {SECONDARY_COLOR};
    }}

    /* ── Base ── */
    html, body, [class*="css"], .stApp {{
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        background-color: {BG_APP} !important;
        color: {TEXT_MAIN} !important;
    }}
    
    /* ── Headers ── */
    h1, h2, h3, h4, h5 {{ 
        color: {TEXT_MAIN} !important; 
        font-weight: 800 !important;
        letter-spacing: -0.02em;
    }}
    p, span, li, label {{
        color: {TEXT_SUB} !important;
    }}
    
    /* ── Metrics ── */
    div[data-testid="stMetric"] {{
        background: {CARD_BG} !important;
        backdrop-filter: blur(10px);
        border: 1px solid {CARD_BORDER} !important;
        border-radius: 20px;
        padding: 24px !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.02), 0 2px 4px -1px rgba(0, 0, 0, 0.01);
    }}
    div[data-testid="stMetricLabel"] {{ color: {TEXT_SUB} !important; font-weight: 600; text-transform: uppercase; font-size: 0.7rem; }}
    div[data-testid="stMetricValue"] {{ color: {TEXT_MAIN} !important; font-weight: 800; }}
    
    /* ── Tabs (CLEAN & AESTHETIC - NO ORANGE) ── */
    .stTabs [data-baseweb="tab-list"] {{
        background: #F1F5F9;
        border-radius: 14px;
        padding: 6px;
        gap: 8px;
        border: 1px solid #E2E8F0;
    }}
    .stTabs [data-baseweb="tab"] {{
        border-radius: 12px;
        color: {TEXT_SUB} !important;
        font-weight: 700 !important;
        height: 44px;
        padding: 0 24px !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        border: none !important;
    }}
    .stTabs [aria-selected="true"] {{
        background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%) !important;
        box-shadow: 0 10px 15px -3px rgba(68, 51, 146, 0.3);
        transform: translateY(-1px);
    }}
    /* RECOVERY COLOR FOR TEXT */
    .stTabs [aria-selected="true"] p, .stTabs [aria-selected="true"] span, .stTabs [aria-selected="true"] div {{
        color: #FFFFFF !important;
    }}
    
    /* ── IMPORTANT: HIDE THE ORANGE BAR ── */
    [data-baseweb="tab-highlight"], [data-baseweb="tab-border"] {{
        display: none !important;
        background-color: transparent !important;
        height: 0 !important;
    }}
    
    /* ── MultiSelect Pills ── */
    [data-testid="stMultiSelect"] span[data-baseweb="tag"] {{
        background-color: var(--primary) !important;
        color: white !important;
        border-radius: 8px;
    }}
    [data-testid="stMultiSelect"] span[data-baseweb="tag"] span {{
        color: white !important;
    }}
    
    /* ── Buttons (FORCED WHITE TEXT) ── */
    .stButton button, .stDownloadButton button {{
        background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 12px;
        font-weight: 700 !important;
        padding: 0.6rem 1.4rem;
        box-shadow: 0 4px 6px -1px rgba(68, 51, 146, 0.2);
        transition: all 0.3s;
    }}
    .stButton button p {{
        color: #FFFFFF !important;
    }}
    .stButton button:hover {{ 
        box-shadow: 0 10px 15px -3px rgba(68, 51, 146, 0.3);
        transform: translateY(-2px);
    }}

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {{
        background-color: #FFFFFF !important;
        border-right: 1px solid #F1F5F9;
    }}
    
    /* ── Chat ── */
    .stChatMessage {{
        background: #FFFFFF !important;
        border: 1px solid #F1F5F9 !important;
        border-radius: 18px;
    }}
    
    /* ── Dataframes ── */
    .stDataFrame {{
        border: 1px solid #F1F5F9;
        border-radius: 12px;
    }}
    
    /* Hide Streamlit elements */
    #MainMenu, footer, header {{visibility: hidden;}}
</style>
""", unsafe_allow_html=True)

if "GOOGLE_API_KEY" not in st.secrets:
    st.warning("⚠️ Warning: Missing GOOGLE_API_KEY in Secrets. AI features will be disabled.")
else:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# ==============================================================================
# 2. MOTOR ETL
# ==============================================================================
def normalize_text(text: str) -> str:
    """
    Normalizes a given text string by removing diacritics (accents),
    converting to uppercase, and stripping leading/trailing whitespace.
    Useful for standardizing categories like DSP names or Months.
    
    Args:
        text (str): The raw string to normalize.
        
    Returns:
        str: The cleaned, uppercase, ASCII-like string.
    """
    if not isinstance(text, str): 
        return str(text)
    # Decompose unicode characters into base char + combining char (NFKD), then filter out combining chars
    text = "".join(c for c in unicodedata.normalize('NFKD', text) if not unicodedata.combining(c))
    return text.upper().strip()

import base64

def get_base64_image(image_path: str) -> str:
    """
    Reads an image file from the local filesystem and encodes it as a Base64 string.
    This is used to embed images directly into HTML/CSS without relying on external URLs.
    
    Args:
        image_path (str): The relative or absolute path to the image file.
        
    Returns:
        str: The Base64 encoded string of the image, or an empty string if the file is not found.
    """
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except Exception as e:
        # Fallback to empty string if image doesn't exist (e.g., logo.png missing)
        return ""

@st.cache_data(ttl=3600, show_spinner="📡 Loading data...")
def load_data() -> pd.DataFrame:
    """
    Loads the primary mock dataset from the Excel file into a Pandas DataFrame.
    The result is cached by Streamlit for 1 hour (3600s) to improve app performance.
    
    Returns:
        pd.DataFrame: The raw dataframe containing the editorial data. Returns an empty DF on failure.
    """
    try:
        return pd.read_excel("Data_Mockup.xlsx")
    except Exception as e:
        st.error("Error: Data_Mockup.xlsx file not found or corrupted.")
        return pd.DataFrame()

@st.cache_data(ttl=3600, show_spinner="⚙️ Processing data...")
def clean_dataframe(df: pd.DataFrame) -> tuple[pd.DataFrame, list]:
    """
    Core ETL pipeline for the dataset. Cleans columns, standardizes string values,
    and infers temporal data (Year/Month) to ensure robust downstream analysis.
    
    Args:
        df (pd.DataFrame): Raw dataframe loaded from load_data().
        
    Returns:
        tuple[pd.DataFrame, list]: 
            - Cleaned DataFrame ready for dashboarding.
            - List of column names that were successfully cleaned.
    """
    try:
        # Standardize column names: uppercase, remove special characters, replace spaces with underscores
        df.columns = [str(c).upper().replace('\n', ' ').replace('/', '_').replace('.', '').strip().replace(' ', '_') for c in df.columns]
        cleaned_cols_log = []
        
        # Columns that should not be text-normalized
        ignore_cols = ['YEAR', 'MONTH', 'WEEK', 'Q', 'INCLUSION_DATE', 'RELEASE_DATE']
        
        # Iterate over columns and apply text normalization to string fields
        for col in df.columns:
            if col not in ignore_cols:
                clean_name = f"{col}_CLEAN"
                df[clean_name] = df[col].apply(lambda x: normalize_text(str(x)) if pd.notnull(x) else "UNKNOWN")
                cleaned_cols_log.append(clean_name)
        
        # Attempt to dynamically locate critical temporal columns
        col_inc = next((c for c in df.columns if 'INCLUSION' in c), None)
        col_year = next((c for c in df.columns if c == 'YEAR'), None)
        col_month = next((c for c in df.columns if c == 'MONTH'), None)

        # Initialize final temporal tracking columns
        df['Year_Final'] = 0
        df['Month_Final'] = 0
        
        # Strategy 1: Extract Year/Month from a datetime inclusion column
        if col_inc:
            dt_inc = pd.to_datetime(df[col_inc], errors='coerce')
            df['Year_Final'] = dt_inc.dt.year.fillna(0).astype(int)
            df['Month_Final'] = dt_inc.dt.month.fillna(0).astype(int)
            
        # Strategy 2: Fallback to manual 'YEAR' column if extraction failed
        if col_year:
            y_man = pd.to_numeric(df[col_year], errors='coerce').fillna(0).astype(int)
            # Only apply manual year if the final year is still 0 (unresolved)
            df['Year_Final'] = df.apply(lambda x: y_man[x.name] if x['Year_Final'] == 0 else x['Year_Final'], axis=1)

        # Strategy 2: Fallback to manual 'MONTH' column if extraction failed
        if col_month:
            # Map string month names (EN/ES) to numeric indices (1-12)
            mapa_mes = {'ENERO':1, 'ENE':1, 'JAN':1, 'FEBRERO':2, 'FEB':2, 'FEB':2, 'MARZO':3, 'MAR':3, 'ABRIL':4, 'ABR':4, 'MAYO':5, 'MAY':5, 'JUNIO':6, 'JUN':6, 'JULIO':7, 'JUL':7, 'AGOSTO':8, 'AGO':8, 'SEPTIEMBRE':9, 'SEP':9, 'OCTUBRE':10, 'OCT':10, 'NOVIEMBRE':11, 'NOV':11, 'DICIEMBRE':12, 'DIC':12,
                        'JANUARY':1, 'FEBRUARY':2, 'MARCH':3, 'APRIL':4, 'MAY':5, 'JUNE':6, 'JULY':7, 'AUGUST':8, 'SEPTEMBER':9, 'OCTOBER':10, 'NOVEMBER':11, 'DECEMBER':12}
            
            def get_month(x):
                s = normalize_text(str(x))
                if s.isdigit(): return int(s)
                return mapa_mes.get(s, 0)
            
            m_man = df[col_month].apply(get_month)
            # Only apply manual month if final month is still 0
            df['Month_Final'] = df.apply(lambda x: m_man[x.name] if x['Month_Final'] == 0 else x['Month_Final'], axis=1)

        # Drop rows where DSP is 'UNKNOWN', as DSP is the core metric of this dashboard
        col_dsp = next((c for c in cleaned_cols_log if 'DSP' in c), None)
        if col_dsp: 
            df = df[df[col_dsp] != 'UNKNOWN']

        # Ensure all object columns are explicitly cast to string to prevent serialization issues
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].astype(str)

        return df, cleaned_cols_log

    except Exception as e:
        st.error(f"Error ETL: {e}")
        return pd.DataFrame(), []

@st.cache_resource(ttl=86400, show_spinner="🤖 Loading IA models...")
def get_valid_models() -> list:
    """
    Connects to the Google Gemini API to fetch available models.
    Filters the list to ensure only text-generation models are presented to the user.
    
    Returns:
        list: Array of valid model names (e.g., 'models/gemini-1.5-flash').
    """
    try:
        models = genai.list_models()
        # Ensure the model supports the 'generateContent' method required by the chat
        valid = [m.name for m in models if 'generateContent' in m.supported_generation_methods]
        return valid
    except Exception as e: 
        # Fails safely if API key is invalid or quota is exhausted
        return []

# ==============================================================================
# 3. HELPERS & CHART CONFIG
# ==============================================================================
CHART_LAYOUT = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(color=TEXT_MAIN, family='Plus Jakarta Sans', size=12),
    margin=dict(t=30, b=40, l=40, r=30),
    template='plotly_white'
)
GRID_STYLE = dict(gridcolor='rgba(0,0,0,0.05)', zerolinecolor='rgba(0,0,0,0.05)')
ACCENT_SEQUENCE = ['#443392', '#333333', '#10B981', '#3B82F6', '#EF4444', '#FBBF24', '#8B5CF6']

# DSP Brand Colors
DSP_COLORS = {
    'SPOTIFY': '#1DB954',
    'AMAZON': '#00A8E1',
    'PANDORA': '#00A0EE',
    'YOUTUBE': '#FF0000',
    'NAPSTER': '#253444',
    'TIDAL': '#000000',
    'APPLE': '#8E8E93',
    'DEEZER': '#A855F7',
}
DEFAULT_DSP_COLOR = '#443392'

def get_dsp_color(dsp_name: str) -> str:
    """
    Returns the designated brand color for a given DSP (Digital Service Provider).
    Used to maintain visual consistency across all charts and rankings.
    
    Args:
        dsp_name (str): The name of the DSP (e.g., 'Spotify', 'Amazon').
        
    Returns:
        str: The HEX color code for the DSP, or a default accent color if not found.
    """
    name = str(dsp_name).upper()
    for key, color in DSP_COLORS.items():
        if key in name:
            return color
    return DEFAULT_DSP_COLOR

def get_greeting() -> str:
    """
    Returns a simple greeting for the dashboard header.
    Can be expanded in the future to handle time-based greetings.
    """
    return "Hey There!"

MONTH_NAMES = {1:'Jan', 2:'Feb', 3:'Mar', 4:'Apr', 5:'May', 6:'Jun',
               7:'Jul', 8:'Aug', 9:'Sep', 10:'Oct', 11:'Nov', 12:'Dec'}

# ==============================================================================
# 4. SIDEBAR
# ==============================================================================
with st.sidebar:
    LOGO_BASE64 = get_base64_image("assets/logo.png")
    st.markdown(f"""
    <div style='text-align: center; padding: 0 0 16px 0;'>
        <img src='data:image/png;base64,{LOGO_BASE64}' width='140' style='border-radius: 8px;'>
        <p style='color: var(--text-main) !important; font-weight: 800; font-size: 1.1rem; margin-top: 12px; margin-bottom: 0;'>EDITORIAL HUB</p>
        <p style='color: var(--text-sub) !important; font-size: 0.65rem; margin-top: 2px; letter-spacing: 0.1em; text-transform: uppercase;'>Analysis Suite</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    valid_models_list = get_valid_models()
    
    # Prioritize 1.5-flash for reliability and higher quotas
    flash_model = next((m for m in valid_models_list if "1.5-flash" in m), None)
    if not flash_model:
        flash_model = next((m for m in valid_models_list if "flash" in m), None)
        
    pro_model = next((m for m in valid_models_list if "pro" in m), None)
    
    default_model = flash_model if flash_model else (valid_models_list[0] if valid_models_list else None)
    
    if valid_models_list:
        sel_model = st.selectbox("🧠 AI Model", valid_models_list, index=valid_models_list.index(default_model) if default_model in valid_models_list else 0)
    else:
        st.info("🤖 AI Model: None (API Key required)")
        sel_model = None
    
    st.divider()
    raw_df = load_data()
    df, cols_clean = clean_dataframe(raw_df)
    
    if not df.empty:
        col_dsp = next((c for c in cols_clean if 'DSP' in c), None)
        pivot = df.groupby(['Year_Final', 'Month_Final', col_dsp]).size().reset_index(name='Count') if col_dsp else pd.DataFrame()
        pivot = pivot[pivot['Count'] > 0]
        truth_table = pivot.to_string(index=False)
        
        # Glassmorphism stat cards
        year_max = df['Year_Final'].max()
        count_ytd = len(df[df['Year_Final'] == year_max])
        
        st.markdown(f"""
        <div style='
            background: linear-gradient(135deg, rgba(68,51,146,0.15) 0%, rgba(51,51,51,0.15) 100%);
            border: 1px solid rgba(68,51,146,0.3);
            padding: 20px; border-radius: 16px; text-align: center; backdrop-filter: blur(10px);
        '>
            <p style='color: var(--text-sub) !important; font-size: 0.7rem; margin: 0; text-transform: uppercase; letter-spacing: 0.1em;'>Total Records</p>
            <p style='color: var(--text-main) !important; font-size: 2rem; font-weight: 800; margin: 6px 0 0 0; 
               background: linear-gradient(135deg, #443392, #333333); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>{len(df):,}</p>
        </div>
        <div style='height: 8px'></div>
        <div style='display: flex; gap: 8px;'>
            <div style='flex: 1; background: var(--card-bg); border: 1px solid var(--card-border); padding: 12px; border-radius: 12px; text-align: center;'>
                <p style='color: var(--text-sub) !important; font-size: 0.6rem; margin: 0; text-transform: uppercase;'>Year {year_max}</p>
                <p style='color: var(--text-main) !important; font-size: 1.1rem; font-weight: 700; margin: 4px 0 0 0;'>{count_ytd:,}</p>
            </div>
            <div style='flex: 1; background: var(--card-bg); border: 1px solid var(--card-border); padding: 12px; border-radius: 12px; text-align: center;'>
                <p style='color: var(--text-sub) !important; font-size: 0.6rem; margin: 0; text-transform: uppercase;'>Active DSPs</p>
                <p style='color: var(--text-main) !important; font-size: 1.1rem; font-weight: 700; margin: 4px 0 0 0;'>{df[col_dsp].nunique() if col_dsp else 0}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<div style='height: 12px'></div>", unsafe_allow_html=True)
        
    st.divider()
    st.markdown("""
    <p style='color: #4B5563 !important; font-size: 0.65rem; text-align: center; letter-spacing: 0.05em;'>
        v33.0 · Editorial Analysis Hub<br>Powered by alisos-records-creative
    </p>
    """, unsafe_allow_html=True)

# ==============================================================================
# 5. MAIN CONTENT
# ==============================================================================
if not df.empty:
    
    # ── Welcome Header ──
    greeting = get_greeting()
    st.markdown(f"""
    <div style='margin-bottom: 8px;'>
        <h1 style='margin: 0; font-size: 1.8rem; font-weight: 800;'>
            {greeting} 👋
        </h1>
        <p style='color: var(--text-sub) !important; font-size: 0.9rem; margin-top: 4px;'>
            Here is the summary of your DSPs · {datetime.now().strftime('%d %b %Y')}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    tab_dash, tab_ai, tab_raw = st.tabs(["📊 Dashboard", "🤖 AI Analyst", "🔎 Data Explorer"])

    # ── TAB 1: DASHBOARD ──
    with tab_dash:
        # ── Filters ──
        all_years = sorted(df['Year_Final'].unique())
        all_months_nums = sorted(df['Month_Final'].unique())
        all_months_labels = {m: MONTH_NAMES.get(m, str(m)) for m in all_months_nums if m > 0}
        
        f1, f2, f3 = st.columns([1, 1, 2])
        with f1:
            sel_year = st.selectbox("📅 Year", ["All"] + [str(y) for y in all_years if y > 0], index=0, key="dash_year")
        with f2:
            month_options = ["All"] + [all_months_labels[m] for m in all_months_labels]
            sel_month_mode = st.selectbox("📆 Month", month_options, index=0, key="dash_month_mode")
        
        # Resolve selected months
        if sel_month_mode == "All":
            sel_months = list(all_months_labels.keys())
        else:
            sel_months = [m for m, name in all_months_labels.items() if name == sel_month_mode]
        
        # Apply filters
        dff = df.copy()
        if sel_year != "All":
            dff = dff[dff['Year_Final'] == int(sel_year)]
        if sel_months:
            dff = dff[dff['Month_Final'].isin(sel_months)]
        
        st.markdown("<div style='height: 8px'></div>", unsafe_allow_html=True)
        
        # ── KPIs ──
        total = len(dff)
        year_max = int(sel_year) if sel_year != "All" else df['Year_Final'].max()
        year_prev = year_max - 1
        count_ytd = len(dff[dff['Year_Final'] == year_max]) if sel_year == "All" else total
        count_prev_df = df[df['Year_Final'] == year_prev]
        if sel_months:
            count_prev_df = count_prev_df[count_prev_df['Month_Final'].isin(sel_months)]
        count_prev = len(count_prev_df)
        growth = ((count_ytd - count_prev) / count_prev * 100) if count_prev > 0 else 0
        n_dsps = dff[col_dsp].nunique() if col_dsp else 0
        top_dsp = dff[col_dsp].mode()[0] if col_dsp and not dff.empty else "N/A"
        
        months_current = dff.groupby('Month_Final').size()
        avg_monthly = months_current.mean() if len(months_current) > 0 else 0
        
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Records", f"{total:,}")
        c2.metric(f"vs {year_prev}", f"{count_ytd:,}", delta=f"{growth:+.1f}%")
        c3.metric("Leading DSP", top_dsp)
        c4.metric("Active DSPs", f"{n_dsps}")
        c5.metric("Monthly Avg", f"{avg_monthly:,.0f}")
        
        st.markdown("<div style='height: 16px'></div>", unsafe_allow_html=True)
        
        # ── Row 1: Bar + Ranking ──
        g1, g2 = st.columns([3, 2])
        with g1:
            st.markdown("##### 📈 Records per Year")
            yd = dff.groupby('Year_Final').size().reset_index(name='Total')
            fig_bar = px.bar(
                yd, x='Year_Final', y='Total', text_auto=True,
                color_discrete_sequence=['#443392']
            )
            fig_bar.update_traces(
                textposition='auto',
                textfont=dict(color='#FFFFFF', size=12, family='Plus Jakarta Sans'),
                marker=dict(color='#443392', line=dict(width=0))
            )
            fig_bar.update_layout(
                **CHART_LAYOUT,
                xaxis={**GRID_STYLE, 'title': ''}, 
                yaxis={**GRID_STYLE, 'title': ''},
                showlegend=False, bargap=0.3,
            )
            st.plotly_chart(fig_bar, use_container_width=True)
            
        with g2:
            st.markdown("##### 🏆 DSP Ranking")
            if col_dsp and not dff.empty:
                dsp_totals = dff[col_dsp].value_counts().nlargest(8)
                top_dsps_list = dsp_totals.index
                
                # Compute YoY growth per DSP
                dsp_by_year = dff.groupby([col_dsp, 'Year_Final']).size().unstack(fill_value=0)
                
                rows_html = ""
                for dsp in top_dsps_list:
                    dsp_color = get_dsp_color(dsp)
                    total_dsp = int(dsp_totals[dsp])
                    
                    # YoY comparison
                    if year_max in dsp_by_year.columns and year_prev in dsp_by_year.columns and dsp in dsp_by_year.index:
                        curr = int(dsp_by_year.loc[dsp, year_max])
                        prev = int(dsp_by_year.loc[dsp, year_prev])
                        if prev > 0:
                            g_pct = ((curr - prev) / prev) * 100
                            is_up = g_pct >= 0
                            badge_bg = 'rgba(16,185,129,0.15)' if is_up else 'rgba(239,68,68,0.15)'
                            badge_color = '#10B981' if is_up else '#EF4444'
                            badge_text = f"{'↑' if is_up else '↓'} {abs(g_pct):.0f}%"
                        elif curr > 0:
                            badge_bg = 'rgba(16,185,129,0.15)'
                            badge_color = '#10B981'
                            badge_text = '✦ New'
                        else:
                            badge_bg = 'rgba(255,255,255,0.05)'
                            badge_color = '#9CA3AF'
                            badge_text = '—'
                    else:
                        badge_bg = 'rgba(255,255,255,0.05)'
                        badge_color = '#9CA3AF'
                        badge_text = '—'

                    rows_html += f"""<div style='display:flex; justify-content:space-between; align-items:center; padding:10px 16px; border-bottom:1px solid var(--card-border);'><div style='display:flex; align-items:center; gap:10px;'><div style='width:8px; height:8px; border-radius:50%; background:{dsp_color};'></div><span style='color:var(--text-main); font-weight:600; font-size:0.88rem;'>{dsp}</span></div><div style='display:flex; align-items:center; gap:12px;'><span style='color:var(--text-sub); font-size:0.82rem;'>{total_dsp:,}</span><span style='background:{badge_bg}; color:{badge_color}; padding:3px 10px; border-radius:20px; font-size:0.73rem; font-weight:600;'>{badge_text}</span></div></div>"""
                
                full_html = f"<div style='background:var(--card-bg); border:1px solid var(--card-border); border-radius:16px; padding:4px 0; overflow:hidden;'>{rows_html}</div>"
                st.html(full_html)
        
        # ── Row 2: Area chart ──
        st.markdown("##### 📉 Monthly Trend")
        monthly = dff.groupby(['Year_Final', 'Month_Final']).size().reset_index(name='Total')
        monthly['SortKey'] = monthly['Year_Final'] * 100 + monthly['Month_Final']
        monthly = monthly.sort_values('SortKey')
        monthly['Label'] = monthly['Month_Final'].map(MONTH_NAMES).fillna('') + ' ' + monthly['Year_Final'].astype(str)
        
        fig_area = go.Figure()
        fig_area.add_trace(go.Scatter(
            x=monthly['Label'], y=monthly['Total'],
            mode='lines+markers',
            fill='tozeroy',
            line=dict(color='#443392', width=3, shape='spline'),
            fillcolor='rgba(68, 51, 146, 0.15)',
            marker=dict(size=8, color='#443392', line=dict(width=2, color="#FFFFFF")),
            hovertemplate='<b>%{x}</b><br>Records: %{y:,}<extra></extra>'
        ))
        fig_area.update_layout(
            **CHART_LAYOUT,
            xaxis=dict(**GRID_STYLE, tickangle=-45, tickfont=dict(size=10), type='category', categoryorder='array', categoryarray=monthly['Label'].tolist()),
            yaxis=GRID_STYLE,
            hovermode='x unified',
        )
        st.plotly_chart(fig_area, use_container_width=True)
        
        # ── Row 3: Donut + Heatmap ──
        r1, r2 = st.columns(2)
        with r1:
            st.markdown("##### 🎯 DSP Distribution")
            if col_dsp:
                dist = dff[col_dsp].value_counts().reset_index()
                dist.columns = ['DSP', 'Total']
                dist_top = dist.head(8)
                dsp_chart_colors = [get_dsp_color(d) for d in dist_top['DSP']]
                
                # Dynamic text color based on background
                text_colors = []
                for c in dsp_chart_colors:
                    # Simple brightness check: if hex is dark -> white text, else black
                    h = c.lstrip('#')
                    rgb = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
                    lum = (0.299*rgb[0] + 0.587*rgb[1] + 0.114*rgb[2])
                    text_colors.append('#FFFFFF' if lum < 128 else '#111111')

                fig_donut = px.pie(
                    dist_top, names='DSP', values='Total', hole=0.65,
                    color_discrete_sequence=dsp_chart_colors
                )
                fig_donut.update_traces(
                    textinfo='percent+label',
                    textfont=dict(size=11, color=text_colors, family='Plus Jakarta Sans'),
                    marker=dict(line=dict(color='#FFFFFF', width=1))
                )
                fig_donut.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color=TEXT_SUB, family='Plus Jakarta Sans'),
                    margin=dict(t=10, b=10, l=10, r=10),
                    showlegend=False,
                )
                st.plotly_chart(fig_donut, use_container_width=True)
        
        with r2:
            st.markdown("##### 🔥 Activity per Month & Year")
            heat_data = dff.groupby(['Year_Final', 'Month_Final']).size().reset_index(name='Count')
            heat_pivot = heat_data.pivot_table(index='Year_Final', columns='Month_Final', values='Count', fill_value=0)
            heat_pivot.columns = [MONTH_NAMES.get(c, str(c)) for c in heat_pivot.columns]
            
            fig_heat = px.imshow(
                heat_pivot.values,
                x=heat_pivot.columns.tolist(),
                y=[str(y) for y in heat_pivot.index],
                color_continuous_scale=[[0, '#F3F4F6'], [0.3, '#DDD6FE'], [0.6, '#443392'], [1, '#333333']],
                aspect='auto'
            )
            fig_heat.update_traces(
                hovertemplate='<b>%{y} · %{x}</b><br>Records: %{z:,}<extra></extra>'
            )
            fig_heat.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color=TEXT_SUB, family='Plus Jakarta Sans'),
                margin=dict(t=10, b=30, l=50, r=10),
                coloraxis_showscale=False,
                xaxis=dict(side='bottom'),
            )
            st.plotly_chart(fig_heat, use_container_width=True)

    # ── TAB 2: CHAT IA ──
    with tab_ai:
        st.markdown(f"""
        <div style='margin-bottom: 24px;'>
            <h2 style='margin: 0; font-size: 1.6rem; color: var(--primary) !important;'>Alisos AI: Strategic Advisor</h2>
            <p style='color: {TEXT_SUB} !important; font-size: 0.9rem; margin-top: 4px;'>
                Direct access to the Editorial Database. Analyze trends, growth, and performance with Gemini Flash.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Suggested prompts
        # Suggested prompts (Interactive Buttons)
        st.markdown("<p style='color: var(--text-sub) !important; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 8px;'>Quick suggestions</p>", unsafe_allow_html=True)
        
        sug_cols = st.columns(4)
        clicked_prompt = None
        
        with sug_cols[0]:
            if st.button("📈 Spotify Projection Q1 2026", use_container_width=True):
                clicked_prompt = "Spotify Projection Q1 2026"
        with sug_cols[1]:
            if st.button("🔄 Compare DSPs last year", use_container_width=True):
                clicked_prompt = "Compare DSPs last year"
        with sug_cols[2]:
            if st.button("📊 Top 10 Growing DSPs", use_container_width=True):
                clicked_prompt = "Top 10 Growing DSPs"
        with sug_cols[3]:
            if st.button("📈 Monthly Trends", use_container_width=True):
                clicked_prompt = "Comprehensive analysis of monthly placement trends by year."
        
        if "messages" not in st.session_state:
            st.session_state.messages = [{"role": "assistant", "content": "👋 Hi! I'm your data analyst. I can do projections, comparisons, and deep analysis. Type your query or use one of the suggestions above."}]

        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        user_input = st.chat_input("Type your query here...")
        
        # Determine strict prompt source
        prompt = user_input if user_input else clicked_prompt
        
        if prompt:
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                caja = st.empty()
                
                def call_ai(prompt_text: str, model_name: str, fallback_name: str):
                    """
                    Invokes the Gemini API to generate Python code based on the user's prompt.
                    Includes robust error handling: retry logic with exponential backoff for rate limits (429/503),
                    and a fallback mechanism to a secondary model if the primary fails.
                    
                    Args:
                        prompt_text (str): The highly engineered system prompt + user query.
                        model_name (str): The primary Gemini model (e.g., 'gemini-1.5-flash').
                        fallback_name (str): The secondary model to try if the primary fails.
                        
                    Returns:
                        GenerateContentResponse: The API response containing the generated text.
                    """
                    config = genai.GenerationConfig(temperature=0, max_output_tokens=8192)
                    try:
                        caja.info(f"⚡ Generating with {model_name.split('/')[-1]}...")
                        return genai.GenerativeModel(model_name).generate_content(prompt_text, generation_config=config)
                    except Exception as e:
                        err = str(e)
                        # Detect rate limits or quota issues
                        if "429" in err or "Quota" in err or "503" in err:
                            caja.warning("⏳ API busy or rate limit reached, retrying in 15s...")
                            bar = st.progress(0)
                            for t in range(15):
                                time.sleep(1)
                                bar.progress((t+1)/15)
                            bar.empty()
                            try:
                                # First retry with the same model
                                return genai.GenerativeModel(model_name).generate_content(prompt_text, generation_config=config)
                            except:
                                # Second retry with the fallback model
                                if fallback_name and fallback_name != model_name:
                                    caja.info(f"🔄 Primary failed. Using fallback: {fallback_name.split('/')[-1]}...")
                                    return genai.GenerativeModel(fallback_name).generate_content(prompt_text, generation_config=config)
                                raise
                        raise e

                def extract_code(text: str) -> str:
                    """
                    Parses the raw text response from the LLM and extracts the Python code block.
                    Handles both explicitly typed blocks (```python) and generic code blocks (```).
                    
                    Args:
                        text (str): Raw output from the LLM.
                        
                    Returns:
                        str: The clean Python code ready for execution.
                    """
                    # Try finding a python specific block first
                    extracted = re.search(r'```python\s*(.*?)\s*```', text, re.DOTALL)
                    if not extracted:
                        # Fallback to generic block
                        extracted = re.search(r'```\s*(.*?)\s*```', text, re.DOTALL)
                    
                    if extracted:
                        return extracted.group(1).strip()
                    # If no code block is found, assume the entire text is the code (fallback)
                    return text.strip()

                code = None
                try:
                    # Limit context to avoid huge prompts
                    # Find key columns dynamically
                    col_artist = next((c for c in cols_clean if 'ARTIST' in c), None)
                    col_genre = next((c for c in cols_clean if 'GENRE' in c or 'ESTILO' in c), None)
                    col_bu = next((c for c in cols_clean if 'BU' in c or 'UNIT' in c), None)
                    
                    # Get top values for context
                    top_artists = df[col_artist].value_counts().head(5).index.tolist() if col_artist else []
                    top_genres = df[col_genre].value_counts().head(5).index.tolist() if col_genre else []
                    
                    # Columns summary
                    col_list = ", ".join(cols_clean)
                    
                    # Sample raw data (10 rows) to show structure
                    sample_rows = df.head(10)[[c for c in df.columns if 'CLEAN' in c or 'Year' in c or 'Month' in c]].to_string(index=False)
                    
                    prompt_sys = f"""YOU ARE THE SENIOR EDITORIAL STRATEGIST FOR ALISOS RECORDS.
YOUR MISSION: Analyze the Editorial Database to provide high-level insights using Python.

DATABASE CONTEXT:
- df: The primary source of truth.
- Columns: {col_list}, Year_Final, Month_Final.
- Sample Data:
{sample_rows}

INSTRUCTIONS:
1. ONLY produce Python code using `df`.
2. **STRICTLY CODE ONLY:** Do NOT include plain text outside backticks. Speak to the user inside code using `st.markdown("### 👑 Alisos Strategic Insights")`.
3. **PERSONA:** You are a friendly, elite Strategic Advisor for Alisos Records. Be polite, executive, and helpful.
4. **NO RAW TEXT:** NEVER output raw pandas Series or DataFrames (like those ending in `dtype: int64`).
5. **VISUALS MANDATORY:** For ANY data query, you MUST generate a BEAUTIFUL Plotly chart (use `px.area`, `px.bar`, or `px.line`).
   - Use `color_discrete_sequence=['#443392']`.
   - Set `template='plotly_white'`.
   - Set font to 'Plus Jakarta Sans'.
6. **KPI CARDS:** Use `st.columns()` and `st.metric()` to show important totals before the charts.
7. **CRITICAL: NO EXTERNAL WINDOWS.** Use `st.plotly_chart(fig, use_container_width=True)`.

USER QUERY: {prompt}
"""

                    # Use flash model first (fast), fallback to pro
                    primary = flash_model if flash_model else sel_model
                    fallback = sel_model if sel_model != primary else None
                    response = call_ai(prompt_sys, primary, fallback)
                    code = extract_code(response.text)
                    
                    # Sanitize: remove any import lines or DataFrame creation the AI might hallucinate
                    clean_lines = []
                    for line in code.split('\n'):
                        stripped = line.strip()
                        if stripped.startswith('import ') or stripped.startswith('from '):
                            continue
                        if 'pd.DataFrame(' in stripped and 'np.random' in code:
                            continue
                        if 'np.random.seed' in stripped:
                            continue
                        if 'np.repeat(' in stripped or 'np.random.choice(' in stripped:
                            continue
                        # Neutralize any .show() that might open a new tab
                        if '.show()' in line:
                            line = line.replace('.show()', '# .show() (Neutralized)')
                        clean_lines.append(line)
                    code = '\n'.join(clean_lines)
                    
                    # Check for truncated code (unclosed brackets)
                    opens = code.count('(') - code.count(')') + code.count('[') - code.count(']')
                    if opens > 0:
                        caja.warning("⚠️ Truncated code. Retrying with shorter response...")
                        prompt_retry = f"The previous code was too long and got cut off. Generate a SHORTER version (max 25 lines) that does the same. NO imports. NO comments.\n\nREQUEST: {prompt}\n\ndf has columns: {col_list}, Year_Final, Month_Final. Use .groupby().size() to count."
                        response2 = call_ai(prompt_retry, primary, fallback)
                        code = extract_code(response2.text)
                        # Re-sanitize
                        clean_lines = [l for l in code.split('\n') if not l.strip().startswith('import ') and not l.strip().startswith('from ')]
                        code = '\n'.join(clean_lines)
                    
                    if not code.strip():
                        caja.warning("⚠️ El modelo no generó código válido para ejecutar.")
                    else:
                        caja.info("🛠️ Executing code...")
                        
                        # Capture stdout just in case the AI uses print() instead of st.write()
                        import contextlib
                        f = io.StringIO()
                        with contextlib.redirect_stdout(f):
                            exec_globals = {
                                "df": df, "pd": pd, "np": np, "st": st, "px": px, "go": go,
                                "LinearRegression": LinearRegression,
                                "normalize_text": normalize_text, "unicodedata": unicodedata, "io": io
                            }
                            exec(code, exec_globals)
                        
                        caja.empty()
                        
                        # If meaningful stdout, show it and save to history
                        out = f.getvalue()
                        if out.strip():
                            st.text(out)
                            st.session_state.messages.append({"role": "assistant", "content": f"```\n{out}\n```"})
                        else:
                            # If no stdout, assume st.markdown/plotly rendered directly. 
                            # We can't easily capture st calls for history without rerunning, 
                            # so we add a generic success message to history.
                            st.session_state.messages.append({"role": "assistant", "content": "✅ Analysis completed."})
                            st.success("✅ Analysis completed.")

                except Exception as e:
                    caja.error(f"Error: {e}")
                    if code:
                        with st.expander("🔍 View generated code"): st.code(code, language='python')

    # ── TAB 3: DATA EXPLORER ──
    with tab_raw:
        st.markdown("""
        <div style='margin-bottom: 16px;'>
            <h2 style='margin: 0; font-size: 1.5rem;'>🔎 Data Explorer</h2>
            <p style='color: var(--text-sub) !important; font-size: 0.85rem; margin-top: 4px;'>Filter and explore data in detail</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Filters in a cleaner layout
        fr1, fr2, fr3 = st.columns([2, 2, 1])
        with fr1:
            years_available = sorted(df['Year_Final'].unique())
            sel_years = st.multiselect("📅 Year", years_available, default=years_available)
        with fr2:
            if col_dsp:
                dsps_available = sorted(df[col_dsp].unique())
                sel_dsps = st.multiselect("🎧 DSP", dsps_available, default=dsps_available)
        with fr3:
            search_text = st.text_input("🔍 Search", placeholder="Text...")
        
        filtered = df[df['Year_Final'].isin(sel_years)]
        if col_dsp and sel_dsps:
            filtered = filtered[filtered[col_dsp].isin(sel_dsps)]
        
        # Apply text search across all string columns
        if search_text:
            mask = filtered.apply(lambda row: row.astype(str).str.contains(search_text, case=False).any(), axis=1)
            filtered = filtered[mask]
        
        # Stats row
        s1, s2, s3, s4 = st.columns(4)
        s1.metric("Records", f"{len(filtered):,}")
        s2.metric("% of Total", f"{len(filtered)/len(df)*100:.1f}%")
        s3.metric("DSPs", f"{filtered[col_dsp].nunique() if col_dsp else 0}")
        s4.metric("Years", f"{filtered['Year_Final'].nunique()}")
        
        st.dataframe(filtered, use_container_width=True, height=500)
