import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from supabase import create_client, Client
import os
import base64

# =========================================================
# 0) 系統設定
# =========================================================
st.set_page_config(
    page_title="福德里社區管理系統",
    page_icon="🏘️",
    layout="wide",
    initial_sidebar_state="expanded" 
)

# =========================================================
# 1) CSS 樣式 (V31.0 數據儀表板版)
# =========================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@500;700;900&display=swap');

html, body, [class*="css"], div, p, span, li, ul {
    font-family: "Noto Sans TC", "Microsoft JhengHei", sans-serif;
    color: #333333;
}

.stApp { background-color: #F0F2F5 !important; }
section[data-testid="stSidebar"] { background-color: #F0F2F5; border-right: none; }

/* 懸浮大卡片 */
.block-container {
    background-color: #FFFFFF;
    border-radius: 25px;
    padding: 3rem 4rem !important;
    box-shadow: 0 4px 20px rgba(0,0,0,0.05);
    margin-top: 2rem; margin-bottom: 2rem;
    max-width: 1100px !important;
}

@media (max-width: 1000px) {
    .block-container { padding: 2rem 1.5rem !important; }
}

header[data-testid="stHeader"] { background-color: transparent !important; }
header[data-testid="stHeader"] .decoration { display: none; }

/* 側邊欄按鈕 */
section[data-testid="stSidebar"] button {
    background-color: #FFFFFF !important; color: #555 !important;
    border: 1px solid transparent !important; box-shadow: 0 2px 5px rgba(0,0,0,0.05) !important;
    border-radius: 25px !important; padding: 12px 0 !important;
    font-weight: 700 !important; width: 100%; margin-bottom: 10px !important;
    transition: all 0.3s;
}
section[data-testid="stSidebar"] button:hover {
    transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0,0,0,0.1) !important;
    color: #000 !important; border: 1px solid #ddd !important;
}

/* 首頁標題 */
.hero-title {
    font-size: 2.5rem; font-weight: 900; color: #2c3e50;
    text-align: center; margin-bottom: 10px;
}
.hero-subtitle {
    font-size: 1.2rem; color: #7f8c8d; text-align: center; margin-bottom: 50px;
}

/* --- 服務卡片 (Service Box) --- */
.service-box {
    display: flex; 
    flex-direction: row; 
    background-color: #F8F9FA; border-radius: 20px;
    padding: 0; margin-bottom: 30px; overflow: hidden;
    border: 1px solid #eee; transition: transform 0.3s;
    min-height: 250px; 
}
.service-box:hover {
    transform: translateY(-5px); box-shadow: 0 10px 20px rgba(0,0,0,0.08);
}

.service-img {
    width: 40%;
    background-size: cover; background-position: center;
    display: flex; align-items: center; justify-content: center;
}
.service-content {
    width: 60%;
    padding: 30px;
    display: flex; flex-direction: column; justify-content: center;
}

@media (max-width: 1000px) {
    .service-box { flex-direction: column !important; height: auto !important; }
    .service-img { width: 100% !important; height: 200px !important; min-height: 200px !important; }
    .service-content { width: 100% !important; padding: 25px !important; }
    .hero-title { font-size: 2rem !important; }
}

.service-title { font-size: 1.8rem; font-weight: 900; margin-bottom: 10px; }
.service-desc { font-size: 1rem; color: #666; line-height: 1.6; margin-bottom: 15px; }
.service-icon-placeholder { font-size: 5rem; }

/* 數據統計樣式 */
.stats-row {
    display: flex; gap: 15px; flex-wrap: wrap; margin-top: 10px;
}
.stat-item {
    background-color: #FFFFFF;
    border: 1px solid #E0E0E0;
    border-radius: 10px;
    padding: 8px 15px;
    font-size: 0.9rem;
    color: #444;
    font-weight: 500;
    display: flex; align-items: center; gap: 8px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.03);
}
.stat-item b { color: #000; font-size: 1.1rem; margin-left: 5px; }
</style>
""", unsafe_allow_html=True)

# =========================================================
# 2) 邏輯處理：資料庫讀取與計算 (Supabase 版)
# =========================================================
@st.cache_resource
def get_supabase_client():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

def calculate_age(dob_str):
    try:
        b_date = datetime.strptime(str(dob_str).strip(), "%Y-%m-%d").date()
        today = date.today()
        return today.year - b_date.year - ((today.month, today.day) < (b_date.month, b_date.day))
    except: return 0

def check_is_fully_retired(row):
    roles = [
        ('祥和_加入日期', '祥和_退出日期'), 
        ('據點週二_加入日期', '據點週二_退出日期'), 
        ('據點週三_加入日期', '據點週三_退出日期'), 
        ('環保_加入日期', '環保_退出日期')
    ]
    has_any = False 
    is_active = False 
    
    for join_col, exit_col in roles:
        join_val = str(row.get(join_col, '')).strip()
        if join_val and join_val != 'nan':
            has_any = True
            exit_val = str(row.get(exit_col, '')).strip()
            if not exit_val or exit_val == 'nan': 
                is_active = True
    
    if not has_any: return False 
    return not is_active

def calculate_year_hours(logs_df):
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

@st.cache_data(ttl=60)
def load_dashboard_stats():
    stats = {
        "vol_count": 0, "vol_age": 0, "vol_hours": 0,
        "eld_count": 0, "eld_age": 0,
        "care_count": 0, "care_items": 0
    }
    
    try:
        supabase = get_supabase_client()
        
        # 1. 抓取主檔
        res_master = supabase.table("master_residents").select("*").execute()
        df_m = pd.DataFrame(res_master.data) if res_master.data else pd.DataFrame()
        
        # 2. 抓取志工打卡
        res_vl = supabase.table("logs").select("*").execute()
        df_vl = pd.DataFrame(res_vl.data) if res_vl.data else pd.DataFrame()
        
        # 3. 抓取關懷戶發放紀錄
        res_cl = supabase.table("care_logs").select("*").execute()
        df_cl = pd.DataFrame(res_cl.data) if res_cl.data else pd.DataFrame()
        
        if not df_m.empty:
            df_m['age'] = df_m['出生年月日'].apply(calculate_age)
            
            # --- 志工數據 ---
            df_v = df_m[df_m['身分_志工'].astype(str).str.upper() == 'TRUE']
            if not df_v.empty:
                active_volunteers = df_v[~df_v.apply(check_is_fully_retired, axis=1)]
                stats["vol_count"] = len(active_volunteers)
                valid_ages = active_volunteers[active_volunteers['age'] > 0]['age']
                stats["vol_age"] = round(valid_ages.mean(), 1) if not valid_ages.empty else 0
                
            # --- 長輩數據 ---
            df_e = df_m[df_m['身分_據點長輩'].astype(str).str.upper() == 'TRUE']
            if not df_e.empty:
                stats["eld_count"] = len(df_e)
                valid_ages = df_e[df_e['age'] > 0]['age']
                stats["eld_age"] = round(valid_ages.mean(), 1) if not valid_ages.empty else 0

            # --- 關懷戶數據 ---
            df_c = df_m[df_m['身分_關懷戶'].astype(str).str.upper() == 'TRUE']
            if not df_c.empty:
                stats["care_count"] = len(df_c)
                
        if not df_vl.empty:
            stats["vol_hours"] = calculate_year_hours(df_vl)
            
        if not df_cl.empty:
            cur_year = datetime.now().year
            df_cl['dt'] = pd.to_datetime(df_cl['發放日期'], errors='coerce')
            df_cl['qty'] = pd.to_numeric(df_cl['發放數量'], errors='coerce').fillna(0)
            stats["care_items"] = int(df_cl[df_cl['dt'].dt.year == cur_year]['qty'].sum())

    except Exception as e:
        print(f"Stats Error: {e}")
    
    return stats

def get_image_as_base64(path):
    try:
        with open(path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except Exception:
        return None

# =========================================================
# 3) 頁面渲染
# =========================================================
with st.sidebar:
    st.markdown("<h2 style='text-align:center; color:#333; margin-bottom:20px;'>🚀 系統快速入口</h2>", unsafe_allow_html=True)
    if st.button("💜 進入 志工管理系統"): st.switch_page("pages/1_volunteer.py")
    if st.button("👴 進入 長輩關懷系統"): st.switch_page("pages/2_elderly.py")
    if st.button("🏠 進入 關懷戶系統"): st.switch_page("pages/3_care.py")
    st.markdown("---")
    st.markdown("<div style='text-align:center; color:#999; font-size:0.8rem; margin-top:20px;'>福德里辦公處 © 2026</div>", unsafe_allow_html=True)

st.markdown('<div class="hero-title">🏘️ 福德里 - 社區數位管理中樞</div>', unsafe_allow_html=True)
st.markdown(f'<div class="hero-subtitle">志工調度．長輩照護．弱勢關懷．一站整合 ({datetime.now().year} 年度數據)</div>', unsafe_allow_html=True)
st.markdown("---")

# 讀取數據
data = load_dashboard_stats()

# 定義服務內容與對應數據
services = [
    {
        "title": "志工管理系統",
        "desc": "整合志工排班、時數統計與榮譽名冊。透過數位化管理，讓志工服務歷程清晰可見，並能快速調度人力支援社區活動。",
        "color": "#4A148C",
        "icon": "💜",
        "img_file": "volunteer.jpg",
        "stats": [
            f"👥 志工總數: <b>{data['vol_count']}</b> 人",
            f"🎂 平均年齡: <b>{data['vol_age']}</b> 歲",
            f"⏳ 本年服務: <b>{data['vol_hours']}</b> 小時"
        ]
    },
    {
        "title": "長輩關懷系統",
        "desc": "針對社區長者提供據點報到、血壓健康追蹤與活動參與記錄。透過數據分析，主動關懷長輩健康狀況，落實在地安老。",
        "color": "#EF6C00",
        "icon": "👴",
        "img_file": "elderly.jpg",
        "stats": [
            f"👥 長者總數: <b>{data['eld_count']}</b> 人",
            f"🎂 平均年齡: <b>{data['eld_age']}</b> 歲"
        ]
    },
    {
        "title": "關懷戶系統",
        "desc": "建立弱勢家庭數位名冊，記錄物資發放與訪視歷程。確保資源能精準送達需要的人手中，不遺漏任何一個角落。",
        "color": "#2E7D32",
        "icon": "🏠",
        "img_file": "care.jpg",
        "stats": [
            f"📉 關懷戶數: <b>{data['care_count']}</b> 戶",
            f"📦 本年發放: <b>{data['care_items']}</b> 份"
        ]
    }
]

# 渲染卡片
for svc in services:
    # 處理圖片
    img_html = f"""<div class="service-img" style="background-color: {svc['color']}15;"><div class="service-icon-placeholder">{svc['icon']}</div></div>"""
    if os.path.exists(svc['img_file']):
        img_b64 = get_image_as_base64(svc['img_file'])
        if img_b64:
            ext = svc['img_file'].split('.')[-1].lower()
            mime = "image/png" if ext == 'png' else "image/jpeg"
            img_html = f"""<div class="service-img" style="background-image: url('data:{mime};base64,{img_b64}');"></div>"""

    # 產生數據 HTML
    stats_html = "".join([f'<div class="stat-item" style="border-left: 4px solid {svc["color"]};">{s}</div>' for s in svc['stats']])

    st.markdown(f"""
<div class="service-box">
{img_html}
<div class="service-content">
<div class="service-title" style="color: {svc['color']}">{svc['title']}</div>
<div class="service-desc">{svc['desc']}</div>
<div class="stats-row">
{stats_html}
</div>
</div>
</div>
""", unsafe_allow_html=True)
