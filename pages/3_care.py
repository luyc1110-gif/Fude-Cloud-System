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
st.set_page_config(page_title="關懷戶管理系統", page_icon="🏠", layout="wide", initial_sidebar_state="collapsed")

if 'page' not in st.session_state:
    st.session_state.page = 'home'

TW_TZ = timezone(timedelta(hours=8))
PRIMARY = "#4A4E69"   # 深藍灰
GREEN   = "#8E9775"   # 苔蘚綠
BG_MAIN = "#F8F9FA"   

# =========================================================
# 1) CSS 樣式 (極致識別度)
# =========================================================
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@500;700;900&display=swap');
html, body, [class*="css"], div, p, span, li, ul {{ font-family: "Noto Sans TC", sans-serif; color: #333 !important; }}
.stApp {{ background-color: {BG_MAIN}; }}
[data-testid="stHeader"], [data-testid="stSidebar"], footer {{ display: none; }}
.block-container {{ padding-top: 1rem !important; max-width: 1250px; }}

/* 表格白底黑字 */
div[data-testid="stDataFrame"] {{ background-color: #FFFFFF !important; border-radius: 10px; padding: 10px; }}
.stDataFrame div, .stDataFrame span {{ color: #000000 !important; }}

/* 下拉選單與輸入框 */
div[data-baseweb="select"] > div, .stTextInput input, .stDateInput input, .stTimeInput input, .stNumberInput input {{
    background-color: #FFFFFF !important; color: #000000 !important;
    border: 2px solid #D1D1D1 !important; border-radius: 12px !important; font-weight: 700 !important;
}}
div[role="listbox"], ul[data-baseweb="menu"], li[role="option"] {{
    background-color: #FFFFFF !important; color: #000000 !important; font-weight: 700 !important;
}}

/* 確認按鈕辨識度：深色背景 + 白字 */
div[data-testid="stFormSubmitButton"] > button {{
    background-color: {PRIMARY} !important; color: #FFFFFF !important;
    border: none !important; border-radius: 12px !important; font-weight: 900 !important;
    padding: 10px 25px !important; box-shadow: 0 4px 10px rgba(0,0,0,0.15) !important;
}}

/* 大看板樣式 */
.care-metric-box {{
    padding: 20px; border-radius: 20px; color: #FFFFFF !important; text-align: center; margin-bottom: 15px;
    box-shadow: 0 8px 20px rgba(0,0,0,0.1); min-height: 140px;
    display: flex; flex-direction: column; justify-content: center;
}}
.care-metric-box div, .care-metric-box span {{ color: #FFFFFF !important; font-weight: 900 !important; }}

div[data-testid="stButton"] > button {{
    width: 100%; background-color: white !important; color: {GREEN} !important;
    border: 2px solid {GREEN} !important; border-radius: 15px !important;
    font-weight: 900 !important; transition: all 0.2s;
}}
div[data-testid="stButton"] > button:hover {{ background-color: {GREEN} !important; color: white !important; }}
</style>
""", unsafe_allow_html=True)

# =========================================================
# 2) 資料邏輯 (精準同步)
# =========================================================
SHEET_ID = "1A3-VwCBYjnWdcEiL6VwbV5-UECcgX7TqKH94sKe8P90"
COLS_MEM = ["姓名", "身分證字號", "性別", "生日", "地址", "電話", "緊急聯絡人", "緊急聯絡人電話", "身分別", "18歲以下子女", "成人數量", "65歲以上長者"]
COLS_HEALTH = ["姓名", "身分證字號", "是否有假牙", "今年洗牙", "握力", "身高", "體重", "聽力測試"]
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

def render_nav():
    st.markdown('<div style="background:white; padding:12px; border-radius:20px; margin-bottom:20px; box-shadow: 0 2px 15px rgba(0,0,0,0.05);">', unsafe_allow_html=True)
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    pages = [("🏠 首頁", 'home'), ("📋 名冊", 'members'), ("🏥 健康", 'health'), ("📦 物資", 'inventory'), ("🤝 訪視", 'visit'), ("📊 統計", 'stats')]
    for i, (label, p_key) in enumerate(pages):
        with [c1, c2, c3, c4, c5, c6][i]:
            if st.button(label, use_container_width=True, key=f"nav_{p_key}"): 
                st.session_state.page = p_key; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- [分頁 0：首頁大看板] ---
if st.session_state.page == 'home':
    if st.button("🚪 回系統大廳"): st.switch_page("Home.py")
    st.markdown("<h1 style='text-align: center;'>福德里 - 關懷戶管理系統</h1>", unsafe_allow_html=True)
    render_nav()
    mems, logs = load_data("care_members", COLS_MEM), load_data("care_logs", COLS_LOG)
    
    if not mems.empty:
        cur_y = datetime.now(TW_TZ).year
        prev_y = cur_y - 1
        mems['age'] = mems['生日'].apply(calculate_age)
        
        # 數據計算
        dist_df = logs.copy()
        dist_df['dt'] = pd.to_datetime(dist_df['發放日期'], errors='coerce')
        cur_val = dist_df[dist_df['dt'].dt.year == cur_y]['發放數量'].replace("","0").astype(float).sum() if not logs.empty else 0
        prev_val = dist_df[dist_df['dt'].dt.year == prev_y]['發放數量'].replace("","0").astype(float).sum() if not logs.empty else 0
        dis_c = len(mems[mems['身分別'].str.contains("身障", na=False)])
        low_c = len(mems[mems['身分別'].str.contains("低收|中低收", na=False)])

        # 第一排卡片
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f'<div class="care-metric-box" style="background:linear-gradient(135deg,#8E9775 0%,#6D6875 100%);"><div>🏠 關懷戶總人數</div><div style="font-size:2.8rem;">{len(mems)} <span style="font-size:1.2rem;">人</span></div><div>平均 {round(mems["age"].mean(),1)} 歲</div></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="care-metric-box" style="background:linear-gradient(135deg,#A4AC86 0%,#8E9775 100%);"><div>♿ 身障關懷人數</div><div style="font-size:2.8rem;">{dis_c} <span style="font-size:1.2rem;">人</span></div></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="care-metric-box" style="background:linear-gradient(135deg,#6D6875 0%,#4A4E69 100%);"><div>📉 低收/中低收</div><div style="font-size:2.8rem;">{low_c} <span style="font-size:1.2rem;">人</span></div></div>', unsafe_allow_html=True)
        
        # 第二排卡片 (年度對比)
        st.markdown("---")
        c4, c5 = st.columns(2)
        with c4: st.markdown(f'<div class="care-metric-box" style="background:linear-gradient(135deg,#BC6C25 0%,#8E9775 100%);"><div>🎁 {cur_y} 當年度發放量</div><div style="font-size:3.5rem;">{int(cur_val)} <span style="font-size:1.5rem;">份</span></div></div>', unsafe_allow_html=True)
        with c5: st.markdown(f'<div class="care-metric-box" style="background:linear-gradient(135deg,#A4AC86 0%,#6D6875 100%);"><div>⏳ {prev_y} 上年度發放量</div><div style="font-size:3.5rem;">{int(prev_val)} <span style="font-size:1.5rem;">份</span></div></div>', unsafe_allow_html=True)

# --- [分頁 1：名冊管理] ---
elif st.session_state.page == 'members':
    render_nav()
    st.markdown("## 📋 關懷戶名冊管理")
    df = load_data("care_members", COLS_MEM)
    with st.expander("➕ 新增關懷戶"):
        with st.form("add_care"):
            c1, c2, c3, c4 = st.columns(4)
            n, p, g, b = c1.text_input("姓名"), c2.text_input("身分證"), c3.selectbox("性別", ["男", "女"]), c4.date_input("生日", value=date(1950, 1, 1))
            addr, ph = st.text_input("地址"), st.text_input("電話")
            ce1, ce2 = st.columns(2)
            en, ep = ce1.text_input("緊急聯絡人"), ce2.text_input("緊急聯絡電話")
            id_t = st.multiselect("身分別 (可多選)", ["低收", "中低收", "中低老人", "身障", "獨居", "獨居有子女"])
            if st.form_submit_button("確認新增關懷戶"):
                if p.upper() in df['身分證字號'].values: st.error("❌ 身分證重複！")
                elif not n: st.error("❌ 姓名為必填")
                else:
                    new = {"姓名":n, "身分證字號":p.upper(), "性別":g, "生日":str(b), "地址":addr, "電話":ph, "緊急聯絡人":en, "緊急聯絡人電話":ep, "身分別":",".join(id_t)}
                    if save_data(pd.concat([df, pd.DataFrame([new])], ignore_index=True), "care_members"): st.success("已新增"); st.rerun()
    if not df.empty:
        df['歲數'] = df['生日'].apply(calculate_age)
        ed = st.data_editor(df, use_container_width=True, num_rows="dynamic", key="mem_ed")
        if st.button("💾 儲存修改內容"):
            if save_data(ed, "care_members"): st.success("名冊已更新")

# --- [分頁 2：健康指標] ---
elif st.session_state.page == 'health':
    render_nav()
    st.markdown("## 🏥 關懷戶健康指標管理")
    h_df, m_df = load_data("care_health", COLS_HEALTH), load_data("care_members", COLS_MEM)
    with st.expander("➕ 登記健康指標數據"):
        with st.form("h_form"):
            sel_n = st.selectbox("選擇關懷戶", m_df['姓名'].tolist() if not m_df.empty else ["無名冊"])
            c1, c2, c3, c4, c5, c6 = st.columns(6)
            dent, wash = c1.selectbox("假牙",["無","有"]), c2.selectbox("洗牙",["否","是"])
            grip, h, w, hear = c3.text_input("握力"), c4.text_input("身高"), c5.text_input("體重"), c6.selectbox("聽力",["正常","需注意"])
            if st.form_submit_button("儲存健康紀錄"):
                pid = m_df[m_df['姓名']==sel_n]['身分證字號'].iloc[0]
                new = {"姓名":sel_n, "身分證字號":pid, "是否有假牙":dent, "今年洗牙":wash, "握力":grip, "身高":h, "體重":w, "聽力測試":hear}
                if save_data(pd.concat([h_df, pd.DataFrame([new])], ignore_index=True), "care_health"): st.success("存檔成功"); st.rerun()
    if not h_df.empty:
        ed_h = st.data_editor(h_df, use_container_width=True, num_rows="dynamic", key="h_ed")
        if st.button("💾 儲存修改"): save_data(ed_h, "care_health")

# --- [分頁 3：物資管理] ---
elif st.session_state.page == 'inventory':
    render_nav()
    st.markdown("## 📦 物資庫存管理")
    inv, logs = load_data("care_inventory", COLS_INV), load_data("care_logs", COLS_LOG)
    with st.form("add_inv"):
        c1, c2, co, qt = st.columns(4)
        do, ty, co, qt = c1.text_input("捐贈者"), c2.selectbox("類型",["食物","日用品","輔具"]), co.text_input("名稱"), qt.number_input("數量", min_value=1)
        if st.form_submit_button("錄入捐贈"):
            new = {"捐贈者":do, "物資類型":ty, "物資內容":co, "總數量":qt, "捐贈日期":str(date.today())}
            save_data(pd.concat([inv, pd.DataFrame([new])], ignore_index=True), "care_inventory"); st.rerun()
    if not inv.empty:
        # 庫存計算與顯示
        sm = []
        for itm, gp in inv.groupby('物資內容'):
            tin = gp['總數量'].replace("","0").astype(float).sum()
            tout = logs[logs['物資內容'] == itm]['發放數量'].replace("","0").astype(float).sum() if not logs.empty else 0
            sm.append({"物資名稱":itm, "類型":gp.iloc[0]['物資類型'], "入庫":tin, "已發放":tout, "剩餘":tin-tout})
        st.dataframe(pd.DataFrame(sm), use_container_width=True)
        ed_i = st.data_editor(inv, use_container_width=True, num_rows="dynamic", key="inv_ed")
        if st.button("💾 儲存修改"): save_data(ed_i, "care_inventory")

# --- [分頁 4：訪視發放 (全功能回歸)] ---
elif st.session_state.page == 'visit':
    render_nav()
    st.markdown("## 🤝 訪視與物資發放紀錄")
    mems, inv, logs = load_data("care_members", COLS_MEM), load_data("care_inventory", COLS_INV), load_data("care_logs", COLS_LOG)
    
    # 庫存計算
    stock_map = {}
    if not inv.empty:
        for itm, gp in inv.groupby('物資內容'):
            tin = gp['總數量'].replace("","0").astype(float).sum()
            tout = logs[logs['物資內容'] == itm]['發放數量'].replace("","0").astype(float).sum() if not logs.empty else 0
            stock_map[itm] = int(tin - tout)
    itm_list = ["(僅訪視)"] + [f"{k} (剩餘: {v})" for k, v in stock_map.items()]

    with st.form("v_form"):
        c1, c2, c3 = st.columns(3)
        vol_list = load_data("members", ["姓名"])['姓名'].tolist() if not load_data("members", ["姓名"]).empty else ["無資料"]
        v, d, p = st.selectbox("志工", vol_list), st.date_input("日期"), st.selectbox("關懷戶", mems['姓名'].tolist())
        sel_i_dis = st.selectbox("選擇物資 (含庫存)", itm_list)
        sel_q = st.number_input("數量", min_value=0, value=1)
        
        # 🔥 優先建議邏輯
        real_i = sel_i_dis.split(" (剩餘:")[0]
        if real_i != "(僅訪視)":
            hist = logs[logs['物資內容'] == real_i]['關懷戶姓名'].value_counts()
            sug = mems[~mems['姓名'].isin(hist.index)]['姓名'].head(5).tolist()
            if sug: st.info(f"💡 **發放優先建議**：尚未領取過「{real_i}」的人：{', '.join(sug)}")
        
        nt = st.text_area("紀錄")
        if st.form_submit_button("確認提交"):
            if real_i != "(僅訪視)" and sel_q > stock_map.get(real_i, 0): st.error("❌ 庫存不足")
            else:
                new = {"志工":v, "發放日期":str(d), "關懷戶姓名":p, "物資內容":real_i, "發放數量":sel_q, "訪視紀錄":nt}
                if save_data(pd.concat([logs, pd.DataFrame([new])], ignore_index=True), "care_logs"): st.success("成功"); time.sleep(1); st.rerun()

    if not logs.empty:
        ed_l = st.data_editor(logs.sort_values('發放日期', ascending=False), use_container_width=True, num_rows="dynamic", key="v_ed")
        if st.button("💾 儲存修改"): save_data(ed_l, "care_logs")

elif st.session_state.page == 'stats':
    render_nav()
    st.info("數據統計連動中...")
