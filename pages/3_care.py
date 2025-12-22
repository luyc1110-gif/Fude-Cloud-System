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
# 1) CSS 樣式
# =========================================================
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@500;700;900&display=swap');
html, body, [class*="css"], div, p, span, li, ul {{ font-family: "Noto Sans TC", sans-serif; color: #333 !important; }}
.stApp {{ background-color: {BG_MAIN}; }}
[data-testid="stHeader"], [data-testid="stSidebar"], footer {{ display: none; }}
.block-container {{ padding-top: 1rem !important; max-width: 1250px; }}

/* 表格白底黑字強化 */
div[data-testid="stDataFrame"], div[data-testid="stTable"] {{
    background-color: #FFFFFF !important;
    border-radius: 10px; padding: 10px;
}}
.stDataFrame div, .stDataFrame span, .stDataFrame p {{ color: #000000 !important; }}

/* 下拉選單與輸入框 */
div[data-baseweb="select"] > div, .stTextInput input, .stDateInput input, .stTimeInput input, .stNumberInput input {{
    background-color: #FFFFFF !important; color: #000000 !important;
    border: 2px solid #D1D1D1 !important; border-radius: 12px !important; font-weight: 700 !important;
}}
div[data-baseweb="select"] span {{ color: #000000 !important; }}

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
# 3) UI 元件
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

# --- 頁面處理 ---
if st.session_state.page == 'home':
    if st.button("🚪 回大廳"): st.switch_page("Home.py")
    st.markdown("<h1 style='text-align: center;'>福德里 - 關懷戶管理系統</h1>", unsafe_allow_html=True)
    render_nav()
    mems, logs = load_data("care_members", COLS_MEM), load_data("care_logs", COLS_LOG)
    if not mems.empty:
        mems['age'] = mems['生日'].apply(calculate_age)
        st.markdown(f'<div class="care-metric-box" style="background:linear-gradient(135deg,#8E9775 0%,#6D6875 100%);"><div>🏠 關懷戶總人數 / 平均年齡</div><div style="font-size:3.5rem;">{len(mems)} 人 / {round(mems["age"].mean(),1)} 歲</div></div>', unsafe_allow_html=True)

elif st.session_state.page == 'members':
    render_nav()
    st.markdown("## 📋 關懷戶名冊管理")
    df = load_data("care_members", COLS_MEM)
    with st.expander("➕ 新增關懷戶"):
        with st.form("add_care"):
            c1, c2, c3, c4 = st.columns(4)
            n, p, g, b = c1.text_input("姓名"), c2.text_input("身分證"), c3.selectbox("性別", ["男", "女"]), c4.date_input("生日", value=date(1950, 1, 1))
            addr, ph = st.text_input("地址"), st.text_input("電話")
            if st.form_submit_button("確認新增"):
                if p.upper() in df['身分證字號'].values: st.error("❌ 該身分證號已存在！")
                else:
                    new = {"姓名":n, "身分證字號":p.upper(), "性別":g, "生日":str(b), "地址":addr, "電話":ph}
                    if save_data(pd.concat([df, pd.DataFrame([new])], ignore_index=True), "care_members"): st.success("成功"); st.rerun()
    if not df.empty:
        df['歲數'] = df['生日'].apply(calculate_age)
        edited_df = st.data_editor(df, use_container_width=True, num_rows="dynamic", key="mem_ed")
        if st.button("💾 儲存修改"): 
            if save_data(edited_df, "care_members"): st.success("已更新")

elif st.session_state.page == 'health':
    render_nav()
    st.markdown("## 🏥 健康狀況管理")
    h_df, m_df = load_data("care_health", COLS_HEALTH), load_data("care_members", COLS_MEM)
    if not h_df.empty:
        st.data_editor(h_df, use_container_width=True, num_rows="dynamic")

elif st.session_state.page == 'inventory':
    render_nav()
    st.markdown("## 📦 物資庫存管理")
    inv, logs = load_data("care_inventory", COLS_INV), load_data("care_logs", COLS_LOG)
    with st.form("add_inv"):
        c1, c2, c3, c4 = st.columns(4)
        do, ty, co, qt = c1.text_input("捐贈者"), c2.selectbox("類型",["食物","日用品","輔具"]), c3.text_input("物資名稱"), c4.number_input("數量", min_value=1)
        if st.form_submit_button("入庫"):
            new = {"捐贈者":do, "物資類型":ty, "物資內容":co, "總數量":qt, "捐贈日期":str(date.today())}
            save_data(pd.concat([inv, pd.DataFrame([new])], ignore_index=True), "care_inventory"); st.rerun()
    if not inv.empty:
        summary = []
        for item, group in inv.groupby('物資內容'):
            total_in = group['總數量'].replace("", "0").astype(float).sum()
            total_out = logs[logs['物資內容'] == item]['發放數量'].replace("", "0").astype(float).sum() if not logs.empty else 0
            summary.append({"物資名稱": item, "入庫": total_in, "發放": total_out, "剩餘": total_in - total_out})
        st.dataframe(pd.DataFrame(summary), use_container_width=True)

# =========================================================
# 4) 訪視發放 (核心修改：庫存顯示與擋存邏輯)
# =========================================================
elif st.session_state.page == 'visit':
    render_nav()
    st.markdown("## 🤝 訪視與物資發放")
    mems, inv, logs = load_data("care_members", COLS_MEM), load_data("care_inventory", COLS_INV), load_data("care_logs", COLS_LOG)
    
    # --- A. 先算好每一項的剩餘庫存 ---
    stock_dict = {}
    if not inv.empty:
        for item, group in inv.groupby('物資內容'):
            tin = group['總數量'].replace("", "0").astype(float).sum()
            tout = logs[logs['物資內容'] == item]['發放數量'].replace("", "0").astype(float).sum() if not logs.empty else 0
            stock_dict[item] = max(0, int(tin - tout))

    # --- B. 製作帶有庫存數字的選單 ---
    item_display_list = ["(僅訪視，不領取)"]
    item_to_real_name = {"(僅訪視，不領取)": "(僅訪視，不領取)"}
    
    for name, stock in stock_dict.items():
        display_text = f"{name} (庫存: {stock})"
        item_display_list.append(display_text)
        item_to_real_name[display_text] = name

    # --- C. 介面 ---
    with st.container(border=True):
        st.markdown("#### 🎁 新增發放紀錄")
        c1, c2, c3 = st.columns(3)
        v_list = load_data("members", ["姓名"])['姓名'].tolist() if not load_data("members", ["姓名"]).empty else ["無資料"]
        sel_v = c1.selectbox("執行志工", v_list)
        sel_d = c2.date_input("日期", value=date.today())
        sel_c = c3.selectbox("關懷戶", mems['姓名'].tolist() if not mems.empty else ["無名冊"])
        
        c4, c5 = st.columns([2, 1])
        sel_i_display = c4.selectbox("選擇物資 (顯示剩餘庫存)", item_display_list)
        sel_q = c5.number_input("數量", min_value=0, value=1)
        
        # 取得真正的物資名稱
        real_item_name = item_to_real_name[sel_i_display]
        
        nt = st.text_area("訪視紀錄內容")
        
        if st.button("確認提交"):
            # 🔥 擋存邏輯：檢查庫存
            if real_item_name == "(僅訪視，不領取)":
                can_save = True
            else:
                current_stock = stock_dict.get(real_item_name, 0)
                if sel_q > current_stock:
                    st.error(f"❌ 無法建檔：發放數量 ({sel_q}) 超過目前庫存 ({current_stock})！")
                    can_save = False
                elif sel_q <= 0:
                    st.warning("⚠️ 請輸入有效的發放數量")
                    can_save = False
                else:
                    can_save = True
            
            # --- D. 存檔 ---
            if can_save:
                new = {"志工":sel_v, "發放日期":str(sel_d), "關懷戶姓名":sel_c, "物資內容":real_item_name, "發放數量":sel_q, "訪視紀錄":nt}
                if save_data(pd.concat([logs, pd.DataFrame([new])], ignore_index=True), "care_logs"):
                    st.success("✅ 紀錄已成功建檔，庫存已連動。"); time.sleep(1); st.rerun()

    if not logs.empty:
        st.markdown("### 📋 歷史清單")
        ed_logs = st.data_editor(logs, use_container_width=True, num_rows="dynamic", key="log_ed")
        if st.button("💾 儲存修改內容"): save_data(ed_logs, "care_logs")

elif st.session_state.page == 'stats':
    render_nav()
    st.info("統計功能連動中...")
