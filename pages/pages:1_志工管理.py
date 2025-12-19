import streamlit as st
import pandas as pd
from datetime import datetime, date
import gspread
import time
import plotly.express as px

# --- 1. 🎨 視覺美學設定 (V5.1 高對比修正版) ---
st.set_page_config(page_title="志工管理系統", page_icon="💜", layout="wide")

# 視覺設計變數
PRIMARY_COLOR = "#673AB7"   # 主色：深紫
TEXT_COLOR = "#212121"      # 文字：深黑 (確保清晰)
BG_COLOR = "#F3E5F5"        # 背景：淺紫

st.markdown(f"""
    <style>
    /* 1. 強制全站字體顏色 (解決字體不清楚) */
    html, body, [class*="css"], .stMarkdown, .stText, p, div {{
        color: {TEXT_COLOR} !important;
        font-family: "Microsoft JhengHei", "微軟正黑體", sans-serif;
    }}
    
    /* 2. 背景設定 */
    .stApp {{
        background-color: #F8F9FA; /* 改用極淺灰白，讓閱讀更舒適 */
        background-image: linear-gradient(180deg, #F3E5F5 0%, #FFFFFF 100%); /* 頂部一點點紫 */
    }}
    
    /* 3. 輸入元件優化 (白底黑字 + 深色標籤) */
    .stTextInput label, .stSelectbox label, .stMultiSelect label, .stDateInput label, .stRadio label, .stTimeInput label {{
        color: {PRIMARY_COLOR} !important;
        font-weight: bold !important;
        font-size: 1.05rem !important;
    }}
    .stTextInput input, .stSelectbox div[data-baseweb="select"], .stDateInput input, .stTimeInput input {{
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border: 1px solid #9575CD !important;
        border-radius: 8px;
    }}
    
    /* 單選與複選框的選項文字 */
    .stRadio div[role="radiogroup"] label p, .stCheckbox label p {{
        color: #333333 !important;
        font-weight: 600 !important;
    }}

    /* 4. 提示框優化 (Info/Warning/Error) - 確保文字深色 */
    .stAlert div[data-testid="stMarkdownContainer"] p {{
        color: #000000 !important;
    }}

    /* 5. 卡片式按鈕 (首頁與篩選用) */
    .card-btn {{
        background-color: white;
        border: 2px solid {PRIMARY_COLOR};
        border-radius: 15px;
        padding: 20px;
        text-align: center;
        cursor: pointer;
        transition: all 0.3s;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        color: {PRIMARY_COLOR} !important;
        font-weight: bold;
    }}
    
    /* 6. 一般按鈕 (膠囊狀) */
    .stButton>button {{
        background: linear-gradient(135deg, {PRIMARY_COLOR} 0%, #512DA8 100%);
        color: white !important;
        border-radius: 50px;
        border: none;
        padding: 8px 25px;
        font-weight: bold;
        box-shadow: 0 4px 10px rgba(103, 58, 183, 0.2);
    }}
    .stButton>button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(103, 58, 183, 0.4);
    }}

    /* 7. 表格樣式 */
    .stDataFrame {{
        background-color: white;
        padding: 15px;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        border: 1px solid #E0E0E0;
    }}
    
    /* 標題樣式 */
    h1, h2, h3 {{
        color: {PRIMARY_COLOR} !important;
        font-weight: 800 !important;
    }}
    </style>
""", unsafe_allow_html=True)

# --- 2. 🔗 Google Sheets 連線 (效能優化版) ---
SHEET_ID = "1A3-VwCBYjnWdcEiL6VwbV5-UECcgX7TqKH94sKe8P90"

ALL_CATEGORIES = ['祥和志工', '關懷據點週二志工', '關懷據點週三志工', '環保志工', '臨時志工']
DEFAULT_ACTIVITIES = ['關懷據點週二活動', '關懷據點週三活動', '環保清潔', '專案活動', '教育訓練']
DISPLAY_ORDER = [
    '姓名', '身分證字號', '性別', '電話', '志工分類', '生日', '地址', '備註',
    '祥和_加入日期', '祥和_退出日期', 
    '據點週二_加入日期', '據點週二_退出日期',
    '據點週三_加入日期', '據點週三_退出日期', 
    '環保_加入日期', '環保_退出日期'
]

@st.cache_resource
def get_google_sheet_client():
    return gspread.service_account_from_dict(st.secrets["gcp_service_account"])

# 🔥 關鍵修正：加入 ttl=60 (快取 60 秒)，解決 API Error 429 問題
@st.cache_data(ttl=60)
def load_data_from_sheet(sheet_name):
    try:
        client = get_google_sheet_client()
        sheet = client.open_by_key(SHEET_ID).worksheet(sheet_name)
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        df = df.astype(str)
        if sheet_name == 'members':
            for c in DISPLAY_ORDER:
                if c not in df.columns: df[c] = ""
        elif sheet_name == 'logs':
            required = ['姓名', '身分證字號', '電話', '志工分類', '動作', '時間', '日期', '活動內容']
            for c in required:
                if c not in df.columns: df[c] = ""
        return df
    except Exception as e:
        # 如果真的出錯，顯示友善訊息
        st.warning(f"連線繁忙中，請稍候再試 ({e})")
        return pd.DataFrame()

def save_data_to_sheet(df, sheet_name):
    try:
        client = get_google_sheet_client()
        sheet = client.open_by_key(SHEET_ID).worksheet(sheet_name)
        sheet.clear()
        sheet.update([df.columns.values.tolist()] + df.values.tolist())
        
        # 🔥 關鍵：寫入資料後，馬上清除快取，這樣下次讀取才會是新的
        load_data_from_sheet.clear()
        
    except Exception as e:
        st.error(f"寫入失敗：{e}")

# --- 3. 🧮 邏輯運算 ---
def calculate_age(birthday_str):
    if not birthday_str or len(birthday_str) < 4: return 0
    try:
        b_date = None
        for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d", "%Y%m%d"]:
            try:
                b_date = datetime.strptime(birthday_str, fmt)
                break
            except: continue
        if b_date:
            today = date.today()
            age = today.year - b_date.year - ((today.month, today.day) < (b_date.month, b_date.day))
            return age
        else: return 0
    except: return 0

def check_is_fully_retired(row):
    roles = [('祥和_加入日期', '祥和_退出日期'), ('據點週二_加入日期', '據點週二_退出日期'),
             ('據點週三_加入日期', '據點週三_退出日期'), ('環保_加入日期', '環保_退出日期')]
    has_any_role = False
    is_active = False
    for join_col, exit_col in roles:
        if join_col in row and str(row[join_col]).strip() != "":
            has_any_role = True
            if not (exit_col in row and str(row[exit_col]).strip() != ""):
                is_active = True
    if not has_any_role: return False 
    return not is_active

# --- 4. 🖥️ UI 導航 ---
if 'page' not in st.session_state:
    st.session_state.page = 'home'

if st.session_state.page != 'home':
    # 導航列
    with st.container():
        c1, c2, c3, spacer = st.columns([1, 1, 1, 5])
        with c1:
            if st.button("🏠 首頁", use_container_width=True): st.session_state.page = 'home'; st.rerun()
        with c2:
            if st.button("⏰ 打卡", use_container_width=True): st.session_state.page = 'checkin'; st.rerun()
        with c3:
            if st.button("📊 報表", use_container_width=True): st.session_state.page = 'report'; st.rerun()
    st.markdown("<hr style='margin: 10px 0; border-top: 1px solid #D1C4E9;'>", unsafe_allow_html=True)

# === 🏠 首頁 ===
if st.session_state.page == 'home':
    st.markdown(f"<h1 style='text-align: center; margin-top: 40px;'>💜 福德里 - 志工管理系統</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; color: #555; font-weight:bold; margin-bottom: 50px;'>請選擇功能模組</p>", unsafe_allow_html=True)
    
    c_spacer_l, c1, c2, c3, c_spacer_r = st.columns([1, 2, 2, 2, 1])
    
    with c1:
        st.info("⚡️ 手機/電腦通用")
        if st.button("⏰ 智能打卡站", key="btn_h1", use_container_width=True):
            st.session_state.page = 'checkin'; st.rerun()
    with c2:
        st.info("📋 新增與修改資料")
        if st.button("📋 志工名冊管理", key="btn_h2", use_container_width=True):
            st.session_state.page = 'members'; st.rerun()
    with c3:
        st.info("📊 統計與分析")
        if st.button("📊 數據分析", key="btn_h3", use_container_width=True):
            st.session_state.page = 'report'; st.rerun()

# === ⏰ 打卡頁 ===
elif st.session_state.page == 'checkin':
    st.markdown("## ⏰ 智能打卡站")
    if 'scan_cooldowns' not in st.session_state: st.session_state['scan_cooldowns'] = {}
    
    tab1, tab2, tab3 = st.tabs(["⚡️ 快速打卡 (現場)", "🛠️ 補登作業 (批次/單筆)", "✏️ 出勤紀錄維護 (修改)"])
    
    # --- Tab 1: 現場掃描 ---
    with tab1:
        c_act, c_spacer = st.columns([1, 2])
        with c_act: 
            raw_act = st.selectbox("📌 選擇活動", DEFAULT_ACTIVITIES)
            final_act = raw_act
            if raw_act in ["專案活動", "教育訓練"]:
                note = st.text_input("📝 請輸入活動名稱", placeholder="例如：社區大掃除")
                if note: final_act = f"{raw_act}：{note}"

        def process_scan():
            pid = st.session_state.scan_box.strip().upper()
            if not pid: return
            now = datetime.now()
            last = st.session_state['scan_cooldowns'].get(pid)
            if last and (now - last).total_seconds() < 120:
                st.warning(f"⏳ 請勿重複刷卡 ({pid})"); st.session_state.scan_box = ""; return
            
            df_m = load_data_from_sheet("members")
            df_l = load_data_from_sheet("logs")
            if df_m.empty: st.error("❌ 無法讀取名單"); return
            
            person = df_m[df_m['身分證字號'] == pid]
            if not person.empty:
                row = person.iloc[0]
                name = row['姓名']
                if check_is_fully_retired(row): st.error(f"❌ {name} 已退出")
                else:
                    today = now.strftime("%Y-%m-%d")
                    t_logs = df_l[(df_l['身分證字號'] == pid) & (df_l['日期'] == today)]
                    action = "簽到"
                    if not t_logs.empty and t_logs.iloc[-1]['動作'] == "簽到": action = "簽退"
                    new_log = pd.DataFrame([{
                        '姓名': name, '身分證字號': pid, '電話': row['電話'], '志工分類': row['志工分類'],
                        '動作': action, '時間': now.strftime("%H:%M:%S"), '日期': today, '活動內容': final_act
                    }])
                    save_data_to_sheet(pd.concat([df_l, new_log], ignore_index=True), "logs")
                    st.session_state['scan_cooldowns'][pid] = now
                    st.success(f"✅ {name} {action} 成功！")
            else: st.error("❌ 查無此人")
            st.session_state.scan_box = ""

        st.text_input("請輸入身分證 (或掃描)", key="scan_box", on_change=process_scan)

    # --- Tab 2: 補登 ---
    with tab2:
        st.info("💡 此處可補登過去遺漏的紀錄")
        entry_mode = st.radio("補登模式", ["單筆補登", "整批補登 (多人)"], horizontal=True)
        
        df_m = load_data_from_sheet("members")
        if not df_m.empty:
            active_m = df_m[~df_m.apply(check_is_fully_retired, axis=1)]
            name_list = active_m['姓名'].tolist()
            
            with st.form("manual_entry_form"):
                c1, c2, c3, c4 = st.columns(4)
                d_date = c1.date_input("日期")
                d_time = c2.time_input("時間", value=datetime.now().time())
                d_action = c3.selectbox("動作", ["簽到", "簽退"])
                d_act = c4.selectbox("活動內容", DEFAULT_ACTIVITIES)
                
                target_names = []
                if entry_mode == "單筆補登":
                    sel = st.selectbox("選擇志工", name_list)
                    target_names = [sel]
                else:
                    target_names = st.multiselect("選擇多位志工", name_list)
                
                if st.form_submit_button("確認補登"):
                    if not target_names:
                        st.error("請至少選擇一位志工")
                    else:
                        logs = load_data_from_sheet("logs")
                        new_rows = []
                        for name in target_names:
                            row = df_m[df_m['姓名'] == name].iloc[0]
                            new_rows.append({
                                '姓名': name, '身分證字號': row['身分證字號'], '電話': row['電話'], 
                                '志工分類': row['志工分類'], '動作': d_action, 
                                '時間': d_time.strftime("%H:%M:%S"), '日期': d_date.strftime("%Y-%m-%d"), 
                                '活動內容': d_act
                            })
                        save_data_to_sheet(pd.concat([logs, pd.DataFrame(new_rows)], ignore_index=True), "logs")
                        st.success(f"已成功補登 {len(new_rows)} 筆資料！")
        else:
            st.warning("無法載入志工名單")

    # --- Tab 3: 維護 ---
    with tab3:
        st.warning("⚠️ 注意：此處修改將直接覆寫雲端資料庫")
        logs = load_data_from_sheet("logs")
        if not logs.empty:
            edited_logs = st.data_editor(logs, num_rows="dynamic", use_container_width=True)
            if st.button("💾 儲存修改 (出勤紀錄)"):
                save_data_to_sheet(edited_logs, "logs")
                st.success("✅ 出勤紀錄已更新！")

# === 📋 名冊頁 ===
elif st.session_state.page == 'members':
    st.markdown("## 📋 志工名冊管理")
    df = load_data_from_sheet("members")
    
    with st.expander("➕ 新增志工 (展開填寫)", expanded=True):
        with st.form("add_member_form"):
            c1, c2, c3 = st.columns(3)
            n = c1.text_input("姓名")
            p = c2.text_input("身分證字號")
            b = c3.text_input("生日 (YYYY-MM-DD)")
            c4, c5 = st.columns([2, 1])
            addr = c4.text_input("地址")
            ph = c5.text_input("電話")
            
            st.markdown("---")
            st.markdown("###### 志工分類與加入日期 (有勾選才填寫)")
            
            cats_selected = []
            col_d1, col_d2 = st.columns(2)
            
            is_xiang = col_d1.checkbox("祥和志工")
            d_xiang = col_d2.text_input("祥和加入日期 (YYYY-MM-DD)", value=str(date.today()) if is_xiang else "")
            
            is_tue = col_d1.checkbox("據點週二志工")
            d_tue = col_d2.text_input("週二加入日期", value=str(date.today()) if is_tue else "")
            
            is_wed = col_d1.checkbox("據點週三志工")
            d_wed = col_d2.text_input("週三加入日期", value=str(date.today()) if is_wed else "")
            
            is_env = col_d1.checkbox("環保志工")
            d_env = col_d2.text_input("環保加入日期", value=str(date.today()) if is_env else "")

            if st.form_submit_button("確認新增"):
                if not p: st.error("身分證必填");
                elif not df.empty and p in df['身分證字號'].values: st.error("身分證重複")
                else:
                    if is_xiang: cats_selected.append("祥和志工")
                    if is_tue: cats_selected.append("關懷據點週二志工")
                    if is_wed: cats_selected.append("關懷據點週三志工")
                    if is_env: cats_selected.append("環保志工")
                    
                    new_data = {
                        '姓名':n, '身分證字號':p, '生日':b, '電話':ph, '地址':addr, 
                        '志工分類':",".join(cats_selected),
                        '祥和_加入日期': d_xiang if is_xiang else "",
                        '據點週二_加入日期': d_tue if is_tue else "",
                        '據點週三_加入日期': d_wed if is_wed else "",
                        '環保_加入日期': d_env if is_env else ""
                    }
                    new = pd.DataFrame([new_data])
                    for c in DISPLAY_ORDER: 
                        if c not in new.columns: new[c] = ""
                    save_data_to_sheet(pd.concat([df, new], ignore_index=True), "members")
                    st.success("新增成功！"); time.sleep(1); st.rerun()

    if not df.empty:
        st.markdown("### 🔍 名單檢視")
        
        if 'view_mode' not in st.session_state: st.session_state.view_mode = 'active'
        
        col_btn1, col_btn2, spacer = st.columns([1, 1, 3])
        with col_btn1:
            if st.button("🟢 只看在職志工", use_container_width=True): st.session_state.view_mode = 'active'; st.rerun()
        with col_btn2:
            if st.button("📋 查看所有名單 (含退出)", use_container_width=True): st.session_state.view_mode = 'all'; st.rerun()
            
        df['狀態'] = df.apply(lambda row: '已退出' if check_is_fully_retired(row) else '在職', axis=1)
        df['年齡'] = df['生日'].apply(calculate_age)
        
        if st.session_state.view_mode == 'active':
            display_df = df[df['狀態'] == '在職']
            st.caption("目前顯示：🟢 在職志工")
        else:
            display_df = df
            st.caption("目前顯示：📋 所有歷史名單")
        
        special_cols = ['狀態', '姓名', '年齡', '電話', '地址', '志工分類']
        date_cols = [c for c in df.columns if '日期' in c]
        other_cols = [c for c in df.columns if c not in special_cols and c not in date_cols and c != '年齡' and c != '狀態']
        final_cols = special_cols + date_cols + other_cols
        final_cols = [c for c in final_cols if c in df.columns]
        
        st.data_editor(display_df[final_cols], use_container_width=True, num_rows="dynamic", key="member_editor")

# === 📊 報表頁 ===
elif st.session_state.page == 'report':
    st.markdown("## 📊 數據分析")
    
    logs = load_data_from_sheet("logs")
    members = load_data_from_sheet("members")
    
    st.markdown("### 📝 近期出勤紀錄")
    if logs.empty: st.info("尚無出勤資料")
    else: st.dataframe(logs, use_container_width=True, height=300)
        
    st.divider()
    
    st.markdown("### 🎂 志工年齡結構 (在職志工)")
    if members.empty: st.info("尚無志工資料")
    else:
        active_members = members[~members.apply(check_is_fully_retired, axis=1)]
        active_members['Calculated_Age'] = active_members['生日'].apply(calculate_age)
        valid_ages = active_members[active_members['Calculated_Age'] > 0]
        
        if valid_ages.empty:
            st.warning("⚠️ 無有效生日資料 (在職志工)，無法計算年齡。")
        else:
            cat_stats = []
            for cat in ALL_CATEGORIES:
                subset = valid_ages[valid_ages['志工分類'].astype(str).str.contains(cat, na=False)]
                if not subset.empty:
                    cat_stats.append({'志工類別': cat, '平均年齡': round(subset['Calculated_Age'].mean(), 1), '人數': len(subset)})
            
            if cat_stats:
                df_stats = pd.DataFrame(cat_stats)
                cols = st.columns(len(cat_stats))
                for idx, row in df_stats.iterrows():
                    with cols[idx]:
                        st.markdown(f"""
                        <div style="background:white; padding:15px; border-radius:10px; border:1px solid #D1C4E9; text-align:center; box-shadow:0 2px 5px rgba(0,0,0,0.05);">
                            <div style="color:#7E57C2; font-weight:bold;">{row['志工類別']}</div>
                            <div style="font-size:2rem; font-weight:900; color:#4527A0;">{row['平均年齡']} <span style="font-size:1rem;">歲</span></div>
                            <div style="color:#666; font-size:1.1rem; font-weight:bold;">共 {row['人數']} 人</div>
                        </div>
                        """, unsafe_allow_html=True)

            st.write("")
            
            bins = [0, 20, 30, 40, 50, 60, 70, 80, 90, 100]
            labels = ['20歲↓', '20-30', '30-40', '40-50', '50-60', '60-70', '70-80', '80-90', '90歲↑']
            valid_ages['Age_Group'] = pd.cut(valid_ages['Calculated_Age'], bins=bins, labels=labels, right=False)
            age_counts = valid_ages['Age_Group'].value_counts().sort_index().reset_index()
            age_counts.columns = ['年齡區間', '人數']
            
            fig = px.pie(
                age_counts, names='年齡區間', values='人數', hole=0.4,
                color_discrete_sequence=px.colors.sequential.Purples_r
            )
            fig.update_traces(textposition='outside', textinfo='label+percent+value')
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#333333', size=14),
                margin=dict(t=20, b=20, l=20, r=20),
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)
