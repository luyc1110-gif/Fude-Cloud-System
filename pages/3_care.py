import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta, timezone
import gspread
import plotly.express as px
import time
import textwrap

# =========================================================
# 0) 系統設定
# =========================================================
st.set_page_config(
    page_title="關懷戶管理系統", 
    page_icon="🏠", 
    layout="wide", 
    initial_sidebar_state="expanded" 
)

# 初始化 Session State
if 'authenticated' not in st.session_state: st.session_state.authenticated = False
if 'page' not in st.session_state: st.session_state.page = 'home'
if 'unlock_members' not in st.session_state: st.session_state.unlock_members = False
if 'unlock_details' not in st.session_state: st.session_state.unlock_details = False

TW_TZ = timezone(timedelta(hours=8))
PRIMARY = "#4A4E69"
GREEN   = "#8E9775"
BG_MAIN = "#F8F9FA"

# =========================================================
# 1) CSS 樣式 (獨立定義，避免與 Python 衝突)
# =========================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@500;700;900&display=swap');

html, body, [class*="css"], div, p, span, li, ul {
    font-family: "Noto Sans TC", "Microsoft JhengHei", sans-serif;
    color: #333333 !important;
}
.stApp { background-color: #F8F9FA !important; }

/* 導航與按鈕樣式 */
.nav-active {
    background: linear-gradient(135deg, #8E9775, #6D6875);
    color: white !important; padding: 12px 0; text-align: center; border-radius: 25px;
    font-weight: 900; margin-bottom: 12px; cursor: default;
}
div[data-testid="stFormSubmitButton"] > button, div[data-testid="stDownloadButton"] > button {
    background-color: #4A4E69 !important; color: #FFFFFF !important; border: none;
    border-radius: 12px; font-weight: 900; padding: 10px 25px;
}

/* --- 核心卡片樣式 (The Care Card) --- */
.care-card {
    background-color: #FFFFFF;
    border-radius: 16px;
    border-left: 6px solid #8E9775; /* 綠色左邊條 */
    box-shadow: 0 4px 15px rgba(0,0,0,0.08);
    margin-bottom: 20px;
    padding: 25px;
    position: relative;
}

.care-header {
    display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 15px;
}
.care-name {
    font-size: 1.8rem; font-weight: 900; color: #333; line-height: 1.2;
}
.care-meta {
    margin-top: 5px; font-size: 0.95rem; color: #666; background: #F5F5F5;
    padding: 4px 10px; border-radius: 8px; font-weight: 600; display: inline-block;
}
.care-tag {
    font-weight: 800; color: #4A4E69; border: 2px solid #4A4E69;
    padding: 6px 14px; border-radius: 20px; font-size: 0.9rem; white-space: nowrap;
}

.care-info-row {
    display: flex; flex-wrap: wrap; gap: 20px; margin-bottom: 12px; color: #444;
}
.care-info-item {
    font-size: 1rem; color: #444; min-width: 140px;
}

/* 分隔線與警示區 */
.care-divider {
    border-top: 1px dashed #E0E0E0; margin-top: 15px; padding-top: 12px;
}
.care-alert-title {
    font-size: 0.85rem; color: #888; margin-bottom: 8px; font-weight: bold;
}
.badge-red {
    display: inline-flex; align-items: center; padding: 4px 12px; border-radius: 20px;
    font-size: 0.85rem; font-weight: bold; background: #FFEBEE; color: #C62828 !important;
    border: 1px solid #FFCDD2; margin-right: 6px; margin-bottom: 6px;
}
.badge-orange {
    display: inline-flex; align-items: center; padding: 4px 12px; border-radius: 20px;
    font-size: 0.85rem; font-weight: bold; background: #FFF3E0; color: #EF6C00 !important;
    border: 1px solid #FFE0B2; margin-right: 6px; margin-bottom: 6px;
}
.badge-green {
    display: inline-flex; align-items: center; padding: 4px 12px; border-radius: 20px;
    font-size: 0.85rem; font-weight: bold; background: #E8F5E9; color: #2E7D32 !important;
    border: 1px solid #C8E6C9;
}

/* 其他小組件樣式 */
.visit-card {
    background-color: #FFFFFF; border-left: 5px solid #8E9775;
    border-radius: 10px; padding: 15px 20px; margin-bottom: 15px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}
.visit-header { display: flex; justify-content: space-between; margin-bottom: 5px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# =========================================================
# 2) 資料邏輯
# =========================================================
SHEET_ID = "1A3-VwCBYjnWdcEiL6VwbV5-UECcgX7TqKH94sKe8P90"
COLS_MEM = ["姓名", "身分證字號", "性別", "生日", "地址", "電話", "緊急聯絡人", "緊急聯絡人電話", "身分別", "18歲以下子女", "成人數量", "65歲以上長者"]
COLS_HEALTH = ["姓名", "身分證字號", "評估日期", "是否有假牙", "今年洗牙", "握力", "身高", "體重", "BMI", "聽力測試", "營養篩檢分數", "營養狀態", "心情溫度計分數", "情緒狀態", "有自殺意念"]
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
        pages = {'home': '📊 關懷概況看板', 'members': '📋 名冊管理', 'health': '🏥 健康追蹤', 'inventory': '📦 物資庫存', 'visit': '🤝 訪視發放', 'stats': '📈 數據統計'}
        for p, label in pages.items():
            if st.session_state.page == p:
                st.markdown(f'<div class="nav-active">{label}</div>', unsafe_allow_html=True)
            else:
                if st.button(label, key=f"nav_{p}", use_container_width=True): st.session_state.page = p; st.rerun()
        st.markdown("---")
        if st.button("🚪 回系統大廳", key="nav_back", use_container_width=True): st.switch_page("Home.py")

# =========================================================
# 4) Pages
# =========================================================

# --- [分頁 0：首頁] ---
if st.session_state.page == 'home':
    render_nav()
    st.markdown(f"<h2 style='color: {GREEN};'>📊 關懷戶概況看板</h2>", unsafe_allow_html=True)
    mems = load_data("care_members", COLS_MEM)
    if not mems.empty:
        mems['age'] = mems['生日'].apply(calculate_age)
        mems_disp = mems[~mems['身分別'].str.contains("一般戶", na=False)]
        c1, c2, c3 = st.columns(3)
        c1.metric("🏠 關懷戶總數", f"{len(mems_disp)} 人")
        c2.metric("♿ 身障關懷", f"{len(mems[mems['身分別'].str.contains('身障', na=False)])} 人")
        c3.metric("📉 低收/中低收", f"{len(mems[mems['身分別'].str.contains('低收|中低收', na=False)])} 人")
        st.info("💡 更多詳細數據與圖表請前往「數據統計」頁面查看。")

# --- [分頁 1：名冊] ---
elif st.session_state.page == 'members':
    render_nav()
    st.markdown("## 📋 關懷戶名冊管理")
    df = load_data("care_members", COLS_MEM)
    with st.expander("➕ 新增關懷戶", expanded=False):
        with st.form("add_care", clear_on_submit=True):
            c1, c2, c3, c4 = st.columns(4)
            n = c1.text_input("姓名")
            p = c2.text_input("身分證")
            g = c3.selectbox("性別", ["男", "女"])
            b = c4.date_input("生日", value=date(1950,1,1))
            addr = st.text_input("地址")
            ph = st.text_input("電話")
            ce1, ce2 = st.columns(2)
            en = ce1.text_input("緊急聯絡人")
            ep = ce2.text_input("緊急聯絡電話")
            cn1, cn2, cn3 = st.columns(3)
            child = cn1.number_input("18歲以下子女", 0)
            adult = cn2.number_input("成人數量", 0)
            senior = cn3.number_input("65歲以上", 0)
            id_t = st.multiselect("身分別", ["低收", "中低收", "中低老人", "身障", "獨居", "獨居有子女", "一般戶"])
            if st.form_submit_button("確認新增"):
                if df[(df['姓名']==n) & (df['身分證字號']==p.upper())].empty:
                    new = {"姓名":n, "身分證字號":p.upper(), "性別":g, "生日":str(b), "地址":addr, "電話":ph, "緊急聯絡人":en, "緊急聯絡人電話":ep, "身分別":",".join(id_t), "18歲以下子女":child, "成人數量":adult, "65歲以上長者":senior}
                    save_data(pd.concat([df, pd.DataFrame([new])], ignore_index=True), "care_members"); st.success("已新增"); time.sleep(1); st.rerun()
                else: st.error("資料重複")

    if st.session_state.unlock_members:
        ed = st.data_editor(df, use_container_width=True, num_rows="dynamic")
        if st.button("💾 儲存"): save_data(ed, "care_members")
    else:
        st.info("🔒 查看完整名冊需管理員權限")
        if st.button("🔓 解鎖"): st.session_state.unlock_members = True; st.rerun()

# --- [分頁 2：健康] ---
elif st.session_state.page == 'health':
    render_nav()
    st.markdown("## 🏥 關懷戶健康與風險評估")
    h_df, m_df = load_data("care_health", COLS_HEALTH), load_data("care_members", COLS_MEM)
    
    with st.expander("➕ 新增/更新 健康評估紀錄", expanded=True):
        with st.form("h_form"):
            sel_n = st.selectbox("選擇關懷戶", m_df['姓名'].tolist() if not m_df.empty else ["無名冊"])
            eval_date = st.date_input("評估日期", value=date.today())
            c1, c2, c3 = st.columns(3)
            h, w = c1.number_input("身高", 0.0, step=0.1), c2.number_input("體重", 0.0, step=0.1)
            grip = c3.text_input("握力")
            dent, wash, hear = st.columns(3)[0].selectbox("假牙", ["無","有"]), st.columns(3)[1].selectbox("洗牙", ["否","是"]), st.columns(3)[2].selectbox("聽力", ["正常","需注意"])
            
            st.markdown("**營養篩檢 (MNA)**")
            q1 = st.radio("食量減少?", ["0分：嚴重", "1分：中度", "2分：無"], horizontal=True)
            q2 = st.radio("體重下降?", ["0分：>3kg", "1分：不知", "2分：1-3kg", "3分：無"], horizontal=True)
            q3 = st.radio("活動能力?", ["0分：臥床", "1分：可下床", "2分：可外出"], horizontal=True)
            q4 = st.radio("心理創傷?", ["0分：有", "2分：無"], horizontal=True)
            q5 = st.radio("精神問題?", ["0分：嚴重", "1分：輕度", "2分：無"], horizontal=True)
            
            bmi_val = w/((h/100)**2) if h>0 else 0
            bmi_score = 0 if bmi_val<19 else (1 if bmi_val<21 else (2 if bmi_val<23 else 3))
            ns = int(q1[0])+int(q2[0])+int(q3[0])+int(q4[0])+int(q5[0])+bmi_score
            n_stat = "正常狀況" if ns>=12 else ("有營養不良風險" if ns>=8 else "營養不良")
            
            st.markdown("**心情溫度計 (BSRS-5)**")
            bs = [st.slider(f"{i+1}.{l}",0,5,0) for i,l in enumerate(["睡眠","緊張","易怒","憂鬱","自卑"])]
            s_risk = st.slider("6.自殺想法",0,5,0)
            ms = sum(bs)
            m_stat = "重度情緒困擾" if ms>=15 else ("中度情緒困擾" if ms>=10 else ("輕度情緒困擾" if ms>=6 else "正常"))
            
            if st.form_submit_button("💾 儲存"):
                if sel_n:
                    pid = m_df[m_df['姓名']==sel_n]['身分證字號'].iloc[0]
                    new = {"姓名":sel_n, "身分證字號":pid, "評估日期":str(eval_date), "是否有假牙":dent, "今年洗牙":wash, "握力":grip, "身高":h, "體重":w, "BMI":round(bmi_val,1), "聽力測試":hear, "營養篩檢分數":ns, "營養狀態":n_stat, "心情溫度計分數":ms, "情緒狀態":m_stat, "有自殺意念":"是" if s_risk>0 else "否"}
                    save_data(pd.concat([h_df, pd.DataFrame([new])], ignore_index=True), "care_health"); st.success("已存檔"); st.rerun()

    if not h_df.empty:
        st.data_editor(h_df.sort_values("評估日期", ascending=False), key="h_ed")
        if st.button("💾 更新表格"): save_data(st.session_state["h_ed"], "care_health")

# --- [分頁 3：物資] ---
elif st.session_state.page == 'inventory':
    render_nav()
    st.markdown("## 📦 物資庫存管理")
    inv = load_data("care_inventory", COLS_INV)
    with st.expander("➕ 新增捐贈", expanded=False):
        with st.form("add_inv"):
            d = st.text_input("捐贈者")
            t = st.selectbox("類型", ["食物","日用品","輔具","現金","服務"])
            i = st.text_input("品名")
            q = st.number_input("數量", 1)
            if st.form_submit_button("錄入"):
                if d and i:
                    save_data(pd.concat([inv, pd.DataFrame([{"捐贈者":d,"物資類型":t,"物資內容":i,"總數量":q,"捐贈日期":str(date.today())}])], ignore_index=True), "care_inventory")
                    st.success("已錄入"); st.rerun()
    if not inv.empty:
        ed = st.data_editor(inv, use_container_width=True, num_rows="dynamic")
        if st.button("💾 更新庫存"): save_data(ed, "care_inventory")

# --- [分頁 4：訪視] ---
elif st.session_state.page == 'visit':
    render_nav()
    st.markdown("## 🤝 訪視紀錄")
    logs, mems = load_data("care_logs", COLS_LOG), load_data("care_members", COLS_MEM)
    with st.form("visit_form"):
        p = st.selectbox("關懷戶", mems['姓名'].unique() if not mems.empty else [])
        d = st.date_input("日期", date.today())
        item = st.text_input("發放物資 (選填)")
        q = st.number_input("數量", 0)
        note = st.text_area("訪視紀錄")
        if st.form_submit_button("提交"):
            if p:
                new = {"志工":"志工","發放日期":str(d),"關懷戶姓名":p,"物資內容":item if item else "(僅訪視)","發放數量":q,"訪視紀錄":note}
                save_data(pd.concat([logs, pd.DataFrame([new])], ignore_index=True), "care_logs"); st.success("已記錄"); st.rerun()
    if not logs.empty:
        st.dataframe(logs.sort_values("發放日期", ascending=False))

# --- [分頁 5：統計 (重點修復區域)] ---
elif st.session_state.page == 'stats':
    render_nav()
    st.markdown("## 📊 數據統計與個案查詢")
    logs, mems = load_data("care_logs", COLS_LOG), load_data("care_members", COLS_MEM)
    h_df = load_data("care_health", COLS_HEALTH)

    tab1, tab2 = st.tabs(["👤 個案詳細檔案", "📈 整體物資統計"])
    
    with tab1:
        if mems.empty: st.info("目前尚無名冊")
        else:
            all_names = mems['姓名'].unique().tolist()
            target_name = st.selectbox("🔍 搜尋姓名", all_names)
            
            if target_name:
                p_data = mems[mems['姓名'] == target_name].iloc[0]
                age = calculate_age(p_data['生日'])
                try:
                    tf = int(p_data['18歲以下子女'] or 0) + int(p_data['成人數量'] or 0) + int(p_data['65歲以上長者'] or 0)
                except: tf = 0

                # --- 產生警示標籤 HTML ---
                tags_html = ""
                has_alert = False
                
                if not h_df.empty:
                    p_health = h_df[h_df['姓名'] == target_name]
                    if not p_health.empty:
                        last_h = p_health.sort_values("評估日期").iloc[-1]
                        
                        # 1. 自殺意念
                        if last_h['有自殺意念'] == "是":
                            tags_html += f"<span class='badge-red'>🚨 檢測到自殺意念</span>"
                            has_alert = True
                        
                        # 2. 情緒
                        ms = last_h['情緒狀態']
                        if "中度" in ms or "重度" in ms:
                            tags_html += f"<span class='badge-red'>🌡️ {ms} ({last_h['心情溫度計分數']})</span>"
                            has_alert = True
                        elif "輕度" in ms:
                            tags_html += f"<span class='badge-orange'>🌡️ {ms} ({last_h['心情溫度計分數']})</span>"
                            has_alert = True
                            
                        # 3. 營養
                        ns = last_h['營養狀態']
                        if "營養不良" in ns:
                            style = "badge-orange" if "風險" in ns else "badge-red"
                            tags_html += f"<span class='{style}'>🍱 {ns} ({last_h['營養篩檢分數']})</span>"
                            has_alert = True

                # 組合底部區域
                if has_alert:
                    alert_content = f"""
                    <div class="care-divider">
                        <div class="care-alert-title">🩺 健康風險提示：</div>
                        <div style="display: flex; flex-wrap: wrap;">{tags_html}</div>
                    </div>"""
                else:
                    alert_content = f"""
                    <div class="care-divider">
                        <span class="badge-green">✅ 目前狀況穩定</span>
                    </div>"""

                # --- 組合卡片 HTML (使用 textwrap.dedent 避免縮排錯誤) ---
                card_html = f"""
                <div class="care-card">
                    <div class="care-header">
                        <div>
                            <div class="care-name">{p_data['姓名']}</div>
                            <div class="care-meta">{p_data['性別']} / {age} 歲</div>
                        </div>
                        <div class="care-tag">{p_data['身分別']}</div>
                    </div>
                    
                    <div class="care-info-row">
                        <div class="care-info-item"><b>📞 電話：</b> {p_data['電話']}</div>
                        <div class="care-info-item" style="flex: 1;"><b>📍 地址：</b> {p_data['地址']}</div>
                    </div>
                    
                    <div class="care-info-item"><b>🏠 家庭結構：</b> 總人數 <b style="font-size:1.1rem;">{tf}</b> 人</div>
                    
                    {alert_content}
                </div>
                """
                st.markdown(textwrap.dedent(card_html), unsafe_allow_html=True)

                # 機敏資料 (保持原樣)
                if st.session_state.unlock_details:
                    if st.button("🔒 隱藏個資"): st.session_state.unlock_details = False; st.rerun()
                    st.markdown(f"<div style='background:#FFF3E0; padding:15px; border-radius:10px; margin-top:10px; color:#E65100;'><b>🆔 身分證：</b> {p_data['身分證字號']} <br> <b>🚨 緊急聯絡：</b> {p_data['緊急聯絡人']} ({p_data['緊急聯絡人電話']})</div>", unsafe_allow_html=True)
                else:
                    c1, c2 = st.columns([3,1])
                    pwd = c1.text_input("輸入密碼查看個資", type="password")
                    if c2.button("解鎖"): 
                        if pwd == st.secrets["admin_password"]: st.session_state.unlock_details = True; st.rerun()
                        else: st.error("密碼錯誤")

                # 歷史紀錄
                st.markdown("### 🤝 歷史紀錄")
                p_logs = logs[logs['關懷戶姓名'] == target_name]
                if not p_logs.empty:
                    for i, row in p_logs.sort_values("發放日期", ascending=False).iterrows():
                        st.markdown(f"<div class='visit-card'><div class='visit-header'><span>📅 {row['發放日期']}</span><span>👮 {row['志工']}</span></div><div>{row['物資內容']} x {row['發放數量']}</div><div style='color:#666; font-size:0.9rem; margin-top:5px;'>{row['訪視紀錄']}</div></div>", unsafe_allow_html=True)
                else:
                    st.info("尚無紀錄")

    with tab2:
        st.write("統計圖表區 (請參閱原代碼)")

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
