import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta, timezone
import gspread
import plotly.express as px
import random
import time

# =========================================================
# 0) 系統設定與初始化
# =========================================================
st.set_page_config(page_title="關懷戶管理系統", page_icon="🏠", layout="wide", initial_sidebar_state="collapsed")

if 'page' not in st.session_state:
    st.session_state.page = 'home'

TW_TZ = timezone(timedelta(hours=8))
PRIMARY = "#8E9775"   # 苔蘚綠
ACCENT  = "#6D6875"   # 灰紫色
BG_MAIN = "#F8F9FA"   

# =========================================================
# 1) CSS 樣式 (強化辨識度)
# =========================================================
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@500;700;900&display=swap');
html, body, [class*="css"], div, p, span, li, ul {{ font-family: "Noto Sans TC", sans-serif; color: #333 !important; }}
.stApp {{ background-color: {BG_MAIN}; }}
[data-testid="stHeader"], [data-testid="stSidebar"], footer {{ display: none; }}
.block-container {{ padding-top: 1rem !important; max-width: 1250px; }}

/* 表格白底黑字 */
div[data-testid="stDataFrame"], div[data-testid="stTable"] {{
    background-color: #FFFFFF !important; border-radius: 10px; padding: 10px;
}}
.stDataFrame div, .stDataFrame span, .stDataFrame p {{ color: #000000 !important; }}

/* 下拉選單與輸入框 */
div[data-baseweb="select"] > div, .stTextInput input, .stDateInput input, .stTimeInput input, .stNumberInput input {{
    background-color: #FFFFFF !important; color: #000000 !important;
    border: 2px solid #D1D1D1 !important; border-radius: 12px !important; font-weight: 700 !important;
}}
div[data-baseweb="select"] span {{ color: #000000 !important; }}

/* 🔥 解決「確認按鈕」辨識度問題：深綠底 + 白字 */
div[data-testid="stFormSubmitButton"] > button {{
    background-color: {PRIMARY} !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 900 !important;
    padding: 10px 20px !important;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important;
}}
div[data-testid="stFormSubmitButton"] > button:hover {{
    background-color: {ACCENT} !important;
}}

.care-metric-box {{
    padding: 30px; border-radius: 20px; color: #FFFFFF !important; text-align: center; margin-bottom: 15px;
    box-shadow: 0 8px 20px rgba(0,0,0,0.1);
}}
.care-metric-box div, .care-metric-box span {{ color: #FFFFFF !important; font-weight: 900 !important; }}

div[data-testid="stButton"] > button {{
    width: 100%; background-color: white !important; color: {PRIMARY} !important;
    border: 2px solid {PRIMARY} !important; border-radius: 15px !important;
    font-weight: 900 !important; font-size: 1.1rem !important; transition: all 0.2s;
}}
div[data-testid="stButton"] > button:hover {{ background-color: {PRIMARY} !important; color: white !important; }}
.dash-card {{ background-color: white; padding: 15px; border-radius: 15px; border-left: 6px solid {PRIMARY}; box-shadow: 0 4px 10px rgba(0,0,0,0.05); margin-bottom: 10px; }}
</style>
""", unsafe_allow_html=True)

# =========================================================
# 2) 資料邏輯
# =========================================================
SHEET_ID = "1A3-VwCBYjnWdcEiL6VwbV5-UECcgX7TqKH94sKe8P90"
COLS_MEM = ["姓名", "身分證字號", "性別", "生日", "地址", "電話", "緊急聯絡人", "緊急聯絡人電話", "身分別", "18歲以下子女", "成人數量", "65歲以上長者"]
COLS_HEALTH = ["姓名", "身分證字號", "是否有假牙", "今年洗牙", "握力", "身高", "體重", "聽力測試"]
COLS_INV = ["捐贈者", "物資類型", "物資內容", "總數量", "捐贈日期"]
COLS_LOG = ["志工", "發放日期", "關懷戶姓名", "物資內容", "發放數量", "訪視紀錄"]

@st.cache_resource
def get_client(): return gspread.service_account_from_dict(st.secrets["gcp_service_account"])

@st.cache_data(ttl=60)
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
# 3) 頁面渲染邏輯
# =========================================================
def render_nav():
    st.markdown('<div style="background:white; padding:12px; border-radius:20px; margin-bottom:20px; box-shadow: 0 2px 15px rgba(0,0,0,0.05);">', unsafe_allow_html=True)
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    pages = [("🏠 首頁", 'home'), ("📋 名冊", 'members'), ("🏥 健康", 'health'), ("📦 物資", 'inventory'), ("🤝 訪視", 'visit'), ("📊 統計", 'stats')]
    for i, (label, p_key) in enumerate(pages):
        with [c1, c2, c3, c4, c5, c6][i]:
            if st.button(label, use_container_width=True, key=f"nav_{p_key}"): 
                st.session_state.page = p_key; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- [分頁 0：首頁] ---
if st.session_state.page == 'home':
    if st.button("🚪 回大廳"): st.switch_page("Home.py")
    st.markdown("<h1 style='text-align: center;'>福德里 - 關懷戶管理系統</h1>", unsafe_allow_html=True)
    render_nav()
    mems, logs = load_data("care_members", COLS_MEM), load_data("care_logs", COLS_LOG)
    if not mems.empty:
        mems['age'] = mems['生日'].apply(calculate_age)
        dis_sub = mems[mems['身分別'].str.contains("身障", na=False)]
        c1, c2 = st.columns(2)
        with c1: st.markdown(f'<div class="care-metric-box" style="background:linear-gradient(135deg,#8E9775 0%,#6D6875 100%);"><div>🏠 關懷戶總人數 / 平均年齡</div><div style="font-size:3.5rem;">{len(mems)} 人 / {round(mems["age"].mean(),1)} 歲</div></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="care-metric-box" style="background:linear-gradient(135deg,#A4AC86 0%,#8E9775 100%);"><div>♿ 身障關懷人數 / 平均年齡</div><div style="font-size:3.5rem;">{len(dis_sub)} 人 / {round(dis_sub["age"].mean(),1) if not dis_sub.empty else 0} 歲</div></div>', unsafe_allow_html=True)

# --- [分頁 1：名冊] ---
elif st.session_state.page == 'members':
    render_nav()
    st.markdown("## 📋 關懷戶名冊管理")
    df = load_data("care_members", COLS_MEM)
    with st.expander("➕ 新增關懷戶資料"):
        with st.form("add_care"):
            c1, c2, c3, c4 = st.columns(4)
            n, p, g, b = c1.text_input("姓名"), c2.text_input("身分證"), c3.selectbox("性別", ["男", "女"]), c4.date_input("生日", value=date(1950, 1, 1))
            addr, ph = st.text_input("地址"), st.text_input("電話")
            # 🔥 補回緊急聯絡人欄位
            ce1, ce2 = st.columns(2)
            en = ce1.text_input("緊急聯絡人")
            ep = ce2.text_input("緊急聯絡人電話")
            id_t = st.multiselect("身分別", ["低收", "中低收", "中低老人", "身障", "獨居", "獨居有子女"])
            if st.form_submit_button("確認新增"):
                if p.upper() in df['身分證字號'].values: st.error("❌ 該身分證號已存在！")
                else:
                    new = {"姓名":n, "身分證字號":p.upper(), "性別":g, "生日":str(b), "地址":addr, "電話":ph, "緊急聯絡人":en, "緊急聯絡人電話":ep, "身分別":",".join(id_t)}
                    if save_data(pd.concat([df, pd.DataFrame([new])], ignore_index=True), "care_members"): st.success("成功"); st.rerun()
    if not df.empty:
        df['歲數'] = df['生日'].apply(calculate_age)
        edited_df = st.data_editor(df, use_container_width=True, num_rows="dynamic", key="mem_ed")
        if st.button("💾 儲存修改"): save_data(edited_df, "care_members")

# --- [分頁 2：健康數據] ---
elif st.session_state.page == 'health':
    render_nav()
    st.markdown("## 🏥 關懷戶健康指標")
    h_df = load_data("care_health", COLS_HEALTH)
    st.data_editor(h_df, use_container_width=True, num_rows="dynamic")

# --- [分頁 3：物資庫存] ---
elif st.session_state.page == 'inventory':
    render_nav()
    st.markdown("## 📦 物資庫存管理")
    inv, logs = load_data("care_inventory", COLS_INV), load_data("care_logs", COLS_LOG)
    with st.form("add_inv"):
        c1, c2, c3, c4 = st.columns(4)
        do, ty, co, qt = c1.text_input("捐贈者"), c2.selectbox("類型",["食物","日用品","輔具"]), c3.text_input("物資名稱"), c4.number_input("數量", min_value=1)
        if st.form_submit_button("確認入庫"):
            new = {"捐贈者":do, "物資類型":ty, "物資內容":co, "總數量":qt, "捐贈日期":str(date.today())}
            if save_data(pd.concat([inv, pd.DataFrame([new])], ignore_index=True), "care_inventory"): st.rerun()
    if not inv.empty:
        summary = []
        for item, group in inv.groupby('物資內容'):
            tin = group['總數量'].replace("", "0").astype(float).sum()
            tout = logs[logs['物資內容'] == item]['發放數量'].replace("", "0").astype(float).sum() if not logs.empty else 0
            summary.append({"物資名稱": item, "累積入庫": tin, "累計發放": tout, "剩餘庫存": tin - tout})
        st.dataframe(pd.DataFrame(summary), use_container_width=True)

# --- [分頁 4：訪視發放] ---
elif st.session_state.page == 'visit':
    render_nav()
    st.markdown("## 🤝 訪視與物資發放")
    mems, inv, logs = load_data("care_members", COLS_MEM), load_data("care_inventory", COLS_INV), load_data("care_logs", COLS_LOG)
    stock_dict = {}
    if not inv.empty:
        for itm, gp in inv.groupby('物資內容'):
            tin = gp['總數量'].replace("", "0").astype(float).sum()
            tout = logs[logs['物資內容'] == itm]['發放數量'].replace("", "0").astype(float).sum() if not logs.empty else 0
            stock_dict[itm] = max(0, int(tin - tout))
    
    itm_list = ["(僅訪視，不領取)"] + [f"{k} (庫存: {v})" for k, v in stock_dict.items()]
    with st.form("add_visit"):
        c1, c2, c3 = st.columns(3)
        v = st.selectbox("志工", load_data("members", ["姓名"])['姓名'].tolist())
        d = st.date_input("日期", value=date.today())
        p = st.selectbox("關懷戶", mems['姓名'].tolist())
        itm_sel = st.selectbox("物資 (顯示剩餘)", itm_list)
        qty = st.number_input("數量", min_value=0, value=1)
        note = st.text_area("訪視紀錄")
        if st.form_submit_button("確認提交紀錄"):
            real_itm = itm_sel.split(" (庫存:")[0]
            if real_itm != "(僅訪視，不領取)" and qty > stock_dict.get(real_itm, 0):
                st.error("❌ 數量超過庫存！")
            else:
                new = {"志工":v, "發放日期":str(d), "關懷戶姓名":p, "物資內容":real_itm, "發放數量":qty, "訪視紀錄":note}
                if save_data(pd.concat([logs, pd.DataFrame([new])], ignore_index=True), "care_logs"): st.success("成功"); time.sleep(1); st.rerun()

# --- [分頁 5：統計數據] ---
elif st.session_state.page == 'stats':
    render_nav()
    st.markdown("## 📊 數據統計查詢")
    inv, logs = load_data("care_inventory", COLS_INV), load_data("care_logs", COLS_LOG)
    t1, t2 = st.tabs(["📦 物資捐贈統計", "🔍 個案歷程查詢"])
    with t1:
        if not inv.empty:
            cts = inv.groupby('物資類型')['總數量'].apply(lambda x: x.astype(float).sum()).reset_index()
            fig = px.bar(cts, x='物資類型', y='總數量', color='物資類型', title="各類物資累計捐贈總量")
            st.plotly_chart(fig, use_container_width=True)
    with t2:
        if not logs.empty:
            m = load_data("care_members", COLS_MEM)
            qn = st.selectbox("選擇關懷戶", m['姓名'].tolist())
            res = logs[logs['關懷戶姓名'] == qn]
            st.markdown(f"#### {qn} 訪視與領取紀錄：{len(res)} 次")
            st.dataframe(res, use_container_width=True)
