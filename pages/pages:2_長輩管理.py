import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta, timezone
import gspread
import time
import os

# =========================================================
# 0) 系統設定
# =========================================================
st.set_page_config(
    page_title="關懷據點管理系統",
    page_icon="👴",
    layout="wide",
    initial_sidebar_state="collapsed",
)

TW_TZ = timezone(timedelta(hours=8))

# 配色變數 (維持您喜歡的紫色系，但稍微溫暖一點)
PRIMARY = "#4A148C"   
ACCENT  = "#8E24AA"   
BG_MAIN = "#F0F2F5"   
TEXT    = "#212121"   

# =========================================================
# 1) CSS 樣式 (沿用 V15.1 的完美設計)
# =========================================================
st.markdown(
    f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@500;700;900&display=swap');

/* 全域字體 */
html, body, [class*="css"], div, p, span, li, ul {{
    font-family: "Noto Sans TC", "Microsoft JhengHei", sans-serif;
    color: {TEXT} !important;
}}
.stApp {{ background-color: {BG_MAIN}; }}

/* 隱藏原生元素 */
[data-testid="stHeader"], [data-testid="stSidebar"], footer {{ display: none; }}
.block-container {{ padding-top: 1rem !important; max-width: 1250px; }}

/* 輸入框與下拉選單 */
.stTextInput input, .stDateInput input, .stTimeInput input, .stNumberInput input {{
    background-color: #FFFFFF !important;
    color: #000000 !important;
    border: 1px solid #9FA8DA !important;
    border-radius: 10px;
    font-weight: 700;
}}
div[data-baseweb="select"] > div {{
    background-color: #FFFFFF !important;
    color: #000000 !important;
    border-radius: 10px;
    border: 1px solid #9FA8DA !important;
}}
div[data-baseweb="select"] span {{ color: #000000 !important; }}
div[role="listbox"] ul {{ background-color: #FFFFFF !important; }}
div[role="option"] {{ color: #000000 !important; }}

label {{
    color: {PRIMARY} !important;
    font-weight: 900 !important;
    font-size: 1.05rem !important;
}}

/* 導航按鈕 */
div[data-testid="stButton"] > button {{
    width: 100%;
    background-color: white !important;
    color: {PRIMARY} !important;
    border: 2px solid {PRIMARY} !important;
    border-radius: 15px !important;
    font-weight: 900 !important;
    font-size: 1.1rem !important;
    padding: 12px 0 !important;
    box-shadow: 0 4px 0px rgba(74, 20, 140, 0.2);
    transition: all 0.1s;
}}
div[data-testid="stButton"] > button:hover {{
    transform: translateY(-2px);
    background-color: #F3E5F5 !important;
}}
div[data-testid="stButton"] > button:active {{ transform: translateY(2px); box-shadow: none; }}

/* 表單送出按鈕 */
div[data-testid="stFormSubmitButton"] > button {{
    background: linear-gradient(135deg, {PRIMARY}, {ACCENT}) !important;
    color: #FFFFFF !important;
    font-weight: 900 !important;
    font-size: 1.2rem !important;
    border: none !important;
    box-shadow: 0 4px 15px rgba(123, 31, 162, 0.3) !important;
}}
div[data-testid="stFormSubmitButton"] > button:hover {{
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(123, 31, 162, 0.5) !important;
}}

/* 卡片容器 */
div[data-testid="stForm"], div[data-testid="stDataFrame"], .streamlit-expanderContent, div[data-testid="stExpander"] details {{
    background-color: white;
    border-radius: 20px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.05);
    padding: 25px;
    margin-bottom: 20px;
    border: 1px solid white;
}}

/* 數據小卡 */
.dash-card {{
    background-color: white;
    padding: 15px;
    border-radius: 15px;
    border-left: 6px solid {ACCENT};
    box-shadow: 0 4px 10px rgba(0,0,0,0.05);
    margin-bottom: 10px;
}}
.dash-label {{ font-size: 1rem; color: #666 !important; font-weight: bold; }}
.dash-value {{ font-size: 1.8rem; color: {PRIMARY} !important; font-weight: 900; margin: 5px 0; }}
.dash-sub {{ font-size: 0.9rem; color: #888 !important; }}

/* 導航列容器 */
.nav-container {{
    background-color: white;
    padding: 15px;
    border-radius: 20px;
    margin-bottom: 20px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.05);
}}

/* Pills 選項樣式 */
div[data-testid="stRadio"] label {{
    background-color: white;
    border: 1px solid #ddd;
    padding: 10px 20px;
    border-radius: 20px;
    margin-right: 10px;
    cursor: pointer;
    font-weight: bold;
    color: {TEXT} !important;
    transition: all 0.2s;
}}
div[data-testid="stRadio"] label:hover {{
    border-color: {PRIMARY};
    color: {PRIMARY} !important;
}}

</style>
""", unsafe_allow_html=True)

# =========================================================
# 2) Google Sheets & Logic
# =========================================================
SHEET_ID = "1A3-VwCBYjnWdcEiL6VwbV5-UECcgX7TqKH94sKe8P90"

# 欄位定義
M_COLS = ["姓名", "身分證字號", "性別", "出生年月日", "電話", "地址", "備註", "加入日期"]
L_COLS = ["姓名", "身分證字號", "日期", "時間", "課程分類", "課程名稱", "收縮壓", "舒張壓", "脈搏"]

# 🔥 V16.1 客製化：里長專屬課程大分類與子分類
COURSE_HIERARCHY = {
    "手作": ["藝術手作", "生活用品"],
    "講座": ["消防", "反詐", "道路安全", "環境", "心靈成長", "家庭關係", "健康"],
    "外出": ["觀摩", "出遊"],
    "延緩失能": ["手作", "料理", "運動", "健康講座"],
    "運動": ["有氧", "毛巾操", "其他運動"],
    "園藝療癒": ["手作"],
    "烹飪": ["甜品", "鹹食", "醃漬品"],
    "歌唱": ["歡唱"]
}

@st.cache_resource
def get_google_sheet_client():
    return gspread.service_account_from_dict(st.secrets["gcp_service_account"])

@st.cache_data(ttl=60)
def load_data(sheet_name):
    try:
        client = get_google_sheet_client()
        sheet = client.open_by_key(SHEET_ID).worksheet(sheet_name)
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        df = df.astype(str)
        
        target_cols = M_COLS if sheet_name == 'elderly_members' else L_COLS
        if df.empty:
            df = pd.DataFrame(columns=target_cols)
        else:
            for c in target_cols:
                if c not in df.columns: df[c] = ""
        return df
    except: return pd.DataFrame(columns=M_COLS if sheet_name == 'elderly_members' else L_COLS)

def save_data(df, sheet_name):
    try:
        client = get_google_sheet_client()
        sheet = client.open_by_key(SHEET_ID).worksheet(sheet_name)
        sheet.clear()
        sheet.update([df.columns.values.tolist()] + df.values.tolist())
        load_data.clear()
    except Exception as e: st.error(f"寫入失敗：{e}")

def get_tw_time():
    return datetime.now(TW_TZ)

def calculate_age(dob_str):
    if not dob_str or len(str(dob_str)) < 4: return 0
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
        if st.button("🏠 首頁概況", use_container_width=True): st.session_state.page = 'home'; st.rerun()
    with c2:
        if st.button("📋 長輩名冊", use_container_width=True): st.session_state.page = 'members'; st.rerun()
    with c3:
        if st.button("🩸 據點報到", use_container_width=True): st.session_state.page = 'checkin'; st.rerun()
    with c4:
        if st.button("📊 統計數據", use_container_width=True): st.session_state.page = 'stats'; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# =========================================================
# 4) Page: Home (首頁)
# =========================================================
if st.session_state.page == 'home':
    st.markdown(f"<h1 style='text-align: center; color: {PRIMARY}; margin-bottom: 30px; margin-top: 20px;'>福德里 - 關懷據點長輩管理系統</h1>", unsafe_allow_html=True)
    
    # 快速入口
    col_l, c1, c2, c3, col_r = st.columns([1.5, 2, 2, 2, 0.5])
    with c1:
        st.info("📋 建立與管理長輩資料")
        if st.button("長輩名冊", key="h_m"): st.session_state.page = 'members'; st.rerun()
    with c2:
        st.info("🩸 課程報到與量血壓")
        if st.button("據點報到", key="h_c"): st.session_state.page = 'checkin'; st.rerun()
    with c3:
        st.info("📊 出勤與健康統計")
        if st.button("統計數據", key="h_s"): st.session_state.page = 'stats'; st.rerun()

    st.markdown("---")
    
    # 今日概況
    logs = load_data("elderly_logs")
    today_str = get_tw_time().strftime("%Y-%m-%d")
    
    today_count = 0
    if not logs.empty:
        today_count = len(logs[logs['日期'] == today_str])
    
    st.markdown(f"### 📅 今日據點即時看板 ({today_str})")
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #4A148C 0%, #7B1FA2 100%); padding: 30px; border-radius: 20px; color: white; text-align: center; margin-bottom: 25px; box-shadow: 0 10px 25px rgba(74, 20, 140, 0.25);">
        <div style="font-size: 1.2rem; opacity: 0.9; color: white !important;">今日服務長輩人次</div>
        <div style="font-size: 4rem; font-weight: 900; margin: 10px 0; color: white !important;">
            {today_count} <span style="font-size: 1.5rem; color: white !important;">人</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# =========================================================
# 5) Page: Members (長輩名冊)
# =========================================================
elif st.session_state.page == 'members':
    render_nav()
    st.markdown("## 📋 長輩名冊管理")
    df = load_data("elderly_members")
    
    with st.expander("➕ 新增長輩資料", expanded=True):
        with st.form("add_elder"):
            c1, c2, c3 = st.columns(3)
            name = c1.text_input("姓名")
            pid = c2.text_input("身分證字號")
            gender = c3.selectbox("性別", ["男", "女"])
            
            c4, c5 = st.columns([1, 2])
            dob = c4.date_input("出生年月日", value=date(1950, 1, 1), min_value=date(1900, 1, 1))
            phone = c5.text_input("電話")
            
            addr = st.text_input("地址")
            note = st.text_input("備註 (例如：過敏史、緊急聯絡人)")
            
            if st.form_submit_button("確認新增"):
                if not pid or not name:
                    st.error("姓名與身分證字號為必填")
                elif not df.empty and pid.upper() in df['身分證字號'].values:
                    st.error("此身分證已存在")
                else:
                    new_row = {
                        "姓名": name, "身分證字號": pid.upper(), "性別": gender,
                        "出生年月日": str(dob), "電話": phone, "地址": addr,
                        "備註": note, "加入日期": str(date.today())
                    }
                    new_df = pd.DataFrame([new_row])
                    save_data(pd.concat([df, new_df], ignore_index=True), "elderly_members")
                    st.success(f"已新增長輩：{name}")
                    time.sleep(1); st.rerun()
    
    st.write("")
    if not df.empty:
        # 計算年齡
        df['年齡'] = df['出生年月日'].apply(calculate_age)
        
        # 調整欄位順序
        view_cols = ["姓名", "性別", "年齡", "電話", "地址", "身分證字號", "出生年月日", "備註"]
        st.markdown("### 🔍 名冊列表")
        st.data_editor(df[view_cols], use_container_width=True, num_rows="dynamic", key="elder_editor")

# =========================================================
# 6) Page: Checkin (據點報到)
# =========================================================
# 1. 課程設定 (全域) - V16.0 升級為大分類+子分類
    st.markdown('<div class="dash-card" style="border-left: 6px solid #FF9800;">', unsafe_allow_html=True)
    st.markdown("#### 1. 今日課程設定")
    
    # 改為三個欄位：大分類 | 子分類 | 課程名稱
    c_main, c_sub, c_name = st.columns([1, 1, 1.5])
    
    with c_main:
        # 選擇大分類
        main_cat = st.selectbox("課程大分類", list(COURSE_HIERARCHY.keys()))
    
    with c_sub:
        # 根據大分類，連動顯示子分類
        sub_list = COURSE_HIERARCHY[main_cat]
        sub_cat = st.selectbox("課程子分類", sub_list)
        
    with c_name:
        course_name = st.text_input("課程名稱 (選填說明)", placeholder="例如：端午節香包製作")
        
    # 自動組合成最終的分類字串，例如 "社會參與-手工藝創作"
    final_course_cat = f"{main_cat}-{sub_cat}"
    
    # 如果有填寫課程名稱，就用課程名稱；如果沒填，就預設用子分類當作名稱，方便志工
    final_course_name = course_name if course_name.strip() else sub_cat
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 2. 報到區
    st.markdown('<div class="dash-card">', unsafe_allow_html=True)
    st.markdown("#### 2. 長輩刷卡/輸入")
    
    def process_checkin():
        pid = st.session_state.elder_pid.strip().upper()
        if not pid: return
        
        # 這裡不需要再檢查 course_name 是否必填，因為我們上面有做預設值防呆
        
        df_m = load_data("elderly_members")
        df_l = load_data("elderly_logs")
        
        person = df_m[df_m['身分證字號'] == pid]
        
        if person.empty:
            st.error("❌ 查無此人，請先至名冊新增。")
        else:
            name = person.iloc[0]['姓名']
            now = get_tw_time()
            
            # 寫入紀錄
            new_log = {
                "姓名": name, "身分證字號": pid,
                "日期": now.strftime("%Y-%m-%d"), "時間": now.strftime("%H:%M:%S"),
                "課程分類": final_course_cat,   # 存入組合後的分類 (例如: 健康促進-肌力強化)
                "課程名稱": final_course_name,  # 存入名稱
                "收縮壓": st.session_state.sbp_val,
                "舒張壓": st.session_state.dbp_val,
                "脈搏": st.session_state.pulse_val
            }
            save_data(pd.concat([df_l, pd.DataFrame([new_log])], ignore_index=True), "elderly_logs")
            st.success(f"✅ {name} 報到成功！({final_course_cat})")
            
        # 清空
        st.session_state.elder_pid = ""
        # 血壓歸零
        st.session_state.sbp_val = 120
        st.session_state.dbp_val = 80
        st.session_state.pulse_val = 72

    # 血壓輸入 (使用 Number Input 或 Slider，這裡用 Number Input 較精準)
    c_bp1, c_bp2, c_bp3 = st.columns(3)
    with c_bp1:
        st.number_input("收縮壓 (高壓)", min_value=50, max_value=250, value=120, key="sbp_val")
    with c_bp2:
        st.number_input("舒張壓 (低壓)", min_value=30, max_value=150, value=80, key="dbp_val")
    with c_bp3:
        st.number_input("脈搏", min_value=30, max_value=200, value=72, key="pulse_val")
        
    st.text_input("請輸入長輩身分證 (Enter 報到)", key="elder_pid", on_change=process_checkin)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 顯示今日報到列表
    st.write("📋 今日已報到名單：")
    logs = load_data("elderly_logs")
    today = get_tw_time().strftime("%Y-%m-%d")
    if not logs.empty:
        today_logs = logs[logs['日期'] == today]
        st.dataframe(today_logs[['時間', '姓名', '課程名稱', '收縮壓', '舒張壓']], use_container_width=True)

# =========================================================
# 7) Page: Stats (統計數據)
# =========================================================
elif st.session_state.page == 'stats':
    render_nav()
    st.markdown("## 📊 統計數據")
    
    members = load_data("elderly_members")
    logs = load_data("elderly_logs")
    
    if members.empty:
        st.info("尚無長輩資料")
    else:
        # 計算基本資料
        members['年齡'] = members['出生年月日'].apply(calculate_age)
        avg_age = round(members['年齡'].mean(), 1)
        male_count = len(members[members['性別'] == '男'])
        female_count = len(members[members['性別'] == '女'])
        
        # 1. 人口結構卡片
        st.markdown("### 👥 長輩結構")
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f"""<div class="dash-card"><div class="dash-label">平均年齡</div><div class="dash-value">{avg_age} <span style="font-size:1rem;">歲</span></div></div>""", unsafe_allow_html=True)
        with c2: st.markdown(f"""<div class="dash-card"><div class="dash-label">男性長輩</div><div class="dash-value">{male_count} <span style="font-size:1rem;">人</span></div></div>""", unsafe_allow_html=True)
        with c3: st.markdown(f"""<div class="dash-card"><div class="dash-label">女性長輩</div><div class="dash-value">{female_count} <span style="font-size:1rem;">人</span></div></div>""", unsafe_allow_html=True)
        
        st.markdown("---")
        
        # 2. 全勤與參與統計
        st.markdown("### 🏆 參與度分析 (全勤統計)")
        
        # 日期區間選擇
        st.markdown('<div style="background:white; padding:20px; border-radius:15px; border:1px solid #ddd; margin-bottom:20px;">', unsafe_allow_html=True)
        d_range = st.date_input("📅 選擇統計區間", value=(date(date.today().year, date.today().month, 1), date.today()))
        st.markdown('</div>', unsafe_allow_html=True)
        
        if not logs.empty and isinstance(d_range, tuple) and len(d_range) == 2:
            start_d, end_d = d_range
            # 轉換 logs 日期格式進行比對
            logs['dt'] = pd.to_datetime(logs['日期'], errors='coerce').dt.date
            mask = (logs['dt'] >= start_d) & (logs['dt'] <= end_d)
            period_logs = logs[mask]
            
            if period_logs.empty:
                st.warning("此區間無上課紀錄")
            else:
                # 找出這段時間內，據點有開課的「所有日期」(Unique Dates)
                course_dates = sorted(period_logs['dt'].unique())
                total_course_days = len(course_dates)
                
                st.write(f"期間共有 **{total_course_days}** 天有課程活動。")
                
                # 計算每位長輩的出席天數
                attendance = period_logs.groupby('姓名')['dt'].nunique().reset_index()
                attendance.columns = ['姓名', '出席天數']
                
                # 找出全勤者 (出席天數 == 總開課天數)
                perfect_attendance = attendance[attendance['出席天數'] == total_course_days]
                
                c_full, c_list = st.columns([1, 2])
                with c_full:
                    st.markdown(f"""<div class="dash-card" style="border-left: 6px solid #4CAF50;"><div class="dash-label">全勤人數</div><div class="dash-value">{len(perfect_attendance)} <span style="font-size:1rem;">人</span></div></div>""", unsafe_allow_html=True)
                    if not perfect_attendance.empty:
                        st.success(f"🏅 全勤名單：{', '.join(perfect_attendance['姓名'].tolist())}")
                
                with c_list:
                    st.markdown("##### 📋 出席統計表")
                    # 合併顯示性別與年齡
                    merge_df = attendance.merge(members[['姓名', '性別', '年齡']], on='姓名', how='left')
                    st.dataframe(merge_df.sort_values('出席天數', ascending=False), use_container_width=True)
