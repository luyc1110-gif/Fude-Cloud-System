import streamlit as st
import pandas as pd
from datetime import datetime
import gspread

# --- 設定網頁 (最簡潔版) ---
st.set_page_config(page_title="系統除錯模式", layout="wide")

# 您的試算表 ID
SHEET_ID = "1A3-VwCBYjnWdcEiL6VwbV5-UECcgX7TqKH94sKe8P90"

st.title("🛠️ 系統連線診斷")

# 1. 顯示目前的機器人身分
try:
    email = st.secrets["gcp_service_account"]["client_email"]
    st.info(f"🤖 正在使用的機器人 Email：\n{email}")
    st.caption("請務必確認 Google 試算表右上角的「共用」裡，有加入這個 Email 並且是「編輯者」。")
except:
    st.error("❌ 讀取不到 Secrets！請檢查 Streamlit 後台設定。")

# 2. 測試連線
st.write("---")
st.write("📡 正在嘗試連線到 Google 試算表...")

try:
    # 建立連線
    gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
    
    # 嘗試抓取檔案
    sh = gc.open_by_key(SHEET_ID)
    st.success(f"✅ 成功找到檔案：{sh.title}")
    
    # 嘗試讀取 members 分頁
    ws = sh.worksheet("members")
    data = ws.get_all_records()
    df = pd.DataFrame(data)
    
    st.success("✅ 成功讀取資料！目前資料預覽：")
    st.dataframe(df)

except Exception as e:
    st.error("❌ 連線失敗！詳細錯誤訊息如下：")
    # 用程式碼區塊顯示錯誤，保證看得到
    st.code(str(e), language="text")
    
    if "403" in str(e):
        st.warning("💡 提示：錯誤代碼 403 代表「權限不足」。請確認試算表有共用給上面的 Email。")
    elif "404" in str(e):
        st.warning("💡 提示：錯誤代碼 404 代表「找不到檔案」。請確認試算表 ID 是否正確，或檔案是否被刪除。")
    elif "API has not been used" in str(e):
        st.warning("💡 提示：Google Drive API 或 Sheets API 可能沒啟用，請去 Google Cloud Console 啟用。")