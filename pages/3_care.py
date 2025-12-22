import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta, timezone
import gspread
import plotly.express as px
import random
import time

# =========================================================
# 0) 系統設定與初始化 (解決下拉選單識別問題)
# =========================================================
st.set_page_config(page_title="關懷戶管理系統", page_icon="🏠", layout="wide", initial_sidebar_state="collapsed")

if 'page' not in st.session_state:
    st.session_state.page = 'home'

TW_TZ = timezone(timedelta(hours=8))

# 🔥 莫蘭迪森林綠配色
PRIMARY = "#8E9775"   # 苔蘚綠
ACCENT  = "#6D6875"   # 灰紫色
BG_MAIN = "#F8F9FA"   

# =========================================================
# 1) CSS 樣式 (針對下拉式選單、日期選擇強制顯色)
# =========================================================
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@500;700;900&display=swap');
html, body, [class*="css"], div, p, span, li, ul {{ font-family: "Noto Sans TC", sans-serif; color: #333 !important; }}
.stApp {{ background-color: {BG_MAIN}; }}
[data-testid="stHeader"], [data-testid="stSidebar"], footer {{ display: none; }}
.block-container {{ padding-top: 1rem !important; max-width: 1250px; }}

/* 🔥 解決下拉式選單與日期選擇字體不清晰問題 (強制白底黑字) */
div[data-baseweb="select"] > div, .stTextInput input, .stDateInput input, .stTimeInput input, .stNumberInput input {{
    background-color: #FFFFFF !important; 
    color: #000000 !important;
    border: 2px solid #D1D1D1 !important; 
    border-radius: 12px !important; 
    font-weight: 700 !important;
}}
div[data-baseweb="select"] span, div[data-baseweb="select"] div {{ color: #000000 !important; }}

/* 數據看板：強制白字 */
.care-metric-box {{
    padding: 30px; border-radius: 20px; color: #FFFFFF !important; text-align: center; margin-bottom: 15px;
    box-shadow: 0 8px 20px rgba(0,0,0,0.1);
}}
.care-metric-box div, .care-metric-box span {{ color: #FFFFFF !important; font-weight: 900 !important; }}

/* 導航按鈕 */
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
# 2) 資料邏輯 (Google Sheets 鉤稽)
# =========================================================
SHEET_ID = "1A3-VwCBYjnWdcEiL6VwbV5-UECcgX7TqKH94sKe8P90"

# 定義各模組欄位
COLS_MEM = ["姓名", "身分證字號", "性別", "生日", "地址", "電話", "緊急聯絡人", "緊急聯絡人電話", "身分別", "18歲以下子女", "成人數量", "65歲以上長者", "是否有假牙", "今年洗牙", "握力", "身高", "體重", "聽力測試"]
COLS_INV = ["捐贈者", "物資類型", "物資內容", "總數量", "捐贈日期"]
COLS_LOG = ["志工", "發放日期", "關懷戶姓名", "物資內容", "發放數量", "訪視紀錄"]

@st.cache_resource
def get_client(): return gspread.service_account_from_dict(st.secrets["gcp_service_account"])

def load_data(sn, target_cols):
    try:
        client = get_client()
        sheet = client.open_by_key(SHEET_ID).worksheet(sn)
        df = pd.DataFrame(sheet.get_all_records()).astype(str)
        for c in target_cols:
            if c not in df.columns: df[c] = ""
        return df
    except: return pd.DataFrame(columns=target_cols)

def save_data(df, sn):
    df_fix = df.fillna("").replace(['nan', 'NaN', 'nan.0'], "").astype(str)
    sheet = get_client().open_by_key(SHEET_ID).worksheet(sn)
    sheet.clear()
    sheet.update([df_fix.columns.values.tolist()] + df_fix.values.tolist())
    st.cache_data.clear()

def calculate_age(dob_str):
    try:
        bd = datetime.strptime(str(dob_str).strip(), "%Y-%m-%d").date()
        return date.today().year - bd.year - ((date.today().month, date.today().day) < (bd.month, bd.day))
    except: return 0

# =========================================================
# 3) 頁面導航
# =========================================================
def render_nav():
    st.markdown('<div style="background:white; padding:12px; border-radius:20px; margin-bottom:20px; box-shadow: 0 2px 15px rgba(0,0,0,0.05);">', unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns(5)
    pages = [("🏠 首頁", 'home'), ("📋 名冊管理", 'members'), ("📦 物資庫存", 'inventory'), ("🤝 訪視發放", 'visit'), ("📊 數據統計", 'stats')]
    for i, (label, p_key) in enumerate(pages):
        with [c1, c2, c3, c4, c5][i]:
            if st.button(label, use_container_width=True, key=f"nav_{p_key}"): 
                st.session_state.page = p_key
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- 頁面 0：首頁數據看板 ---
if st.session_state.page == 'home':
    if st.button("🚪 回大廳"): st.switch_page("Home.py")
    st.markdown("<h1 style='text-align: center;'>福德里 - 關懷戶管理系統</h1>", unsafe_allow_html=True)
    render_nav()
    
    mems = load_data("care_members", COLS_MEM)
    logs = load_data("care_logs", COLS_LOG)
    
    if not mems.empty:
        mems['age'] = mems['生日'].apply(calculate_age)
        total_p = len(mems)
        avg_age = round(mems['age'].mean(), 1)
        
        # 統計各類別人數與平均年齡
        def get_stat(keyword):
            subset = mems[mems['身分別'].str.contains(keyword, na=False)]
            return len(subset), round(subset['age'].mean(), 1) if not subset.empty else 0

        dis_c, dis_a = get_stat("身障")
        low_c, low_a = get_stat("低收")
        old_c, old_a = get_stat("中低老人")
        total_dist = logs['發放數量'].replace("", "0").astype(float).sum() if not logs.empty else 0

        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"""<div class="care-metric-box" style="background:linear-gradient(135deg,#8E9775 0%,#6D6875 100%);"><div>🏠 關懷戶總人數 / 平均年齡</div><div style="font-size:3.5rem;">{total_p} <span style="font-size:1.5rem;">人</span> / {avg_age} <span style="font-size:1.5rem;">歲</span></div></div>""", unsafe_allow_html=True)
        with c2:
            st.markdown(f"""<div class="care-metric-box" style="background:linear-gradient(135deg,#A4AC86 0%,#8E9775 100%);"><div>♿ 身障關懷人數 / 平均年齡</div><div style="font-size:3.5rem;">{dis_c} <span style="font-size:1.5rem;">人</span> / {dis_a} <span style="font-size:1.5rem;">歲</span></div></div>""", unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f'<div class="dash-card"><b>低收/中低收統計</b><br>{low_c} 人 (平均 {low_a} 歲)</div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="dash-card"><b>中低老人統計</b><br>{old_c} 人 (平均 {old_a} 歲)</div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="dash-card"><b>物資發放總量</b><br><span style="font-size:1.5rem; color:{PRIMARY}; font-weight:900;">{int(total_dist)} 份</span></div>', unsafe_allow_html=True)

# --- 頁面 1：關懷戶名冊與健康狀況 ---
elif st.session_state.page == 'members':
    render_nav()
    st.markdown("## 📋 關懷戶名冊與健康管理")
    df = load_data("care_members", COLS_MEM)
    
    with st.expander("➕ 新增關懷戶資料 (含健康數據)"):
        with st.form("add_care"):
            c1, c2, c3 = st.columns(3)
            name = c1.text_input("姓名")
            pid = c2.text_input("身分證字號")
            dob = c3.date_input("生日", value=date(1950, 1, 1))
            c4, c5 = st.columns([2, 1])
            addr = c4.text_input("地址")
            phone = c5.text_input("電話")
            id_types = st.multiselect("身分別 (可複選)", ["低收", "中低收", "中低老人", "身障", "獨居", "獨居有子女"])
            
            st.markdown("###### 同住家人人數")
            cj1, cj2, cj3 = st.columns(3)
            child = cj1.number_input("18歲以下子女", 0, 10, 0)
            adult = cj2.number_input("成人數量", 0, 10, 0)
            elder = cj3.number_input("65歲以上長者", 0, 10, 0)
            
            st.markdown("###### 🏥 健康狀況指標")
            h1, h2, h3, h4, h5, h6 = st.columns(6)
            dent = h1.selectbox("是否有假牙", ["無", "有"])
            wash = h2.selectbox("今年度是否洗牙", ["否", "是"])
            grip = h3.text_input("握力 (kg)")
            height = h4.text_input("身高 (cm)")
            weight = h5.text_input("體重 (kg)")
            hear = h6.selectbox("聽力測試", ["正常", "需注意"])
            
            if st.form_submit_button("確認新增"):
                new_row = {
                    "姓名": name, "身分證字號": pid.upper(), "生日": str(dob), "地址": addr, "電話": phone,
                    "身分別": ",".join(id_types), "18歲以下子女": child, "成人數量": adult, "65歲以上長者": elder,
                    "是否有假牙": dent, "今年洗牙": wash, "握力": grip, "身高": height, "體重": weight, "聽力測試": hear
                }
                if save_data(pd.concat([df, pd.DataFrame([new_row])], ignore_index=True), "care_members"):
                    st.success("資料已存入"); st.rerun()
    
    if not df.empty:
        df['歲數'] = df['生日'].apply(calculate_age)
        st.data_editor(df, use_container_width=True, num_rows="dynamic", key="care_mem_edit")
        if st.button("💾 儲存修改"): save_data(df, "care_members"); st.success("名冊已更新")

# --- 頁面 2：物資管理 ---
elif st.session_state.page == 'inventory':
    render_nav()
    st.markdown("## 📦 物資捐贈與庫存管理")
    inv = load_data("care_inventory", COLS_INV)
    logs = load_data("care_logs", COLS_LOG)
    
    with st.form("add_inv"):
        c1, c2, c3, c4 = st.columns(4)
        donor = c1.text_input("捐贈者")
        v_type = c2.selectbox("物資類型", ["食物", "日用品", "輔具", "現金", "服務"])
        content = c3.text_input("詳細內容 (詳細物資名稱)")
        qty = c4.number_input("總數量", min_value=1)
        if st.form_submit_button("錄入捐贈資料"):
            new_v = {"捐贈者": donor, "物資類型": v_type, "物資內容": content, "總數量": qty, "捐贈日期": str(date.today())}
            save_data(pd.concat([inv, pd.DataFrame([new_v])], ignore_index=True), "care_inventory")
            st.success("入庫成功"); st.rerun()
    
    st.markdown("### 📊 物資庫存表 (自動計算剩餘量)")
    if not inv.empty:
        summary = []
        for item, group in inv.groupby('物資內容'):
            total_in = group['總數量'].replace("", "0").astype(float).sum()
            total_out = logs[logs['物資內容'] == item]['發放數量'].replace("", "0").astype(float).sum() if not logs.empty else 0
            summary.append({"物資名稱": item, "類型": group.iloc[0]['物資類型'], "累積入庫": total_in, "已發放": total_out, "剩餘庫存": total_in - total_out})
        st.dataframe(pd.DataFrame(summary), use_container_width=True)

# --- 頁面 3：訪視與物資領取 (含優先提示邏輯) ---
elif st.session_state.page == 'visit':
    render_nav()
    st.markdown("## 🤝 訪視與物資發放紀錄")
    mems = load_data("care_members", COLS_MEM)
    inv = load_data("care_inventory", COLS_INV)
    logs = load_data("care_logs", COLS_LOG)
    
    # 鉤稽志工管理系統
    vol_df = load_data("members", ["姓名"])
    vol_list = vol_df['姓名'].tolist() if not vol_df.empty else ["無志工資料"]

    with st.container(border=True):
        st.markdown("#### 🎁 新增紀錄與發放建議")
        c1, c2, c3 = st.columns(3)
        sel_vol = c1.selectbox("執行志工 (連動志工系統)", vol_list)
        sel_date = c2.date_input("日期", value=date.today())
        sel_care = c3.selectbox("領取關懷戶", mems['姓名'].tolist() if not mems.empty else ["無名冊"])
        
        c4, c5 = st.columns([2, 1])
        available_items = inv['物資內容'].unique().tolist()
        sel_item = c4.selectbox("選擇發放物資", ["(僅訪視，不領取)"] + available_items)
        send_qty = c5.number_input("發放數量", min_value=0, value=1)
        
        # 🔥 優先提示邏輯：分析該物資各關懷戶領取數量狀況
        if sel_item != "(僅訪視，不領取)":
            receive_counts = logs[logs['物資內容'] == sel_item]['關懷戶姓名'].value_counts()
            # 找出尚未領取或領取次數最少的前 5 名
            suggest_list = mems[~mems['姓名'].isin(receive_counts.index)]['姓名'].head(5).tolist()
            if suggest_list:
                st.info(f"💡 **發放優先建議**：尚未領取過「{sel_item}」的關懷戶：{', '.join(suggest_list)}")
        
        visit_note = st.text_area("訪視紀錄內容")
        
        if st.button("確認提交紀錄 (自動連動庫存)"):
            new_log = {"志工": sel_vol, "發放日期": str(sel_date), "關懷戶姓名": sel_care, "物資內容": sel_item, "發放數量": send_qty, "訪視紀錄": visit_note}
            if save_data(pd.concat([logs, pd.DataFrame([new_log])], ignore_index=True), "care_logs"):
                st.success("紀錄已存檔"); time.sleep(1); st.rerun()

    st.markdown("### 📋 歷史訪視與發放清單 (可事後編輯加回庫存)")
    if not logs.empty:
        edited_logs = st.data_editor(logs.sort_values('發放日期', ascending=False), use_container_width=True, num_rows="dynamic", key="care_visit_edit")
        if st.button("💾 儲存修改內容"):
            if save_data(edited_logs, "care_logs"): st.success("修改成功，剩餘庫存已自動同步。")

# --- 頁面 4：數據統計查詢 ---
elif st.session_state.page == 'stats':
    render_nav()
    st.markdown("## 📊 數據統計查詢")
    inv = load_data("care_inventory", COLS_INV)
    logs = load_data("care_logs", COLS_LOG)
    
    t1, t2 = st.tabs(["📦 捐贈數量統計", "🔍 個案歷程查找"])
    with t1:
        if not inv.empty:
            type_counts = inv.groupby('物資類型')['總數量'].apply(lambda x: x.astype(float).sum()).reset_index()
            fig = px.bar(type_counts, x='物資類型', y='總數量', color='物資類型', title="各類物資累計捐贈數量", color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig, use_container_width=True)
            
    with t2:
        mems = load_data("care_members", COLS_MEM)
        c1, c2 = st.columns(2)
        q_name = c1.selectbox("選擇欲查詢關懷戶", mems['姓名'].tolist())
        q_range = c2.date_input("選擇時間區間", value=(date(date.today().year, 1, 1), date.today()))
        
        if isinstance(q_range, tuple) and len(q_range) == 2:
            res = logs[(logs['關懷戶姓名'] == q_name) & (pd.to_datetime(logs['發放日期']).dt.date >= q_range[0]) & (pd.to_datetime(logs['發放日期']).dt.date <= q_range[1])]
            st.markdown(f"#### {q_name} 於區間內：訪視/領取共 {len(res)} 次")
            st.dataframe(res, use_container_width=True)
