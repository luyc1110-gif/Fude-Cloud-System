import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta, timezone
import gspread
import time
import os
import plotly.express as px
import random

# =========================================================
# 0) 系統設定
# =========================================================
st.set_page_config(
    page_title="長輩關懷系統",
    page_icon="👴",
    layout="wide",
    initial_sidebar_state="collapsed",
)

TW_TZ = timezone(timedelta(hours=8))

# 🔥 莫蘭迪長輩系統配色定義
PRIMARY = "#B5838D"   # 暮色粉 (莫蘭迪主色)
ACCENT  = "#6D597A"   # 煙燻紫 (點綴色)
BG_MAIN = "#F8F9FA"   # 極淺灰底
TEXT    = "#444444"   # 炭灰色字

# =========================================================
# 1) CSS 樣式 (V30.0 莫蘭迪卡片強化版)
# =========================================================
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@500;700;900&display=swap');

html, body, [class*="css"], div, p, span, li, ul {{
    font-family: "Noto Sans TC", "Microsoft JhengHei", sans-serif;
    color: {TEXT} !important;
}}
.stApp {{ background-color: {BG_MAIN}; }}
[data-testid="stHeader"], [data-testid="stSidebar"], footer {{ display: none; }}
.block-container {{ padding-top: 1rem !important; max-width: 1250px; }}

/* 🔥 強制下拉選單與輸入框高對比 (白底黑字) */
.stTextInput input, .stDateInput input, .stTimeInput input, .stNumberInput input, div[data-baseweb="select"] > div {{
    background-color: #FFFFFF !important; 
    color: #000000 !important;
    border: 1.5px solid #D1D1D1 !important; 
    border-radius: 12px !important;
    font-weight: 700 !important;
}}
div[data-baseweb="select"] span, div[data-baseweb="select"] div {{ color: #000000 !important; }}
div[role="listbox"], ul[data-baseweb="menu"], li[role="option"] {{
    background-color: #FFFFFF !important; color: #000000 !important; font-weight: 700 !important;
}}

/* 導航按鈕 (莫蘭迪風) */
div[data-testid="stButton"] > button {{
    width: 100%; background-color: white !important; color: {PRIMARY} !important;
    border: 1.5px solid {PRIMARY} !important; border-radius: 15px !important;
    font-weight: 900 !important; font-size: 1.1rem !important;
    padding: 10px 0 !important; box-shadow: 0 4px 10px rgba(0,0,0,0.02);
    transition: all 0.2s;
}}
div[data-testid="stButton"] > button:hover {{
    background-color: {PRIMARY} !important; color: white !important;
    transform: translateY(-2px);
}}

/* 數據卡片 (白底莫蘭迪陰影) */
.custom-card {{
    background-color: white; border-radius: 20px; padding: 25px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.05); border: 1px solid rgba(0,0,0,0.03);
    width: 100%; margin-bottom: 20px;
}}

/* 戰情小卡 */
.dash-card {{
    background-color: white; padding: 18px; border-radius: 18px; border-left: 6px solid {PRIMARY};
    box-shadow: 0 4px 15px rgba(0,0,0,0.03); margin-bottom: 12px;
}}
.nav-container {{
    background-color: white; padding: 12px; border-radius: 20px;
    margin-bottom: 20px; box-shadow: 0 2px 15px rgba(0,0,0,0.04);
}}
</style>
""", unsafe_allow_html=True)

# =========================================================
# 2) Logic & Data (修正 NaN 錯誤)
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

@st.cache_data(ttl=60)
def load_data(sheet_name):
    try:
        client = get_google_sheet_client()
        sheet = client.open_by_key(SHEET_ID).worksheet(sheet_name)
        data = sheet.get_all_records()
        df = pd.DataFrame(data).astype(str)
        target_cols = M_COLS if sheet_name == 'elderly_members' else L_COLS
        for c in target_cols: 
            if c not in df.columns: df[c] = ""
        return df
    except: return pd.DataFrame(columns=M_COLS if sheet_name == 'elderly_members' else L_COLS)

def save_data(df, sheet_name):
    try:
        # 🔥 修正 NaN 錯誤：儲存前清除所有無效值，並強制轉為字串
        df_to_save = df.copy()
        df_to_save = df_to_save.replace(['nan', 'NaN', 'None', '<NA>', 'nan.0'], "")
        df_to_save = df_to_save.fillna("")
        
        client = get_google_sheet_client()
        sheet = client.open_by_key(SHEET_ID).worksheet(sheet_name)
        sheet.clear()
        sheet.update([df_to_save.columns.values.tolist()] + df_to_save.values.tolist())
        load_data.clear()
        return True
    except Exception as e:
        st.error(f"寫入失敗：{e}")
        return False

def get_tw_time(): return datetime.now(TW_TZ)

def calculate_age(dob_str):
    try:
        b_date = datetime.strptime(str(dob_str).strip(), "%Y-%m-%d").date()
        today = date.today()
        return today.year - b_date.year - ((today.month, today.day) < (b_date.month, b_date.day))
    except: return 0

# =========================================================
# 3) Navigation
# =========================================================
if 'page' not in st.session_state: st.session_state.page = 'home'

def render_nav():
    st.markdown('<div class="nav-container">', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("🏠 長輩首頁", use_container_width=True): st.session_state.page = 'home'; st.rerun()
    with c2:
        if st.button("📋 長輩名冊", use_container_width=True): st.session_state.page = 'members'; st.rerun()
    with c3:
        if st.button("🩸 據點報到", use_container_width=True): st.session_state.page = 'checkin'; st.rerun()
    with c4:
        if st.button("📊 統計數據", use_container_width=True): st.session_state.page = 'stats'; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# =========================================================
# 4) Pages
# =========================================================
if st.session_state.page == 'home':
    c_back, c_empty = st.columns([1, 4])
    with c_back:
        if st.button("🚪 回系統大廳"): st.switch_page("Home.py")
    st.markdown(f"<h1 style='text-align: center; color: #444; margin-bottom: 30px;'>福德里 - 關懷據點系統</h1>", unsafe_allow_html=True)
    
    col_l, c1, c2, c3, col_r = st.columns([1.5, 2, 2, 2, 0.5])
    with c1:
        if st.button("📋 長輩名冊", key="h_m"): st.session_state.page = 'members'; st.rerun()
    with c2:
        if st.button("🩸 據點報到", key="h_c"): st.session_state.page = 'checkin'; st.rerun()
    with c3:
        if st.button("📊 統計數據", key="h_s"): st.session_state.page = 'stats'; st.rerun()

    st.markdown("---")
    logs = load_data("elderly_logs")
    members = load_data("elderly_members")
    this_year, today_str = get_tw_time().year, get_tw_time().strftime("%Y-%m-%d")
    
    year_count = len(logs[pd.to_datetime(logs['日期'], errors='coerce').dt.year == this_year]) if not logs.empty else 0
    today_count = len(logs[logs['日期'] == today_str]) if not logs.empty else 0
    
    avg_age = round(members['出生年月日'].apply(calculate_age).mean(), 1) if not members.empty else 0
    male_count = len(members[members['性別'] == '男']) if not members.empty else 0
    female_count = len(members[members['性別'] == '女']) if not members.empty else 0

    st.markdown(f"### 📅 據點數據看板 ({today_str})")
    
    # 🔥🔥🔥 修改：莫蘭迪配色數據卡片 (年度 & 今日) 🔥🔥🔥
    c_year, c_today = st.columns(2)
    with c_year:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, {PRIMARY} 0%, {ACCENT} 100%); padding: 30px; border-radius: 20px; color: white; text-align: center; box-shadow: 0 8px 25px rgba(181, 131, 141, 0.2);">
            <div style="font-size: 1.1rem; opacity: 0.9; color: white !important;">📅 {this_year} 年度總服務人次</div>
            <div style="font-size: 3.5rem; font-weight: 900; margin: 10px 0; color: white !important;">{year_count}</div>
        </div>
        """, unsafe_allow_html=True)
    with c_today:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #E5989B 0%, {PRIMARY} 100%); padding: 30px; border-radius: 20px; color: white; text-align: center; box-shadow: 0 8px 25px rgba(229, 152, 155, 0.2);">
            <div style="font-size: 1.1rem; opacity: 0.9; color: white !important;">☀️ 今日服務人次</div>
            <div style="font-size: 3.5rem; font-weight: 900; margin: 10px 0; color: white !important;">{today_count}</div>
        </div>
        """, unsafe_allow_html=True)

    st.write("")
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(f"""<div class="dash-card"><div style="color:#888;font-weight:bold;">平均年齡</div><div style="font-size:1.8rem;color:{PRIMARY};font-weight:900;">{avg_age} 歲</div></div>""", unsafe_allow_html=True)
    with c2: st.markdown(f"""<div class="dash-card"><div style="color:#888;font-weight:bold;">男性長輩</div><div style="font-size:1.8rem;color:{PRIMARY};font-weight:900;">{male_count} 人</div></div>""", unsafe_allow_html=True)
    with c3: st.markdown(f"""<div class="dash-card"><div style="color:#888;font-weight:bold;">女性長輩</div><div style="font-size:1.8rem;color:{PRIMARY};font-weight:900;">{female_count} 人</div></div>""", unsafe_allow_html=True)

elif st.session_state.page == 'members':
    render_nav()
    st.markdown("## 📋 長輩名冊管理")
    df = load_data("elderly_members")
    with st.expander("➕ 新增長輩資料"):
        with st.form("add_elder"):
            c1, c2, c3 = st.columns(3)
            name, pid, gender = c1.text_input("姓名"), c2.text_input("身分證字號"), c3.selectbox("性別", ["男", "女"])
            c4, c5 = st.columns([1, 2])
            dob, phone = c4.date_input("出生年月日", value=date(1950, 1, 1), min_value=date(1900, 1, 1)), c5.text_input("電話")
            addr, note = st.text_input("地址"), st.text_input("備註")
            if st.form_submit_button("確認新增"):
                if not pid or not name: st.error("姓名與身分證字號為必填")
                else:
                    new_row = {"姓名": name, "身分證字號": pid.upper(), "性別": gender, "出生年月日": str(dob), "電話": phone, "地址": addr, "備註": note, "加入日期": str(date.today())}
                    if save_data(pd.concat([df, pd.DataFrame([new_row])], ignore_index=True), "elderly_members"):
                        st.success(f"已新增：{name}"); time.sleep(1); st.rerun()
    if not df.empty:
        df['年齡'] = df['出生年月日'].apply(calculate_age)
        st.data_editor(df[["姓名", "性別", "年齡", "電話", "地址", "身分證字號", "出生年月日", "備註"]], use_container_width=True, num_rows="dynamic", key="elder_editor")

elif st.session_state.page == 'checkin':
    render_nav()
    st.markdown("## 🩸 據點報到站")
    if 'elder_pid' not in st.session_state: st.session_state.elder_pid = ""
    if 'checkin_msg' not in st.session_state: st.session_state.checkin_msg = (None, None)

    st.markdown('<div class="custom-card" style="border-left: 6px solid #E5989B;">', unsafe_allow_html=True)
    st.markdown("#### 1. 設定報到活動與時間")
    c1, c2, c3 = st.columns([1.5, 1.5, 2])
    with c1: main_cat = st.selectbox("課程大分類", list(COURSE_HIERARCHY.keys()))
    with c2: sub_cat = st.selectbox("課程子分類", COURSE_HIERARCHY[main_cat])
    with c3: course_name = st.text_input("課程名稱 (選填)", placeholder="例如：樂齡肌力訓練")
    final_course_cat, final_course_name = f"{main_cat}-{sub_cat}", (course_name if course_name.strip() else sub_cat)
    st.markdown("---")
    cd1, cd2 = st.columns(2)
    with cd1: target_date = st.date_input("報到日期", value=get_tw_time().date())
    with cd2: target_time = st.time_input("報到時間", value=get_tw_time().time())
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="custom-card">', unsafe_allow_html=True)
    c_title, c_msg = st.columns([2, 3])
    with c_title: st.markdown("#### 2. 長輩掃描報到 (支援條碼槍)")
    with c_msg:
        m_type, m_txt = st.session_state.checkin_msg
        if m_type == "error": st.error(m_txt)
        elif m_type == "success": st.success(m_txt)

    def process_checkin():
        pid = st.session_state.elder_pid.strip().upper()
        if not pid: return
        df_m, df_l = load_data("elderly_members"), load_data("elderly_logs")
        sel_date_str, sel_time_str = target_date.strftime("%Y-%m-%d"), target_time.strftime("%H:%M:%S")
        person = df_m[df_m['身分證字號'] == pid]
        if person.empty: st.session_state.checkin_msg = ("error", "❌ 查無此人")
        else:
            name = person.iloc[0]['姓名']
            if not df_l.empty and not df_l[(df_l['身分證字號'] == pid) & (df_l['日期'] == sel_date_str) & (df_l['課程名稱'] == final_course_name)].empty:
                st.session_state.checkin_msg = ("error", f"❌ 重複：{name} 今日已報到過此活動")
            else:
                new_log = {"姓名": name, "身分證字號": pid, "日期": sel_date_str, "時間": sel_time_str, "課程分類": final_course_cat, "課程名稱": final_course_name, "收縮壓": st.session_state.sbp_val, "舒張壓": st.session_state.dbp_val, "脈搏": st.session_state.pulse_val}
                if save_data(pd.concat([df_l, pd.DataFrame([new_log])], ignore_index=True), "elderly_logs"):
                    st.session_state.checkin_msg = ("success", f"✅ {name} 報到成功")
        st.session_state.elder_pid = ""

    cb1, cb2, cb3 = st.columns(3)
    with cb1: st.number_input("收縮壓", min_value=50, max_value=250, value=120, key="sbp_val")
    with cb2: st.number_input("舒張壓", min_value=30, max_value=150, value=80, key="dbp_val")
    with cb3: st.number_input("脈搏", min_value=30, max_value=200, value=72, key="pulse_val")
    st.text_input("身分證字號掃描區 (條碼槍請對準此處)", key="elder_pid", on_change=process_checkin)
    st.markdown('</div>', unsafe_allow_html=True)

    logs_view = load_data("elderly_logs")
    sel_date_str = target_date.strftime("%Y-%m-%d")
    date_mask = (logs_view['日期'] == sel_date_str)
    if not logs_view[date_mask].empty:
        st.markdown(f"### 📋 {sel_date_str} 報到名單管理")
        today_df = logs_view[date_mask].sort_values('時間', ascending=False)
        edited = st.data_editor(today_df, use_container_width=True, num_rows="dynamic", key="checkin_editor")
        if st.button("💾 儲存名單修改"):
            logs_view[date_mask] = edited
            if save_data(logs_view, "elderly_logs"): st.success("紀錄已更新！")

elif st.session_state.page == 'stats':
    render_nav()
    st.markdown("## 📊 統計數據")
    members, logs = load_data("elderly_members"), load_data("elderly_logs")
    if members.empty or logs.empty: st.info("尚無數據")
    else:
        logs['dt'] = pd.to_datetime(logs['日期'], errors='coerce')
        st.markdown('<div class="custom-card">', unsafe_allow_html=True)
        d_range = st.date_input("📅 選擇統計區間", value=(date(date.today().year, date.today().month, 1), date.today()))
        st.markdown('</div>', unsafe_allow_html=True)
        
        if isinstance(d_range, tuple) and len(d_range) == 2:
            f_logs = logs[(logs['dt'].dt.date >= d_range[0]) & (logs['dt'].dt.date <= d_range[1])].copy()
            tab_c, tab_h = st.tabs(["📚 課程成效分析", "🏥 長輩健康追蹤"])
            
            with tab_c:
                merged = f_logs.merge(members[['姓名', '性別']], on='姓名', how='left')
                m1, m2, m3 = st.columns(3)
                with m1: st.markdown(f"""<div class="dash-card"><div style="color:#888;">總參與人次</div><div style="font-size:1.8rem;color:{PRIMARY};font-weight:900;">{len(merged)} 次</div></div>""", unsafe_allow_html=True)
                with m2: st.markdown(f"""<div class="dash-card"><div style="color:#888;">男性參與</div><div style="font-size:1.8rem;color:{PRIMARY};font-weight:900;">{len(merged[merged['性別']=='男'])} 次</div></div>""", unsafe_allow_html=True)
                with m3: st.markdown(f"""<div class="dash-card"><div style="color:#888;">女性參與</div><div style="font-size:1.8rem;color:{PRIMARY};font-weight:900;">{len(merged[merged['性別']=='女'])} 次</div></div>""", unsafe_allow_html=True)
                
                unique_sessions = merged.drop_duplicates(subset=['日期', '課程名稱', '課程分類']).copy()
                unique_sessions['大分類'] = unique_sessions['課程分類'].apply(lambda x: x.split('-')[0] if '-' in x else x)
                unique_sessions['子分類'] = unique_sessions['課程分類'].apply(lambda x: x.split('-')[1] if '-' in x else x)

                st.markdown("### 2. 課程場次占比 (靈動泡泡圖)")
                main_cts = unique_sessions['大分類'].value_counts().reset_index()
                main_cts.columns = ['類別', '場次']
                
                random.seed(42) 
                main_cts['x_rnd'] = [random.uniform(0, 10) for _ in range(len(main_cts))]
                main_cts['y_rnd'] = [random.uniform(0, 10) for _ in range(len(main_cts))]
                main_cts['顯示標籤'] = main_cts['類別'] + '<br>' + main_cts['場次'].astype(str) + '場'
                
                fig_bubble = px.scatter(
                    main_cts, x="x_rnd", y="y_rnd", size="場次", color="類別", text="顯示標籤", size_max=100, 
                    color_discrete_sequence=px.colors.sequential.RdPu # 🔥 改為莫蘭迪粉紫色調
                )
                fig_bubble.update_traces(textposition='middle center', textfont=dict(size=14, color='white', family="Noto Sans TC"))
                fig_bubble.update_layout(
                    showlegend=False, height=450, 
                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, title=""),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, title=""),
                    plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                    margin=dict(t=20, b=20, l=20, r=20)
                )
                st.plotly_chart(fig_bubble, use_container_width=True)

                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("#### 大分類明細")
                    st.dataframe(main_cts[['類別', '場次']], use_container_width=True, column_config={"場次": st.column_config.ProgressColumn("場次", format="%d", min_value=0, max_value=int(main_cts['場次'].max() or 1))})
                with c2:
                    sc1, sc2 = st.columns([1.2, 2])
                    with sc1: st.markdown("#### 子分類鑽取")
                    with sc2: sel_m = st.selectbox("請選擇大分類", sorted(main_cts['類別'].unique()), label_visibility="collapsed", key="sel_main_stats")
                    sub_cts = unique_sessions[unique_sessions['大分類']==sel_m]['子分類'].value_counts().reset_index()
                    sub_cts.columns = ['子分類', '場次']
                    st.dataframe(sub_cts, use_container_width=True, column_config={"場次": st.column_config.ProgressColumn("場次", format="%d", min_value=0, max_value=int(sub_cts['場次'].max() or 1))})

            with tab_h:
                target_elder = st.selectbox("🔍 請選擇長輩查看趨勢", sorted(f_logs['姓名'].unique()), key="sel_elder_health")
                e_logs = f_logs[f_logs['姓名']==target_elder].sort_values('dt')
                e_logs['收縮壓'] = pd.to_numeric(e_logs['收縮壓'], errors='coerce')
                high_bp = len(e_logs[e_logs['收縮壓']>=140])
                st.markdown(f"""<div class="dash-card" style="border-left:6px solid #E91E63"><div style="color:#888;">血壓異常次數 (≥140)</div><div style="font-size:1.8rem;color:{PRIMARY};font-weight:900;">{high_bp} 次</div></div>""", unsafe_allow_html=True)
                fig = px.line(e_logs, x='dt', y=['收縮壓'], markers=True, title="收縮壓變化趨勢", color_discrete_sequence=[PRIMARY])
                fig.add_hline(y=140, line_dash="dash", line_color="#E91E63")
                st.plotly_chart(fig, use_container_width=True)
