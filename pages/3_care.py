import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta, timezone
import gspread
import plotly.express as px
import random
import time

# =========================================================
# 0) 系統設定
# =========================================================
st.set_page_config(
    page_title="關懷戶管理系統", 
    page_icon="🏠", 
    layout="wide", 
    initial_sidebar_state="expanded" 
)

# 1. 初始化登入狀態
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

# 2. 頁面狀態初始化
if 'page' not in st.session_state:
    st.session_state.page = 'home'

# 3. 初始化局部解鎖狀態
if 'unlock_members' not in st.session_state: st.session_state.unlock_members = False
if 'unlock_details' not in st.session_state: st.session_state.unlock_details = False

TW_TZ = timezone(timedelta(hours=8))
PRIMARY = "#4A4E69"   # 深藍灰
GREEN   = "#8E9775"   # 苔蘚綠
BG_MAIN = "#F8F9FA"   # 淺灰底
TEXT    = "#333333"

# =========================================================
# 1) CSS 樣式
# =========================================================
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@500;700;900&display=swap');

html, body, [class*="css"], div, p, span, li, ul {{
    font-family: "Noto Sans TC", "Microsoft JhengHei", sans-serif;
    color: {TEXT} !important;
}}

.stApp {{ background-color: {BG_MAIN} !important; }}
section[data-testid="stSidebar"] {{ background-color: {BG_MAIN}; border-right: none; }}

/* 懸浮大卡片 */
.block-container {{
    background-color: #FFFFFF; border-radius: 25px;
    padding: 3rem 3rem !important; box-shadow: 0 4px 20px rgba(0,0,0,0.05);
    margin-top: 2rem; margin-bottom: 2rem; max-width: 95% !important;
}}

header[data-testid="stHeader"] {{ display: block !important; background-color: transparent !important; }}
header[data-testid="stHeader"] .decoration {{ display: none; }}

/* 側邊欄按鈕 */
section[data-testid="stSidebar"] button {{
    background-color: #FFFFFF !important; color: #666 !important;
    border: 1px solid transparent !important; box-shadow: 0 4px 6px rgba(0,0,0,0.05) !important;
    border-radius: 25px !important; padding: 10px 0 !important;
    font-weight: 700 !important; width: 100%; margin-bottom: 8px !important;
    transition: all 0.2s;
}}
section[data-testid="stSidebar"] button:hover {{
    transform: translateY(-2px); box-shadow: 0 6px 12px rgba(0,0,0,0.1) !important;
    color: {GREEN} !important;
}}
.nav-active {{
    background: linear-gradient(135deg, {GREEN}, #6D6875);
    color: white !important; padding: 12px 0; text-align: center; border-radius: 25px;
    font-weight: 900; box-shadow: 0 4px 10px rgba(142, 151, 117, 0.4);
    margin-bottom: 12px; cursor: default;
}}

/* 輸入框優化 */
div[data-testid="stDataFrame"], div[data-testid="stTable"] {{
    background-color: #FFFFFF !important; border-radius: 10px; padding: 5px;
}}
div[data-baseweb="select"] > div, .stTextInput input, .stDateInput input, .stTimeInput input, .stNumberInput input {{
    background-color: #F8F9FA !important; color: #000000 !important;
    border: 2px solid #E0E0E0 !important; border-radius: 12px !important; font-weight: 700 !important;
}}
div[role="listbox"], ul[data-baseweb="menu"], li[role="option"] {{
    background-color: #FFFFFF !important; color: #000000 !important;
}}
li[role="option"]:hover {{
    background-color: #E8F5E9 !important; color: {GREEN} !important;
}}

/* 按鈕樣式 */
div[data-testid="stFormSubmitButton"] > button,
div[data-testid="stDownloadButton"] > button {{
    background-color: {PRIMARY} !important; color: #FFFFFF !important;
    border: none !important; border-radius: 12px !important; font-weight: 900 !important;
    padding: 10px 25px !important;
}}
div[data-testid="stFormSubmitButton"] > button:hover,
div[data-testid="stDownloadButton"] > button:hover {{
    background-color: {GREEN} !important;
    transform: translateY(-2px); box-shadow: 0 4px 10px rgba(0,0,0,0.15);
}}

/* 看板卡片 */
.care-metric-box {{
    padding: 20px; border-radius: 20px; color: #FFFFFF !important; text-align: center; margin-bottom: 15px;
    box-shadow: 0 8px 20px rgba(0,0,0,0.1); min-height: 140px;
    display: flex; flex-direction: column; justify-content: center;
}}
.care-metric-box div, .care-metric-box span {{ color: #FFFFFF !important; font-weight: 900 !important; }}

/* 訪視卡片 */
.visit-card {{
    background-color: #FFFFFF; border-left: 5px solid {GREEN};
    border-radius: 10px; padding: 15px 20px; margin-bottom: 15px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05); border-top: 1px solid #eee; border-right: 1px solid #eee; border-bottom: 1px solid #eee;
}}
.visit-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }}
.visit-date {{ font-weight: 900; font-size: 1.1rem; color: #333; }}
.visit-volunteer {{ font-size: 0.9rem; color: #666; background: #f0f0f0; padding: 4px 12px; border-radius: 15px; }}
.visit-tag {{
    display: inline-block; background-color: {GREEN}; color: white !important;
    padding: 4px 10px; border-radius: 5px; font-size: 0.9rem; font-weight: bold; margin-bottom: 8px;
}}
.visit-tag.only {{ background-color: #9E9E9E; }} 
.visit-note {{ font-size: 1rem; color: #444; line-height: 1.5; background: #FAFAFA; padding: 10px; border-radius: 8px; }}

/* 庫存管理卡片 */
.stock-card {{
    background-color: white; border: 1px solid #eee; border-radius: 15px;
    padding: 20px; margin-bottom: 20px; position: relative;
    transition: all 0.3s ease; height: 100%;
}}
.stock-card:hover {{
    transform: translateY(-5px); box-shadow: 0 10px 20px rgba(0,0,0,0.08); border-color: {GREEN};
}}
.stock-top {{ display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 15px; }}
.stock-icon {{ font-size: 2.5rem; background: #F5F5F5; width: 60px; height: 60px; display: flex; align-items: center; justify-content: center; border-radius: 50%; }}
.stock-info {{ text-align: right; width: 100%; padding-left: 10px; }}
.stock-name {{ font-size: 1.3rem; font-weight: 900; color: #333; margin-bottom: 3px; line-height: 1.2; }}
.stock-donor {{ font-size: 0.9rem; color: {PRIMARY}; background: #EFEBE9; padding: 2px 8px; border-radius: 8px; font-weight: bold; display: inline-block; margin-bottom: 5px; }}
.stock-type {{ font-size: 0.8rem; color: #888; background: #f0f0f0; padding: 2px 8px; border-radius: 8px; display: inline-block; }}
.stock-bar-bg {{ width: 100%; height: 10px; background: #eee; border-radius: 5px; overflow: hidden; margin-top: 10px; }}
.stock-bar-fill {{ height: 100%; border-radius: 5px; transition: width 0.5s ease; }}
.stock-stats {{ display: flex; justify-content: space-between; margin-top: 10px; font-size: 0.9rem; color: #666; font-weight: bold; }}
.stock-warning {{ color: #D32F2F; font-weight: bold; display: flex; align-items: center; gap: 5px; margin-top: 10px; font-size: 0.9rem; }}

/* 卡片上浮效果 */
div[data-testid="stVerticalBlockBorderWrapper"] {{
    transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
    border: 2px solid #E0E0E0 !important; background-color: #FFFFFF;
}}
div[data-testid="stVerticalBlockBorderWrapper"]:hover {{
    transform: translateY(-8px); box-shadow: 0 12px 24px rgba(0,0,0,0.15);
    border-color: {GREEN} !important; z-index: 10;
}}
.inv-card-header {{ font-weight: 900; font-size: 1.1rem; color: #333; margin-bottom: 5px; }}
.inv-card-stock {{ font-size: 0.9rem; color: #666; background-color: #eee; padding: 2px 8px; border-radius: 10px; display: inline-block; margin-bottom: 10px; }}
.inv-card-stock.low {{ color: #D32F2F !important; background-color: #FFEBEE !important; border: 1px solid #D32F2F; }}

/* 健康警示標籤 */
.health-alert {{ padding: 10px; border-radius: 10px; margin-top: 5px; font-weight: bold; font-size: 0.9rem; display: flex; align-items: center; }}
.alert-red {{ background-color: #FFEBEE; color: #C62828 !important; border: 1px solid #C62828; }}
.alert-orange {{ background-color: #FFF3E0; color: #EF6C00 !important; border: 1px solid #EF6C00; }}
.alert-green {{ background-color: #E8F5E9; color: #2E7D32 !important; border: 1px solid #2E7D32; }}

</style>
""", unsafe_allow_html=True)

# =========================================================
# 2) 資料邏輯
# =========================================================
SHEET_ID = "1A3-VwCBYjnWdcEiL6VwbV5-UECcgX7TqKH94sKe8P90"
COLS_MEM = ["姓名", "身分證字號", "性別", "生日", "地址", "電話", "緊急聯絡人", "緊急聯絡人電話", "身分別", "18歲以下子女", "成人數量", "65歲以上長者"]

# 更新健康欄位以包含新評估項目
COLS_HEALTH = [
    "姓名", "身分證字號", "評估日期",
    "是否有假牙", "今年洗牙", "握力", "身高", "體重", "BMI", "聽力測試",
    "營養篩檢分數", "營養狀態",
    "心情溫度計分數", "情緒狀態", "有自殺意念"
]

COLS_INV = ["捐贈者", "物資類型", "物資內容", "總數量", "捐贈日期"]
COLS_LOG = ["志工", "發放日期", "關懷戶姓名", "物資內容", "發放數量", "訪視紀錄"]

@st.cache_resource
def get_client(): return gspread.service_account_from_dict(st.secrets["gcp_service_account"])

@st.cache_data(ttl=10)
def load_data(sn, target_cols):
    try:
        client = get_client(); sheet = client.open_by_key(SHEET_ID).worksheet(sn)
        df = pd.DataFrame(sheet.get_all_records()).astype(str)
        for c in target_cols:
            if c not in df.columns: df[c] = ""
        return df
    except: return pd.DataFrame(columns=target_cols)

def save_data(df, sn):
    try:
        df_fix = df.fillna("").replace(['nan', 'NaN', 'nan.0', 'None', '<NA>'], "").astype(str)
        client = get_client(); sheet = client.open_by_key(SHEET_ID).worksheet(sn)
        sheet.clear(); sheet.update([df_fix.columns.values.tolist()] + df_fix.values.tolist())
        st.cache_data.clear(); return True
    except Exception as e:
        st.error(f"寫入失敗：{e}"); return False

def calculate_age(dob_str):
    try:
        bd = datetime.strptime(str(dob_str).strip(), "%Y-%m-%d").date()
        today = date.today(); return today.year - bd.year - ((today.month, today.day) < (bd.month, bd.day))
    except: return 0

# =========================================================
# 3) Navigation
# =========================================================
def render_nav():
    with st.sidebar:
        st.markdown(f"<h2 style='color:{GREEN}; margin-bottom:5px; padding-left:10px;'>🏠 關懷戶中心</h2>", unsafe_allow_html=True)
        st.write("") 
        if st.session_state.page == 'home':
            st.markdown('<div class="nav-active">📊 關懷概況看板</div>', unsafe_allow_html=True)
        else:
            if st.button("📊 關懷概況看板", key="nav_home", use_container_width=True): st.session_state.page = 'home'; st.rerun()
        if st.session_state.page == 'members':
            st.markdown('<div class="nav-active">📋 名冊管理</div>', unsafe_allow_html=True)
        else:
            if st.button("📋 名冊管理", key="nav_members", use_container_width=True): st.session_state.page = 'members'; st.rerun()
        if st.session_state.page == 'health':
            st.markdown('<div class="nav-active">🏥 健康追蹤</div>', unsafe_allow_html=True)
        else:
            if st.button("🏥 健康追蹤", key="nav_health", use_container_width=True): st.session_state.page = 'health'; st.rerun()
        if st.session_state.page == 'inventory':
            st.markdown('<div class="nav-active">📦 物資庫存</div>', unsafe_allow_html=True)
        else:
            if st.button("📦 物資庫存", key="nav_inv", use_container_width=True): st.session_state.page = 'inventory'; st.rerun()
        if st.session_state.page == 'visit':
            st.markdown('<div class="nav-active">🤝 訪視發放</div>', unsafe_allow_html=True)
        else:
            if st.button("🤝 訪視發放", key="nav_visit", use_container_width=True): st.session_state.page = 'visit'; st.rerun()
        if st.session_state.page == 'stats':
            st.markdown('<div class="nav-active">📈 數據統計</div>', unsafe_allow_html=True)
        else:
            if st.button("📈 數據統計", key="nav_stats", use_container_width=True): st.session_state.page = 'stats'; st.rerun()
        st.markdown("---")
        if st.button("🚪 回系統大廳", key="nav_back", use_container_width=True): st.switch_page("Home.py")
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.markdown("<div style='text-align:center; color:#999; font-size:0.8rem;'>Designed for Fude Community</div>", unsafe_allow_html=True)

# =========================================================
# 4) Pages
# =========================================================

# --- [分頁 0：首頁] ---
if st.session_state.page == 'home':
    render_nav()
    st.markdown(f"<h2 style='color: {GREEN};'>📊 關懷戶概況看板</h2>", unsafe_allow_html=True)
    mems, logs = load_data("care_members", COLS_MEM), load_data("care_logs", COLS_LOG)
    
    if not mems.empty:
        mems['age'] = mems['生日'].apply(calculate_age)
        mems_display = mems[~mems['身分別'].str.contains("一般戶", na=False)]
        
        cur_y = datetime.now(TW_TZ).year
        prev_y = cur_y - 1
        
        dist_df = logs.copy()
        if not logs.empty:
            dist_df['dt'] = pd.to_datetime(dist_df['發放日期'], errors='coerce')
            cur_val = dist_df[dist_df['dt'].dt.year == cur_y]['發放數量'].replace("","0").astype(float).sum()
            prev_val = dist_df[dist_df['dt'].dt.year == prev_y]['發放數量'].replace("","0").astype(float).sum()
        else: cur_val = prev_val = 0
        
        dis_c = len(mems[mems['身分別'].str.contains("身障", na=False)])
        low_c = len(mems[mems['身分別'].str.contains("低收|中低收", na=False)])
        
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f'<div class="care-metric-box" style="background:linear-gradient(135deg,#8E9775 0%,#6D6875 100%);"><div>🏠 關懷戶總人數</div><div style="font-size:2.8rem;">{len(mems_display)} <span style="font-size:1.2rem;">人</span></div><div>平均 {round(mems_display["age"].mean(),1)} 歲</div></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="care-metric-box" style="background:linear-gradient(135deg,#A4AC86 0%,#8E9775 100%);"><div>♿ 身障關懷人數</div><div style="font-size:2.8rem;">{dis_c} <span style="font-size:1.2rem;">人</span></div></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="care-metric-box" style="background:linear-gradient(135deg,#6D6875 0%,#4A4E69 100%);"><div>📉 低收/中低收</div><div style="font-size:2.8rem;">{low_c} <span style="font-size:1.2rem;">人</span></div></div>', unsafe_allow_html=True)
        c4, c5 = st.columns(2)
        with c4: st.markdown(f'<div class="care-metric-box" style="background:linear-gradient(135deg,#BC6C25 0%,#8E9775 100%);"><div>🎁 {cur_y} 當年度發放量</div><div style="font-size:3.5rem;">{int(cur_val)} <span style="font-size:1.5rem;">份</span></div></div>', unsafe_allow_html=True)
        with c5: st.markdown(f'<div class="care-metric-box" style="background:linear-gradient(135deg,#A4AC86 0%,#6D6875 100%);"><div>⏳ {prev_y} 上年度發放量</div><div style="font-size:3.5rem;">{int(prev_val)} <span style="font-size:1.5rem;">份</span></div></div>', unsafe_allow_html=True)

# --- [分頁 1：名冊] ---
elif st.session_state.page == 'members':
    render_nav()
    st.markdown("## 📋 關懷戶名冊管理")
    df = load_data("care_members", COLS_MEM)
    
    with st.expander("➕ 新增關懷戶 (展開填寫)", expanded=False):
        with st.form("add_care", clear_on_submit=True):
            c1, c2, c3, c4 = st.columns(4)
            n = c1.text_input("姓名")
            p = c2.text_input("身分證")
            g = c3.selectbox("性別", ["男", "女"])
            b = c4.date_input("生日", value=date(1950, 1, 1), min_value=date(1911, 1, 1), max_value=date(2025, 12, 31))
            addr = st.text_input("地址")
            ph = st.text_input("電話")
            ce1, ce2 = st.columns(2)
            en = ce1.text_input("緊急聯絡人")
            ep = ce2.text_input("緊急聯絡電話")
            cn1, cn2, cn3 = st.columns(3)
            child = cn1.number_input("18歲以下子女", min_value=0, value=0, step=1)
            adult = cn2.number_input("成人數量", min_value=0, value=0, step=1)
            senior = cn3.number_input("65歲以上長者", min_value=0, value=0, step=1)
            id_t = st.multiselect("身分別", ["低收", "中低收", "中低老人", "身障", "獨居", "獨居有子女", "一般戶"])
            
            if st.form_submit_button("確認新增"):
                is_duplicate = False
                if not df.empty:
                    mask = (df['姓名'] == n) & (df['身分證字號'] == p.upper())
                    if not df[mask].empty: is_duplicate = True

                if is_duplicate: st.error(f"❌ 資料重複！名冊中已有「{n} ({p})」的資料。")
                elif not n or not p: st.error("❌ 姓名與身分證字號必填")
                else:
                    new = {
                        "姓名": n, "身分證字號": p.upper(), "性別": g, "生日": str(b), 
                        "地址": addr, "電話": ph, "緊急聯絡人": en, "緊急聯絡人電話": ep, 
                        "身分別": ",".join(id_t),
                        "18歲以下子女": str(child), "成人數量": str(adult), "65歲以上長者": str(senior)
                    }
                    if save_data(pd.concat([df, pd.DataFrame([new])], ignore_index=True), "care_members"):
                        st.success("✅ 已新增！"); time.sleep(1); st.rerun()
    
    st.markdown("### 📝 完整名冊 (需權限)")
    if st.session_state.unlock_members:
        if not df.empty:
            df['歲數'] = df['生日'].apply(calculate_age)
            ed = st.data_editor(df, use_container_width=True, num_rows="dynamic", key="mem_ed")
            if st.button("💾 儲存修改"): 
                if save_data(ed, "care_members"): st.success("已更新")
    else:
        st.info("🔒 為保護個資，查看完整表格需輸入管理員密碼。")
        c_pwd, c_btn = st.columns([2, 1])
        with c_pwd: pwd_m = st.text_input("請輸入密碼", type="password", key="unlock_m_pwd")
        with c_btn: 
            if st.button("🔓 解鎖名冊"):
                if pwd_m == st.secrets["admin_password"]:
                    st.session_state.unlock_members = True; st.rerun()
                else: st.error("❌ 密碼錯誤")

# --- [分頁 2：健康 (大幅更新)] ---
elif st.session_state.page == 'health':
    render_nav()
    st.markdown("## 🏥 關懷戶健康與風險評估")
    h_df, m_df = load_data("care_health", COLS_HEALTH), load_data("care_members", COLS_MEM)
    
    with st.expander("➕ 新增/更新 健康評估紀錄", expanded=True):
        with st.form("h_form"):
            st.markdown("### 1. 基本資料與生理量測")
            sel_n = st.selectbox("選擇關懷戶", m_df['姓名'].tolist() if not m_df.empty else ["無名冊"])
            eval_date = st.date_input("評估日期", value=date.today())
            
            c1, c2, c3 = st.columns(3)
            h = c1.number_input("身高 (cm)", min_value=0.0, step=0.1)
            w = c2.number_input("體重 (kg)", min_value=0.0, step=0.1)
            grip = c3.text_input("握力 (kg)")
            
            c4, c5, c6 = st.columns(3)
            dent = c4.selectbox("是否有假牙", ["無", "有"])
            wash = c5.selectbox("今年洗牙", ["否", "是"])
            hear = c6.selectbox("聽力狀況", ["正常", "需注意"])

            st.markdown("---")
            st.markdown("### 2. 營養評估 (MNA篩檢)")
            # MNA 題目
            q1 = st.radio("Q1. 過去三個月是否因食慾不振/消化/吞嚥問題而減少食量？",
                          ["0分：食量嚴重減少", "1分：食量中度減少", "2分：食量沒有改變"], horizontal=True)
            q2 = st.radio("Q2. 過去三個月體重下降情況",
                          ["0分：下降>3公斤", "1分：不知道", "2分：下降1-3公斤", "3分：沒有下降"], horizontal=True)
            q3 = st.radio("Q3. 活動能力",
                          ["0分：需長期臥床或坐輪椅", "1分：可下床但不能外出", "2分：可以外出"], horizontal=True)
            q4 = st.radio("Q4. 過去三個月內有無受到心理創傷或急性疾病？",
                          ["0分：有", "2分：沒有"], horizontal=True)
            q5 = st.radio("Q5. 精神心理問題",
                          ["0分：嚴重失智或憂鬱", "1分：輕度失智", "2分：沒有問題"], horizontal=True)
            
            # BMI 自動計算與評分
            bmi_val = 0.0
            bmi_score = 0
            if h > 0 and w > 0:
                bmi_val = w / ((h/100)**2)
                if bmi_val < 19: bmi_score = 0
                elif 19 <= bmi_val < 21: bmi_score = 1
                elif 21 <= bmi_val < 23: bmi_score = 2
                else: bmi_score = 3
            
            st.info(f"📏 根據身高體重自動換算 BMI: {round(bmi_val, 1)} (得分: {bmi_score})")
            
            # 營養分數計算
            s1 = int(q1.split("分")[0])
            s2 = int(q2.split("分")[0])
            s3 = int(q3.split("分")[0])
            s4 = int(q4.split("分")[0])
            s5 = int(q5.split("分")[0])
            nutri_score = s1 + s2 + s3 + s4 + s5 + bmi_score
            
            if nutri_score >= 12: nutri_status = "正常狀況"
            elif 8 <= nutri_score <= 11: nutri_status = "有營養不良風險"
            else: nutri_status = "營養不良"

            st.markdown("---")
            st.markdown("### 3. 心情溫度計 (BSRS-5)")
            st.caption("請評估過去一週的困擾程度 (0:完全沒有 ~ 5:非常嚴重)")
            
            b1, b2 = st.columns(2)
            bq1 = b1.slider("1. 睡眠困難", 0, 5, 0)
            bq2 = b2.slider("2. 感覺緊張不安", 0, 5, 0)
            bq3 = b1.slider("3. 覺得容易動怒", 0, 5, 0)
            bq4 = b2.slider("4. 感覺憂鬱、心情低落", 0, 5, 0)
            bq5 = b1.slider("5. 覺得比不上別人", 0, 5, 0)
            bq6 = b2.slider("6. 有自殺想法", 0, 5, 0) # 獨立指標

            # 情緒分數計算 (前5題加總)
            mood_score = bq1 + bq2 + bq3 + bq4 + bq5 
            # 依據使用者定義的標準 (0-5, 6-9, 10-14, 15+)
            if mood_score >= 15: mood_status = "重度情緒困擾"
            elif mood_score >= 10: mood_status = "中度情緒困擾"
            elif mood_score >= 6: mood_status = "輕度情緒困擾"
            else: mood_status = "正常"
            
            suicide_risk = "是" if bq6 > 0 else "否"

            # 預覽結果區塊
            if st.columns(1)[0].checkbox("顯示本次評估結果預覽"):
                res_col1, res_col2 = st.columns(2)
                with res_col1:
                    st.markdown(f"**🍱 營養總分**: {nutri_score} ({nutri_status})")
                with res_col2:
                    st.markdown(f"**🌡️ 情緒總分**: {mood_score} ({mood_status})")
                    if suicide_risk == "是":
                        st.markdown("<span style='color:red; font-weight:bold;'>⚠️ 檢測到自殺意念</span>", unsafe_allow_html=True)

            if st.form_submit_button("💾 儲存完整評估紀錄"):
                if not sel_n or sel_n == "無名冊":
                    st.error("❌ 請選擇有效的關懷戶")
                else:
                    pid = m_df[m_df['姓名']==sel_n]['身分證字號'].iloc[0]
                    new_h = {
                        "姓名": sel_n, "身分證字號": pid, "評估日期": str(eval_date),
                        "是否有假牙": dent, "今年洗牙": wash, "握力": grip, 
                        "身高": str(h), "體重": str(w), "BMI": str(round(bmi_val,1)), "聽力測試": hear,
                        "營養篩檢分數": str(nutri_score), "營養狀態": nutri_status,
                        "心情溫度計分數": str(mood_score), "情緒狀態": mood_status, "有自殺意念": suicide_risk
                    }
                    if save_data(pd.concat([h_df, pd.DataFrame([new_h])], ignore_index=True), "care_health"): 
                        st.success("✅ 健康評估已存檔！"); st.rerun()

    if not h_df.empty:
        st.markdown("#### 📂 歷史健康紀錄")
        ed_h = st.data_editor(h_df.sort_values("評估日期", ascending=False), use_container_width=True, num_rows="dynamic", key="h_ed")
        if st.button("💾 儲存修改內容"): save_data(ed_h, "care_health")

# --- [分頁 3：物資] ---
elif st.session_state.page == 'inventory':
    render_nav()
    st.markdown("## 📦 物資庫存管理")
    inv, logs = load_data("care_inventory", COLS_INV), load_data("care_logs", COLS_LOG)
    
    with st.expander("➕ 新增捐贈物資 / 款項", expanded=False):
        existing_donors = sorted(list(set(inv['捐贈者'].dropna().unique()))) if not inv.empty else []
        
        st.markdown(f"<div style='background:#f9f9f9; padding:10px; border-radius:10px; margin-bottom:10px;'><b>⚙️ 步驟 1：設定來源與類型</b></div>", unsafe_allow_html=True)
        c_mode1, c_mode2 = st.columns(2)
        with c_mode1:
            donor_mode = st.radio("👤 捐贈者來源", ["從歷史名單選擇", "輸入新單位"], horizontal=True)
        with c_mode2:
            sel_type = st.selectbox("📦 物資類型", ["食物","日用品","輔具","現金","服務"])
            type_history = []
            if not inv.empty:
                type_history = sorted(inv[inv['物資類型'] == sel_type]['物資內容'].unique().tolist())
            if type_history:
                item_mode = st.radio(f"📝 {sel_type}名稱來源", ["從歷史紀錄選擇", "輸入新名稱"], horizontal=True)
            else:
                st.caption(f"💡 目前「{sel_type}」類尚無紀錄，請直接輸入新名稱。")
                item_mode = "輸入新名稱"

        with st.form("add_inv_form"):
            st.markdown(f"<div style='background:#f9f9f9; padding:10px; border-radius:10px; margin-bottom:10px;'><b>✍️ 步驟 2：填寫細節</b></div>", unsafe_allow_html=True)
            c1, c2, c3 = st.columns([1.5, 1.5, 1])
            with c1:
                if donor_mode == "從歷史名單選擇":
                    final_donor = st.selectbox("捐贈單位/人", existing_donors) if existing_donors else ""
                else:
                    final_donor = st.text_input("輸入新單位/人", placeholder="例如：善心人士張先生")
            with c2:
                if item_mode == "從歷史紀錄選擇" and type_history:
                    final_item_name = st.selectbox(f"選擇{sel_type}品項", type_history)
                else:
                    final_item_name = st.text_input(f"輸入{sel_type}名稱", placeholder="例如：白米")
            with c3:
                qt = st.number_input("數量/金額", min_value=1)
            
            if st.form_submit_button("✅ 錄入庫存"):
                if not final_donor: st.error("❌ 請填寫捐贈者！")
                elif not final_item_name: st.error("❌ 請填寫物資名稱！")
                else:
                    new = {
                        "捐贈者": final_donor, "物資類型": sel_type, 
                        "物資內容": final_item_name, "總數量": qt, "捐贈日期": str(date.today())
                    }
                    if save_data(pd.concat([inv, pd.DataFrame([new])], ignore_index=True), "care_inventory"): 
                        st.success(f"已成功錄入：{final_donor} 捐贈 {final_item_name} x {qt}")
                        time.sleep(1); st.rerun()

    if not inv.empty:
        st.markdown("### 📊 庫存概況 (智慧卡片)")
        inv_summary = []
        for (item_name, donor_name), group in inv.groupby(['物資內容', '捐贈者']):
            total_in = group['總數量'].replace("","0").astype(float).sum()
            composite_name = f"{item_name} ({donor_name})"
            total_out = logs[logs['物資內容'] == composite_name]['發放數量'].replace("","0").astype(float).sum() if not logs.empty else 0
            remain = total_in - total_out
            if remain > 0:
                m_type = group.iloc[0]['物資類型']
                icon_map = {"食物": "🍱", "日用品": "🧻", "輔具": "🦯", "現金": "💰", "服務": "🧹"}
                icon = icon_map.get(m_type, "📦")
                pct = int((remain / total_in * 100)) if total_in > 0 else 0
                if pct < 0: pct = 0
                bar_color = "#8E9775"
                if remain <= 5: bar_color = "#D32F2F"
                elif pct < 30: bar_color = "#FBC02D"
                inv_summary.append({
                    "name": item_name, "donor": donor_name, "type": m_type, "icon": icon,
                    "in": int(total_in), "out": int(total_out), "remain": int(remain),
                    "pct": pct, "bar_color": bar_color
                })
        
        if not inv_summary:
            st.info("💡 目前無庫存 (或已全數發放完畢)")
        else:
            for i in range(0, len(inv_summary), 3):
                cols = st.columns(3)
                for j in range(3):
                    if i + j < len(inv_summary):
                        item = inv_summary[i + j]
                        with cols[j]:
                            warning_html = f'<div class="stock-warning">⚠️ 庫存告急！僅剩 {item["remain"]}</div>' if item["remain"] <= 5 else ""
                            st.markdown(f"""
<div class="stock-card">
<div class="stock-top">
<div class="stock-icon">{item['icon']}</div>
<div class="stock-info">
<div class="stock-name">{item['name']}</div>
<div class="stock-donor">{item['donor']}</div>
</div>
</div>
<div class="stock-stats">
<span>總入庫: {item['in']}</span>
<span>已發放: {item['out']}</span>
</div>
<div class="stock-bar-bg">
<div class="stock-bar-fill" style="width: {item['pct']}%; background-color: {item['bar_color']};"></div>
</div>
<div style="text-align:right; margin-top:5px; font-size:0.85rem; color:#888;">
剩餘庫存: <span style="font-size:1.2rem; color:{item['bar_color']}; font-weight:900;">{item['remain']}</span>
</div>
{warning_html}
</div>
""", unsafe_allow_html=True)

        with st.expander("🛠️ 進階管理：編輯原始庫存資料 (點擊展開)"):
            ed_i = st.data_editor(inv, use_container_width=True, num_rows="dynamic", key="inv_ed")
            if st.button("💾 儲存修改內容"): save_data(ed_i, "care_inventory")

# --- [分頁 4：訪視] ---
elif st.session_state.page == 'visit':
    render_nav()
    st.markdown("## 🤝 訪視與物資發放紀錄")
    mems = load_data("care_members", COLS_MEM)
    inv = load_data("care_inventory", COLS_INV)
    logs = load_data("care_logs", COLS_LOG)
    
    stock_map = {}
    if not inv.empty:
        for (item_name, donor_name), group in inv.groupby(['物資內容', '捐贈者']):
            total_in = group['總數量'].replace("","0").astype(float).sum()
            composite_name = f"{item_name} ({donor_name})"
            total_out = logs[logs['物資內容'] == composite_name]['發放數量'].replace("","0").astype(float).sum() if not logs.empty else 0
            remain = int(total_in - total_out)
            if remain > 0: stock_map[composite_name] = remain
    
    st.markdown("#### 1. 選擇訪視對象")
    all_tags = set()
    if not mems.empty:
        for s in mems['身分別'].astype(str):
            for t in s.split(','):
                if t.strip(): all_tags.add(t.strip())
    c_filter, c_person = st.columns([1, 2])
    with c_filter:
        sel_tag = st.selectbox("🌪️ 依身分別篩選", ["(全部顯示)"] + sorted(list(all_tags)))
    with c_person:
        filtered_mems = mems if sel_tag == "(全部顯示)" else mems[mems['身分別'].str.contains(sel_tag, na=False)]
        target_p = st.selectbox("👤 選擇關懷戶", filtered_mems['姓名'].tolist() if not filtered_mems.empty else [])

    st.markdown("#### 2. 填寫訪視內容與物資")
    with st.form("visit_multi_form"):
        c1, c2 = st.columns(2)
        try:
            v_df = load_data("members", ["姓名"]) 
            v_list = v_df['姓名'].tolist() if not v_df.empty else ["預設志工"]
        except: v_list = ["預設志工"]
        visit_who = c1.selectbox("執行志工", v_list)
        visit_date = c2.date_input("日期", value=date.today())
        
        st.write("📦 **點擊下方卡片輸入數量 (0 代表不發)**")
        quantities = {}
        if not stock_map:
            st.info("💡 目前無任何庫存物資，僅能進行純訪視記錄。")
        else:
            valid_items = sorted(stock_map.items())
            for i in range(0, len(valid_items), 3):
                cols = st.columns(3)
                for j in range(3):
                    if i + j < len(valid_items):
                        c_name, c_stock = valid_items[i+j]
                        with cols[j]:
                            with st.container(border=True):
                                st.markdown(f'<div class="inv-card-header">{c_name}</div>', unsafe_allow_html=True)
                                stock_class = "low" if c_stock < 5 else "normal"
                                stock_label = f"⚠️ 庫存告急: {c_stock}" if c_stock < 5 else f"庫存: {c_stock}"
                                st.markdown(f'<div class="inv-card-stock {stock_class}">{stock_label}</div>', unsafe_allow_html=True)
                                qty = st.number_input("發放數量", min_value=0, max_value=c_stock, step=1, key=f"q_{c_name}")
                                quantities[c_name] = qty

        note = st.text_area("訪視紀錄 / 備註")
        submitted = st.form_submit_button("✅ 確認提交紀錄")
        
        if submitted:
            if not target_p: st.error("❌ 請先選擇關懷戶！")
            else:
                items_to_give = [(k, v) for k, v in quantities.items() if v > 0]
                new_logs = []
                if items_to_give:
                    for item_name, amount in items_to_give:
                        new_logs.append({
                            "志工": visit_who, "發放日期": str(visit_date), "關懷戶姓名": target_p,
                            "物資內容": item_name, "發放數量": amount, "訪視紀錄": note
                        })
                else:
                    new_logs.append({
                        "志工": visit_who, "發放日期": str(visit_date), "關懷戶姓名": target_p,
                        "物資內容": "(僅訪視)", "發放數量": 0, "訪視紀錄": note
                    })
                if save_data(pd.concat([logs, pd.DataFrame(new_logs)], ignore_index=True), "care_logs"):
                    st.success(f"✅ 已成功紀錄！"); time.sleep(1); st.rerun()

    if not logs.empty:
        st.markdown("#### 📝 最近 20 筆訪視紀錄")
        ed_l = st.data_editor(logs.sort_values('發放日期', ascending=False).head(20), use_container_width=True, num_rows="dynamic", key="v_ed")
        if st.button("💾 儲存歷史紀錄修改"): save_data(ed_l, "care_logs")

# --- [分頁 5：統計 (加入健康警示)] ---
elif st.session_state.page == 'stats':
    render_nav()
    st.markdown("## 📊 數據統計與個案查詢")
    logs, mems = load_data("care_logs", COLS_LOG), load_data("care_members", COLS_MEM)
    h_df = load_data("care_health", COLS_HEALTH)

    tab1, tab2 = st.tabs(["👤 個案詳細檔案", "📈 整體物資統計"])
    
    with tab1:
        if mems.empty: st.info("目前尚無關懷戶名冊資料")
        else:
            all_names = mems['姓名'].unique().tolist()
            target_name = st.selectbox("🔍 請選擇或輸入關懷戶姓名", all_names)
            if target_name:
                p_data = mems[mems['姓名'] == target_name].iloc[0]
                age = calculate_age(p_data['生日'])
                try:
                    c = int(p_data['18歲以下子女']) if p_data['18歲以下子女'] else 0
                    a = int(p_data['成人數量']) if p_data['成人數量'] else 0
                    s = int(p_data['65歲以上長者']) if p_data['65歲以上長者'] else 0
                    total_fam = c + a + s
                except: total_fam = 0

                # 基本資料卡片
                st.markdown(f"""
<div style="background-color: white; padding: 20px; border-radius: 15px; border-left: 5px solid {GREEN}; box-shadow: 0 4px 10px rgba(0,0,0,0.1); margin-bottom: 10px;">
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
<div style="font-size: 1.8rem; font-weight: 900; color: #333;">{p_data['姓名']} <span style="font-size: 1rem; color: #666; background: #eee; padding: 2px 8px; border-radius: 10px;">{p_data['性別']} / {age} 歲</span></div>
<div style="font-weight: bold; color: {PRIMARY}; border: 2px solid {PRIMARY}; padding: 5px 15px; border-radius: 20px;">{p_data['身分別']}</div>
</div>
<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 10px;">
<div><b>📞 電話：</b> {p_data['電話']}</div>
<div><b>📍 地址：</b> {p_data['地址']}</div>
</div>
<div style="color: #555;"><b>🏠 家庭結構：</b> 總人數 <b>{total_fam}</b> 人</div>
</div>
""", unsafe_allow_html=True)
                
                # --- 新增：健康狀態與風險警示 ---
                if not h_df.empty:
                    # 抓取該個案最近的一筆評估
                    p_health = h_df[h_df['姓名'] == target_name]
                    if not p_health.empty:
                        last_h = p_health.sort_values("評估日期").iloc[-1]
                        
                        st.markdown("### 🩺 健康與風險評估摘要")
                        st.caption(f"最近評估日期：{last_h['評估日期']}")
                        
                        warn_html = ""
                        
                        # 檢查營養
                        ns = last_h['營養狀態']
                        if "營養不良" in ns: # 包含 '有營養不良風險' 或 '營養不良'
                            color = "alert-orange" if "風險" in ns else "alert-red"
                            warn_html += f"<div class='health-alert {color}'>🍱 營養狀態：{ns} (分數: {last_h['營養篩檢分數']})</div>"
                        else:
                            warn_html += f"<div class='health-alert alert-green'>🍱 營養狀態：{ns}</div>"
                        
                        # 檢查情緒與自殺意念
                        ms = last_h['情緒狀態']
                        sr = last_h['有自殺意念']
                        
                        if sr == "是":
                            warn_html += f"<div class='health-alert alert-red'>🚨 嚴重警示：檢測到自殺意念！</div>"
                        
                        if "中度" in ms or "重度" in ms:
                             warn_html += f"<div class='health-alert alert-red'>🌡️ 情緒狀態：{ms} (分數: {last_h['心情溫度計分數']})</div>"
                        elif "輕度" in ms:
                             warn_html += f"<div class='health-alert alert-orange'>🌡️ 情緒狀態：{ms} (分數: {last_h['心情溫度計分數']})</div>"
                        else:
                             warn_html += f"<div class='health-alert alert-green'>🌡️ 情緒狀態：{ms}</div>"
                             
                        st.markdown(warn_html, unsafe_allow_html=True)
                    else:
                        st.info("尚無健康評估資料")

                # 機敏資料
                if not st.session_state.unlock_details:
                    st.info("🔒 詳細個資已隱藏。")
                    c_pwd, c_btn = st.columns([2, 1])
                    with c_pwd: pwd_stat = st.text_input("請輸入密碼解鎖個資", type="password", key="unlock_stat_pwd")
                    with c_btn:
                        if st.button("🔓 解鎖查看"):
                            if pwd_stat == st.secrets["admin_password"]:
                                st.session_state.unlock_details = True; st.rerun()
                            else: st.error("❌ 密碼錯誤")
                else:
                    if st.button("🔒 隱藏機敏資料"): st.session_state.unlock_details = False; st.rerun()
                    st.markdown(f"""
<div style="background-color: #FFF8E1; padding: 20px; border-radius: 15px; border: 1px dashed #FFB74D; margin-bottom: 20px;">
<div style="font-weight:bold; color:#F57C00; margin-bottom:10px;">⚠️ 機敏個資區域 (已解鎖)</div>
<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 15px;">
<div><b>🆔 身分證：</b> {p_data['身分證字號']}</div>
<div><b>🎂 生日：</b> {p_data['生日']}</div>
</div>
<hr style="border-top: 1px dashed #ccc;">
<div style="margin-top: 10px; color: #555;">
<b>🏠 家庭結構明細：</b> 18歲以下 <b>{p_data['18歲以下子女']}</b> 人，成人 <b>{p_data['成人數量']}</b> 人，65歲以上 <b>{p_data['65歲以上長者']}</b> 人
</div>
<div style="margin-top: 10px; color: #D32F2F;">
<b>🚨 緊急聯絡人：</b> {p_data['緊急聯絡人']} ({p_data['緊急聯絡人電話']})
</div>
</div>
""", unsafe_allow_html=True)
                
                st.markdown("### 🤝 歷史訪視紀錄")
                p_logs = logs[logs['關懷戶姓名'] == target_name]
                if p_logs.empty: st.info("尚無訪視紀錄。")
                else:
                    p_logs = p_logs.sort_values("發放日期", ascending=False)
                    for idx, row in p_logs.iterrows():
                        tag_class = "only" if row['物資內容'] == "(僅訪視)" else ""
                        item_display = row['物資內容'] if row['物資內容'] == "(僅訪視)" else f"{row['物資內容']} x {row['發放數量']}"
                        st.markdown(f"""
<div class="visit-card">
<div class="visit-header">
<span class="visit-date">📅 {row['發放日期']}</span>
<span class="visit-volunteer">👮 志工：{row['志工']}</span>
</div>
<div style="margin-bottom:8px;">
<span class="visit-tag {tag_class}">{item_display}</span>
</div>
<div class="visit-note">{row['訪視紀錄']}</div>
</div>
""", unsafe_allow_html=True)

    with tab2:
        inv = load_data("care_inventory", COLS_INV)
        if not inv.empty:
            inv['qty'] = pd.to_numeric(inv['總數量'], errors='coerce').fillna(0)
            st.markdown("### 🎁 捐贈來源與物資分析")
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("#### 🏆 愛心捐贈芳名錄")
                donor_stat = inv.groupby('捐贈者')['qty'].sum().reset_index().sort_values('qty', ascending=False)
                fig_donor = px.pie(donor_stat, values='qty', names='捐贈者', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
                st.plotly_chart(fig_donor, use_container_width=True)
            with c2:
                st.markdown("#### 📦 物資種類結構")
                fig_sun = px.sunburst(inv, path=['物資類型', '物資內容'], values='qty', color='物資類型', color_discrete_sequence=px.colors.qualitative.Set3)
                st.plotly_chart(fig_sun, use_container_width=True)
            st.markdown("#### 📝 歷年捐贈明細總表")
            st.dataframe(inv, use_container_width=True)
        else: st.info("目前尚無捐贈紀錄")
