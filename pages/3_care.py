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

/* 庫存與警示標籤 */
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

/* 評估結果標籤 */
.alert-box {{ padding: 10px; border-radius: 8px; margin-bottom: 10px; font-weight: bold; }}
.alert-normal {{ background-color: #E8F5E9; color: #2E7D32; border: 1px solid #A5D6A7; }}
.alert-risk {{ background-color: #FFF3E0; color: #EF6C00; border: 1px solid #FFCC80; }}
.alert-danger {{ background-color: #FFEBEE; color: #C62828; border: 1px solid #EF9A9A; }}

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
</style>
""", unsafe_allow_html=True)

# =========================================================
# 2) 資料邏輯
# =========================================================
SHEET_ID = "1A3-VwCBYjnWdcEiL6VwbV5-UECcgX7TqKH94sKe8P90"
COLS_MEM = ["姓名", "身分證字號", "性別", "生日", "地址", "電話", "緊急聯絡人", "緊急聯絡人電話", "身分別", "18歲以下子女", "成人數量", "65歲以上長者"]
COLS_HEALTH = ["姓名", "身分證字號", "是否有假牙", "今年洗牙", "握力", "身高", "體重", "聽力測試", "營養評估總分", "心情溫度計總分", "自殺意念註記"]
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
                if is_duplicate: st.error(f"❌ 資料重複！")
                elif not n or not p: st.error("❌ 姓名與身分證必填")
                else:
                    new = {
                        "姓名": n, "身分證字號": p.upper(), "性別": g, "生日": str(b), 
                        "地址": addr, "電話": ph, "緊急聯絡人": en, "緊急聯絡人電話": ep, 
                        "身分別": ",".join(id_t), "18歲以下子女": str(child), "成人數量": str(adult), "65歲以上長者": str(senior)
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
                if pwd_m == st.secrets["admin_password"]: st.session_state.unlock_members = True; st.rerun()
                else: st.error("❌ 密碼錯誤")

# --- [分頁 2：健康 (含 MNA 與 BSRS-5)] ---
elif st.session_state.page == 'health':
    render_nav()
    st.markdown("## 🏥 關懷戶健康指標管理")
    h_df, m_df = load_data("care_health", COLS_HEALTH), load_data("care_members", COLS_MEM)
    
    with st.expander("➕ 登記健康 / 營養 / 心情評估 (展開)", expanded=True):
        with st.form("h_form"):
            st.markdown("#### 1. 選擇對象與基礎測量")
            sel_n = st.selectbox("選擇關懷戶", m_df['姓名'].tolist() if not m_df.empty else ["無名冊"])
            c1, c2, c3, c4, c5, c6 = st.columns(6)
            dent = c1.selectbox("假牙",["無","有"])
            wash = c2.selectbox("洗牙",["否","是"])
            grip = c3.text_input("握力")
            h = c4.text_input("身高 (cm)")
            w = c5.text_input("體重 (kg)")
            hear = c6.selectbox("聽力",["正常","需注意"])

            st.markdown("---")
            st.markdown("#### 2. 營養評估 (MNA簡易版)")
            
            # MNA 題目邏輯
            score_n = 0
            
            # Q1
            st.markdown("**1. 過去三個月食量是否減少？**")
            q1 = st.radio("食量變化", ["食量嚴重減少 (0分)", "食量中度減少 (1分)", "食量沒有改變 (2分)"], horizontal=True, key="mna_1")
            score_n += int(q1.split("(")[1][0])

            # Q2
            st.markdown("**2. 過去三個月體重下降情況？**")
            q2 = st.radio("體重變化", ["下降 > 3kg (0分)", "不知道 (1分)", "下降 1-3kg (2分)", "沒有下降 (3分)"], horizontal=True, key="mna_2")
            score_n += int(q2.split("(")[1][0])
            
            # Q3
            st.markdown("**3. 活動能力？**")
            q3 = st.radio("活動能力", ["臥床/輪椅 (0分)", "可下床但不能外出 (1分)", "可以外出 (2分)"], horizontal=True, key="mna_3")
            score_n += int(q3.split("(")[1][0])
            
            # Q4
            st.markdown("**4. 過去三個月有無心理創傷或急性疾病？**")
            q4 = st.radio("創傷疾病", ["有 (0分)", "沒有 (2分)"], horizontal=True, key="mna_4")
            score_n += int(q4.split("(")[1][0])
            
            # Q5
            st.markdown("**5. 精神心理問題？**")
            q5 = st.radio("精神狀況", ["嚴重失智或憂鬱 (0分)", "輕度失智 (1分)", "沒有問題 (2分)"], horizontal=True, key="mna_5")
            score_n += int(q5.split("(")[1][0])

            # Q6 (自動判定 BMI)
            st.markdown("**6. BMI 判定 (系統自動計算)**")
            st.caption("依據上方填寫之身高體重自動換算得分：BMI<19 (0分), 19-21 (1分), 21-23 (2分), >23 (3分)")

            st.markdown("---")
            st.markdown("#### 3. 心情溫度計 (BSRS-5)")
            st.caption("分數說明：0=完全沒有，1=輕微，2=中等，3=厲害，4=非常厲害，5=非常嚴重")
            
            score_m = 0
            # 題目清單
            bsrs_q = ["1. 睡眠困難（難以入睡、易醒早醒）", "2. 感覺緊張不安", "3. 覺得容易動怒", "4. 感覺憂鬱、心情低落", "5. 覺得比不上別人"]
            
            cols_m = st.columns(5)
            for idx, q_text in enumerate(bsrs_q):
                with cols_m[idx]:
                    val = st.selectbox(q_text.split(" ")[1], [0,1,2,3,4,5], key=f"bsrs_{idx}")
                    score_m += val
            
            # 第六題自殺意念 (獨立判斷)
            st.markdown("**6. 有自殺想法**")
            suicide_score = st.slider("自殺想法強度 (0-5)", 0, 5, 0, key="bsrs_suicide")
            score_m += suicide_score
            has_suicide_idea = "是" if suicide_score > 0 else "否"

            if st.form_submit_button("儲存健康與評估紀錄"):
                # --- 自動計算 BMI 分數 ---
                bmi_score = 0
                try:
                    # 確保轉為 float 並檢查是否 > 0
                    h_val = float(h)
                    w_val = float(w)
                    if h_val > 0 and w_val > 0:
                        bmi = w_val / ((h_val / 100.0) ** 2)
                        
                        if bmi < 19: bmi_score = 0
                        elif bmi < 21: bmi_score = 1
                        elif bmi < 23: bmi_score = 2
                        else: bmi_score = 3
                    else:
                        bmi_score = 0 # 數值異常則 0 分
                except:
                    bmi_score = 0 # 轉換錯誤則 0 分
                
                # 加總 MNA 分數
                final_mna_score = score_n + bmi_score

                pid = m_df[m_df['姓名']==sel_n]['身分證字號'].iloc[0]
                new = {
                    "姓名": sel_n, "身分證字號": pid, 
                    "是否有假牙": dent, "今年洗牙": wash, "握力": grip, "身高": h, "體重": w, "聽力測試": hear,
                    "營養評估總分": str(final_mna_score), 
                    "心情溫度計總分": str(score_m), 
                    "自殺意念註記": has_suicide_idea
                }
                if save_data(pd.concat([h_df, pd.DataFrame([new])], ignore_index=True), "care_health"): 
                    st.success(f"✅ 已存檔！營養評估得分：{final_mna_score} (含BMI {bmi_score}分)"); time.sleep(1); st.rerun()

    if not h_df.empty:
        st.markdown("### 📋 歷史健康紀錄")
        ed_h = st.data_editor(h_df, use_container_width=True, num_rows="dynamic", key="h_ed")
        if st.button("💾 儲存修改內容"): save_data(ed_h, "care_health")

# --- [分頁 3：物資庫存] ---
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
                if not final_donor or not final_item_name: st.error("❌ 欄位未填寫完整")
                else:
                    new = {"捐贈者": final_donor, "物資類型": sel_type, "物資內容": final_item_name, "總數量": qt, "捐贈日期": str(date.today())}
                    if save_data(pd.concat([inv, pd.DataFrame([new])], ignore_index=True), "care_inventory"): 
                        st.success("已錄入"); time.sleep(1); st.rerun()

    if not inv.empty:
        st.markdown("### 📊 庫存概況")
        inv_summary = []
        for (item_name, donor_name), group in inv.groupby(['物資內容', '捐贈者']):
            total_in = group['總數量'].replace("","0").astype(float).sum()
            composite_name = f"{item_name} ({donor_name})"
            total_out = logs[logs['物資內容'] == composite_name]['發放數量'].replace("","0").astype(float).sum() if not logs.empty else 0
            remain = total_in - total_out
            if remain > 0:
                m_type = group.iloc[0]['物資類型']
                icon_map = {"食物": "🍱", "日用品": "🧻", "輔具": "🦯", "現金": "💰", "服務": "🧹"}
                pct = int((remain / total_in * 100)) if total_in > 0 else 0
                if pct < 0: pct = 0
                bar_color = "#8E9775"
                if remain <= 5: bar_color = "#D32F2F"
                elif pct < 30: bar_color = "#FBC02D"
                inv_summary.append({
                    "name": item_name, "donor": donor_name, "type": m_type, "icon": icon_map.get(m_type,"📦"),
                    "in": int(total_in), "out": int(total_out), "remain": int(remain),
                    "pct": pct, "bar_color": bar_color
                })
        
        if not inv_summary: st.info("💡 無庫存")
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
<div class="stock-top"><div class="stock-icon">{item['icon']}</div><div class="stock-info"><div class="stock-name">{item['name']}</div><div class="stock-donor">{item['donor']}</div></div></div>
<div class="stock-stats"><span>總入庫: {item['in']}</span><span>已發放: {item['out']}</span></div>
<div class="stock-bar-bg"><div class="stock-bar-fill" style="width: {item['pct']}%; background-color: {item['bar_color']};"></div></div>
<div style="text-align:right; margin-top:5px; font-size:0.85rem; color:#888;">剩餘: <span style="font-size:1.2rem; color:{item['bar_color']}; font-weight:900;">{item['remain']}</span></div>
{warning_html}
</div>
""", unsafe_allow_html=True)

        with st.expander("🛠️ 進階管理：編輯原始庫存資料"):
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
            if (total_in - total_out) > 0: stock_map[composite_name] = int(total_in - total_out)
    
    c_filter, c_person = st.columns([1, 2])
    with c_filter:
        tag_opts = ["(全部顯示)"] + sorted(list(set([t.strip() for s in mems['身分別'].astype(str) for t in s.split(',') if t.strip()])))
        sel_tag = st.selectbox("🌪️ 依身分別篩選", tag_opts)
    with c_person:
        if sel_tag == "(全部顯示)": filtered_mems = mems
        else: filtered_mems = mems[mems['身分別'].str.contains(sel_tag, na=False)] if not mems.empty else mems
        target_p = st.selectbox("👤 選擇關懷戶", filtered_mems['姓名'].tolist() if not filtered_mems.empty else [])

    with st.form("visit_multi_form"):
        c1, c2 = st.columns(2)
        visit_who = c1.selectbox("執行志工", ["預設志工","志工A","志工B"]) 
        visit_date = c2.date_input("日期", value=date.today())
        
        st.write("📦 **點擊下方卡片輸入數量 (0 代表不發)**")
        quantities = {} 
        if not stock_map: st.info("💡 無庫存，僅記錄訪視")
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
                                st.markdown(f'<div class="inv-card-stock {stock_class}">庫存: {c_stock}</div>', unsafe_allow_html=True)
                                quantities[c_name] = st.number_input("數量", min_value=0, max_value=c_stock, step=1, key=f"q_{c_name}")

        note = st.text_area("訪視紀錄 / 備註")
        if st.form_submit_button("✅ 確認提交紀錄"):
            if not target_p: st.error("❌ 請選擇關懷戶")
            else:
                items_to_give = [(k, v) for k, v in quantities.items() if v > 0]
                new_logs = []
                if items_to_give:
                    for item_name, amount in items_to_give:
                        new_logs.append({"志工": visit_who, "發放日期": str(visit_date), "關懷戶姓名": target_p, "物資內容": item_name, "發放數量": amount, "訪視紀錄": note})
                else:
                    new_logs.append({"志工": visit_who, "發放日期": str(visit_date), "關懷戶姓名": target_p, "物資內容": "(僅訪視)", "發放數量": 0, "訪視紀錄": note})
                if save_data(pd.concat([logs, pd.DataFrame(new_logs)], ignore_index=True), "care_logs"):
                    st.success("已紀錄"); time.sleep(1); st.rerun()

    if not logs.empty:
        st.markdown("#### 📝 最近 20 筆紀錄")
        ed_l = st.data_editor(logs.sort_values('發放日期', ascending=False).head(20), use_container_width=True, num_rows="dynamic", key="v_ed")
        if st.button("💾 儲存紀錄修改"): save_data(ed_l, "care_logs")

# --- [分頁 5：統計與個案卡片 (新增評估判讀)] ---
elif st.session_state.page == 'stats':
    render_nav()
    st.markdown("## 📊 數據統計與個案查詢")
    logs, mems = load_data("care_logs", COLS_LOG), load_data("care_members", COLS_MEM)
    h_df = load_data("care_health", COLS_HEALTH)

    tab1, tab2 = st.tabs(["👤 個案詳細檔案", "📈 整體物資統計"])
    
    with tab1:
        if mems.empty: st.info("無名冊")
        else:
            all_names = mems['姓名'].unique().tolist()
            target_name = st.selectbox("🔍 搜尋關懷戶", all_names)
            if target_name:
                p_data = mems[mems['姓名'] == target_name].iloc[0]
                
                # 撈取最新的健康資料
                p_health = pd.DataFrame()
                if not h_df.empty:
                    p_health_recs = h_df[h_df['姓名'] == target_name]
                    if not p_health_recs.empty:
                        # 取最後一筆
                        p_health = p_health_recs.iloc[-1]
                
                age = calculate_age(p_data['生日'])
                
                # 1. 顯示基本卡片
                st.markdown(f"""
<div style="background-color: white; padding: 20px; border-radius: 15px; border-left: 5px solid {GREEN}; box-shadow: 0 4px 10px rgba(0,0,0,0.1); margin-bottom: 20px;">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
        <div style="font-size: 1.8rem; font-weight: 900; color: #333;">{p_data['姓名']} <span style="font-size: 1rem; color: #666; background: #eee; padding: 2px 8px; border-radius: 10px;">{p_data['性別']} / {age} 歲</span></div>
        <div style="font-weight: bold; color: {PRIMARY}; border: 2px solid {PRIMARY}; padding: 5px 15px; border-radius: 20px;">{p_data['身分別']}</div>
    </div>
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
        <div><b>📞 電話：</b> {p_data['電話']}</div>
        <div><b>📍 地址：</b> {p_data['地址']}</div>
    </div>
</div>
""", unsafe_allow_html=True)

                # 2. 顯示健康與評估警示 (如果有資料)
                if not p_health.empty:
                    # 判讀 MNA
                    try:
                        n_score = int(float(p_health.get('營養評估總分', 0)))
                    except: n_score = 0
                    
                    n_html = ""
                    if n_score >= 12: n_html = f"<div class='alert-box alert-normal'>🥗 營養狀況正常 ({n_score}分)</div>"
                    elif n_score >= 8: n_html = f"<div class='alert-box alert-risk'>⚠️ 有營養不良風險 ({n_score}分)</div>"
                    else: n_html = f"<div class='alert-box alert-danger'>🚨 營養不良 ({n_score}分)</div>"

                    # 判讀 Mood
                    try:
                        m_score = int(float(p_health.get('心情溫度計總分', 0)))
                    except: m_score = 0
                    suicide = p_health.get('自殺意念註記', '否')

                    m_html = ""
                    if suicide == '是':
                        m_html = f"<div class='alert-box alert-danger'>🚨 高自殺風險：個案有自殺意念！ (總分 {m_score})</div>"
                    elif m_score >= 15:
                        m_html = f"<div class='alert-box alert-danger'>🛑 重度情緒困擾 ({m_score}分)</div>"
                    elif m_score >= 10:
                        m_html = f"<div class='alert-box alert-risk'>⚠️ 中度情緒困擾 ({m_score}分)</div>"
                    elif m_score >= 6:
                        m_html = f"<div class='alert-box alert-risk'>⚠️ 輕度情緒困擾 ({m_score}分)</div>"
                    else:
                        m_html = f"<div class='alert-box alert-normal'>😊 情緒狀況正常 ({m_score}分)</div>"

                    st.markdown("### 🩺 最新評估結果")
                    c_h1, c_h2 = st.columns(2)
                    with c_h1: st.markdown(n_html, unsafe_allow_html=True)
                    with c_h2: st.markdown(m_html, unsafe_allow_html=True)
                
                # 3. 隱私資料
                if not st.session_state.unlock_details:
                    st.info("🔒 詳細個資(身分證、緊急聯絡) 已隱藏。")
                    if st.button("🔓 解鎖查看"): 
                        # 這裡簡化流程，實際可用密碼框
                        st.session_state.unlock_details = True; st.rerun()
                else:
                    st.markdown(f"""
<div style="background-color: #FFF8E1; padding: 20px; border-radius: 15px; border: 1px dashed #FFB74D; margin-bottom: 20px;">
    <div><b>🆔 身分證：</b> {p_data['身分證字號']}</div>
    <div><b>🚨 緊急聯絡：</b> {p_data['緊急聯絡人']} ({p_data['緊急聯絡人電話']})</div>
</div>
""", unsafe_allow_html=True)
                    if st.button("🔒 隱藏"): st.session_state.unlock_details = False; st.rerun()

                # 4. 歷史紀錄
                p_logs = logs[logs['關懷戶姓名'] == target_name].sort_values("發放日期", ascending=False)
                if not p_logs.empty:
                    st.markdown("### 🤝 歷史訪視")
                    for idx, row in p_logs.iterrows():
                         st.markdown(f"<div class='visit-card'><div class='visit-header'><span class='visit-date'>{row['發放日期']}</span></div><div class='visit-note'>{row['物資內容']} x {row['發放數量']} | {row['訪視紀錄']}</div></div>", unsafe_allow_html=True)

    with tab2:
        inv = load_data("care_inventory", COLS_INV)
        if not inv.empty:
            inv['qty'] = pd.to_numeric(inv['總數量'], errors='coerce').fillna(0)
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("#### 🏆 愛心捐贈")
                fig_donor = px.pie(inv.groupby('捐贈者')['qty'].sum().reset_index(), values='qty', names='捐贈者', hole=0.4)
                st.plotly_chart(fig_donor, use_container_width=True)
            with c2:
                st.markdown("#### 📦 物資結構")
                fig_sun = px.sunburst(inv, path=['物資類型', '物資內容'], values='qty', color='物資類型')
                st.plotly_chart(fig_sun, use_container_width=True)
