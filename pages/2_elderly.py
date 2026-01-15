import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta, timezone
import gspread
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

# 🔥 [移除] 原本這裡的「全域門禁」程式碼已刪除，現在進入系統不用馬上打密碼了！

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
    background-color: {BG_MAIN}; /* 讓側邊欄跟背景同色，看起來更寬闊 */
    border-right: none;           /* 去掉側邊欄右邊那條死板的分隔線 */
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

/* 1. 將所有日期選單內的文字強制改為「白色」，確保在深色背景下清晰可見 */
div[data-baseweb="calendar"] div, 
div[data-baseweb="calendar"] button, 
div[data-baseweb="calendar"] h1, 
div[data-baseweb="calendar"] h2, 
div[data-baseweb="calendar"] h3, 
div[data-baseweb="calendar"] h4, 
div[data-baseweb="calendar"] h5, 
div[data-baseweb="calendar"] h6 {{
    color: #FFFFFF !important;
}}

/* 2. 將月份左右切換的箭頭改為「白色」 */
div[data-baseweb="calendar"] svg {{
    fill: #FFFFFF !important;
}}

/* 3. 修正「滑鼠移過去」和「被選中」日期的文字顏色 */
div[data-baseweb="calendar"] button:hover,
div[data-baseweb="calendar"] button[aria-selected="true"] {{
    color: #FFFFFF !important; 
    font-weight: bold !important;
}}

/* 4. 確保選單背景維持深色 (避免半白半黑的狀況) */
div[data-baseweb="calendar"] {{
    background-color: #262730 !important;
}}

</style>
""", unsafe_allow_html=True)

# =========================================================
# 2) Logic & Data (優化版)
# =========================================================
SHEET_ID = "1A3-VwCBYjnWdcEiL6VwbV5-UECcgX7TqKH94sKe8P90"
COURSE_HIERARCHY = {
    "手作": ["藝術手作", "生活用品"], "講座": ["消防", "反詐", "道路安全", "環境", "心靈成長", "家庭關係", "健康"],
    "外出": ["觀摩", "出遊"], "延緩失能": ["手作", "料理", "運動", "健康講座"],
    "運動": ["有氧", "毛巾操", "其他運動"], "園藝療癒": ["手作"], "烹飪": ["甜品", "鹹食", "醃漬品"], "歌唱": ["歡唱"]
}
M_COLS = ["姓名", "身分證字號", "性別", "出生年月日", "電話", "地址", "備註", "加入日期"]
L_COLS = ["姓名", "身分證字號", "日期", "時間", "課程分類", "課程名稱", "收縮壓", "舒張壓", "脈搏"]

@st.cache_resource
def get_google_sheet_client():
    return gspread.service_account_from_dict(st.secrets["gcp_service_account"])

# 🔥 優化 A: 讀取速度提升
@st.cache_data(ttl=60)
def load_data(sheet_name):
    try:
        client = get_google_sheet_client()
        sheet = client.open_by_key(SHEET_ID).worksheet(sheet_name)
        # 改用 get_all_values (List of Lists) 讀取速度較快
        data = sheet.get_all_values()
        if not data: 
            target_cols = M_COLS if sheet_name == 'elderly_members' else L_COLS
            return pd.DataFrame(columns=target_cols)
            
        headers = data.pop(0)
        df = pd.DataFrame(data, columns=headers)
        
        # 確保欄位存在
        target_cols = M_COLS if sheet_name == 'elderly_members' else L_COLS
        for c in target_cols: 
            if c not in df.columns: df[c] = ""
        return df
    except: 
        return pd.DataFrame(columns=M_COLS if sheet_name == 'elderly_members' else L_COLS)

# 維持舊版 save_data (僅用於編輯修改資料)
def save_data(df, sheet_name):
    try:
        df_to_save = df.copy()
        df_to_save = df_to_save.replace(['nan', 'NaN', 'None', '<NA>'], "")
        df_to_save = df_to_save.fillna("")
        client = get_google_sheet_client()
        sheet = client.open_by_key(SHEET_ID).worksheet(sheet_name)
        sheet.clear()
        sheet.update([df_to_save.columns.values.tolist()] + df_to_save.values.tolist())
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"寫入失敗：{e}"); return False

# 🔥 優化 B: 單筆追加 (用於新增長輩、單人報到)
def append_data(sheet_name, row_dict, col_order):
    try:
        values = [str(row_dict.get(c, "")).strip() for c in col_order]
        client = get_google_sheet_client()
        sheet = client.open_by_key(SHEET_ID).worksheet(sheet_name)
        sheet.append_row(values)
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"新增失敗：{e}"); return False

# 🔥 優化 C: 批次追加 (專用於批次補登，速度極快)
def batch_append_data(sheet_name, rows_list, col_order):
    try:
        # rows_list 是一個包含多個字典的 list
        values_to_write = []
        for row in rows_list:
            values_to_write.append([str(row.get(c, "")).strip() for c in col_order])
            
        client = get_google_sheet_client()
        sheet = client.open_by_key(SHEET_ID).worksheet(sheet_name)
        sheet.append_rows(values_to_write)
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"批次失敗：{e}"); return False

def get_tw_time(): return datetime.now(TW_TZ)

def calculate_age(dob_str):
    try:
        b_date = datetime.strptime(str(dob_str).strip(), "%Y-%m-%d").date()
        today = date.today()
        return today.year - b_date.year - ((today.month, today.day) < (b_date.month, b_date.day))
    except: return 0

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

        # 3. 長輩名冊
        if st.session_state.page == 'members':
            st.markdown('<div class="nav-active">📋 長輩名冊管理</div>', unsafe_allow_html=True)
        else:
            if st.button("📋 長輩名冊管理", key="nav_members", use_container_width=True):
                st.session_state.page = 'members'; st.rerun()

        # 4. 統計數據
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
if st.session_state.page == 'home':
    render_nav()
    st.markdown(f"<h2 style='color: {PRIMARY};'>📊 據點關懷概況</h2>", unsafe_allow_html=True)
    
    logs, members = load_data("elderly_logs"), load_data("elderly_members")
    this_year = get_tw_time().year
    today_str = get_tw_time().strftime("%Y-%m-%d")
    
    year_count = len(logs[pd.to_datetime(logs['日期'], errors='coerce').dt.year == this_year]) if not logs.empty else 0
    today_count = len(logs[logs['日期'] == today_str]) if not logs.empty else 0
    
    # 總體平均年齡
    avg_age = round(members['出生年月日'].apply(calculate_age).mean(), 1) if not members.empty else 0
    
    male_m = members[members['性別'] == '男']
    female_m = members[members['性別'] == '女']
    
    male_count = len(male_m)
    female_count = len(female_m)
    male_avg_age = round(male_m['出生年月日'].apply(calculate_age).mean(), 1) if not male_m.empty else 0
    female_avg_age = round(female_m['出生年月日'].apply(calculate_age).mean(), 1) if not female_m.empty else 0
    
    total_members = len(members)

    # 頂部看板
    st.markdown(f"""
    <div style="display: flex; gap: 20px;">
        <div style="flex: 1; background: linear-gradient(135deg, #FF9800 0%, #F57C00 100%); padding: 30px; border-radius: 20px; color: white; text-align: center; box-shadow: 0 10px 25px rgba(245, 124, 0, 0.3);">
            <div style="font-size: 1.2rem; opacity: 0.9; color: white !important;">📅 {this_year} 年度 - 據點總服務人次</div>
            <div style="font-size: 3.5rem; font-weight: 900; margin: 10px 0; color: white !important;">
                {year_count} <span style="font-size: 1.5rem; color: white !important;">人次</span>
            </div>
        </div>
        <div style="flex: 1; background: linear-gradient(135deg, #7E57C2 0%, #512DA8 100%); padding: 30px; border-radius: 20px; color: white; text-align: center; box-shadow: 0 10px 25px rgba(126, 87, 194, 0.3);">
            <div style="font-size: 1.2rem; opacity: 0.9; color: white !important;">☀️ 今日服務人次</div>
            <div style="font-size: 3.5rem; font-weight: 900; margin: 10px 0; color: white !important;">
                {today_count} <span style="font-size: 1.5rem; color: white !important;">人次</span>
            </div>
        </div>
    </div>
    <br>
    """, unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown(f"""
        <div class="dash-card">
            <div class="dash-label">👥 長輩總數 / 平均年齡</div>
            <div class="dash-value">{total_members} <span style="font-size:1rem;color:#888;">人</span></div>
            <div class="dash-sub">全體平均：{avg_age} 歲</div>
        </div>""", unsafe_allow_html=True)
        
    with c2:
        st.markdown(f"""
        <div class="dash-card">
            <div class="dash-label">♂ 男性長輩</div>
            <div class="dash-value">{male_count} <span style="font-size:1rem;color:#888;">人</span></div>
            <div class="dash-sub">
                <span style="color:#1E88E5; font-weight:bold;">平均 {male_avg_age} 歲</span>
            </div>
        </div>""", unsafe_allow_html=True)
        
    with c3:
        st.markdown(f"""
        <div class="dash-card">
            <div class="dash-label">♀ 女性長輩</div>
            <div class="dash-value">{female_count} <span style="font-size:1rem;color:#888;">人</span></div>
            <div class="dash-sub">
                <span style="color:#E91E63; font-weight:bold;">平均 {female_avg_age} 歲</span>
            </div>
        </div>""", unsafe_allow_html=True)

# --- [分頁 1：名冊 (局部上鎖)] ---
elif st.session_state.page == 'members':
    render_nav()
    st.markdown("## 📋 長輩名冊管理")
    df = load_data("elderly_members")
    
    # 🟢 1. 新增功能 (公開，方便填寫)
    with st.expander("➕ 新增長輩資料 (展開填寫)", expanded=True):
        with st.form("add_elder"):
            c1, c2, c3 = st.columns(3)
            name, pid, gender = c1.text_input("姓名"), c2.text_input("身分證字號"), c3.selectbox("性別", ["男", "女"])
            c4, c5 = st.columns([1, 2])
            dob, phone = c4.date_input("出生年月日", value=date(2025, 1, 1), min_value=date(1900, 1, 1)), c5.text_input("電話")
            addr, note = st.text_input("地址"), st.text_input("備註")
            if st.form_submit_button("確認新增"):
                if not pid or not name: st.error("姓名與身分證字號為必填")
                else:
                    new_row = {"姓名": name, "身分證字號": pid.upper(), "性別": gender, "出生年月日": str(dob), "電話": phone, "地址": addr, "備註": note, "加入日期": str(date.today())}
                    # --- 修改為 append_data ---
                    if append_data("elderly_members", new_row, M_COLS):
                        st.success(f"已新增：{name}"); time.sleep(1); st.rerun()
    
    # 🔒 2. 完整名冊 (需密碼才能看)
    st.markdown("### 📝 完整名冊資料 (需管理員權限)")
    
    if st.session_state.unlock_elder_list:
        # 已解鎖狀態：顯示表格
        if st.button("🔒 鎖定表格"):
            st.session_state.unlock_elder_list = False
            st.rerun()
            
        if not df.empty:
            df['年齡'] = df['出生年月日'].apply(calculate_age)
            st.data_editor(df[["姓名", "性別", "年齡", "電話", "地址", "身分證字號", "出生年月日", "備註"]], use_container_width=True, num_rows="dynamic", key="elder_editor")
    else:
        # 未解鎖狀態：顯示密碼框
        st.info("為了保護長輩個資，查看完整名冊請輸入密碼。")
        c_pwd, c_btn = st.columns([2, 1])
        with c_pwd:
            pwd = st.text_input("請輸入管理員密碼", type="password", key="unlock_list_pwd")
        with c_btn:
            st.markdown("<br>", unsafe_allow_html=True) # 排版用
            if st.button("🔓 解鎖名冊"):
                if pwd == st.secrets["admin_password"]:
                    st.session_state.unlock_elder_list = True
                    st.success("✅ 解鎖成功！")
                    st.rerun()
                else:
                    st.error("❌ 密碼錯誤")

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

    def do_checkin(pid, sbp, dbp, pulse):
        df_m = load_data("elderly_members")
        df_l = load_data("elderly_logs")
        pid_clean = pid.strip().upper()
        person = df_m[df_m['身分證字號'] == pid_clean]
        
        if person.empty:
            st.error(f"❌ 查無此人 ({pid_clean})，請先至名冊新增。")
            return
            
        name = person.iloc[0]['姓名']
        alerts = check_health_alert(sbp, dbp, pulse)
        
        new_log = {
            "姓名": name, "身分證字號": pid_clean,
            "日期": get_tw_time().strftime("%Y-%m-%d"), "時間": get_tw_time().strftime("%H:%M:%S"),
            "課程分類": final_course_cat, "課程名稱": final_course_name,
            "收縮壓": sbp, "舒張壓": dbp, "脈搏": pulse
        }
        # --- 修改為 append_data (原本是 save_data) ---
        append_data("elderly_logs", new_log, L_COLS)
        
        if alerts:
            st.warning(f"✅ {name} 報到成功，但數值異常：{' / '.join(alerts)}")
        else:
            st.success(f"✅ {name} 報到成功！")

    st.markdown('<div class="dash-card" style="border-left: 6px solid #FF9800;">', unsafe_allow_html=True)
    st.markdown("#### 1. 今日課程設定")
    c_main, c_sub, c_name = st.columns([1, 1, 1.5])
    with c_main: main_cat = st.selectbox("課程大分類", list(COURSE_HIERARCHY.keys()))
    with c_sub: 
        sub_list = COURSE_HIERARCHY[main_cat]
        sub_cat = st.selectbox("課程子分類", sub_list)
    with c_name: course_name = st.text_input("課程名稱 (選填)", placeholder="例如：端午節香包製作")
    
    final_course_cat = f"{main_cat}-{sub_cat}"
    final_course_name = course_name if course_name.strip() else sub_cat
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="dash-card">', unsafe_allow_html=True)
    st.markdown("#### 2. 長輩報到與量測輸入")
    
    c_bp1, c_bp2, c_bp3 = st.columns(3)
    sbp_val = c_bp1.number_input("收縮壓 (高壓)", min_value=50, max_value=250, value=120)
    dbp_val = c_bp2.number_input("舒張壓 (低壓)", min_value=30, max_value=150, value=80)
    pulse_val = c_bp3.number_input("脈搏", min_value=30, max_value=200, value=72)

    tab1, tab2 = st.tabs(["🔍 掃描/輸入身分證", "📋 下拉選單選取"])
    
    with tab1:
        input_pid = st.text_input("請掃描或輸入身分證字號", key="scan_pid_field")
        if st.button("確認報到 (身分證)", key="btn_do_scan"):
            if input_pid:
                do_checkin(input_pid, sbp_val, dbp_val, pulse_val)
                st.rerun()

    with tab2:
        df_m = load_data("elderly_members")
        if not df_m.empty:
            member_options = [f"{idx}. {row.姓名} ({row.身分證字號})" for idx, row in enumerate(df_m.itertuples(index=False), start=1)]
            selected_member = st.selectbox("請選擇長輩", ["--- 請選擇 ---"] + member_options)
            if st.button("確認報到 (選單)", key="btn_do_select"):
                if selected_member != "--- 請選擇 ---":
                    sel_pid = selected_member.split("(")[-1].replace(")", "")
                    do_checkin(sel_pid, sbp_val, dbp_val, pulse_val)
                    st.rerun()
        else:
            st.warning("名冊中尚無資料")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.write("📋 今日已報到名單 (您可以直接點擊下方格子修改內容)：")
    
    logs = load_data("elderly_logs")
    today_str = get_tw_time().strftime("%Y-%m-%d")
    
    if not logs.empty:
        today_logs = logs[logs['日期'] == today_str].copy()
        if not today_logs.empty:
            edited_df = st.data_editor(today_logs, column_order=['時間', '姓名', '收縮壓', '舒張壓', '脈搏', '課程名稱', '課程分類', '身分證字號'], use_container_width=True, num_rows="dynamic", key="today_checkin_editor")
            if st.button("💾 儲存名單修改"):
                other_logs = logs[logs['日期'] != today_str]
                final_logs = pd.concat([other_logs, edited_df], ignore_index=True)
                if save_data(final_logs, "elderly_logs"):
                    st.success("✅ 名單已更新至雲端！"); time.sleep(1); st.rerun()
        else: st.info("今日尚無報到紀錄。")
    else: st.info("資料庫目前無任何紀錄。")

    st.markdown("---")
    with st.expander("🕒 批次補登系統 (手動補錄過去資料)", expanded=False):
        df_m = load_data("elderly_members")
        if df_m.empty: st.warning("目前名冊中無長輩資料。")
        else:
            with st.form("manual_batch_form_new"):
                c_date, c_time = st.columns(2)
                back_date = c_date.date_input("選擇補登日期", value=get_tw_time().date())
                back_time = c_time.time_input("選擇補登時間", value=get_tw_time().time())
                member_options = [f"{idx}. {row.姓名} ({row.身分證字號})" for idx, row in enumerate(df_m.itertuples(index=False), start=1)]
                selected_members = st.multiselect("選擇補登長輩 (多選)", options=member_options)
                c_s, c_d, c_p = st.columns(3)
                b_sbp = c_s.number_input("補登收縮壓", value=120)
                b_dbp = c_d.number_input("補登舒張壓", value=80)
                b_pulse = c_p.number_input("補登脈搏", value=72)
                if st.form_submit_button("🚀 執行補登"):
                    if not selected_members: st.error("請先選擇長輩！")
                    else:
                        # 準備資料 List
                        new_entries = []
                        s_date = back_date.strftime("%Y-%m-%d")
                        s_time = back_time.strftime("%H:%M:%S")
                        
                        for label in selected_members:
                            target_pid = label.split("(")[-1].replace(")", "")
                            target_name = label.split(". ")[1].split(" (")[0]
                            # 建立字典
                            new_entries.append({
                                "姓名": target_name, "身分證字號": target_pid, 
                                "日期": s_date, "時間": s_time, 
                                "課程分類": final_course_cat, "課程名稱": final_course_name, 
                                "收縮壓": b_sbp, "舒張壓": b_dbp, "脈搏": b_pulse
                            })
                        
                        # --- 修改這裡：使用 batch_append_data 一次寫入 ---
                        # 直接把 list 丟進去，不用讀取舊資料，也不用 concat
                        if batch_append_data("elderly_logs", new_entries, L_COLS):
                            st.success(f"✅ 已成功補登 {len(new_entries)} 筆紀錄"); time.sleep(1); st.rerun()

# --- [分頁 4：統計 (完全公開)] ---
elif st.session_state.page == 'stats':
    render_nav()
    st.markdown("## 📊 統計數據")
    members, logs = load_data("elderly_members"), load_data("elderly_logs")
    if members.empty or logs.empty: st.info("尚無數據")
    else:
        logs['dt'] = pd.to_datetime(logs['日期'], errors='coerce')
        st.markdown('<div class="dash-card">', unsafe_allow_html=True)
        d_range = st.date_input("📅 選擇統計區間", value=(date(date.today().year, date.today().month, 1), date.today()))
        st.markdown('</div>', unsafe_allow_html=True)
        if isinstance(d_range, tuple) and len(d_range) == 2:
            f_logs = logs[(logs['dt'].dt.date >= d_range[0]) & (logs['dt'].dt.date <= d_range[1])].copy()
            tab_c, tab_h = st.tabs(["📚 課程成效", "🏥 長輩健康"])
            with tab_c:
                merged = f_logs.merge(members[['姓名', '性別']], on='姓名', how='left')
                st.markdown("### 1. 參與人次統計")
                m1, m2, m3 = st.columns(3)
                with m1: st.markdown(f"""<div class="dash-card"><div style="color:#666;">總參與人次</div><div style="font-size:1.8rem;color:{PRIMARY};font-weight:900;">{len(merged)} 次</div></div>""", unsafe_allow_html=True)
                with m2: st.markdown(f"""<div class="dash-card"><div style="color:#666;">男性參與</div><div style="font-size:1.8rem;color:{PRIMARY};font-weight:900;">{len(merged[merged['性別']=='男'])} 次</div></div>""", unsafe_allow_html=True)
                with m3: st.markdown(f"""<div class="dash-card"><div style="color:#666;">女性參與</div><div style="font-size:1.8rem;color:{PRIMARY};font-weight:900;">{len(merged[merged['性別']=='女'])} 次</div></div>""", unsafe_allow_html=True)
                
                unique_sessions = merged.drop_duplicates(subset=['日期', '課程名稱', '課程分類']).copy()
                unique_sessions['大分類'] = unique_sessions['課程分類'].apply(lambda x: x.split('-')[0] if '-' in x else x)
                unique_sessions['子分類'] = unique_sessions['課程分類'].apply(lambda x: x.split('-')[1] if '-' in x else x)

                st.markdown("### 2. 課程場次占比 (靈動泡泡圖)")
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
                    st.dataframe(main_cts[['類別', '場次']], use_container_width=True, column_config={"場次": st.column_config.ProgressColumn("熱度", format="%d", min_value=0, max_value=int(main_cts['場次'].max() or 1))})
                with c2:
                    sc1, sc2 = st.columns([1.2, 2])
                    with sc1: st.markdown("#### 子分類鑽取")
                    with sc2: sel_m = st.selectbox("請選擇大分類", sorted(main_cts['類別'].unique()), label_visibility="collapsed", key="sel_main_stats")
                    sub_cts = unique_sessions[unique_sessions['大分類']==sel_m]['子分類'].value_counts().reset_index()
                    sub_cts.columns = ['子分類', '場次']
                    st.dataframe(sub_cts, use_container_width=True, column_config={"場次": st.column_config.ProgressColumn("熱度", format="%d", min_value=0, max_value=int(sub_cts['場次'].max() or 1))})

            with tab_h:
                target_elder = st.selectbox("🔍 請選擇長輩", sorted(f_logs['姓名'].unique()), key="sel_elder_health")
                e_logs = f_logs[f_logs['姓名']==target_elder].sort_values('dt')
                e_logs['收縮壓'] = pd.to_numeric(e_logs['收縮壓'], errors='coerce')
                high_bp = len(e_logs[e_logs['收縮壓']>=140])
                st.markdown(f"""<div class="dash-card" style="border-left:6px solid #E91E63"><div style="color:#666;">血壓異常次數</div><div style="font-size:1.8rem;color:{PRIMARY};font-weight:900;">{high_bp} 次</div></div>""", unsafe_allow_html=True)
                fig = px.line(e_logs, x='dt', y=['收縮壓'], markers=True, title="收縮壓變化趨勢")
                fig.add_hline(y=140, line_dash="dash", line_color="red")
                st.plotly_chart(fig, use_container_width=True)
