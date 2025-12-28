import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta, timezone
import gspread

# =========================================================
# 0) 系統設定
# =========================================================
st.set_page_config(
    page_title="福德里社區管理系統",
    page_icon="🏘️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 🔥 莫蘭迪配色定義
COLORS = {
    "volunteer": "#9A8C98", # 煙燻紫
    "elderly": "#B5838D",   # 暮色粉
    "care": "#8E9775",      # 鼠尾草綠
    "bg": "#F8F9FA"         # 極淺灰底
}

# =========================================================
# 1) CSS 樣式
# =========================================================
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@500;700;900&display=swap');
html, body, [class*="css"], div, p, span, li, ul {{
    font-family: "Noto Sans TC", "Microsoft JhengHei", sans-serif;
}}
[data-testid="stSidebar"] {{ display: none; }}
.stApp {{ background-color: {COLORS['bg']}; }}

/* 大按鈕卡片樣式 */
.big-btn {{
    width: 100%;
    padding: 30px 20px;
    border-radius: 25px;
    text-align: center;
    background-color: white;
    box-shadow: 0 10px 30px rgba(0,0,0,0.05);
    border: 1px solid rgba(0,0,0,0.05);
    transition: all 0.3s ease;
    margin-bottom: 15px;
    height: 320px; /* 固定高度讓版面整齊 */
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
}}
.big-btn:hover {{
    transform: translateY(-8px);
    box-shadow: 0 15px 40px rgba(0,0,0,0.1);
}}
.icon {{ font-size: 3.5rem; margin-bottom: 15px; display: block; }}
.btn-title {{ font-size: 1.6rem; font-weight: 900; margin-bottom: 15px; display: block; }}

/* 數據顯示區樣式 */
.stats-container {{
    text-align: left;
    width: 100%;
    padding: 0 10px;
    margin-top: 5px;
}}
.stat-row {{
    display: flex;
    justify-content: space-between;
    font-size: 0.95rem;
    color: #666;
    margin-bottom: 8px;
    border-bottom: 1px dashed #eee;
    padding-bottom: 4px;
}}
.stat-val {{
    font-weight: 900;
    font-size: 1.1rem;
}}

/* 莫蘭迪色系文字設定 */
.theme-vol {{ color: {COLORS['volunteer']}; }}
.theme-elder {{ color: {COLORS['elderly']}; }}
.theme-care {{ color: {COLORS['care']}; }}

/* 按鈕樣式微調 */
div[data-testid="stButton"] > button {{
    border-radius: 50px !important;
    font-weight: 700 !important;
    padding: 10px 20px !important;
    border: 1.5px solid transparent !important;
    margin-top: -10px; /* 拉近與卡片的距離 */
}}
.st-vol button {{ background-color: {COLORS['volunteer']} !important; color: white !important; }}
.st-elder button {{ background-color: {COLORS['elderly']} !important; color: white !important; }}
.st-care button {{ background-color: {COLORS['care']} !important; color: white !important; }}
</style>
""", unsafe_allow_html=True)

# =========================================================
# 2) 數據計算邏輯 (從 Google Sheet 抓取)
# =========================================================
SHEET_ID = "1A3-VwCBYjnWdcEiL6VwbV5-UECcgX7TqKH94sKe8P90"

@st.cache_resource
def get_client():
    return gspread.service_account_from_dict(st.secrets["gcp_service_account"])

@st.cache_data(ttl=300) # 緩存 5 分鐘，避免每次重新整理都跑去抓資料
def load_all_stats():
    client = get_client()
    sh = client.open_by_key(SHEET_ID)
    
    # 預設值
    stats = {
        "vol_count": 0, "vol_age": 0, "vol_hours": 0,
        "eld_count": 0, "eld_age": 0,
        "care_count": 0, "care_items": 0
    }
    
    try:
        # 1. 志工數據
        df_v = pd.DataFrame(sh.worksheet("members").get_all_records()).astype(str)
        df_vl = pd.DataFrame(sh.worksheet("logs").get_all_records()).astype(str)
        
        if not df_v.empty:
            stats["vol_count"] = len(df_v)
            # 計算平均年齡
            df_v['age'] = df_v['生日'].apply(calculate_age)
            avg = df_v[df_v['age'] > 0]['age'].mean()
            stats["vol_age"] = round(avg, 1) if pd.notnull(avg) else 0
            
        if not df_vl.empty:
            stats["vol_hours"] = calculate_year_hours(df_vl)

        # 2. 長輩數據
        df_e = pd.DataFrame(sh.worksheet("elderly_members").get_all_records()).astype(str)
        if not df_e.empty:
            stats["eld_count"] = len(df_e)
            df_e['age'] = df_e['出生年月日'].apply(calculate_age)
            avg = df_e[df_e['age'] > 0]['age'].mean()
            stats["eld_age"] = round(avg, 1) if pd.notnull(avg) else 0

        # 3. 關懷戶數據
        df_c = pd.DataFrame(sh.worksheet("care_members").get_all_records()).astype(str)
        df_cl = pd.DataFrame(sh.worksheet("care_logs").get_all_records()).astype(str)
        
        if not df_c.empty:
            stats["care_count"] = len(df_c)
            
        if not df_cl.empty:
            cur_year = datetime.now().year
            df_cl['dt'] = pd.to_datetime(df_cl['發放日期'], errors='coerce')
            df_cl['qty'] = pd.to_numeric(df_cl['發放數量'], errors='coerce').fillna(0)
            # 統計當年度發放總量
            stats["care_items"] = int(df_cl[df_cl['dt'].dt.year == cur_year]['qty'].sum())

    except Exception as e:
        print(f"數據讀取錯誤: {e}")
    
    return stats

def calculate_age(dob_str):
    try:
        b_date = datetime.strptime(str(dob_str).strip(), "%Y-%m-%d").date()
        today = date.today()
        return today.year - b_date.year - ((today.month, today.day) < (b_date.month, b_date.day))
    except: return 0

def calculate_year_hours(logs_df):
    """計算當年度志工總時數"""
    try:
        cur_year = datetime.now().year
        logs_df['dt'] = pd.to_datetime(logs_df['日期'] + ' ' + logs_df['時間'], errors='coerce')
        logs_df = logs_df.dropna(subset=['dt'])
        year_logs = logs_df[logs_df['dt'].dt.year == cur_year].sort_values(['姓名', 'dt'])
        
        total_seconds = 0
        for (name, d), group in year_logs.groupby(['姓名', '日期']):
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
                else: i += 1
        return int(total_seconds // 3600)
    except: return 0

# =========================================================
# 3) 頁面呈現
# =========================================================

# 讀取數據 (有快取，速度快)
data = load_all_stats()

st.markdown("<h1 style='text-align: center; color: #444; margin-top: 20px;'>🏘️ 福德里社區管理中樞</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center; color: #888; font-size: 1.2rem; margin-bottom: 40px;'>人文關懷．數位整合 ({datetime.now().year} 年度)</p>", unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)

# 1. 志工系統卡片
with c1:
    html_vol = f"""
    <div class="big-btn">
        <span class="icon">💜</span>
        <span class="btn-title theme-vol">志工管理</span>
        <div class="stats-container">
            <div class="stat-row"><span>👥 志工總數</span><span class="stat-val theme-vol">{data['vol_count']} 人</span></div>
            <div class="stat-row"><span>🎂 平均年齡</span><span class="stat-val theme-vol">{data['vol_age']} 歲</span></div>
            <div class="stat-row" style="border-bottom:none;"><span>⏳ 本年服務</span><span class="stat-val theme-vol">{data['vol_hours']} 小時</span></div>
        </div>
    </div>
    """
    st.markdown(html_vol, unsafe_allow_html=True)
    st.markdown('<div class="st-vol">', unsafe_allow_html=True)
    if st.button("點擊進入志工系統", use_container_width=True): st.switch_page("pages/1_volunteer.py")
    st.markdown('</div>', unsafe_allow_html=True)

# 2. 長輩系統卡片
with c2:
    html_elder = f"""
    <div class="big-btn">
        <span class="icon">👴</span>
        <span class="btn-title theme-elder">長輩關懷</span>
        <div class="stats-container">
            <div class="stat-row"><span>👥 長者總數</span><span class="stat-val theme-elder">{data['eld_count']} 人</span></div>
            <div class="stat-row"><span>🎂 平均年齡</span><span class="stat-val theme-elder">{data['eld_age']} 歲</span></div>
            <div class="stat-row" style="border-bottom:none;"><span>📅 資料更新</span><span class="stat-val theme-elder">即時</span></div>
        </div>
    </div>
    """
    st.markdown(html_elder, unsafe_allow_html=True)
    st.markdown('<div class="st-elder">', unsafe_allow_html=True)
    if st.button("點擊進入長輩系統", use_container_width=True): st.switch_page("pages/2_elderly.py")
    st.markdown('</div>', unsafe_allow_html=True)

# 3. 關懷戶系統卡片
with c3:
    html_care = f"""
    <div class="big-btn">
        <span class="icon">🏠</span>
        <span class="btn-title theme-care">關懷戶系統</span>
        <div class="stats-container">
            <div class="stat-row"><span>📉 關懷戶數</span><span class="stat-val theme-care">{data['care_count']} 戶</span></div>
            <div class="stat-row"><span>📦 物資發放</span><span class="stat-val theme-care">{data['care_items']} 份</span></div>
            <div class="stat-row" style="border-bottom:none;"><span>📊 統計區間</span><span class="stat-val theme-care">{datetime.now().year}年</span></div>
        </div>
    </div>
    """
    st.markdown(html_care, unsafe_allow_html=True)
    st.markdown('<div class="st-care">', unsafe_allow_html=True)
    if st.button("點擊進入關懷戶系統", use_container_width=True): st.switch_page("pages/3_care.py")
    st.markdown('</div>', unsafe_allow_html=True)
