import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta, timezone
from supabase import create_client, Client
import time
import os
import plotly.express as px
import random

# =========================================================
# 0) 系統設定 (🎨 這裡可以調整全站基礎設定)
# =========================================================
st.set_page_config(
    page_title="長輩關懷系統",
    page_icon="👴",
    layout="wide",
    initial_sidebar_state="expanded", 
)

# 初始化頁面狀態
if 'page' not in st.session_state: st.session_state.page = 'home'
# 初始化名冊解鎖狀態 (預設鎖住)
if 'unlock_elder_list' not in st.session_state: st.session_state.unlock_elder_list = False

TW_TZ = timezone(timedelta(hours=8))

# 🎨【配色調整區】修改這邊的色碼，可以改變整站的主題色
PRIMARY = "#EF6C00"   # 🔥 主色調：用於按鈕背景、強調文字 (目前是深橙色)
ACCENT  = "#FFA726"   # ✨ 輔助色：用於邊框、裝飾線條 (目前是亮橙色)
BG_MAIN = "#F0F2F5"   # 🌫️ 網頁大背景顏色 (目前是淺灰)
TEXT    = "#212121"   # 📝 主要文字顏色 (目前是深灰)

# =========================================================
# 1) CSS 樣式 (已加入詳細註解，方便您調整)
# =========================================================
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@500;700;900&display=swap');

/* 全站文字字型設定 */
html, body, [class*="css"], div, p, span, li, ul {{
    font-family: "Noto Sans TC", "Microsoft JhengHei", sans-serif;
    color: {TEXT} !important;
}}

/* 🌫️ 1. 整體網頁背景顏色 */
.stApp {{
    background-color: {BG_MAIN} !important;
}}

/* 🗂️ 2. 側邊欄 (Sidebar) 設定 */
section[data-testid="stSidebar"] {{
    background-color: {BG_MAIN};  /* 讓側邊欄跟背景同色，看起來更寬闊 */
    border-right: none;           /* 去掉側邊欄右邊那條死板的分隔線 */
    min-width: 200px !important;  /* 新增：限制最小寬度 */
    max-width: 220px !important;  /* 新增：限制最大寬度，避免在平板上佔用過多空間 */
}}

/* ⬜ 3. 【關鍵】主內容區的「懸浮大卡片」樣式 */
.block-container {{
    background-color: #FFFFFF;      /* ⬜ 卡片背景色 (白色) */
    border-radius: 25px;            /* 📏 圓角大小 (數字越大越圓) */
    padding: 3rem 3rem !important;  /* ↔️ 內距：控制內容離邊框的距離 */
    box-shadow: 0 4px 20px rgba(0,0,0,0.05); /* 🌫️ 陰影：讓卡片有浮起來的感覺 */
    margin-top: 2rem;               /* ⬆️ 距離視窗頂部的距離 */
    margin-bottom: 2rem;            /* ⬇️ 距離視窗底部的距離 */
    max-width: 95% !important;      /* ↔️ 卡片寬度 (佔螢幕 95%) */
}}

/* 頂部 Header 設定 (保持透明，不擋住內容) */
header[data-testid="stHeader"] {{
    display: block !important;
    background-color: transparent !important;
}}
header[data-testid="stHeader"] .decoration {{ display: none; }}

/* 🔘 4. 側邊欄按鈕樣式 */
section[data-testid="stSidebar"] button {{
    background-color: #FFFFFF !important;
    color: #666 !important;
    border: 1px solid transparent !important;
    box-shadow: 0 4px 6px rgba(0,0,0,0.05) !important;
    border-radius: 25px !important;  /* 📏 按鈕圓角 */
    padding: 10px 0 !important;      /* ↕️ 按鈕高度 */
    font-weight: 700 !important;
    width: 100%; 
    margin-bottom: 8px !important;   /* ⬇️ 按鈕之間的間距 */
    transition: all 0.2s;            /* 動畫過渡效果 */
}}
/* 滑鼠移過去按鈕時的特效 */
section[data-testid="stSidebar"] button:hover {{
    transform: translateY(-2px);     /* 微微上浮 */
    box-shadow: 0 6px 12px rgba(0,0,0,0.1) !important;
    color: {PRIMARY} !important;     /* 變色 */
}}

/* 🌟 5. 側邊欄「目前選中」的按鈕樣式 */
.nav-active {{
    background: linear-gradient(135deg, {PRIMARY}, {ACCENT}); /* 🌈 漸層背景 */
    color: white !important;
    padding: 12px 0; 
    text-align: center; 
    border-radius: 25px;
    font-weight: 900; 
    box-shadow: 0 4px 10px rgba(239, 108, 0, 0.3); /* 發光陰影 */
    margin-bottom: 12px; 
    cursor: default;
}}

/* 📊 6. 內部統計小卡片 (Dash Card) */
.dash-card {{
    background-color: #F8F9FA;       /* 淺灰底色 */
    padding: 20px; 
    border-radius: 15px;             /* 圓角 */
    border-left: 6px solid {ACCENT}; /* 👈 左邊那條裝飾線的顏色 */
    margin-bottom: 15px;
}}
.dash-label {{ font-size: 1.1rem; color: #444 !important; font-weight: bold; margin-bottom: 5px; }}
.dash-value {{ font-size: 2.2rem; color: {PRIMARY} !important; font-weight: 900; margin: 10px 0; }} /* 數字顏色 */
.dash-sub {{ font-size: 0.95rem; color: #666 !important; line-height: 1.6; }}

/* 📝 7. 輸入框與下拉選單樣式 */
div[data-baseweb="select"] > div {{
    background-color: #FFFFFF !important;
    color: #000000 !important;
    border: 2px solid #E0E0E0 !important; /* 邊框顏色 */
    border-radius: 12px !important;
}}
/* 修正多選下拉選單的標籤背景與文字顏色 */
span[data-baseweb="tag"] {{
    background-color: #EF6C00 !important; /* 背景改成你的主色調 */
}}
span[data-baseweb="tag"] span {{
    color: #FFFFFF !important; /* 文字強制變白色 */
}}
div[data-baseweb="select"] span {{ color: #000000 !important; }}
ul[data-baseweb="menu"] {{ background-color: #FFFFFF !important; }}
li[role="option"] {{ color: #000000 !important; background-color: #FFFFFF !important; }}
li[role="option"]:hover {{
    background-color: #FFF3E0 !important; /* 滑鼠移過去的背景色 */
    color: {PRIMARY} !important;
}}
.stTextInput input, .stDateInput input, .stTimeInput input, .stNumberInput input {{
    background-color: #F8F9FA !important;
    border: 1px solid #E0E0E0 !important;
    border-radius: 12px !important;
    color: #333 !important;
}}

/* 🖱️ 8. 主要操作按鈕 (提交、下載) */
div[data-testid="stFormSubmitButton"] > button,
div[data-testid="stDownloadButton"] > button {{
    background-color: {PRIMARY} !important; /* 按鈕背景色 */
    color: #FFFFFF !important;              /* 文字顏色 */
    border: none !important; 
    border-radius: 12px !important;
    padding: 10px 20px !important;
}}
div[data-testid="stFormSubmitButton"] > button *, 
div[data-testid="stDownloadButton"] > button * {{
    color: #FFFFFF !important; font-weight: 900 !important;
}}
/* 滑鼠移過去按鈕 */
div[data-testid="stFormSubmitButton"] > button:hover,
div[data-testid="stDownloadButton"] > button:hover {{
    background-color: {ACCENT} !important;
    transform: translateY(-2px);
    box-shadow: 0 4px 10px rgba(0,0,0,0.2);
}}

/* Toast 訊息框 */
div[data-baseweb="toast"] {{
    background-color: #FFFFFF !important; border: 3px solid {PRIMARY} !important;
    border-radius: 15px !important; padding: 15px !important;
    box-shadow: 0 5px 20px rgba(0,0,0,0.3) !important;
}}
div[data-baseweb="toast"] * {{ color: #000000 !important; font-weight: 900 !important; }}

/* 🔥 6. 日期選單樣式 (強制明亮主題，修復反黑與顏色錯亂) */
div[data-baseweb="popover"], div[data-baseweb="popover"] > div, div[data-baseweb="calendar"] {{
    background-color: #FFFFFF !important;
}}
div[data-baseweb="calendar"] *, div[data-baseweb="popover"] * {{
    color: #212121 !important; 
    fill: #212121 !important; /* 月份切換箭頭顏色 */
}}
/* 選中的日期背景與文字 */
div[data-baseweb="calendar"] button[aria-selected="true"] {{ 
    background-color: #4A148C !important; 
    border-radius: 8px !important;
}}
div[data-baseweb="calendar"] button[aria-selected="true"] * {{ 
    color: #FFFFFF !important; 
}}
/* 滑鼠游標經過的日期背景 */
div[data-baseweb="calendar"] button:hover {{
    background-color: #F3E5F5 !important; 
    border-radius: 8px !important;
}}

</style>
""", unsafe_allow_html=True)

# =========================================================
# 2) Logic & Data (Supabase 單一真實來源版)
# =========================================================
SHEET_ID = "1A3-VwCBYjnWdcEiL6VwbV5-UECcgX7TqKH94sKe8P90"
COURSE_HIERARCHY = {
    "手作": ["藝術手作", "生活用品"], "講座": ["消防", "反詐", "道路安全", "環境", "心靈成長", "家庭關係", "健康"],
    "外出": ["觀摩", "出遊"], "延緩失能": ["手作", "料理", "運動", "健康講座"],
    "運動": ["有氧", "毛巾操", "其他運動"], "園藝療癒": ["手作"], "烹飪": ["甜品", "鹹食", "醃漬品"], "歌唱": ["歡唱"]
}
M_COLS = ["姓名", "身分證字號", "性別", "出生年月日", "電話", "地址", "備註", "加入日期"]
L_COLS = ["姓名", "身分證字號", "日期", "時間", "場次時段", "課程分類", "課程名稱", "收縮壓", "舒張壓", "脈搏"]

@st.cache_resource
def get_supabase_client():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

@st.cache_data(ttl=60)
def load_data(sheet_name, target_cols=None):
    try:
        supabase = get_supabase_client()
        response = supabase.table(sheet_name).select("*").execute()
        df = pd.DataFrame(response.data)
        
        t_cols = target_cols if target_cols is not None else (M_COLS if sheet_name == 'master_residents' else L_COLS)
        if df.empty: return pd.DataFrame(columns=t_cols)
        
        for c in t_cols:
            if c not in df.columns: df[c] = ""
        return df
    except Exception as e:
        st.error(f"資料庫讀取失敗：{e}")
        t_cols = target_cols if target_cols is not None else (M_COLS if sheet_name == 'master_residents' else L_COLS)
        return pd.DataFrame(columns=t_cols)

def append_data(sheet_name, row_dict, col_order=None):
    try:
        supabase = get_supabase_client()
        clean_data = {k: str(v).strip() for k, v in row_dict.items() if str(v).strip() and str(v).strip() != 'nan'}
        supabase.table(sheet_name).insert(clean_data).execute()
        load_data.clear()
        return True
    except Exception as e:
        st.error(f"新增失敗：{e}")
        return False

def batch_append_data(sheet_name, rows_list, col_order=None):
    try:
        supabase = get_supabase_client()
        clean_rows = []
        for r in rows_list:
            # 清理單筆資料，排除 nan 或空字串
            clean_dict = {k: str(v).strip() for k, v in r.items() if str(v).strip() and str(v).strip() != 'nan'}
            if clean_dict:
                clean_rows.append(clean_dict)
                
        if clean_rows:
            # 將整理好的多筆資料清單 (List) 一次性寫入資料庫
            supabase.table(sheet_name).insert(clean_rows).execute()
            
        load_data.clear()
        return True
    except Exception as e:
        st.error(f"批次新增失敗：{e}")
        return False

def get_tw_time(): return datetime.now(TW_TZ)

def calculate_age(dob_str):
    try:
        b_date = datetime.strptime(str(dob_str).strip(), "%Y-%m-%d").date()
        today = date.today()
        return today.year - b_date.year - ((today.month, today.day) < (b_date.month, b_date.day))
    except: return 0

COLS_MASTER = ['姓名', '身分證字號', '性別', '出生年月日', '電話', '地址', '緊急聯絡人', '緊急聯絡電話', '身分_志工', '身分_關懷戶', '身分_據點長輩', '志工分類', '關懷_身分別', '同住_18歲以下', '同住_成人', '同住_65歲以上', '拒絕物資', '人際關係']
CURRENT_COLS = ["姓名", "身分證字號", "性別", "出生年月日", "電話", "地址", "緊急聯絡人", "緊急聯絡電話"] 

def get_elderly_members():
    df = load_data("master_residents")
    if df.empty: return pd.DataFrame(columns=CURRENT_COLS)
    if '身分_據點長輩' not in df.columns: df['身分_據點長輩'] = ""
    elder_df = df[df['身分_據點長輩'].astype(str).str.upper() == 'TRUE'].copy()
    for c in CURRENT_COLS:
        if c not in elder_df.columns: elder_df[c] = ""
    return elder_df[CURRENT_COLS].reset_index(drop=True)

def add_or_update_elderly_to_master(new_data):
    uid = new_data.get('身分證字號', '').upper()
    if not uid or uid == 'NAN':
        uid = f"TEMP_{new_data.get('姓名', '').strip()}_{new_data.get('電話', '').strip()}"
        new_data['身分證字號'] = uid

    master_data = {k: str(v) for k, v in new_data.items()}
    master_data['身分_據點長輩'] = 'TRUE'

    try:
        supabase = get_supabase_client()
        existing = supabase.table("master_residents").select("id").eq("身分證字號", uid).execute()
        if existing.data:
            record_id = existing.data[0]['id']
            supabase.table("master_residents").update(master_data).eq("id", record_id).execute()
        else:
            for c in COLS_MASTER:
                if c not in master_data: master_data[c] = "FALSE" if "身分_" in c else ""
            supabase.table("master_residents").insert(master_data).execute()
        load_data.clear()
        return True
    except Exception as e: return False

def archive_elderly_in_master(uid, reason):
    try:
        supabase = get_supabase_client()
        existing = supabase.table("master_residents").select("id").eq("身分證字號", uid).execute()
        if existing.data:
            record_id = existing.data[0]['id']
            update_data = {'身分_據點長輩': 'FALSE'}
            if "過世" in reason or "搬遷" in reason:
                update_data['身分_關懷戶'] = 'FALSE'
                update_data['身分_志工'] = 'FALSE'
            supabase.table("master_residents").update(update_data).eq("id", record_id).execute()
            load_data.clear()
            return True
        return False
    except Exception as e: return False

# =========================================================
# 3) Navigation (側邊欄版)
# =========================================================
def render_nav():
    with st.sidebar:
        # 標題區
        st.markdown(f"<h2 style='color:{PRIMARY}; margin-bottom:5px; padding-left:10px;'>🏠 長輩關懷中心</h2>", unsafe_allow_html=True)
        st.write("") 

        # 1. 首頁
        if st.session_state.page == 'home':
            st.markdown('<div class="nav-active">📊 據點概況看板</div>', unsafe_allow_html=True)
        else:
            if st.button("📊 據點概況看板", key="nav_home", use_container_width=True):
                st.session_state.page = 'home'; st.rerun()

        # 2. 據點報到
        if st.session_state.page == 'checkin':
            st.markdown('<div class="nav-active">🩸 據點報到</div>', unsafe_allow_html=True)
        else:
            if st.button("🩸 據點報到", key="nav_checkin", use_container_width=True):
                st.session_state.page = 'checkin'; st.rerun()

        # 3. 統計數據 (原名冊按鈕已移除)
        if st.session_state.page == 'stats':
            st.markdown('<div class="nav-active">📈 詳細統計報表</div>', unsafe_allow_html=True)
        else:
            if st.button("📈 詳細統計報表", key="nav_stats", use_container_width=True):
                st.session_state.page = 'stats'; st.rerun()

        st.markdown("---")
        # 回大廳按鈕
        if st.button("🚪 回系統大廳", key="nav_back", use_container_width=True):
            st.switch_page("Home.py")
        
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.markdown("<div style='text-align:center; color:#999; font-size:0.8rem;'>Designed for Fude Community</div>", unsafe_allow_html=True)
# =========================================================
# 4) Pages
# =========================================================

# --- [分頁 0：首頁 (完全公開)] ---
# --- [分頁 0：首頁 (完全公開)] ---
if st.session_state.page == 'home':
    render_nav()
    st.markdown(f"<h2 style='color: {PRIMARY};'>📊 據點關懷概況</h2>", unsafe_allow_html=True)
    
    logs, members = load_data("elderly_logs"), get_elderly_members()
    this_year = get_tw_time().year
    
    if not logs.empty:
        # 計算年度總人次
        logs['dt_year'] = pd.to_datetime(logs['日期'], errors='coerce').dt.year
        this_year_logs = logs[logs['dt_year'] == this_year]
        year_count = len(this_year_logs)
        
        # 計算今年已服務場次 (以日期、時段、課程作去重)
        unique_sessions = this_year_logs.drop_duplicates(subset=['日期', '場次時段', '課程名稱', '課程分類'])
        year_session_count = len(unique_sessions)
    else:
        year_count = 0
        year_session_count = 0
    
    # 總體平均年齡
    avg_age = round(members['出生年月日'].apply(calculate_age).mean(), 1) if not members.empty else 0
    
    male_m = members[members['性別'] == '男']
    female_m = members[members['性別'] == '女']
    
    male_count = len(male_m)
    female_count = len(female_m)
    male_avg_age = round(male_m['出生年月日'].apply(calculate_age).mean(), 1) if not male_m.empty else 0
    female_avg_age = round(female_m['出生年月日'].apply(calculate_age).mean(), 1) if not female_m.empty else 0
    
    total_members = len(members)

    # 頂部看板 (替換右側看板為場次統計)
    st.markdown(f"""
    <div style="display: flex; gap: 20px;">
        <div style="flex: 1; background: linear-gradient(135deg, #FF9800 0%, #F57C00 100%); padding: 30px; border-radius: 20px; color: white; text-align: center; box-shadow: 0 10px 25px rgba(245, 124, 0, 0.3);">
            <div style="font-size: 1.2rem; opacity: 0.9; color: white !important;">📅 {this_year} 年度 - 據點總服務人次</div>
            <div style="font-size: 3.5rem; font-weight: 900; margin: 10px 0; color: white !important;">
                {year_count} <span style="font-size: 1.5rem; color: white !important;">人次</span>
            </div>
        </div>
        <div style="flex: 1; background: linear-gradient(135deg, #7E57C2 0%, #512DA8 100%); padding: 30px; border-radius: 20px; color: white; text-align: center; box-shadow: 0 10px 25px rgba(126, 87, 194, 0.3);">
            <div style="font-size: 1.2rem; opacity: 0.9; color: white !important;">🎯 今年已服務場次</div>
            <div style="font-size: 3.5rem; font-weight: 900; margin: 10px 0; color: white !important;">
                {year_session_count} <span style="font-size: 1.5rem; color: white !important;">場</span>
            </div>
        </div>
    </div>
    <br>
    """, unsafe_allow_html=True)

    # 🔴 2. [新增] 退出/結案功能 (將長輩移出名單)
    with st.expander("📤 長輩退出/結案 (移除名單)", expanded=False):
        st.markdown("""
        <div style="background-color:#FFF3E0; padding:10px; border-radius:10px; border-left:5px solid #FF9800; margin-bottom:10px;">
        ⚠️ <b>注意：</b> 此操作會將長輩從「服務中名單」移除，並封存至 residents_archive。<br>
        過去的服務紀錄與血壓數據<b>不會</b>消失，但該長輩將無法再進行報到。
        </div>
        """, unsafe_allow_html=True)

        if members.empty:
            st.info("目前無長輩資料可供操作。")
        else:
            member_options_exit = [
                f"{row.姓名} ({row.身分證字號})"
                for row in members.itertuples(index=False)
            ]
            c_sel, c_reason = st.columns([1, 1])
            with c_sel:
                target_exit = st.selectbox("選擇退出長輩", ["--- 請選擇 ---"] + member_options_exit)
            with c_reason:
                exit_reason = st.selectbox("退出/結案原因", ["過世", "搬遷/無法聯繫", "自願退出", "進入長照機構", "其他"])

            if st.button("確認執行退出 (無法復原)", type="primary"):
                if target_exit == "--- 請選擇 ---":
                    st.error("請先選擇長輩！")
                else:
                    target_pid = target_exit.split("(")[-1].replace(")", "")
                    rec = members[members['身分證字號'] == target_pid].iloc[0]

                    # 1. 寫入共用封存表
                    archive_row = {
                        "姓名":        str(rec.get("姓名", "")),
                        "身分證字號":   target_pid,
                        "性別":        str(rec.get("性別", "")),
                        "出生年月日":   str(rec.get("出生年月日", "")),
                        "電話":        str(rec.get("電話", "")),
                        "地址":        str(rec.get("地址", "")),
                        "緊急聯絡人":   str(rec.get("緊急聯絡人", "")),
                        "緊急聯絡電話": str(rec.get("緊急聯絡電話", "")),
                        "退出身份":    "長者",
                        "退出原因":    exit_reason,
                        "退出日期":    str(date.today()),
                        "備註":        "",
                    }

                    # 2. 更新 master_residents
                    try:
                        supabase = get_supabase_client()
                        supabase.table("residents_archive").insert(archive_row).execute()
                        supabase.table("master_residents").update(
                            {"身分_據點長輩": "FALSE"}
                        ).eq("身分證字號", target_pid).execute()
                        load_data.clear()
                        st.success("✅ 已結案並封存至 residents_archive！")
                        import time; time.sleep(1); st.rerun()
                    except Exception as e:
                        st.error(f"操作失敗：{e}")

# --- [分頁 2：據點報到 (完全公開)] ---
elif st.session_state.page == 'checkin':
    render_nav()
    st.markdown("## 🩸 據點報到與健康量測")

    def check_health_alert(sbp, dbp, pulse):
        alerts = []
        if sbp >= 140 or dbp >= 90: alerts.append(f"⚠️ 血壓偏高 ({sbp}/{dbp})")
        elif sbp <= 90 or dbp <= 60: alerts.append(f"⚠️ 血壓偏低 ({sbp}/{dbp})")
        if pulse > 100: alerts.append(f"💓 心跳過快 ({pulse})")
        elif pulse < 60: alerts.append(f"💓 心跳過慢 ({pulse})")
        return alerts

    def do_checkin(pid, sbp, dbp, pulse, course_cat, course_name, session_period):
        df_m = get_elderly_members()
        pid_clean = pid.strip().upper()
        person = df_m[df_m['身分證字號'] == pid_clean]
    
        if person.empty:
            st.error(f"❌ 查無此人 ({pid_clean})，請先確認名冊。")
            return
        
        name = person.iloc[0]['姓名']
        alerts = check_health_alert(sbp, dbp, pulse)
    
        new_log = {
            "姓名": name, "身分證字號": pid_clean,
            "日期": get_tw_time().strftime("%Y-%m-%d"), "時間": get_tw_time().strftime("%H:%M:%S"),
            "場次時段": session_period,
            "課程分類": course_cat,
            "課程名稱": course_name,
            "收縮壓": sbp, "舒張壓": dbp, "脈搏": pulse
        }
        append_data("elderly_logs", new_log, L_COLS)
    
        if alerts:
            st.warning(f"✅ {name} 報到成功，但數值異常：{' / '.join(alerts)}")
        else:
            st.success(f"✅ {name} 報到成功！")

    # 分離兩種報到模式
    tab_live, tab_batch = st.tabs(["📍 現場報到", "🕒 批次補登"])

    # ---------------------------------------------------------
    # 模式 1：現場報到
    # ---------------------------------------------------------
    with tab_live:
        st.markdown('<div class="dash-card" style="border-left: 6px solid #FF9800;">', unsafe_allow_html=True)
        st.markdown("#### a. 課程設定")
        c_period, c_main, c_sub, c_name = st.columns([1, 1, 1, 1.5])
        with c_period: session_period = st.selectbox("場次時段", ["上午場", "下午場", "晚上場"], key="live_period")
        with c_main: main_cat = st.selectbox("課程大分類", list(COURSE_HIERARCHY.keys()), key="live_main")
        with c_sub: 
            sub_list = COURSE_HIERARCHY[main_cat]
            sub_cat = st.selectbox("課程子分類", sub_list, key="live_sub")
        with c_name: course_name = st.text_input("課程名稱 (選填)", placeholder="例如：端午節香包製作", key="live_name")

        final_course_cat = f"{main_cat}-{sub_cat}"
        final_course_name = course_name if course_name.strip() else sub_cat
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="dash-card">', unsafe_allow_html=True)
        st.markdown("#### 🩺 b. 報到與健康量測")
        
        # 加入一個自訂的 UI 容器包覆量測區塊
        st.markdown("""
        <div style="background-color: #FAFAFA; border: 2px solid #E0E0E0; border-radius: 15px; padding: 15px 20px; margin-bottom: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.03);">
        """, unsafe_allow_html=True)
        
        c_bp1, c_bp2, c_bp3 = st.columns(3)
        with c_bp1: 
            st.markdown("<div style='color:#D32F2F; font-weight:900; margin-bottom:5px; font-size:1.05rem;'>🔴 收縮壓 (高壓)</div>", unsafe_allow_html=True)
            sbp_val = st.number_input("建議標準: 90~140", min_value=50, max_value=250, value=120, key="live_sbp", label_visibility="collapsed")
        with c_bp2: 
            st.markdown("<div style='color:#1976D2; font-weight:900; margin-bottom:5px; font-size:1.05rem;'>🔵 舒張壓 (低壓)</div>", unsafe_allow_html=True)
            dbp_val = st.number_input("建議標準: 60~90", min_value=30, max_value=150, value=80, key="live_dbp", label_visibility="collapsed")
        with c_bp3: 
            st.markdown("<div style='color:#388E3C; font-weight:900; margin-bottom:5px; font-size:1.05rem;'>💚 脈搏 (心跳)</div>", unsafe_allow_html=True)
            pulse_val = st.number_input("建議標準: 60~100", min_value=30, max_value=200, value=72, key="live_pulse", label_visibility="collapsed")
            
        st.markdown("</div>", unsafe_allow_html=True)

        # --- 新增：即時異常數值提示 ---
        realtime_alerts = []
        if sbp_val >= 140 or dbp_val >= 90: realtime_alerts.append(f"血壓偏高 ({sbp_val}/{dbp_val})")
        elif sbp_val <= 90 or dbp_val <= 60: realtime_alerts.append(f"血壓偏低 ({sbp_val}/{dbp_val})")
        
        if pulse_val > 100: realtime_alerts.append(f"心跳過快 ({pulse_val})")
        elif pulse_val < 60: realtime_alerts.append(f"心跳過慢 ({pulse_val})")
        
        if realtime_alerts:
            st.error(f"🚨 **量測數值異常：** {' / '.join(realtime_alerts)}。請留意長輩狀況！", icon="⚠️")
        else:
            st.write("") # 若無異常，維持排版間距
        sub_tab1, sub_tab2 = st.tabs(["🔍 掃描/輸入身分證", "📋 下拉選單選取"])
        
        with sub_tab1:
            input_pid = st.text_input("請掃描或輸入身分證字號", key="scan_pid_field")
            if st.button("確認報到 (身分證)", key="btn_do_scan"):
                if input_pid:
                    do_checkin(input_pid, sbp_val, dbp_val, pulse_val, final_course_cat, final_course_name, session_period)
                    st.rerun()

        with sub_tab2:
            df_m = get_elderly_members()
            if not df_m.empty:
                member_options = [f"{idx}. {row.姓名}" for idx, row in enumerate(df_m.itertuples(index=False), start=1)]
                selected_member = st.selectbox("請選擇長輩", ["--- 請選擇 ---"] + member_options, key="live_sel")
                if st.button("確認報到 (選單)", key="btn_do_select"):
                    if selected_member != "--- 請選擇 ---":
                        sel_name = selected_member.split(". ")[1] 
                        sel_pid = df_m[df_m['姓名'] == sel_name].iloc[0]['身分證字號']
                        
                        do_checkin(sel_pid, sbp_val, dbp_val, pulse_val, final_course_cat, final_course_name, session_period)
                        st.rerun()
            else:
                st.warning("名單中尚無資料")
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("---")
        st.write("📋 今日已報到名單：")
        logs = load_data("elderly_logs")
        today_str = get_tw_time().strftime("%Y-%m-%d")
        
        if not logs.empty:
            today_logs = logs[logs['日期'] == today_str].copy()
            if not today_logs.empty:
                # 繪製標籤式名單
                tags_html = '<div style="display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 15px;">'
                checked_in_names = today_logs['姓名'].unique()
                for name in checked_in_names:
                    tags_html += f'<span style="background-color: {PRIMARY}; color: white; padding: 6px 14px; border-radius: 20px; font-weight: bold; font-size: 0.95rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">{name}</span>'
                tags_html += '</div>'
                st.markdown(tags_html, unsafe_allow_html=True)
                
                # 將原有的資料編輯器收合，維持畫面簡潔
                if st.toggle("✏️ 開啟資料修改面板", value=False):
                    edited_df = st.data_editor(today_logs, column_order=['時間', '場次時段', '姓名', '收縮壓', '舒張壓', '脈搏', '課程名稱', '課程分類', '身分證字號'], use_container_width=True, num_rows="dynamic", key="today_checkin_editor")
                    if st.button("💾 儲存名單修改"):
                        with st.spinner("寫入資料庫..."):
                            supabase = get_supabase_client()
                            for _, row in edited_df.iterrows():
                                if 'id' in row and pd.notna(row['id']):
                                    up_data = {k: str(v) for k, v in row.items() if k != 'id' and pd.notna(v)}
                                    supabase.table("elderly_logs").update(up_data).eq("id", int(row['id'])).execute()
                            load_data.clear()
                            st.success("✅ 名單已更新")
                            time.sleep(1); st.rerun()
            else: 
                st.info("今日尚無報到紀錄。")
        else: 
            st.info("資料庫目前無任何紀錄。")

    # ---------------------------------------------------------
    # 模式 2：批次補登 (無血壓欄位)
    # ---------------------------------------------------------
    with tab_batch:
        df_m = get_elderly_members()
        if df_m.empty: 
            st.warning("目前名冊中無長輩資料。")
        else:
            if "batch_success" not in st.session_state:
                st.session_state.batch_success = False

            st.markdown("#### a. 課程與時間設定")
            c_date, c_time = st.columns([1, 1])
            with c_date: back_date = st.date_input("選擇補登日期", value=get_tw_time().date())
            with c_time: back_time = st.time_input("選擇補登時間", value=get_tw_time().replace(second=0, microsecond=0).time(), step=60)
            
            bc_period, bc_main, bc_sub, bc_name = st.columns([1, 1, 1, 1.5])
            with bc_period: b_period = st.selectbox("場次時段", ["上午場", "下午場", "晚上場"], key="b_period")
            with bc_main: b_main_cat = st.selectbox("課程大分類", list(COURSE_HIERARCHY.keys()), key="b_main_cat")
            with bc_sub: b_sub_cat = st.selectbox("課程子分類", COURSE_HIERARCHY[b_main_cat], key="b_sub_cat")
            with bc_name: b_course_name_input = st.text_input("課程名稱 (選填)", key="b_course_name")
            
            st.markdown("#### b. 報到設定")
            member_options = [f"{idx}. {row.姓名} ({row.身分證字號})" for idx, row in enumerate(df_m.itertuples(index=False), start=1)]
            selected_members = st.multiselect("下拉選單選擇長輩 (可多選)", options=member_options, key="b_members")
            
            submitted = st.button("🚀 執行批次補登", type="primary")

            if submitted:
                if not selected_members: 
                    st.error("請先選擇長輩！")
                else:
                    new_entries = []
                    s_date = back_date.strftime("%Y-%m-%d")
                    s_time = back_time.strftime("%H:%M:%S")
                    
                    for label in selected_members:
                        target_pid = label.split("(")[-1].replace(")", "")
                        target_name = label.split(". ")[1].split(" (")[0]
                        b_course_cat = f"{b_main_cat}-{b_sub_cat}"
                        b_course_name = b_course_name_input.strip() if b_course_name_input.strip() else b_sub_cat
                        new_entries.append({
                            "姓名": target_name, "身分證字號": target_pid, 
                            "日期": s_date, "時間": s_time, 
                            "場次時段": b_period,
                            "課程分類": b_course_cat, "課程名稱": b_course_name, 
                            "收縮壓": "", "舒張壓": "", "脈搏": ""  
                        })
                    
                    if batch_append_data("elderly_logs", new_entries, L_COLS):
                        st.session_state.batch_success = True

            if st.session_state.batch_success:
                st.success("✅ 已成功補登紀錄！")
                st.session_state.batch_success = False 
                time.sleep(1)
                st.rerun()
# --- [分頁 4：統計 (完全公開)] ---
elif st.session_state.page == 'stats':
    render_nav()
    st.markdown("## 📊 統計數據")
    members, logs = get_elderly_members(), load_data("elderly_logs")
    if members.empty or logs.empty: st.info("尚無數據")
    else:
        logs['dt'] = pd.to_datetime(logs['日期'], errors='coerce')
        st.markdown('<div class="dash-card">', unsafe_allow_html=True)
        d_range = st.date_input(
            "📅 選擇統計區間",
            value=(date(date.today().year, date.today().month, 1), date.today()),
        )

        # 加上更嚴格的防護，並在 UI 上給提示
        if not isinstance(d_range, (list, tuple)) or len(d_range) != 2:
            st.warning("請選擇完整的開始與結束日期。")
            st.stop()  # ← 強制停止，避免後續元件在不完整狀態下渲染
        st.markdown('</div>', unsafe_allow_html=True)
        if isinstance(d_range, tuple) and len(d_range) == 2:
            f_logs = logs[(logs['dt'].dt.date >= d_range[0]) & (logs['dt'].dt.date <= d_range[1])].copy()
            tab_c, tab_h = st.tabs(["📚 課程成效", "🏥 長輩健康"])
            with tab_c:
                merged = f_logs.merge(members[['姓名', '性別']], on='姓名', how='left')
                
                # 將計算不重複場次的程式碼提前，以便上方卡片使用
                unique_sessions = merged.drop_duplicates(subset=['日期', '場次時段', '課程名稱', '課程分類']).copy()
                total_sessions_count = len(unique_sessions)
                
                st.markdown("### 1. 參與人次統計")
                # 這裡改成 4 個欄位
                m1, m2, m3, m4 = st.columns(4)
                with m1: st.markdown(f"""<div class="dash-card"><div style="color:#666;">已舉辦場次</div><div style="font-size:1.8rem;color:{PRIMARY};font-weight:900;">{total_sessions_count} 場</div></div>""", unsafe_allow_html=True)
                with m2: st.markdown(f"""<div class="dash-card"><div style="color:#666;">總參與人次</div><div style="font-size:1.8rem;color:{PRIMARY};font-weight:900;">{len(merged)} 人次</div></div>""", unsafe_allow_html=True)
                with m3: st.markdown(f"""<div class="dash-card"><div style="color:#666;">男性參與</div><div style="font-size:1.8rem;color:{PRIMARY};font-weight:900;">{len(merged[merged['性別']=='男'])} 人次</div></div>""", unsafe_allow_html=True)
                with m4: st.markdown(f"""<div class="dash-card"><div style="color:#666;">女性參與</div><div style="font-size:1.8rem;color:{PRIMARY};font-weight:900;">{len(merged[merged['性別']=='女'])} 人次</div></div>""", unsafe_allow_html=True)
                
                unique_sessions['大分類'] = unique_sessions['課程分類'].apply(lambda x: x.split('-')[0] if '-' in x else x)
                unique_sessions['子分類'] = unique_sessions['課程分類'].apply(lambda x: x.split('-')[1] if '-' in x else x)

                st.markdown("### 2. 課程場次占比")
                main_cts = unique_sessions['大分類'].value_counts().reset_index()
                main_cts.columns = ['類別', '場次']
                
                random.seed(42)
                main_cts['x_rnd'] = [random.uniform(0, 10) for _ in range(len(main_cts))]
                main_cts['y_rnd'] = [random.uniform(0, 10) for _ in range(len(main_cts))]
                main_cts['顯示標籤'] = main_cts['類別'] + '<br>' + main_cts['場次'].astype(str) + '次'
                
                fig_bubble = px.scatter(main_cts, x="x_rnd", y="y_rnd", size="場次", color="類別", text="顯示標籤", size_max=100, color_discrete_sequence=px.colors.qualitative.Pastel)
                fig_bubble.update_traces(textposition='middle center', textfont=dict(size=14, color='black', family="Noto Sans TC"))
                fig_bubble.update_layout(showlegend=False, height=450, xaxis=dict(showgrid=False, zeroline=False, showticklabels=False), yaxis=dict(showgrid=False, zeroline=False, showticklabels=False), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', margin=dict(t=20, b=20, l=20, r=20))
                st.plotly_chart(fig_bubble, use_container_width=True)

                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("#### 大分類明細")
                    main_html = '<div style="display: flex; flex-wrap: wrap; gap: 12px; padding-top: 5px;">'
                    for _, row in main_cts.iterrows():
                        cat_name = row['類別']
                        count = row['場次']
                        # 移除多行縮排，改為單行寫法
                        main_html += f'<div style="background: #FFF3E0; border: 1px solid #FFCC80; border-radius: 12px; padding: 12px 16px; display: flex; align-items: center; justify-content: space-between; flex: 1 1 calc(50% - 12px); min-width: 140px; box-shadow: 0 2px 6px rgba(0,0,0,0.05);"><span style="font-weight: 900; color: #E65100; font-size: 1.1rem;">{cat_name}</span><span style="background-color: #EF6C00; color: white; border-radius: 20px; padding: 4px 12px; font-size: 0.9rem; font-weight: bold;">{count} 場</span></div>'
                    main_html += '</div>'
                    st.markdown(main_html, unsafe_allow_html=True)

                with c2:
                    st.markdown("#### 子分類鑽取")
                    sel_m = st.selectbox("請選擇大分類", sorted(main_cts['類別'].unique()), label_visibility="collapsed", key="sel_main_stats")
                    
                    sub_cts = unique_sessions[unique_sessions['大分類']==sel_m]['子分類'].value_counts().reset_index()
                    sub_cts.columns = ['子分類', '場次']
                    
                    sub_html = '<div style="display: flex; flex-wrap: wrap; gap: 12px; padding-top: 5px;">'
                    if not sub_cts.empty:
                        for _, row in sub_cts.iterrows():
                            sub_name = row['子分類']
                            count = row['場次']
                            # 移除多行縮排，改為單行寫法
                            sub_html += f'<div style="background: #FFFFFF; border: 1px solid #E0E0E0; border-left: 5px solid #FFA726; border-radius: 8px; padding: 12px 16px; display: flex; align-items: center; justify-content: space-between; flex: 1 1 calc(50% - 12px); min-width: 140px; box-shadow: 0 2px 5px rgba(0,0,0,0.05);"><span style="font-weight: bold; color: #424242; font-size: 1.05rem;">{sub_name}</span><span style="background-color: #F5F5F5; color: #616161; border-radius: 20px; padding: 4px 12px; font-size: 0.9rem; font-weight: bold;">{count} 場</span></div>'
                    else:
                        sub_html += '<div style="color: #999;">此分類尚無子分類資料。</div>'
                    sub_html += '</div>'
                    st.markdown(sub_html, unsafe_allow_html=True)
                # --- 新增：全勤名單 ---
                st.markdown("### 3. 🏆 全勤長輩名單")
                
                # 總課程場次數
                total_sessions_count = len(unique_sessions)
                
                if total_sessions_count > 0:
                    # 計算每位長輩出席的不重複場次數量
                    elder_attendance = merged.groupby('姓名').apply(
                        lambda x: len(x.drop_duplicates(subset=['日期', '場次時段', '課程名稱', '課程分類']))
                    ).reset_index(name='出席場次')
                    
                    # 篩選出 出席場次 == 總場次 的長輩
                    perfect_attendance = elder_attendance[elder_attendance['出席場次'] == total_sessions_count]
                    
                    if not perfect_attendance.empty:
                        st.success(f"本區間共有 {total_sessions_count} 堂課，以下 {len(perfect_attendance)} 位長輩全勤：")
                        st.markdown(f"**{'、'.join(perfect_attendance['姓名'].tolist())}**")
                    else:
                        st.info(f"本區間共有 {total_sessions_count} 堂課，目前無人全勤。")
                else:
                    st.info("此區間內尚無任何課程紀錄。")

            with tab_h:
                st.markdown("### 🚨 區間血壓異常警示總覽")
                
                # 確保血壓欄位為數值格式
                f_logs['收縮壓'] = pd.to_numeric(f_logs['收縮壓'], errors='coerce')
                f_logs['舒張壓'] = pd.to_numeric(f_logs['舒張壓'], errors='coerce')
                
                # 判定異常：收縮壓 >= 140 或 <= 90，舒張壓 >= 90 或 <= 60
                f_logs['血壓異常'] = (
                    (f_logs['收縮壓'] >= 140) | (f_logs['舒張壓'] >= 90) | 
                    (f_logs['收縮壓'] <= 90) | (f_logs['舒張壓'] <= 60)
                )
                
                # 計算每位長輩的量測總次數與異常總次數
                health_summary = f_logs.groupby('姓名').agg(
                    量測次數=('日期', 'count'),
                    異常次數=('血壓異常', 'sum')
                ).reset_index()
                
                # 篩選出有異常的長輩並依異常次數排序
                abnormal_list = health_summary[health_summary['異常次數'] > 0].sort_values(by=['異常次數', '量測次數'], ascending=[False, True])
                
                if not abnormal_list.empty:
                    # 用單行卡片 HTML 顯示異常名單
                    abnormal_html = '<div style="display: flex; flex-wrap: wrap; gap: 12px; margin-bottom: 20px;">'
                    for _, row in abnormal_list.iterrows():
                        name = row['姓名']
                        ab_count = int(row['異常次數'])
                        total_count = int(row['量測次數'])
                        pct = int((ab_count / total_count) * 100)
                        
                        abnormal_html += f'<div style="background: #FFEBEE; border-left: 5px solid #F44336; border-radius: 8px; padding: 12px 16px; min-width: 160px; box-shadow: 0 2px 5px rgba(0,0,0,0.05);"><div style="font-weight: 900; color: #B71C1C; font-size: 1.1rem; margin-bottom: 4px;">{name}</div><div style="color: #424242; font-size: 0.95rem;">異常：<b>{ab_count}</b> / {total_count} 次 ({pct}%)</div></div>'
                    
                    abnormal_html += '</div>'
                    st.markdown(abnormal_html, unsafe_allow_html=True)
                else:
                    st.success("本區間內所有長輩血壓量測皆為正常。")
                
                st.markdown("---")
                st.markdown("### 🔍 個別長輩健康趨勢")
                
                target_elder = st.selectbox("請選擇長輩", sorted(f_logs['姓名'].unique()), key="sel_elder_health")
                e_logs = f_logs[f_logs['姓名']==target_elder].sort_values('dt')
                
                # 取得該長輩的異常總數
                high_bp = len(e_logs[e_logs['血壓異常'] == True])
                
                st.markdown(f"""<div class="dash-card" style="border-left:6px solid #E91E63"><div style="color:#666;">血壓異常次數</div><div style="font-size:1.8rem;color:{PRIMARY};font-weight:900;">{high_bp} 次</div></div>""", unsafe_allow_html=True)
                
                # 同時繪製收縮壓與舒張壓
                fig = px.line(e_logs, x='dt', y=['收縮壓', '舒張壓'], markers=True, title="血壓變化趨勢")
                fig.add_hline(y=140, line_dash="dash", line_color="red", annotation_text="收縮壓過高 (140)")
                fig.add_hline(y=90, line_dash="dash", line_color="orange", annotation_text="舒張壓過高 (90)")
                st.plotly_chart(fig, use_container_width=True)
