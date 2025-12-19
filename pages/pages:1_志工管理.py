import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta, timezone
import gspread
import time
import plotly.express as px
import os
import base64

# --- 1. 🎨 視覺美學設定 (V8.0 完美對齊+卡片回歸版) ---
st.set_page_config(page_title="志工管理系統", page_icon="💜", layout="wide")

TW_TZ = timezone(timedelta(hours=8))
PRIMARY = "#4A148C"    # 尊爵紫 (深)
ACCENT = "#7B1FA2"     # 亮紫
BG_MAIN = "#F3F4F6"    # 極淺灰背景

st.markdown(f"""
    <style>
    /* 全域字體 */
    html, body, [class*="css"], .stMarkdown, div, p {{
        color: #212121 !important;
        font-family: "Microsoft JhengHei", "微軟正黑體", sans-serif;
    }}
    .stApp {{ background-color: {BG_MAIN}; }}
    
    /* 🔥 1. 圖片容器終極對齊術 */
    div[data-testid="stImage"] {{
        height: 100px;              /* 設定固定高度 */
        display: flex;
        align-items: center;        /* 垂直置中 */
        justify-content: center;    /* 水平置中 */
        margin-bottom: 5px;         /* 與下方按鈕的距離 */
        overflow: hidden;           /* 超出範圍隱藏 */
    }}
    div[data-testid="stImage"] img {{
        max-height: 90px !important;  /* 圖片最大高度 */
        max-width: 100px !important;  /* 圖片最大寬度 */
        object-fit: contain !important; /* 🔥 關鍵：保持比例，完整顯示 */
        padding: 5px;
    }}

    /* 🔥 2. 找回您喜歡的「大卡片按鈕」樣式 */
    .stButton>button {{
        width: 100%;
        height: auto;               /* 高度自動 */
        padding: 15px 0;            /* 增加內距 */
        background-color: white !important;
        color: {PRIMARY} !important;
        border: 2px solid {PRIMARY} !important; /* 深紫邊框 */
        border-radius: 15px !important;
        font-size: 20px !important;
        font-weight: 900 !important;
        box-shadow: 0 4px 0px rgba(74, 20, 140, 0.2); /* 立體陰影 */
        transition: all 0.2s;
    }}
    .stButton>button:hover {{
        transform: translateY(-3px);
        background-color: #F3E5F5 !important; /* 滑鼠移過去變淺紫 */
        box-shadow: 0 6px 0px rgba(74, 20, 140, 0.3);
    }}
    .stButton>button:active {{
        transform: translateY(2px);
        box-shadow: none;
    }}
    
    /* 輸入框白底黑字 */
    .stTextInput input, .stSelectbox div[data-baseweb="select"], .stDateInput input, .stTimeInput input {{
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border: 1px solid #9FA8DA !important;
        border-radius: 8px;
    }}
    .stTextInput label, .stSelectbox label, .stDateInput label {{
        color: {PRIMARY} !important;
        font-weight: bold;
    }}
    
    /* 統計小卡 (戰情室) */
    .dash-card {{
        background-color: white;
        padding: 15px;
        border-radius: 12px;
        border-left: 5px solid {ACCENT};
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        margin-bottom: 10px;
    }}
    .dash-label {{ font-size: 1rem; color: #666; font-weight: bold; }}
    .dash-value {{ font-size: 1.8rem; color: {PRIMARY}; font-weight: 900; margin: 5px 0; }}
    .dash-sub {{ font-size: 0.9rem; color: #888; }}

    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    </style>
""", unsafe_allow_html=True)

# --- 2. 🔗 Google Sheets 連線 ---
SHEET_ID = "1A3-VwCBYjnWdcEiL6VwbV5-UECcgX7TqKH94sKe8P90"

ALL_CATEGORIES = ['祥和志工', '關懷據點週二志工', '關懷據點週三志工', '環保志工', '臨時志工']
DEFAULT_ACTIVITIES = ['關懷據點週二活動', '關懷據點週三活動', '環保清潔', '專案活動', '教育訓練']
DISPLAY_ORDER = [
    '姓名', '身分證字號', '性別', '電話', '志工分類', '生日', '地址', '備註',
    '祥和_加入日期', '祥和_退出日期', 
    '據點週二_加入日期', '據點週二_退出日期',
    '據點週三_加入日期', '據點週三_退出日期', 
    '環保_加入日期', '環保_退出日期'
]

@st.cache_resource
def get_google_sheet_client():
    return gspread.service_account_from_dict(st.secrets["gcp_service_account"])

@st.cache_data(ttl=60)
def load_data_from_sheet(sheet_name):
    try:
        client = get_google_sheet_client()
        sheet = client.open_by_key(SHEET_ID).worksheet(sheet_name)
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        df = df.astype(str)
        if sheet_name == 'members':
            for c in DISPLAY_ORDER:
                if c not in df.columns: df[c] = ""
        elif sheet_name == 'logs':
            required = ['姓名', '身分證字號', '電話', '志工分類', '動作', '時間', '日期', '活動內容']
            for c in required:
                if c not in df.columns: df[c] = ""
        return df
    except Exception as e:
        return pd.DataFrame()

def save_data_to_sheet(df, sheet_name):
    try:
        client = get_google_sheet_client()
        sheet = client.open_by_key(SHEET_ID).worksheet(sheet_name)
        sheet.clear()
        sheet.update([df.columns.values.tolist()] + df.values.tolist())
        load_data_from_sheet.clear()
    except Exception as e:
        st.error(f"寫入失敗：{e}")

# --- 3. 🧮 邏輯運算 ---
def get_tw_time():
    return datetime.now(TW_TZ)

def calculate_age(birthday_str):
    if not birthday_str or len(birthday_str) < 4: return 0
    try:
        b_date = None
        for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d", "%Y%m%d"]:
            try:
                b_date = datetime.strptime(birthday_str, fmt)
                break
            except: continue
        if b_date:
            today = date.today()
            age = today.year - b_date.year - ((today.month, today.day) < (b_date.month, b_date.day))
            return age
        else: return 0
    except: return 0

def check_is_fully_retired(row):
    roles = [('祥和_加入日期', '祥和_退出日期'), ('據點週二_加入日期', '據點週二_退出日期'),
             ('據點週三_加入日期', '據點週三_退出日期'), ('環保_加入日期', '環保_退出日期')]
    has_any_role = False
    is_active = False
    for join_col, exit_col in roles:
        if join_col in row and str(row[join_col]).strip() != "":
            has_any_role = True
            if not (exit_col in row and str(row[exit_col]).strip() != ""):
                is_active = True
    if not has_any_role: return False 
    return not is_active

def calculate_hours_year(logs_df, year):
    if logs_df.empty: return 0
    logs_df['dt'] = pd.to_datetime(logs_df['日期'] + ' ' + logs_df['時間'], errors='coerce')
    logs_df = logs_df.dropna(subset=['dt'])
    year_logs = logs_df[logs_df['dt'].dt.year == year].copy()
    if year_logs.empty: return 0
    total_seconds = 0
    year_logs = year_logs.sort_values(['姓名', 'dt'])
    for (name, date_val), group in year_logs.groupby(['姓名', '日期']):
        actions = group['動作'].tolist()
        times = group['dt'].tolist()
        i = 0
        while i < len(actions):
            if actions[i] == '簽到':
                for j in range(i + 1, len(actions)):
                    if actions[j] == '簽退':
                        total_seconds += (times[j] - times[i]).total_seconds()
                        i = j
                        break
                i += 1
            else:
                i += 1
    return total_seconds

# --- 4. 🖥️ UI 導航 ---
if 'page' not in st.session_state:
    st.session_state.page = 'home'

if st.session_state.page != 'home':
    with st.container():
        c1, c2, c3, spacer = st.columns([1, 1, 1, 4])
        with c1:
            if st.button("🏠 首頁", use_container_width=True): st.session_state.page = 'home'; st.rerun()
        with c2:
            if st.button("⏰ 打卡", use_container_width=True): st.session_state.page = 'checkin'; st.rerun()
        with c3:
            if st.button("📊 報表", use_container_width=True): st.session_state.page = 'report'; st.rerun()
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

# === 🏠 首頁 (卡片回歸+圖片對齊) ===
if st.session_state.page == 'home':
    st.markdown(f"<h1 style='text-align: center; color: {PRIMARY}; margin-bottom: 30px;'>💜 福德里 - 志工管理系統</h1>", unsafe_allow_html=True)
    
    # 版面：置中
    col_spacer_l, c1, c2, c3, col_spacer_r = st.columns([1, 2, 2, 2, 1])
    
    # 🔥 1. 智能打卡
    with c1:
        # 圖片
        if os.path.exists("icon_checkin.png"):
            st.image("icon_checkin.png") # 因為 CSS 已經控制了 stImage，所以這裡直接呼叫即可
        else:
            st.markdown("<div style='text-align:center; font-size:60px;'>⏰</div>", unsafe_allow_html=True)
        # 按鈕 (卡片樣式)
        if st.button("智能打卡站", key="home_btn1"):
            st.session_state.page = 'checkin'; st.rerun()

    # 🔥 2. 志工名冊
    with c2:
        if os.path.exists("icon_members.png"):
            st.image("icon_members.png")
        else:
            st.markdown("<div style='text-align:center; font-size:60px;'>📋</div>", unsafe_allow_html=True)
        if st.button("志工名冊", key="home_btn2"):
            st.session_state.page = 'members'; st.rerun()

    # 🔥 3. 數據分析
    with c3:
        if os.path.exists("icon_report.png"):
            st.image("icon_report.png")
        else:
            st.markdown("<div style='text-align:center; font-size:60px;'>📊</div>", unsafe_allow_html=True)
        if st.button("數據分析", key="home_btn3"):
            st.session_state.page = 'report'; st.rerun()
    
    st.markdown("---")
    st.markdown(f"### 📊 {datetime.now().year} 年度即時概況")
    
    logs = load_data_from_sheet("logs")
    members = load_data_from_sheet("members")
    
    this_year = datetime.now().year
    total_sec = calculate_hours_year(logs, this_year)
    total_hours = int(total_sec // 3600)
    total_mins = int((total_sec % 3600) // 60)
    
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #7E57C2 0%, #512DA8 100%); padding: 25px; border-radius: 15px; color: white; text-align: center; margin-bottom: 20px; box-shadow: 0 4px 10px rgba(81, 45, 168, 0.3);">
        <div style="font-size: 1.2rem; opacity: 0.9;">📅 {this_year} 年度 - 全體志工總服務時數</div>
        <div style="font-size: 3.5rem; font-weight: 900; margin: 10px 0;">{total_hours} <span style="font-size: 1.5rem;">小時</span> {total_mins} <span style="font-size: 1.5rem;">分</span></div>
    </div>
    """, unsafe_allow_html=True)
    
    if not members.empty:
        active_m = members[~members.apply(check_is_fully_retired, axis=1)].copy()
        active_m['age'] = active_m['生日'].apply(calculate_age)
        valid_age = active_m[active_m['age'] > 0]
        
        cols = st.columns(4)
        for idx, cat in enumerate(ALL_CATEGORIES):
            if cat == "臨時志工": continue
            subset = active_m[active_m['志工分類'].astype(str).str.contains(cat, na=False)]
            count = len(subset)
            age_subset = valid_age[valid_age['志工分類'].astype(str).str.contains(cat, na=False)]
            avg_age = round(age_subset['age'].mean(), 1) if not age_subset.empty else 0
            
            with cols[idx % 4]:
                st.markdown(f"""
                <div class="dash-card">
                    <div class="dash-label">{cat.replace('志工','')}</div>
                    <div class="dash-value">{count} <span style="font-size:1rem;color:#888;">人</span></div>
                    <div class="dash-sub">平均 {avg_age} 歲</div>
                </div>
                """, unsafe_allow_html=True)

# === ⏰ 打卡頁 ===
elif st.session_state.page == 'checkin':
    st.markdown("## ⏰ 智能打卡站")
    tw_now = get_tw_time()
    st.caption(f"📅 台灣時間：{tw_now.strftime('%Y-%m-%d %H:%M:%S')}")
    
    if 'scan_cooldowns' not in st.session_state: st.session_state['scan_cooldowns'] = {}
    
    tab1, tab2, tab3 = st.tabs(["⚡️ 現場打卡", "🛠️ 補登
