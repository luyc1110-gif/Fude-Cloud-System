import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta, timezone
import gspread
import time
import plotly.express as px
import os

# =========================================================
# 0) App Config
# =========================================================
st.set_page_config(
    page_title="志工管理系統",
    page_icon="💜",
    layout="wide",
    initial_sidebar_state="collapsed",
)

TW_TZ = timezone(timedelta(hours=8))

PRIMARY = "#4A148C"   # 尊爵紫
ACCENT  = "#7B1FA2"   # 亮紫
BG_MAIN = "#F0F2F5"   # 灰藍底
TEXT    = "#212121"
MUTED   = "#666666"
CARD_BG = "#FFFFFF"

# =========================================================
# 1) Styles (V13.0 沉浸式去黑條版)
# =========================================================
st.markdown(
    f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@500;700;900&display=swap');

:root {{
  --primary: {PRIMARY};
  --accent: {ACCENT};
  --bg: {BG_MAIN};
  --text: {TEXT};
  --muted: {MUTED};
  --card: {CARD_BG};
}}

.stApp {{ background: var(--bg); }}

/* 🔥 1. 斬除黑條與白邊 (讓畫面置頂) */
[data-testid="stHeader"] {{
    display: none; /* 隱藏上方黑條選單 */
}}
.block-container {{
    padding-top: 1rem !important; /* 縮小上方留白 */
    padding-bottom: 2rem;
    max-width: 1250px;
}}
[data-testid="stSidebar"] {{ display: none; }} /* 隱藏側邊欄 */

/* 全域字體 */
html, body, [data-testid="stAppViewContainer"] * {{
  font-family: "Noto Sans TC","Microsoft JhengHei","微軟正黑體",sans-serif;
  color: var(--text);
}}

/* 還原 Material Icons */
.material-icons, .material-icons-outlined, span[translate="no"] {{
  font-family: "Material Icons" !important;
}}

/* ===== Top Bar ===== */
.topbar {{
  background: rgba(255,255,255,0.95);
  border: 1px solid rgba(255,255,255,0.8);
  border-radius: 99px;
  padding: 10px 20px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.05);
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
  position: sticky;
  top: 10px; /* 懸浮位置 */
  z-index: 999;
}}
.brand {{ display: flex; align-items: center; gap: 12px; }}
.brand-badge {{
  width: 40px; height: 40px; border-radius: 50%;
  background: linear-gradient(135deg, var(--accent), var(--primary));
  color: white; font-size: 20px; display: grid; place-items: center;
}}
.brand-title {{ font-weight: 900; font-size: 1.1rem; }}
.brand-sub {{ font-size: 0.85rem; color: var(--muted); }}

/* ===== 志工分類選擇卡 (Category Card) ===== */
.cat-card {{
    background-color: white;
    border: 1px solid #E0E0E0;
    border-radius: 16px;
    padding: 15px;
    text-align: center;
    transition: all 0.2s;
    height: 100%;
    box-shadow: 0 2px 5px rgba(0,0,0,0.02);
}}
.cat-card:hover {{
    border-color: var(--primary);
    box-shadow: 0 4px 12px rgba(74, 20, 140, 0.1);
    transform: translateY(-2px);
}}
.cat-title {{
    font-weight: 900;
    color: var(--primary);
    margin-bottom: 10px;
    font-size: 1.1rem;
}}

/* ===== 萬物皆卡片 (Forms, Expanders, Dataframes) ===== */
div[data-testid="stForm"], div[data-testid="stDataFrame"], .streamlit-expanderContent, div[data-testid="stExpander"] details {{
    background-color: white;
    border-radius: 20px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.05);
    border: 1px solid white;
    padding: 25px;
    margin-bottom: 20px;
}}

/* ===== 按鈕美化 ===== */
/* 一般導航按鈕 */
div[data-testid="stButton"] > button {{
  width: 100%;
  border-radius: 99px !important;
  border: 1.5px solid rgba(74, 20, 140, 0.2) !important;
  background: white !important;
  color: var(--primary) !important;
  font-weight: 900 !important;
  box-shadow: 0 4px 10px rgba(0,0,0,0.05);
  transition: all 0.2s;
}}
div[data-testid="stButton"] > button:hover {{
  background: #F3E5F5 !important;
  transform: translateY(-2px);
}}

/* 表單送出按鈕 (紫色實心) */
div[data-testid="stFormSubmitButton"] > button {{
  background: linear-gradient(135deg, var(--accent), var(--primary)) !important;
  color: white !important;
  border: none !important;
  box-shadow: 0 8px 20px rgba(74, 20, 140, 0.3) !important;
}}
div[data-testid="stFormSubmitButton"] > button:hover {{
  transform: translateY(-2px);
  box-shadow: 0 12px 25px rgba(74, 20, 140, 0.4) !important;
}}

/* 輸入框美化 (白底黑字) */
.stTextInput input, .stSelectbox div[data-baseweb="select"], .stDateInput input, .stTimeInput input {{
    background-color: #FFFFFF !important;
    color: #000000 !important;
    border: 1px solid #BDBDBD !important;
    border-radius: 10px;
}}
label {{ color: var(--primary) !important; font-weight: bold !important; }}

/* 首頁的大卡片 Tile (保持V12不變) */
.tile {{
  background: white;
  border-radius: 26px;
  padding: 20px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.08);
  border: 1px solid rgba(255,255,255,0.8);
  text-align: center;
}}
.tile-icon {{
  display: flex; justify-content: center; align-items: flex-end;
  height: 110px; margin-bottom: 10px;
}}
.tile-title {{
  font-weight: 900; font-size: 1.3rem; color: var(--primary);
  margin-bottom: 10px;
}}

/* 戰情室小卡 */
.stat {{
  background: white; border-radius: 18px; padding: 16px;
  border-left: 6px solid var(--accent);
  box-shadow: 0 4px 15px rgba(0,0,0,0.05);
}}
.stat-label {{ font-size: 0.9rem; color: var(--muted); font-weight: bold; }}
.stat-value {{ font-size: 2rem; font-weight: 900; color: var(--primary); }}
.stat-sub {{ font-size: 0.85rem; color: #888; }}

/* 隱藏預設 Footer */
footer {{ visibility: hidden; }}
</style>
""",
    unsafe_allow_html=True,
)

# =========================================================
# 2) Helpers (UI)
# =========================================================
def spacer(h=14):
    st.markdown(f"<div style='height:{h}px'></div>", unsafe_allow_html=True)

def card_open(title=None, subtitle=None):
    # 用 HTML 模擬卡片開頭，這裡主要靠 CSS 的 div[data-testid="stExpander"] 等控制
    # 為了保持結構簡單，我們在 st.form / st.expander 標題裡直接寫
    pass 

def topbar(page_name: str):
    st.markdown(
        f"""
<div class="topbar">
  <div class="brand">
    <div class="brand-badge">💜</div>
    <div>
      <div class="brand-title">福德里 志工管理系統</div>
      <div class="brand-sub">{page_name}</div>
    </div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

# =========================================================
# 3) Google Sheets
# =========================================================
SHEET_ID = "1A3-VwCBYjnWdcEiL6VwbV5-UECcgX7TqKH94sKe8P90"

ALL_CATEGORIES = ["祥和志工", "關懷據點週二志工", "關懷據點週三志工", "環保志工", "臨時志工"]
DEFAULT_ACTIVITIES = ["關懷據點週二活動", "關懷據點週三活動", "環保清潔", "專案活動", "教育訓練"]

DISPLAY_ORDER = [
    "姓名", "身分證字號", "性別", "電話", "志工分類", "生日", "地址", "備註",
    "祥和_加入日期", "祥和_退出日期",
    "據點週二_加入日期", "據點週二_退出日期",
    "據點週三_加入日期", "據點週三_退出日期",
    "環保_加入日期", "環保_退出日期",
]

@st.cache_resource
def get_google_sheet_client():
    return gspread.service_account_from_dict(st.secrets["gcp_service_account"])

@st.cache_data(ttl=60)
def load_data_from_sheet(sheet_name: str) -> pd.DataFrame:
    try:
        client = get_google_sheet_client()
        sheet = client.open_by_key(SHEET_ID).worksheet(sheet_name)
        data = sheet.get_all_records()
        df = pd.DataFrame(data)

        if df.empty:
            if sheet_name == "members":
                df = pd.DataFrame(columns=DISPLAY_ORDER)
            elif sheet_name == "logs":
                df = pd.DataFrame(columns=["姓名", "身分證字號", "電話", "志工分類", "動作", "時間", "日期", "活動內容"])
            return df

        df = df.astype(str)

        if sheet_name == "members":
            for c in DISPLAY_ORDER:
                if c not in df.columns:
                    df[c] = ""
        elif sheet_name == "logs":
            required = ["姓名", "身分證字號", "電話", "志工分類", "動作", "時間", "日期", "活動內容"]
            for c in required:
                if c not in df.columns:
                    df[c] = ""

        return df
    except Exception:
        return pd.DataFrame()

def save_data_to_sheet(df: pd.DataFrame, sheet_name: str):
    try:
        client = get_google_sheet_client()
        sheet = client.open_by_key(SHEET_ID).worksheet(sheet_name)
        sheet.clear()
        df2 = df.copy().fillna("").astype(str)
        sheet.update([df2.columns.values.tolist()] + df2.values.tolist())
        load_data_from_sheet.clear()
        st.toast("✅ 已儲存", icon="✅")
    except Exception as e:
        st.error(f"寫入失敗：{e}")

# =========================================================
# 4) Logic
# =========================================================
def get_tw_time():
    return datetime.now(TW_TZ)

def parse_date_any(s: str):
    if not s or str(s).strip() == "":
        return None
    s = str(s).strip()
    for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d", "%Y%m%d"]:
        try:
            return datetime.strptime(s, fmt).date()
        except Exception:
            pass
    return None

def calculate_age(birthday_str: str) -> int:
    b = parse_date_any(birthday_str)
    if not b:
        return 0
    today = date.today()
    return today.year - b.year - ((today.month, today.day) < (b.month, b.day))

def check_is_fully_retired(row: pd.Series) -> bool:
    roles = [
        ("祥和_加入日期", "祥和_退出日期"),
        ("據點週二_加入日期", "據點週二_退出日期"),
        ("據點週三_加入日期", "據點週三_退出日期"),
        ("環保_加入日期", "環保_退出日期"),
    ]
    has_any_role = False
    is_active = False
    for join_col, exit_col in roles:
        join_val = str(row.get(join_col, "")).strip()
        exit_val = str(row.get(exit_col, "")).strip()
        if join_val != "":
            has_any_role = True
            if exit_val == "":
                is_active = True
    if not has_any_role:
        return False
    return not is_active

def build_sessions(logs_df: pd.DataFrame) -> pd.DataFrame:
    if logs_df.empty:
        return pd.DataFrame(columns=["姓名", "身分證字號", "日期", "活動內容", "start", "end", "seconds"])

    df = logs_df.copy()
    df["dt"] = pd.to_datetime(df["日期"].astype(str) + " " + df["時間"].astype(str), errors="coerce")
    df = df.dropna(subset=["dt"]).sort_values(["姓名", "日期", "dt"])

    sessions = []
    for (name, d), g in df.groupby(["姓名", "日期"], dropna=False):
        actions = g["動作"].astype(str).tolist()
        dts = g["dt"].tolist()
        acts = g["活動內容"].astype(str).tolist()
        pids = g["身分證字號"].astype(str).tolist()

        i = 0
        while i < len(actions):
            if actions[i] == "簽到":
                j = i + 1
                while j < len(actions) and actions[j] != "簽退":
                    j += 1
                if j < len(actions) and actions[j] == "簽退":
                    sec = (dts[j] - dts[i]).total_seconds()
                    if sec > 0:
                        sessions.append({
                            "姓名": name,
                            "身分證字號": pids[i],
                            "日期": d,
                            "活動內容": acts[i] if acts[i] else acts[j],
                            "start": dts[i],
                            "end": dts[j],
                            "seconds": sec,
                        })
                    i = j + 1
                else:
                    i += 1
            else:
                i += 1

    return pd.DataFrame(sessions)

def seconds_to_hm(total_seconds: float):
    total_seconds = int(total_seconds or 0)
    h = total_seconds // 3600
    m = (total_seconds % 3600) // 60
    return h, m

# =========================================================
# 5) Navigation State
# =========================================================
if "page" not in st.session_state:
    st.session_state.page = "home"

def goto(page_key: str):
    st.session_state.page = page_key
    st.rerun()

def render_nav():
    page_map = {
        "home": "🏠 首頁",
        "checkin": "⏰ 打卡站",
        "members": "📋 志工名冊",
        "report": "📊 報表分析",
    }
    topbar(page_map.get(st.session_state.page, ""))
    
    # 導航列
    cols = st.columns([1.2, 1.2, 1.2, 1.2, 4.2])
    with cols[0]:
        if st.button("🏠 首頁", use_container_width=True): goto("home")
    with cols[1]:
        if st.button("⏰ 打卡站", use_container_width=True): goto("checkin")
    with cols[2]:
        if st.button("📋 志工名冊", use_container_width=True): goto("members")
    with cols[3]:
        if st.button("📊 報表分析", use_container_width=True): goto("report")

    spacer(14)

# =========================================================
# 6) HOME
# =========================================================
def page_home():
    # 首頁不顯示 topbar，因為中間有大標題
    # 這裡放一點 padding 把內容壓下來，因為 header 隱藏了
    spacer(30)
    
    st.markdown(
        f"""
<div style="text-align:center; margin-top: 10px;">
  <div style="font-size: 2.5rem; font-weight: 900; color: {PRIMARY}; letter-spacing: 1px;">福德里 - 志工管理系統</div>
  <div style="color: {MUTED}; margin-top: 8px; font-weight: 700; font-size: 1.1rem;">打卡、名冊、報表，一套搞定。</div>
</div>
""",
        unsafe_allow_html=True,
    )
    spacer(30)

    col_spacer_l, c1, c2, c3, col_spacer_r = st.columns([1.5, 2, 2, 2, 0.5])

    def tile(icon_path, emoji_fallback, title, btn_text, btn_key, target_page):
        st.markdown("<div class='tile'>", unsafe_allow_html=True)
        st.markdown("<div class='tile-icon'>", unsafe_allow_html=True)
        if icon_path and os.path.exists(icon_path):
            st.image(icon_path, width=120)
        else:
            st.markdown(f"<div style='font-size:86px; line-height:1;'>{emoji_fallback}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        # st.markdown(f"<div class='tile-title'>{title}</div>", unsafe_allow_html=True)
        
        if st.button(title, key=btn_key): # 直接用大卡片按鈕顯示標題
            goto(target_page)
        st.markdown("</div>", unsafe_allow_html=True)

    with c1:
        tile("icon_checkin.png", "⏰", "智能打卡站", "進入打卡", "home_btn_checkin", "checkin")
    with c2:
        tile("icon_members.png", "📋", "志工名冊", "進入名冊", "home_btn_members", "members")
    with c3:
        tile("icon_report.png", "📊", "數據分析", "進入報表", "home_btn_report", "report")

    spacer(30)

    logs = load_data_from_sheet("logs")
    members = load_data_from_sheet("members")

    this_year = datetime.now().year
    sessions = build_sessions(logs)
    total_sec = 0
    if not sessions.empty:
        sessions["year"] = pd.to_datetime(sessions["start"]).dt.year
        y = sessions[sessions["year"] == this_year]
        total_sec = y["seconds"].sum()

    total_h, total_m = seconds_to_hm(total_sec)

    # 戰情大看板
    st.markdown(f"### 📊 {this_year} 年度即時概況")
    st.markdown(
        f"""
<div style="padding: 30px; border-radius: 20px; background: linear-gradient(135deg, #7E57C2 0%, #512DA8 100%); color: white; text-align:center; box-shadow: 0 10px 25px rgba(81,45,168,0.2);">
  <div style="opacity:0.9; font-weight: 900; font-size: 1.1rem; margin-bottom: 5px;">📅 {this_year} 年度 - 全體志工總服務時數</div>
  <div style="font-size: 3.5rem; font-weight: 900; line-height: 1;">
    {total_h}<span style="font-size:1.5rem; margin:0 10px;">小時</span>
    {total_m}<span style="font-size:1.5rem;">分</span>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    if members.empty:
        return

    dfm = members.copy()
    dfm["狀態"] = dfm.apply(lambda r: "已退出" if check_is_fully_retired(r) else "在職", axis=1)
    active_m = dfm[dfm["狀態"] == "在職"].copy()
    active_m["年齡"] = active_m["生日"].apply(calculate_age)
    valid_age = active_m[active_m["年齡"] > 0].copy()

    spacer(14)
    
    cols = st.columns(4)
    idx = 0
    for cat in ALL_CATEGORIES:
        if cat == "臨時志工": continue
        
        subset = active_m[active_m["志工分類"].astype(str).str.contains(cat, na=False)]
        age_subset = valid_age[valid_age["志工分類"].astype(str).str.contains(cat, na=False)]
        count = len(subset)
        avg_age = round(age_subset["年齡"].mean(), 1) if not age_subset.empty else 0

        with cols[idx % 4]:
            st.markdown(
                f"""
<div class="stat">
  <div class="stat-label">{cat.replace('志工','')}</div>
  <div class="stat-value">{count}<span style="font-size:1rem; color:#888; font-weight:900;"> 人</span></div>
  <div class="stat-sub">平均 {avg_age} 歲</div>
</div>
""",
                unsafe_allow_html=True,
            )
        idx += 1

# =========================================================
# 7) CHECKIN
# =========================================================
def page_checkin():
    render_nav()
    st.markdown("## ⏰ 智能打卡站")
    st.caption(f"📅 台灣時間：{get_tw_time().strftime('%Y-%m-%d %H:%M:%S')}")

    if "scan_cooldowns" not in st.session_state:
        st.session_state["scan_cooldowns"] = {}

    tab1, tab2, tab3 = st.tabs(["⚡️ 現場打卡", "🛠️ 補登作業", "✏️ 紀錄修改"])

    with tab1:
        st.info("💡 輸入身分證或刷卡，系統自動判斷簽到/簽退")
        with st.form("checkin_form"):
            c1, c2 = st.columns([1, 2])
            with c1:
                raw_act = st.selectbox("📌 選擇活動", DEFAULT_ACTIVITIES)
            with c2:
                note = st.text_input("📝 活動說明 (專案活動/教育訓練必填)", placeholder="例如：社區大掃除")
            
            pid = st.text_input("請輸入身分證（或掃描）", placeholder="例如：A123456789")
            
            if st.form_submit_button("送出打卡"):
                pid = pid.strip().upper()
                if not pid:
                    st.warning("請輸入身分證")
                else:
                    final_act = raw_act
                    if raw_act in ["專案活動", "教育訓練"] and note:
                        final_act = f"{raw_act}：{note}"
                    
                    now = get_tw_time()
                    last = st.session_state["scan_cooldowns"].get(pid)
                    if last and (now - last).total_seconds() < 120:
                        st.warning(f"⏳ 請勿重複刷卡（{pid}）")
                    else:
                        df_m = load_data_from_sheet("members")
                        df_l = load_data_from_sheet("logs")
                        
                        person = df_m[df_m["身分證字號"].astype(str).str.upper() == pid]
                        if person.empty:
                            st.error("❌ 查無此人")
                        else:
                            row = person.iloc[0]
                            name = row.get("姓名", "")
                            if check_is_fully_retired(row):
                                st.error(f"❌ {name} 已退出")
                            else:
                                today = now.strftime("%Y-%m-%d")
                                t_logs = pd.DataFrame()
                                if not df_l.empty:
                                    t_logs = df_l[(df_l["身分證字號"].astype(str).str.upper() == pid) & (df_l["日期"].astype(str) == today)]
                                
                                action = "簽到"
                                if not t_logs.empty and str(t_logs.iloc[-1].get("動作", "")) == "簽到":
                                    action = "簽退"
                                
                                new_log = pd.DataFrame([{
                                    "姓名": name, "身分證字號": pid, "電話": row.get("電話", ""),
                                    "志工分類": row.get("志工分類", ""), "動作": action,
                                    "時間": now.strftime("%H:%M:%S"), "日期": today, "活動內容": final_act
                                }])
                                
                                save_data_to_sheet(pd.concat([df_l, new_log], ignore_index=True) if not df_l.empty else new_log, "logs")
                                st.session_state["scan_cooldowns"][pid] = now
                                st.success(f"✅ {name} {action} 成功！")

    with tab2:
        df_m = load_data_from_sheet("members")
        if df_m.empty:
            st.info("無名冊資料")
        else:
            df_m2 = df_m.copy()
            df_m2["狀態"] = df_m2.apply(lambda r: "已退出" if check_is_fully_retired(r) else "在職", axis=1)
            active_m = df_m2[df_m2["狀態"] == "在職"]
            name_list = active_m["姓名"].dropna().astype(str).tolist()

            with st.form("manual_form"):
                st.write("### 🛠️ 補登操作")
                entry_mode = st.radio("模式", ["單筆補登", "整批補登"], horizontal=True)
                c1, c2, c3, c4 = st.columns(4)
                d_date = c1.date_input("日期", value=date.today())
                d_time = c2.time_input("時間", value=get_tw_time().time())
                d_action = c3.selectbox("動作", ["簽到", "簽退"])
                d_act = c4.selectbox("活動", DEFAULT_ACTIVITIES)

                if entry_mode == "單筆補登":
                    names = [st.selectbox("志工", name_list)]
                else:
                    names = st.multiselect("選擇多位", name_list)

                if st.form_submit_button("✅ 確認補登"):
                    if not names or (len(names)==1 and names[0]==""):
                        st.warning("請選擇志工")
                    else:
                        logs = load_data_from_sheet("logs")
                        new_rows = []
                        for n in names:
                            row = active_m[active_m["姓名"].astype(str) == str(n)].iloc[0]
                            new_rows.append({
                                "姓名": n, "身分證字號": row.get("身分證字號", ""), 
                                "電話": row.get("電話", ""), "志工分類": row.get("志工分類", ""),
                                "動作": d_action, "時間": d_time.strftime("%H:%M:%S"),
                                "日期": d_date.strftime("%Y-%m-%d"), "活動內容": d_act
                            })
                        save_data_to_sheet(pd.concat([logs, pd.DataFrame(new_rows)], ignore_index=True) if not logs.empty else pd.DataFrame(new_rows), "logs")
                        st.success("✅ 已補登")

    with tab3:
        logs = load_data_from_sheet("logs")
        if logs.empty: st.info("無資料")
        else:
            edited = st.data_editor(logs, num_rows="dynamic", use_container_width=True)
            if st.button("💾 儲存修改"):
                save_data_to_sheet(edited, "logs")
                st.success("✅ 已更新")

# =========================================================
# 8) MEMBERS
# =========================================================
def page_members():
    render_nav()
    st.markdown("## 📋 志工名冊管理")
    df = load_data_from_sheet("members")

    # 🔥🔥 新增志工：卡片式分類選擇 (設計感升級) 🔥🔥
    with st.expander("➕ 新增志工", expanded=True):
        with st.form("add_member_form"):
            st.markdown("#### 1. 基本資料")
            c1, c2, c3 = st.columns(3)
            n = c1.text_input("姓名")
            p = c2.text_input("身分證")
            b = c3.text_input("生日（YYYY-MM-DD）")
            c4, c5 = st.columns([2, 1])
            addr = c4.text_input("地址")
            ph = c5.text_input("電話")

            spacer(10)
            st.markdown("#### 2. 志工分類與加入日期 (請勾選並確認日期)")
            
            # 卡片式佈局
            cat_cols = st.columns(4)
            
            # 定義分類邏輯
            # 1. 祥和
            with cat_cols[0]:
                st.markdown('<div class="cat-card"><div class="cat-title">祥和志工</div>', unsafe_allow_html=True)
                is_x = st.checkbox("加入", key="cx_x")
                d_x = st.date_input("加入日期", value=date.today(), key="dx_x") if is_x else ""
                st.markdown('</div>', unsafe_allow_html=True)

            # 2. 據點週二
            with cat_cols[1]:
                st.markdown('<div class="cat-card"><div class="cat-title">週二據點</div>', unsafe_allow_html=True)
                is_t = st.checkbox("加入", key="cx_t")
                d_t = st.date_input("加入日期", value=date.today(), key="dx_t") if is_t else ""
                st.markdown('</div>', unsafe_allow_html=True)

            # 3. 據點週三
            with cat_cols[2]:
                st.markdown('<div class="cat-card"><div class="cat-title">週三據點</div>', unsafe_allow_html=True)
                is_w = st.checkbox("加入", key="cx_w")
                d_w = st.date_input("加入日期", value=date.today(), key="dx_w") if is_w else ""
                st.markdown('</div>', unsafe_allow_html=True)

            # 4. 環保
            with cat_cols[3]:
                st.markdown('<div class="cat-card"><div class="cat-title">環保志工</div>', unsafe_allow_html=True)
                is_e = st.checkbox("加入", key="cx_e")
                d_e = st.date_input("加入日期", value=date.today(), key="dx_e") if is_e else ""
                st.markdown('</div>', unsafe_allow_html=True)

            spacer(10)
            submitted = st.form_submit_button("✅ 確認新增")

    if submitted:
        if not p:
            st.error("身分證必填")
        else:
            cats = []
            if is_x: cats.append("祥和志工")
            if is_t: cats.append("關懷據點週二志工")
            if is_w: cats.append("關懷據點週三志工")
            if is_e: cats.append("環保志工")

            new_data = {
                "姓名": n, "身分證字號": str(p).upper(), "生日": b, "電話": ph, "地址": addr,
                "志工分類": ",".join(cats),
                "祥和_加入日期": str(d_x) if is_x else "",
                "據點週二_加入日期": str(d_t) if is_t else "",
                "據點週三_加入日期": str(d_w) if is_w else "",
                "環保_加入日期": str(d_e) if is_e else ""
            }
            
            df_check = df.copy() if not df.empty else pd.DataFrame(columns=DISPLAY_ORDER)
            if not df_check.empty and (df_check["身分證字號"].astype(str).str.upper() == str(p).upper()).any():
                st.error("此身分證已存在")
            else:
                new = pd.DataFrame([new_data])
                for c in DISPLAY_ORDER:
                    if c not in new.columns: new[c] = ""
                for c in DISPLAY_ORDER:
                    if c not in df_check.columns: df_check[c] = ""
                
                out = pd.concat([df_check, new[DISPLAY_ORDER]], ignore_index=True)
                save_data_to_sheet(out, "members")
                st.success("✅ 新增成功")
                time.sleep(0.5)
                st.rerun()

    # ---- 檢視與編輯 ----
    if not df.empty:
        st.write("")
        mode = st.radio("檢視模式", ["🟢 在職", "📋 全部 (含退出)"], horizontal=True)
        df2 = df.copy()
        df2["狀態"] = df2.apply(lambda r: "已退出" if check_is_fully_retired(r) else "在職", axis=1)
        df2["年齡"] = df2["生日"].apply(calculate_age)
        
        show_df = df2[df2["狀態"] == "在職"] if "在職" in mode else df2
        
        cols = ["身分證字號", "狀態", "姓名", "年齡", "電話", "地址", "志工分類"] + [c for c in df2.columns if "日期" in c] + ["備註"]
        cols = [c for c in cols if c in show_df.columns]
        
        edited = st.data_editor(show_df[cols], use_container_width=True, num_rows="dynamic", key="members_editor", disabled=["身分證字號", "狀態", "年齡"])
        
        if st.button("💾 儲存名冊修改"):
            # 合併邏輯: 以身分證為 key
            base = df2.copy()
            base["身分證字號"] = base["身分證字號"].astype(str).str.upper()
            ed = edited.copy()
            ed["身分證字號"] = ed["身分證字號"].astype(str).str.upper()
            
            # 更新邏輯 (簡單版：直接 merge update)
            # 因為 data_editor 只能編輯顯示的 row，這裡要謹慎
            # 為了安全，這裡示範最簡單的：將編輯後的 dataframe 覆蓋回去 (需注意過濾問題)
            # 完整版應該用 merge，這裡簡化處理：
            # 若是在職模式，只更新在職的人；若是全部，更新全部。
            
            # 比較安全的做法：遍歷 edited 的每一列，更新 base 對應的列
            for i, r in ed.iterrows():
                pid = r["身分證字號"]
                # 找到 base 裡面的 index
                idx = base[base["身分證字號"] == pid].index
                if not idx.empty:
                    for c in cols:
                        if c in ["狀態", "年齡"]: continue # 這些是算出來的，不存
                        if c in base.columns:
                            base.at[idx[0], c] = r[c]
            
            save_data_to_sheet(base[DISPLAY_ORDER], "members")
            st.success("✅ 名冊已更新")

# =========================================================
# 9) REPORT
# =========================================================
def page_report():
    render_nav()
    st.markdown("## 📊 數據分析")
    
    logs = load_data_from_sheet("logs")
    sessions = build_sessions(logs)
    
    if sessions.empty:
        st.info("尚無完整簽到退紀錄")
    else:
        # 年度篩選
        years = sorted(pd.to_datetime(sessions["start"]).dt.year.unique().tolist(), reverse=True)
        sel_year = st.selectbox("選擇年度", years)
        
        y_sess = sessions[pd.to_datetime(sessions["start"]).dt.year == sel_year].copy()
        
        if y_sess.empty:
            st.warning(f"{sel_year} 無資料")
        else:
            y_sess["hours"] = y_sess["seconds"] / 3600
            
            # 圖表 1: 每月時數
            y_sess["month"] = pd.to_datetime(y_sess["start"]).dt.month
            mon_agg = y_sess.groupby("month")["hours"].sum().reset_index()
            fig1 = px.bar(mon_agg, x="month", y="hours", title=f"{sel_year} 每月總時數趨勢", color_discrete_sequence=[ACCENT])
            st.plotly_chart(fig1, use_container_width=True)
            
            # 圖表 2: 活動佔比
            act_agg = y_sess.groupby("活動內容")["hours"].sum().reset_index()
            fig2 = px.pie(act_agg, names="活動內容", values="hours", title=f"{sel_year} 活動類型佔比", hole=0.4, color_discrete_sequence=px.colors.sequential.Purples_r)
            st.plotly_chart(fig2, use_container_width=True)

    spacer(10)
    st.markdown("### 📝 原始出勤紀錄")
    if not logs.empty:
        st.dataframe(logs, use_container_width=True, height=400)
    else:
        st.info("無資料")

# =========================================================
# 10) Router
# =========================================================
if st.session_state.page == "home":
    page_home()
elif st.session_state.page == "checkin":
    page_checkin()
elif st.session_state.page == "members":
    page_members()
elif st.session_state.page == "report":
    page_report()
else:
    goto("home")
