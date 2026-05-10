import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import date, timedelta
import urllib.parse
import requests
import secrets
import json
import traceback
import gspread

from google.cloud import bigquery
from google.oauth2 import service_account

# ─────────────────────────────────────────────
# BigQuery 설정
# ─────────────────────────────────────────────
PROJECT_ID = "abandon-animal"
DATASET_ID = "animal_dashboard"
TABLE_ID = "animal_notices"
TABLE_NAME = f"`{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}`"

ALL_OPTION = "전체"

# ─────────────────────────────────────────────
# 페이지 설정
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="유실유기동물 현황 대시보드",
    page_icon="🐾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# 색상 토큰 (warm report tone)
# ─────────────────────────────────────────────
TOKENS = {
    "bg":        "#f6f1e7",   # warm cream background
    "surface":   "#ffffff",
    "surface_2": "#fbf7ef",
    "ink":       "#1a2540",   # deep navy text
    "ink_2":     "#5b5546",   # warm muted
    "ink_3":     "#968b76",   # warm light
    "line":      "#ebe2cf",
    "line_2":    "#f3ecdc",
    "navy":      "#1e2a44",   # primary accent
    "navy_2":    "#2c3a5a",
    "amber":     "#c8841e",   # secondary accent
    "amber_2":   "#e0a64c",
    "green":     "#6b9472",   # adoption / positive
    "rose":      "#b56b6b",   # euthanasia / negative
    "lilac":     "#8a82b6",
    "teal":      "#5a8a8a",
    "warm_gray": "#b4a896",
}

STATUS_COLORS = {
    "보호중": "#2c4775",
    "입양":   "#6b9472",
    "자연사": "#b4a896",
    "안락사": "#b56b6b",
    "반환":   "#c8841e",
    "기증":   "#8a82b6",
    "방사":   "#5a8a8a",
    "미상":   "#d3cdbe",
}

# ─────────────────────────────────────────────
# 커스텀 CSS — Pretendard, warm report tone, slim sidebar
# ─────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css');

html, body, [class*="css"], .stApp, [data-testid="stSidebar"] * {{
    font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, 'Apple SD Gothic Neo', sans-serif !important;
    font-feature-settings: 'ss06' on, 'tnum' on;
}}

.stApp {{
    background: {TOKENS["bg"]};
}}

/* Hide Streamlit chrome */
#MainMenu, footer, header {{ visibility: hidden; }}
.stDeployButton {{ display: none; }}

/* ───── Block container padding ───── */
.block-container {{
    padding: 1.6rem 2.2rem 3rem !important;
    max-width: 1480px !important;
}}

/* ───── Sidebar — slim, dark navy ───── */
[data-testid="stSidebar"] {{
    background: {TOKENS["navy"]} !important;
    border-right: 1px solid rgba(255,255,255,0.05);
    min-width: 220px !important;
    max-width: 240px !important;
    width: 220px !important;
}}
[data-testid="stSidebar"] > div:first-child {{
    padding-top: 0.6rem;
}}
[data-testid="stSidebar"] * {{
    color: #cdd4e2 !important;
}}
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stDateInput label {{
    color: #8a93a6 !important;
    font-size: 10.5px !important;
    font-weight: 500 !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
    margin-bottom: 4px !important;
}}
[data-testid="stSidebar"] [data-testid="stSelectbox"] > div > div,
[data-testid="stSidebar"] [data-testid="stDateInput"] > div > div {{
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 7px !important;
    color: #e8ecf3 !important;
    font-size: 12.5px !important;
    min-height: 36px !important;
}}
[data-testid="stSidebar"] [data-testid="stDateInput"] input {{
    background: transparent !important;
    color: #e8ecf3 !important;
    font-size: 12px !important;
}}
[data-testid="stSidebar"] hr {{
    border-color: rgba(255,255,255,0.07) !important;
    margin: 14px 0 !important;
}}

/* ───── Tabs ───── */
.stTabs [data-baseweb="tab-list"] {{
    background: transparent;
    border-radius: 0;
    padding: 0;
    gap: 4px;
    border: none;
    border-bottom: 1px solid {TOKENS["line"]};
    margin-bottom: 18px;
}}
.stTabs [data-baseweb="tab"] {{
    border-radius: 0;
    padding: 10px 4px 14px !important;
    font-size: 13.5px;
    font-weight: 500;
    color: {TOKENS["ink_2"]};
    background: transparent !important;
    border: none !important;
    margin-right: 22px !important;
    position: relative;
}}
.stTabs [aria-selected="true"] {{
    color: {TOKENS["ink"]} !important;
    font-weight: 700;
    background: transparent !important;
}}
.stTabs [aria-selected="true"]::after {{
    content: '';
    position: absolute;
    left: 0; right: 0; bottom: -1px;
    height: 2px;
    background: {TOKENS["amber"]};
    border-radius: 1px;
}}
.stTabs [data-baseweb="tab-highlight"],
.stTabs [data-baseweb="tab-border"] {{
    display: none;
}}

/* ───── Native metric (we mostly use custom card) ───── */
[data-testid="stMetric"] {{
    background: {TOKENS["surface"]};
    border: 1px solid {TOKENS["line"]};
    border-radius: 14px;
    padding: 20px 22px !important;
}}
[data-testid="stMetricLabel"] {{
    font-size: 12px !important;
    color: {TOKENS["ink_2"]} !important;
    font-weight: 500;
}}
[data-testid="stMetricValue"] {{
    font-size: 32px !important;
    font-weight: 700 !important;
    color: {TOKENS["ink"]} !important;
    letter-spacing: -0.03em;
}}

/* ───── DataFrame ───── */
[data-testid="stDataFrame"] {{
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid {TOKENS["line"]};
    box-shadow: none;
}}
[data-testid="stDataFrame"] [role="columnheader"] {{
    background: {TOKENS["surface_2"]} !important;
    color: {TOKENS["ink_2"]} !important;
    font-weight: 500 !important;
    font-size: 11.5px !important;
}}

/* ───── Buttons ───── */
.stDownloadButton > button {{
    background: {TOKENS["surface"]} !important;
    border: 1px solid {TOKENS["line"]} !important;
    border-radius: 8px !important;
    color: {TOKENS["ink"]} !important;
    font-size: 12.5px !important;
    font-weight: 500 !important;
    padding: 9px 18px !important;
    font-family: 'Pretendard', sans-serif !important;
    transition: all 0.15s !important;
    box-shadow: none !important;
}}
.stDownloadButton > button:hover {{
    border-color: {TOKENS["amber"]} !important;
    color: {TOKENS["amber"]} !important;
}}

.stButton > button {{
    background: {TOKENS["navy"]} !important;
    border: none !important;
    border-radius: 8px !important;
    color: white !important;
    font-size: 12.5px !important;
    font-weight: 500 !important;
    padding: 10px 22px !important;
    font-family: 'Pretendard', sans-serif !important;
    box-shadow: 0 1px 2px rgba(26,37,64,0.08);
}}
.stButton > button:hover {{
    background: {TOKENS["navy_2"]} !important;
    box-shadow: 0 2px 6px rgba(26,37,64,0.12);
}}

[data-testid="stSidebar"] .stButton > button {{
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    color: #cdd4e2 !important;
    box-shadow: none !important;
    width: 100%;
    font-size: 12px !important;
}}
[data-testid="stSidebar"] .stButton > button:hover {{
    background: rgba(255,255,255,0.08) !important;
    color: #ffffff !important;
}}
[data-testid="stSidebar"] .stLinkButton > a {{
    background: {TOKENS["amber"]} !important;
    color: #ffffff !important;
    border: none !important;
}}

/* ───── Section header ───── */
.section-header {{
    font-size: 14px;
    font-weight: 600;
    color: {TOKENS["ink"]};
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 0 2px 2px;
    margin-bottom: 8px;
    letter-spacing: -0.005em;
}}
.section-header .sub {{
    font-size: 11.5px;
    color: {TOKENS["ink_3"]};
    font-weight: 400;
    margin-left: 6px;
}}

.modebar {{ display: none !important; }}

/* ───── Login page bg override ───── */
.login-wrap {{
    background: {TOKENS["bg"]};
}}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Google OAuth 설정 및 로그인 페이지
# ─────────────────────────────────────────────
try:
    GOOGLE_CLIENT_ID     = st.secrets["GOOGLE_CLIENT_ID"]
    GOOGLE_CLIENT_SECRET = st.secrets["GOOGLE_CLIENT_SECRET"]
    REDIRECT_URI         = st.secrets["REDIRECT_URI"]
    WHITELIST_SHEET_ID   = st.secrets["WHITELIST_SHEET_ID"]
    WHITELIST_GID        = int(st.secrets.get("WHITELIST_GID", 0))
except Exception:
    st.warning("⚠️ Streamlit Secrets 설정이 필요합니다. 로컬 테스트 중이라면 무시하셔도 됩니다.")

AUTHORIZATION_URL = "https://accounts.google.com/o/oauth2/auth"
TOKEN_URL         = "https://oauth2.googleapis.com/token"
USERINFO_URL      = "https://www.googleapis.com/oauth2/v3/userinfo"


def get_google_auth_url(state: str) -> str:
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "online",
        "prompt": "select_account",
    }
    return AUTHORIZATION_URL + "?" + urllib.parse.urlencode(params)


def exchange_code_for_userinfo(code: str) -> dict | None:
    try:
        token_resp = requests.post(TOKEN_URL, data={
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": REDIRECT_URI,
            "grant_type": "authorization_code",
        }, timeout=10)
        access_token = token_resp.json().get("access_token")
        if not access_token:
            return None
        return requests.get(
            USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        ).json()
    except Exception:
        return None


def load_whitelist() -> set:
    creds_info = json.loads(json.dumps(dict(st.secrets["gcp_service_account"])))
    gc = gspread.service_account_from_dict(creds_info)
    sh = gc.open_by_key(WHITELIST_SHEET_ID)
    ws = next((w for w in sh.worksheets() if w.id == WHITELIST_GID), sh.worksheets()[0])
    return {str(r.get("email", "")).strip().lower() for r in ws.get_all_records() if r.get("email")}


def show_login_page():
    params = st.query_params
    code = params.get("code")

    if code:
        with st.spinner("Google 계정을 확인하는 중..."):
            user_info = exchange_code_for_userinfo(code)
        if not user_info or "email" not in user_info:
            st.error("⚠️ Google 인증에 실패했습니다. 다시 시도해 주세요.")
            st.query_params.clear()
            st.stop()

        email = user_info["email"].strip().lower()
        try:
            whitelist = load_whitelist()
        except Exception as e:
            st.error(f"⚠️ 접근권한 시트를 불러올 수 없습니다.\n\n오류: `{type(e).__name__}: {e}`")
            st.code(traceback.format_exc(), language="text")
            st.query_params.clear()
            st.stop()

        if email not in whitelist:
            st.error(f"❌ **{email}** 은(는) 접근 권한이 없는 계정입니다.\n관리자에게 접근 권한을 요청하세요.")
            st.query_params.clear()
            st.stop()

        st.session_state.update({
            "authenticated": True,
            "user_email": email,
            "user_name": user_info.get("name") or email,
            "user_picture": user_info.get("picture", ""),
        })
        st.query_params.clear()
        st.rerun()
        return

    _, col, _ = st.columns([1, 1.6, 1])
    with col:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown(
            f'''
            <div style="text-align:center;margin-bottom:8px;">
                <div style="width:64px;height:64px;border-radius:16px;
                    background:linear-gradient(160deg,{TOKENS["navy_2"]},{TOKENS["navy"]});
                    border:1px solid rgba(0,0,0,0.04);
                    display:flex;align-items:center;justify-content:center;
                    font-size:28px;margin:0 auto 18px;color:{TOKENS["amber_2"]};">🐾</div>
            </div>
            <div style="text-align:center;font-size:10.5px;letter-spacing:0.14em;
                color:{TOKENS["ink_3"]};font-weight:500;text-transform:uppercase;margin-bottom:6px;">
                REPORT · 동물자유연대
            </div>
            <h2 style="text-align:center;margin:0 0 6px;font-size:22px;
                font-weight:700;color:{TOKENS["ink"]};letter-spacing:-0.025em;">
                유실유기동물 현황 대시보드
            </h2>
            <p style="text-align:center;color:{TOKENS["ink_2"]};margin-bottom:30px;font-size:12.5px;">
                동물자유연대 구성원 전용 페이지입니다.
            </p>
            ''',
            unsafe_allow_html=True,
        )
        if "oauth_state" not in st.session_state:
            st.session_state["oauth_state"] = secrets.token_hex(16)
        st.link_button(
            "🔐  Google 계정으로 로그인",
            get_google_auth_url(st.session_state["oauth_state"]),
            use_container_width=True,
            type="primary",
        )
        st.markdown("<br>", unsafe_allow_html=True)
        st.caption("접근 권한 요청: 관리자에게 Google 계정 이메일 주소를 알려주세요.")


# ─────────────────────────────────────────────
# 인증 게이트웨이
# ─────────────────────────────────────────────
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if not st.session_state["authenticated"]:
    show_login_page()
    st.stop()

# ─────────────────────────────────────────────
# BigQuery 연결 및 조회 함수
# ─────────────────────────────────────────────
@st.cache_resource
def get_bq_client():
    creds_info = dict(st.secrets["gcp_service_account"])
    credentials = service_account.Credentials.from_service_account_info(creds_info)
    return bigquery.Client(credentials=credentials, project=PROJECT_ID)


def run_bq_query(query: str, params=None) -> pd.DataFrame:
    client = get_bq_client()
    job_config = bigquery.QueryJobConfig(query_parameters=params or [])
    return client.query(query, job_config=job_config).to_dataframe()


def _filter_sql(date_from, date_to, sido_sel, status_sel):
    where = ["happen_date BETWEEN @date_from AND @date_to"]
    params = [
        bigquery.ScalarQueryParameter("date_from", "DATE", date_from),
        bigquery.ScalarQueryParameter("date_to", "DATE", date_to),
    ]
    if sido_sel != ALL_OPTION:
        where.append("sido = @sido")
        params.append(bigquery.ScalarQueryParameter("sido", "STRING", sido_sel))
    if status_sel != ALL_OPTION:
        where.append("process_state = @status")
        params.append(bigquery.ScalarQueryParameter("status", "STRING", status_sel))
    return " AND ".join(where), params


@st.cache_data(ttl=3600)
def load_dashboard_data(date_from, date_to, sido_sel, status_sel):
    where_sql, params = _filter_sql(date_from, date_to, sido_sel, status_sel)

    daily_query = f"""
        SELECT happen_date AS dt, COUNT(*) AS cnt
        FROM {TABLE_NAME}
        WHERE {where_sql}
        GROUP BY happen_date
        ORDER BY happen_date
    """
    status_query = f"""
        SELECT COALESCE(process_state, '미상') AS status_name, COUNT(*) AS cnt
        FROM {TABLE_NAME} WHERE {where_sql}
        GROUP BY 1 ORDER BY 2 DESC
    """
    sido_query = f"""
        SELECT COALESCE(sido, '미상') AS region, COUNT(*) AS cnt
        FROM {TABLE_NAME} WHERE {where_sql}
        GROUP BY 1 ORDER BY 2 DESC
    """
    breed_query = f"""
        SELECT CONCAT(COALESCE(breed, '미상'), '(', COALESCE(animal_type, '미상'), ')') AS breed_name,
               COUNT(*) AS cnt
        FROM {TABLE_NAME} WHERE {where_sql}
        GROUP BY 1 ORDER BY 2 DESC LIMIT 12
    """
    table_query = f"""
        SELECT
          notice_no AS col_notice_no,
          FORMAT_DATE('%Y.%m.%d', happen_date) AS col_happen_date,
          happen_place AS col_happen_place,
          animal_type AS col_animal_type,
          breed AS col_breed,
          age AS col_age,
          FORMAT_DATE('%Y.%m.%d', notice_start_date) AS col_notice_start,
          FORMAT_DATE('%Y.%m.%d', notice_end_date) AS col_notice_end,
          process_state AS col_process_state,
          neuter_status AS col_neuter,
          special_mark AS col_special,
          care_name AS col_care_name,
          org_name AS col_org_name,
          sido AS col_sido,
          sigungu AS col_sigungu,
          end_reason AS col_end_reason
        FROM {TABLE_NAME} WHERE {where_sql}
        ORDER BY happen_date DESC, notice_no DESC LIMIT 500
    """
    kpi_query = f"""
        SELECT
          COUNT(*) AS total_count,
          COUNTIF(process_state = '입양') AS adoption_count,
          COUNTIF(process_state = '안락사') AS euthanasia_count,
          COUNTIF(process_state = '보호중') AS protected_count,
          MAX(happen_date) AS latest_date
        FROM {TABLE_NAME} WHERE {where_sql}
    """
    animal_type_query = f"""
        SELECT COALESCE(animal_type, '미상') AS animal_type_name, COUNT(*) AS cnt
        FROM {TABLE_NAME} WHERE {where_sql}
        GROUP BY 1 ORDER BY 2 DESC
    """

    daily_df = run_bq_query(daily_query, params).rename(columns={"dt": "날짜", "cnt": "건수"})
    status_df = run_bq_query(status_query, params).rename(columns={"status_name": "상태", "cnt": "건수"})
    sido_df = run_bq_query(sido_query, params).rename(columns={"region": "지역", "cnt": "건수"})
    breed_df = run_bq_query(breed_query, params).rename(columns={"breed_name": "품종", "cnt": "건수"})
    table_df = run_bq_query(table_query, params).rename(columns={
        "col_notice_no": "공고번호", "col_happen_date": "발생일자", "col_happen_place": "발생장소",
        "col_animal_type": "축종", "col_breed": "품종", "col_age": "나이",
        "col_notice_start": "공고시작일", "col_notice_end": "공고종료일",
        "col_process_state": "처리상태", "col_neuter": "중성화여부", "col_special": "특이사항",
        "col_care_name": "보호소명", "col_org_name": "관할기관",
        "col_sido": "시도", "col_sigungu": "시군구", "col_end_reason": "종료사유",
    })
    kpi_df = run_bq_query(kpi_query, params)
    animal_type_df = run_bq_query(animal_type_query, params).rename(columns={"animal_type_name": "축종", "cnt": "건수"})

    return {
        "daily_df": daily_df, "status_df": status_df, "sido_df": sido_df,
        "breed_df": breed_df, "table_df": table_df,
        "kpi_df": kpi_df, "animal_type_df": animal_type_df,
    }


@st.cache_data(ttl=3600)
def load_daily_report_data(target_date, sido_sel, status_sel):
    prev_date = target_date - timedelta(days=1)
    where = ["happen_date IN (@target_date, @prev_date)"]
    params = [
        bigquery.ScalarQueryParameter("target_date", "DATE", target_date),
        bigquery.ScalarQueryParameter("prev_date", "DATE", prev_date),
    ]
    if sido_sel != ALL_OPTION:
        where.append("sido = @sido")
        params.append(bigquery.ScalarQueryParameter("sido", "STRING", sido_sel))
    if status_sel != ALL_OPTION:
        where.append("process_state = @status")
        params.append(bigquery.ScalarQueryParameter("status", "STRING", status_sel))
    where_sql = " AND ".join(where)

    daily_summary_query = f"""
        SELECT happen_date,
          COUNT(*) AS total_count,
          COUNTIF(process_state = '입양') AS adoption_count,
          COUNTIF(process_state = '안락사') AS euthanasia_count,
          COUNTIF(process_state = '보호중') AS protected_count
        FROM {TABLE_NAME} WHERE {where_sql} GROUP BY happen_date
    """
    sido_compare_query = f"""
        SELECT COALESCE(sido, '미상') AS region,
          SUM(IF(happen_date = @prev_date, 1, 0)) AS prev_cnt,
          SUM(IF(happen_date = @target_date, 1, 0)) AS target_cnt
        FROM {TABLE_NAME} WHERE {where_sql}
        GROUP BY 1 ORDER BY 3 DESC, 2 DESC LIMIT 10
    """
    animal_compare_query = f"""
        SELECT COALESCE(animal_type, '미상') AS animal_name,
          SUM(IF(happen_date = @prev_date, 1, 0)) AS prev_cnt,
          SUM(IF(happen_date = @target_date, 1, 0)) AS target_cnt
        FROM {TABLE_NAME} WHERE {where_sql}
        GROUP BY 1 ORDER BY 3 DESC, 2 DESC
    """
    detail_query = f"""
        SELECT
          notice_no AS col_notice_no,
          FORMAT_DATE('%Y.%m.%d', happen_date) AS col_happen_date,
          happen_place AS col_happen_place,
          animal_type AS col_animal_type,
          breed AS col_breed, age AS col_age,
          process_state AS col_process_state,
          special_mark AS col_special,
          care_name AS col_care_name,
          org_name AS col_org_name
        FROM {TABLE_NAME} WHERE happen_date = @target_date
        ORDER BY notice_no DESC LIMIT 300
    """

    sido_compare_df = run_bq_query(sido_compare_query, params).rename(columns={
        "region": "지역", "prev_cnt": "전일", "target_cnt": "기준일"
    })
    animal_compare_df = run_bq_query(animal_compare_query, params).rename(columns={
        "animal_name": "축종", "prev_cnt": "전일", "target_cnt": "기준일"
    })
    detail_df = run_bq_query(detail_query, params).rename(columns={
        "col_notice_no": "공고번호", "col_happen_date": "발생일자",
        "col_happen_place": "발생장소", "col_animal_type": "축종",
        "col_breed": "품종", "col_age": "나이", "col_process_state": "처리상태",
        "col_special": "특이사항", "col_care_name": "보호소명", "col_org_name": "관할기관",
    })

    return {
        "summary_df": run_bq_query(daily_summary_query, params),
        "sido_compare_df": sido_compare_df,
        "animal_compare_df": animal_compare_df,
        "detail_df": detail_df,
        "target_date": target_date, "prev_date": prev_date,
    }


@st.cache_data(ttl=3600)
def load_monthly_report_data(date_to, sido_sel, status_sel):
    current_month_start = date_to.replace(day=1)
    prev_month_end = current_month_start - timedelta(days=1)
    prev_month_start = prev_month_end.replace(day=1)

    where = ["happen_date BETWEEN @prev_month_start AND @date_to"]
    params = [
        bigquery.ScalarQueryParameter("prev_month_start", "DATE", prev_month_start),
        bigquery.ScalarQueryParameter("current_month_start", "DATE", current_month_start),
        bigquery.ScalarQueryParameter("date_to", "DATE", date_to),
    ]
    if sido_sel != ALL_OPTION:
        where.append("sido = @sido")
        params.append(bigquery.ScalarQueryParameter("sido", "STRING", sido_sel))
    if status_sel != ALL_OPTION:
        where.append("process_state = @status")
        params.append(bigquery.ScalarQueryParameter("status", "STRING", status_sel))
    where_sql = " AND ".join(where)

    monthly_kpi_query = f"""
        SELECT IF(happen_date < @current_month_start, 'prev', 'current') AS period,
          COUNT(*) AS total_count,
          COUNTIF(process_state = '입양') AS adoption_count,
          COUNTIF(process_state = '안락사') AS euthanasia_count,
          COUNTIF(process_state = '보호중') AS protected_count
        FROM {TABLE_NAME} WHERE {where_sql} GROUP BY 1
    """
    sido_month_query = f"""
        SELECT COALESCE(sido, '미상') AS region,
          SUM(IF(happen_date < @current_month_start, 1, 0)) AS prev_cnt,
          SUM(IF(happen_date >= @current_month_start, 1, 0)) AS cur_cnt
        FROM {TABLE_NAME} WHERE {where_sql}
        GROUP BY 1 ORDER BY 3 DESC, 2 DESC LIMIT 10
    """
    month_daily_query = f"""
        SELECT CAST(EXTRACT(DAY FROM happen_date) AS STRING) AS day_num, COUNT(*) AS cnt
        FROM {TABLE_NAME}
        WHERE happen_date BETWEEN @current_month_start AND @date_to
        GROUP BY 1 ORDER BY CAST(day_num AS INT64)
    """
    status_month_query = f"""
        SELECT IF(happen_date < @current_month_start, 'prev', 'current') AS period,
          COALESCE(process_state, '미상') AS status_name, COUNT(*) AS cnt
        FROM {TABLE_NAME} WHERE {where_sql}
        GROUP BY 1, 2 ORDER BY 1, 3 DESC
    """

    sido_month_df = run_bq_query(sido_month_query, params).rename(columns={
        "region": "지역", "prev_cnt": "전월", "cur_cnt": "이번월"
    })
    month_daily_raw = run_bq_query(month_daily_query, params)
    month_daily_raw["day_num"] = month_daily_raw["day_num"] + "일"
    month_daily_df = month_daily_raw.rename(columns={"day_num": "일", "cnt": "건수"})
    status_month_raw = run_bq_query(status_month_query, params)
    status_month_raw["period"] = status_month_raw["period"].map({"prev": "전월", "current": "이번월"})
    status_month_df = status_month_raw.rename(columns={"status_name": "상태", "cnt": "건수"})

    return {
        "monthly_kpi_df": run_bq_query(monthly_kpi_query, params),
        "sido_month_df": sido_month_df, "month_daily_df": month_daily_df,
        "status_month_df": status_month_df,
        "current_month_start": current_month_start,
        "prev_month_start": prev_month_start, "prev_month_end": prev_month_end,
    }

# ─────────────────────────────────────────────
# Plotly 공통 레이아웃
# ─────────────────────────────────────────────
PLOTLY_FONT = dict(family="Pretendard, sans-serif", size=12, color=TOKENS["ink_2"])
PLOTLY_LAYOUT = dict(
    font=PLOTLY_FONT,
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(t=10, b=24, l=36, r=16),
    legend=dict(
        bgcolor="rgba(0,0,0,0)", bordercolor="rgba(0,0,0,0)",
        font=dict(size=11, color=TOKENS["ink_2"]),
        orientation="h", y=-0.18,
    ),
    xaxis=dict(showgrid=False, showline=False, zeroline=False,
               tickfont=dict(size=10, color=TOKENS["ink_3"])),
    yaxis=dict(gridcolor=TOKENS["line_2"], showline=False, zeroline=False,
               tickfont=dict(size=10, color=TOKENS["ink_3"])),
    hoverlabel=dict(
        bgcolor=TOKENS["surface"], bordercolor=TOKENS["line"],
        font=dict(family="Pretendard", size=12, color=TOKENS["ink"]),
    ),
)

# ─────────────────────────────────────────────
# 차트 헬퍼
# ─────────────────────────────────────────────
def empty_figure(message="표시할 데이터가 없습니다"):
    fig = go.Figure()
    layout = {k: v for k, v in PLOTLY_LAYOUT.items() if k not in ("xaxis", "yaxis")}
    layout.update(
        height=260,
        annotations=[dict(text=message, x=0.5, y=0.5, showarrow=False,
                          font=dict(size=12.5, color=TOKENS["ink_3"]))],
        xaxis=dict(visible=False), yaxis=dict(visible=False),
    )
    fig.update_layout(**layout)
    return fig


def apply_layout(fig, **kwargs):
    base = {k: v for k, v in PLOTLY_LAYOUT.items() if k not in kwargs}
    base.update(kwargs)
    fig.update_layout(**base)
    return fig


def chart_area(df, x_col, y_col, color=None):
    if df.empty:
        return empty_figure()
    color = color or TOKENS["navy"]
    r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df[x_col], y=df[y_col],
        mode="lines",
        line=dict(color=color, width=2, shape="spline", smoothing=0.6),
        fill="tozeroy",
        fillcolor=f"rgba({r},{g},{b},0.07)",
        hovertemplate="%{x}<br><b>%{y:,}건</b><extra></extra>",
    ))
    apply_layout(
        fig,
        xaxis=dict(showgrid=False, showline=False, zeroline=False,
                   tickfont=dict(size=10, color=TOKENS["ink_3"]),
                   tickangle=-30, nticks=10),
        yaxis=dict(gridcolor=TOKENS["line_2"], showline=False, zeroline=False,
                   tickfont=dict(size=10, color=TOKENS["ink_3"])),
        height=280,
        margin=dict(t=8, b=30, l=42, r=12),
    )
    return fig


def chart_donut(labels, values, total_label="총 발생"):
    if len(labels) == 0 or sum(values) == 0:
        return empty_figure()
    colors = [STATUS_COLORS.get(str(label), TOKENS["navy"]) for label in labels]
    fig = go.Figure(go.Pie(
        labels=labels, values=values, hole=0.62,
        marker=dict(colors=colors, line=dict(color="#ffffff", width=3)),
        textfont=dict(size=11, family="Pretendard", color=TOKENS["ink_2"]),
        textinfo="label+percent",
        textposition="outside",
        hovertemplate="%{label}: <b>%{value:,}건</b> (%{percent})<extra></extra>",
        sort=False,
    ))
    total = sum(values)
    fig.update_layout(
        font=PLOTLY_FONT,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        hoverlabel=PLOTLY_LAYOUT["hoverlabel"],
        showlegend=False,
        annotations=[
            dict(text=f"<b>{total:,}</b>", x=0.5, y=0.54,
                 font=dict(size=20, color=TOKENS["ink"], family="Pretendard"),
                 showarrow=False),
            dict(text=total_label, x=0.5, y=0.44,
                 font=dict(size=11, color=TOKENS["ink_3"], family="Pretendard"),
                 showarrow=False),
        ],
        height=320,
        margin=dict(t=20, b=20, l=20, r=20),
    )
    return fig


def chart_hbar(labels, values, highlight_top=True):
    if len(labels) == 0:
        return empty_figure()
    max_val = max(values) if values else 0
    r_margin = max(60, len(f"{int(max_val):,}") * 7 + 30)
    colors = []
    for i, _ in enumerate(values):
        if highlight_top and i == 0:
            colors.append(TOKENS["amber"])
        elif highlight_top and i < 3:
            colors.append(TOKENS["navy_2"])
        else:
            colors.append("#7a89a8")
    fig = go.Figure(go.Bar(
        y=labels, x=values, orientation="h",
        marker=dict(color=colors),
        text=[f"{int(v):,}" for v in values],
        textposition="outside",
        textfont=dict(size=10, color=TOKENS["ink_2"], family="Pretendard"),
        hovertemplate="%{y}: <b>%{x:,}건</b><extra></extra>",
        cliponaxis=False,
    ))
    apply_layout(
        fig,
        xaxis=dict(showgrid=True, gridcolor=TOKENS["line_2"],
                   showline=False, zeroline=False,
                   tickfont=dict(size=10, color=TOKENS["ink_3"])),
        yaxis=dict(showgrid=False, showline=False, zeroline=False,
                   tickfont=dict(size=11, color=TOKENS["ink_2"]),
                   autorange="reversed"),
        height=380,
        margin=dict(t=8, b=8, l=90, r=r_margin),
    )
    return fig


def chart_grouped_bar(categories, series, colors=None):
    if len(categories) == 0:
        return empty_figure()
    colors = colors or [TOKENS["warm_gray"], TOKENS["navy"]]
    fig = go.Figure()
    for i, (name, data) in enumerate(series):
        fig.add_trace(go.Bar(
            name=name, x=categories, y=data,
            marker=dict(color=colors[i % len(colors)]),
            hovertemplate=f"{name}<br>%{{x}}: <b>%{{y:,}}건</b><extra></extra>",
        ))
    apply_layout(
        fig,
        barmode="group", bargap=0.3, bargroupgap=0.08,
        xaxis=dict(showgrid=False, showline=False, zeroline=False,
                   tickfont=dict(size=11, color=TOKENS["ink_2"]), tickangle=-30),
        yaxis=dict(gridcolor=TOKENS["line_2"], showline=False, zeroline=False,
                   tickfont=dict(size=10, color=TOKENS["ink_3"])),
        height=280,
        margin=dict(t=8, b=40, l=42, r=12),
        legend=dict(orientation="h", y=-0.22, x=0,
                    font=dict(size=11.5, color=TOKENS["ink_2"]),
                    bgcolor="rgba(0,0,0,0)"),
    )
    return fig


def chart_treemap(labels, values):
    if len(labels) == 0:
        return empty_figure()
    # navy-to-warm palette
    palette = ["#1e2a44", "#2c3a5a", "#3d4d6e", "#5b6a89", "#7c89a4", "#9aa5bb",
               "#b8c0cf", "#d3d8e1", "#c8841e", "#d99c3e", "#e2b669", "#e8c98a"]
    colors = [palette[i % len(palette)] for i in range(len(labels))]
    fig = go.Figure(go.Treemap(
        labels=labels, values=values, parents=[""] * len(labels),
        marker=dict(colors=colors, line=dict(color="#ffffff", width=2)),
        textfont=dict(size=11, family="Pretendard", color="#ffffff"),
        texttemplate="<b>%{label}</b><br>%{value:,}",
        hovertemplate="<b>%{label}</b><br>%{value:,}건<extra></extra>",
        tiling=dict(pad=2),
    ))
    apply_layout(fig, height=280, margin=dict(t=4, b=4, l=4, r=4))
    return fig


def chart_vbar(categories, values, color=None):
    if len(categories) == 0:
        return empty_figure()
    color = color or TOKENS["navy"]
    fig = go.Figure(go.Bar(
        x=categories, y=values,
        marker=dict(color=color),
        hovertemplate="%{x}: <b>%{y:,}건</b><extra></extra>",
    ))
    apply_layout(
        fig,
        xaxis=dict(showgrid=False, showline=False, zeroline=False,
                   tickfont=dict(size=10, color=TOKENS["ink_3"]),
                   tickangle=-45, nticks=10),
        yaxis=dict(gridcolor=TOKENS["line_2"], showline=False, zeroline=False,
                   tickfont=dict(size=10, color=TOKENS["ink_3"])),
        height=280,
        margin=dict(t=10, b=20, l=42, r=8),
    )
    return fig


def chart_sparkline(values, color):
    """Tiny inline trend line for KPI cards. Returns a small Plotly figure."""
    if not values or len(values) < 2:
        # fallback: tiny flat line
        values = [1, 1, 1, 1]
    r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
    fig = go.Figure(go.Scatter(
        y=values, mode="lines",
        line=dict(color=color, width=1.6, shape="spline", smoothing=0.5),
        fill="tozeroy",
        fillcolor=f"rgba({r},{g},{b},0.14)",
        hoverinfo="skip",
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=2, b=2, l=2, r=2),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        height=42,
        showlegend=False,
    )
    return fig


# ─────────────────────────────────────────────
# UI 헬퍼
# ─────────────────────────────────────────────
def fmt_int(value):
    try:
        return f"{int(value):,}"
    except Exception:
        return "0"


def pct(numerator, denominator):
    if not denominator:
        return "0.0%"
    return f"{numerator / denominator * 100:.1f}%"


def kpi_card(label, value, sub_text, accent_color, value_unit=""):
    """Render a KPI card. Sparkline is drawn separately by caller via plotly_chart."""
    delta_color = TOKENS["ink_3"]
    arrow = ""
    sub_clean = sub_text
    if sub_text.startswith("▲"):
        delta_color = "#557955"; arrow = "▲"; sub_clean = sub_text[1:].strip()
    elif sub_text.startswith("▼"):
        delta_color = "#a25555"; arrow = "▼"; sub_clean = sub_text[1:].strip()

    return f"""
    <div style="
        background:{TOKENS['surface']};
        border:1px solid {TOKENS['line']};
        border-radius:14px;
        padding:20px 22px 16px;
        position:relative;
        overflow:hidden;
        min-height:148px;
    ">
        <div style="position:absolute;left:0;top:20px;bottom:20px;width:3px;
            border-radius:0 2px 2px 0;background:{accent_color};"></div>
        <div style="font-size:12px;color:{TOKENS['ink_2']};font-weight:500;
            letter-spacing:0.02em;margin-bottom:10px;">{label}</div>
        <div style="font-size:36px;font-weight:700;letter-spacing:-0.035em;
            line-height:1;color:{TOKENS['ink']};font-variant-numeric:tabular-nums;">
            {value}<span style="font-size:15px;color:{TOKENS['ink_2']};font-weight:500;margin-left:3px;">{value_unit}</span>
        </div>
        <div style="margin-top:14px;font-size:11.5px;font-weight:500;color:{delta_color};">
            {arrow} {sub_clean}
        </div>
    </div>"""


def section_title(text, sub=None):
    sub_html = f'<span class="sub">{sub}</span>' if sub else ''
    st.markdown(f'<div class="section-header">{text}{sub_html}</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────
# 사이드바
# ─────────────────────────────────────────────
with st.sidebar:
    name    = st.session_state.get("user_name", "사용자")
    email   = st.session_state.get("user_email", "")
    picture = st.session_state.get("user_picture", "")
    initial = name[0] if name else "?"

    avatar = (
        f"<img src='{picture}' style='width:36px;height:36px;border-radius:50%;object-fit:cover;'>"
        if picture else
        f"<div style='width:36px;height:36px;border-radius:50%;font-size:13px;"
        f"background:linear-gradient(135deg,{TOKENS['amber']},#8a5e1a);font-weight:600;"
        f"display:flex;align-items:center;justify-content:center;color:white;flex-shrink:0;'>{initial}</div>"
    )

    st.markdown(f"""
    <div style="padding:6px 0 14px;">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:14px;">
            <div style="width:34px;height:34px;border-radius:9px;
                background:linear-gradient(160deg,{TOKENS['navy_2']},{TOKENS['navy']});
                border:1px solid rgba(255,255,255,0.08);
                display:flex;align-items:center;justify-content:center;
                font-size:15px;color:{TOKENS['amber_2']};">🐾</div>
            <div style="line-height:1.25;">
                <div style="color:#ffffff;font-weight:600;font-size:12.5px;">유실유기동물</div>
                <div style="color:#8a93a6;font-size:10.5px;letter-spacing:0.04em;">현황 리포트</div>
            </div>
        </div>
        <div style="display:flex;align-items:center;gap:10px;padding:10px 0;
            border-top:1px solid rgba(255,255,255,0.06);
            border-bottom:1px solid rgba(255,255,255,0.06);">
            {avatar}
            <div style="flex:1;min-width:0;">
                <div style="color:#e8ecf3;font-size:12px;font-weight:500;
                    white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{name}</div>
                <div style="color:#8a93a6;font-size:10.5px;
                    white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{email}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    sido_options = [
        ALL_OPTION, "서울특별시", "경기도", "부산광역시", "인천광역시",
        "대구광역시", "광주광역시", "대전광역시", "울산광역시",
        "세종특별자치시", "경상남도", "경상북도", "전라남도",
        "전북특별자치도", "충청남도", "충청북도",
        "강원특별자치도", "제주특별자치도",
    ]
    sido_sel = st.selectbox("지역", sido_options)

    status_options = [ALL_OPTION, "보호중", "입양", "자연사", "안락사", "반환", "기증", "방사"]
    status_sel = st.selectbox("처리 상태", status_options)

    st.markdown(
        '<div style="color:#8a93a6;font-size:10.5px;font-weight:500;'
        'letter-spacing:0.06em;text-transform:uppercase;margin:14px 0 6px;">'
        '접수일 범위</div>',
        unsafe_allow_html=True,
    )
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        date_from = st.date_input("시작일", value=date(2026, 1, 1), label_visibility="collapsed")
    with col_d2:
        date_to = st.date_input("종료일", value=date.today(), label_visibility="collapsed")

    if date_from > date_to:
        st.error("시작일은 종료일보다 늦을 수 없습니다.")
        st.stop()

    st.markdown('<div style="height:14px;"></div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div style="color:#8a93a6;font-size:10.5px;line-height:1.7;padding:10px 0;
        border-top:1px solid rgba(255,255,255,0.06);">
        <div style="color:#cdd4e2;font-weight:500;margin-bottom:4px;">데이터 소스</div>
        BigQuery · {DATASET_ID}.{TABLE_ID}<br>
        캐시 갱신 주기: 1시간
    </div>
    """, unsafe_allow_html=True)

    if st.button("로그아웃", use_container_width=True, key="btn_logout"):
        for k in ["authenticated", "user_email", "user_name", "user_picture", "oauth_state"]:
            st.session_state.pop(k, None)
        st.rerun()

# ─────────────────────────────────────────────
# BigQuery 데이터 로드
# ─────────────────────────────────────────────
try:
    dashboard_data = load_dashboard_data(date_from, date_to, sido_sel, status_sel)
except Exception as e:
    st.error("BigQuery에서 데이터를 불러오지 못했습니다.")
    st.code(f"{type(e).__name__}: {e}\n\n{traceback.format_exc()}", language="text")
    st.stop()

daily_df       = dashboard_data["daily_df"]
status_df      = dashboard_data["status_df"]
sido_df        = dashboard_data["sido_df"]
breed_df       = dashboard_data["breed_df"]
table_df       = dashboard_data["table_df"]
kpi_df         = dashboard_data["kpi_df"]
animal_type_df = dashboard_data["animal_type_df"]

kpi = kpi_df.iloc[0].to_dict() if not kpi_df.empty else {}
total_count      = int(kpi.get("total_count") or 0)
adoption_count   = int(kpi.get("adoption_count") or 0)
euthanasia_count = int(kpi.get("euthanasia_count") or 0)
protected_count  = int(kpi.get("protected_count") or 0)
latest_date      = kpi.get("latest_date")

# ─────────────────────────────────────────────
# 상단 헤더
# ─────────────────────────────────────────────
latest_text = latest_date.strftime("%Y-%m-%d") if pd.notna(latest_date) else "데이터 없음"
period_text = f"{date_from:%Y.%m.%d} — {date_to:%Y.%m.%d}"
st.markdown(f"""
<div style="display:flex;align-items:flex-end;justify-content:space-between;
    margin:4px 0 22px;padding-bottom:20px;border-bottom:1px solid {TOKENS['line']};">
    <div>
        <div style="font-size:11px;color:{TOKENS['ink_3']};letter-spacing:0.14em;
            text-transform:uppercase;font-weight:500;margin-bottom:6px;">
            REPORT · 동물자유연대
        </div>
        <h1 style="font-size:26px;font-weight:700;color:{TOKENS['ink']};
            margin:0;letter-spacing:-0.025em;">
            유실유기동물 현황
        </h1>
        <div style="font-size:12.5px;color:{TOKENS['ink_2']};margin-top:8px;">
            데이터 출처 BigQuery · 마지막 데이터 기준일
            <b style="color:{TOKENS['ink']};font-weight:600;">{latest_text}</b> · 캐시 1시간
        </div>
    </div>
    <div style="display:flex;align-items:center;gap:8px;">
        <div style="background:{TOKENS['surface']};border:1px solid {TOKENS['line']};
            border-radius:8px;padding:7px 14px;font-size:12px;color:{TOKENS['ink']};">
            <span style="color:{TOKENS['ink_3']};font-size:10.5px;letter-spacing:0.04em;
                text-transform:uppercase;margin-right:8px;">기간</span>{period_text}
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 탭
# ─────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["대시보드", "일간 보고서", "월간 보고서"])

# ══════════════════════════════════════════════
# TAB 1 — 대시보드
# ══════════════════════════════════════════════
with tab1:
    # KPI cards + sparklines
    daily_values = daily_df["건수"].tolist() if not daily_df.empty else []
    spark_navy  = daily_values
    spark_green = daily_values[::-1]  # placeholder series for adoption trend
    spark_rose  = daily_values
    spark_amber = daily_values

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(kpi_card("총 발생 건수", fmt_int(total_count), "선택 기간 누계", TOKENS["navy"], "건"), unsafe_allow_html=True)
        st.plotly_chart(chart_sparkline(spark_navy, TOKENS["navy"]),
                        use_container_width=True, config={"displayModeBar": False, "staticPlot": True},
                        key="kpi_spark_1")
    with k2:
        st.markdown(kpi_card("입양률", pct(adoption_count, total_count), f"▲ 입양 {fmt_int(adoption_count)}건", TOKENS["green"]), unsafe_allow_html=True)
        st.plotly_chart(chart_sparkline(spark_green, TOKENS["green"]),
                        use_container_width=True, config={"displayModeBar": False, "staticPlot": True},
                        key="kpi_spark_2")
    with k3:
        st.markdown(kpi_card("안락사율", pct(euthanasia_count, total_count), f"안락사 {fmt_int(euthanasia_count)}건", TOKENS["rose"]), unsafe_allow_html=True)
        st.plotly_chart(chart_sparkline(spark_rose, TOKENS["rose"]),
                        use_container_width=True, config={"displayModeBar": False, "staticPlot": True},
                        key="kpi_spark_3")
    with k4:
        st.markdown(kpi_card("현재 보호중", fmt_int(protected_count), "선택 기간 기준", TOKENS["amber"], "건"), unsafe_allow_html=True)
        st.plotly_chart(chart_sparkline(spark_amber, TOKENS["amber"]),
                        use_container_width=True, config={"displayModeBar": False, "staticPlot": True},
                        key="kpi_spark_4")

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

    c1, c2 = st.columns([3, 2])
    with c1:
        section_title("일별 유기동물 발생 추이", period_text)
        st.plotly_chart(chart_area(daily_df, "날짜", "건수"),
                        use_container_width=True, config={"displayModeBar": False},
                        key="dash_chart_area")
    with c2:
        section_title("축종·품종별 분포", "상위 12개")
        fig2 = chart_treemap(breed_df["품종"].tolist(), breed_df["건수"].tolist()) if not breed_df.empty else empty_figure()
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False}, key="dash_chart_tree")

    c3, c4 = st.columns(2)
    with c3:
        section_title("처리 상태 비율", f"전체 {fmt_int(total_count)}건")
        fig3 = chart_donut(status_df["상태"].tolist(), status_df["건수"].tolist()) if not status_df.empty else empty_figure()
        st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False}, key="dash_chart_donut")
    with c4:
        section_title("시·도별 접수 건수", "17개 광역자치단체")
        fig4 = chart_hbar(sido_df["지역"].tolist(), sido_df["건수"].tolist()) if not sido_df.empty else empty_figure()
        st.plotly_chart(fig4, use_container_width=True, config={"displayModeBar": False}, key="dash_chart_hbar")

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    section_title("상세 데이터", "최근 500건 · 발생일자 내림차순")
    st.dataframe(table_df, use_container_width=True, hide_index=True, height=300)

    csv = table_df.to_csv(index=False, encoding="utf-8-sig")
    st.download_button("↓  CSV 다운로드", data=csv.encode("utf-8-sig"),
                       file_name="유실유기동물_상세데이터.csv", mime="text/csv",
                       key="dash_btn_dl")

# ══════════════════════════════════════════════
# TAB 2 — 일간 보고서
# ══════════════════════════════════════════════
with tab2:
    target_date = latest_date if pd.notna(latest_date) else date_to
    if isinstance(target_date, pd.Timestamp):
        target_date = target_date.date()

    try:
        daily_report = load_daily_report_data(target_date, sido_sel, status_sel)
    except Exception as e:
        st.error("일간 보고서 데이터를 불러오지 못했습니다.")
        st.code(f"{type(e).__name__}: {e}", language="text")
        daily_report = None

    if daily_report:
        prev_date   = daily_report["prev_date"]
        target_date = daily_report["target_date"]
        summary_df  = daily_report["summary_df"]
        target_row  = summary_df[summary_df["happen_date"] == pd.to_datetime(target_date)]
        prev_row    = summary_df[summary_df["happen_date"] == pd.to_datetime(prev_date)]

        target_total     = int(target_row["total_count"].iloc[0]) if not target_row.empty else 0
        prev_total       = int(prev_row["total_count"].iloc[0])   if not prev_row.empty   else 0
        target_adopt     = int(target_row["adoption_count"].iloc[0])   if not target_row.empty else 0
        target_euth      = int(target_row["euthanasia_count"].iloc[0]) if not target_row.empty else 0
        target_protected = int(target_row["protected_count"].iloc[0])  if not target_row.empty else 0
        delta_total      = target_total - prev_total
        delta_arrow      = "▲" if delta_total >= 0 else "▼"

        st.markdown(f"""
        <div style="display:inline-flex;align-items:center;gap:10px;
            padding:7px 16px;background:{TOKENS['surface_2']};
            border:1px solid {TOKENS['line']};border-radius:8px;
            font-size:12px;color:{TOKENS['ink_2']};margin-bottom:20px;">
            <span style="color:{TOKENS['amber']};font-weight:600;">●</span>
            기준일 <b style="color:{TOKENS['ink']};font-weight:600;">{target_date:%Y년 %m월 %d일}</b>
            <span style="color:{TOKENS['ink_3']};">vs</span>
            <b style="color:{TOKENS['ink']};font-weight:600;">{prev_date:%Y년 %m월 %d일}</b>
        </div>
        """, unsafe_allow_html=True)

        d1, d2, d3, d4 = st.columns(4)
        with d1:
            st.markdown(kpi_card("기준일 접수", fmt_int(target_total),
                                 f"{delta_arrow} 전일 대비 {delta_total:+,}건",
                                 TOKENS["navy"], "건"), unsafe_allow_html=True)
        with d2:
            st.markdown(kpi_card("입양률", pct(target_adopt, target_total),
                                 f"입양 {fmt_int(target_adopt)}건",
                                 TOKENS["green"]), unsafe_allow_html=True)
        with d3:
            st.markdown(kpi_card("안락사율", pct(target_euth, target_total),
                                 f"안락사 {fmt_int(target_euth)}건",
                                 TOKENS["rose"]), unsafe_allow_html=True)
        with d4:
            st.markdown(kpi_card("보호중", fmt_int(target_protected), "기준일 기준",
                                 TOKENS["amber"], "건"), unsafe_allow_html=True)

        st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

        dc1, dc2 = st.columns(2)
        sido_compare = daily_report["sido_compare_df"]
        animal_compare = daily_report["animal_compare_df"]
        with dc1:
            section_title("시·도별 접수 건수 비교", "상위 10개 지역")
            fig_d1 = chart_grouped_bar(
                sido_compare["지역"].tolist(),
                [(f"{prev_date:%m/%d}", sido_compare["전일"].tolist()),
                 (f"{target_date:%m/%d}", sido_compare["기준일"].tolist())],
                colors=[TOKENS["warm_gray"], TOKENS["navy"]],
            ) if not sido_compare.empty else empty_figure()
            st.plotly_chart(fig_d1, use_container_width=True,
                            config={"displayModeBar": False}, key="daily_chart_bar1")
        with dc2:
            section_title("축종별 접수 건수 비교")
            fig_d2 = chart_grouped_bar(
                animal_compare["축종"].tolist(),
                [(f"{prev_date:%m/%d}", animal_compare["전일"].tolist()),
                 (f"{target_date:%m/%d}", animal_compare["기준일"].tolist())],
                colors=[TOKENS["warm_gray"], TOKENS["amber"]],
            ) if not animal_compare.empty else empty_figure()
            st.plotly_chart(fig_d2, use_container_width=True,
                            config={"displayModeBar": False}, key="daily_chart_bar2")

        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        section_title(f"상세 데이터", f"{target_date:%Y.%m.%d} 발생 건")
        daily_detail_df = daily_report["detail_df"]
        st.dataframe(daily_detail_df, use_container_width=True, hide_index=True, height=240)

        csv_d = daily_detail_df.to_csv(index=False, encoding="utf-8-sig")
        st.download_button("↓  일간 데이터 다운로드", data=csv_d.encode("utf-8-sig"),
                           file_name=f"유실유기동물_{target_date:%Y%m%d}.csv",
                           mime="text/csv", key="daily_btn_dl")

# ══════════════════════════════════════════════
# TAB 3 — 월간 보고서
# ══════════════════════════════════════════════
with tab3:
    try:
        monthly_report = load_monthly_report_data(date_to, sido_sel, status_sel)
    except Exception as e:
        st.error("월간 보고서 데이터를 불러오지 못했습니다.")
        st.code(f"{type(e).__name__}: {e}", language="text")
        monthly_report = None

    if monthly_report:
        current_month_start = monthly_report["current_month_start"]
        prev_month_start    = monthly_report["prev_month_start"]
        prev_month_end      = monthly_report["prev_month_end"]

        st.markdown(f"""
        <div style="display:inline-flex;align-items:center;gap:10px;
            padding:7px 16px;background:{TOKENS['surface_2']};
            border:1px solid {TOKENS['line']};border-radius:8px;
            font-size:12px;color:{TOKENS['ink_2']};margin-bottom:20px;">
            <span style="color:{TOKENS['amber']};font-weight:600;">●</span>
            비교 기간
            <b style="color:{TOKENS['ink']};font-weight:600;">{prev_month_start:%Y년 %m월}</b>
            <span style="color:{TOKENS['ink_3']};">→</span>
            <b style="color:{TOKENS['ink']};font-weight:600;">{current_month_start:%Y년 %m월}</b>
        </div>
        """, unsafe_allow_html=True)

        monthly_kpi_df = monthly_report["monthly_kpi_df"]
        cur_kpi_rows = monthly_kpi_df[monthly_kpi_df["period"] == "current"]
        prev_kpi_rows = monthly_kpi_df[monthly_kpi_df["period"] == "prev"]
        current_kpi = cur_kpi_rows.iloc[0].to_dict() if not cur_kpi_rows.empty else {}
        prev_kpi    = prev_kpi_rows.iloc[0].to_dict() if not prev_kpi_rows.empty else {}

        current_total     = int(current_kpi.get("total_count") or 0)
        prev_total        = int(prev_kpi.get("total_count") or 0)
        current_adopt     = int(current_kpi.get("adoption_count") or 0)
        current_euth      = int(current_kpi.get("euthanasia_count") or 0)
        current_protected = int(current_kpi.get("protected_count") or 0)
        month_delta       = current_total - prev_total
        month_delta_pct   = f"{(month_delta / prev_total * 100):+.1f}%" if prev_total else "비교 불가"
        delta_arrow_m     = "▲" if month_delta >= 0 else "▼"

        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.markdown(kpi_card("이번 달 접수", fmt_int(current_total),
                                 f"{delta_arrow_m} 전월 대비 {month_delta:+,}건 ({month_delta_pct})",
                                 TOKENS["navy"], "건"), unsafe_allow_html=True)
        with m2:
            st.markdown(kpi_card("입양률", pct(current_adopt, current_total),
                                 f"입양 {fmt_int(current_adopt)}건",
                                 TOKENS["green"]), unsafe_allow_html=True)
        with m3:
            st.markdown(kpi_card("안락사율", pct(current_euth, current_total),
                                 f"안락사 {fmt_int(current_euth)}건",
                                 TOKENS["rose"]), unsafe_allow_html=True)
        with m4:
            st.markdown(kpi_card("보호중", fmt_int(current_protected),
                                 "이번 달 기준", TOKENS["amber"], "건"), unsafe_allow_html=True)

        st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

        mc1, mc2 = st.columns(2)
        sido_month_df  = monthly_report["sido_month_df"]
        month_daily_df = monthly_report["month_daily_df"]
        with mc1:
            section_title("시·도별 월간 접수 건수 비교", "상위 10개 지역")
            fig_m1 = chart_grouped_bar(
                sido_month_df["지역"].tolist(),
                [(f"{prev_month_start:%Y.%m}", sido_month_df["전월"].tolist()),
                 (f"{current_month_start:%Y.%m}", sido_month_df["이번월"].tolist())],
                colors=[TOKENS["warm_gray"], TOKENS["navy"]],
            ) if not sido_month_df.empty else empty_figure()
            st.plotly_chart(fig_m1, use_container_width=True,
                            config={"displayModeBar": False}, key="monthly_chart_bar1")
        with mc2:
            section_title(f"{current_month_start:%Y년 %m월} 일별 발생", "이번 달")
            fig_m2 = chart_vbar(month_daily_df["일"].tolist(),
                                month_daily_df["건수"].tolist(),
                                color=TOKENS["navy"]) if not month_daily_df.empty else empty_figure()
            st.plotly_chart(fig_m2, use_container_width=True,
                            config={"displayModeBar": False}, key="monthly_chart_vbar")

        status_month_df = monthly_report["status_month_df"]
        md1, md2 = st.columns(2)
        with md1:
            section_title("처리 상태", f"{prev_month_start:%Y년 %m월}")
            prev_status = status_month_df[status_month_df["period"] == "전월"] if not status_month_df.empty else pd.DataFrame()
            fig_s1 = chart_donut(prev_status["상태"].tolist(), prev_status["건수"].tolist(), total_label="전월 합계") if not prev_status.empty else empty_figure()
            st.plotly_chart(fig_s1, use_container_width=True,
                            config={"displayModeBar": False}, key="monthly_chart_donut1")
        with md2:
            section_title("처리 상태", f"{current_month_start:%Y년 %m월}")
            current_status = status_month_df[status_month_df["period"] == "이번월"] if not status_month_df.empty else pd.DataFrame()
            fig_s2 = chart_donut(current_status["상태"].tolist(), current_status["건수"].tolist(), total_label="이번 달 합계") if not current_status.empty else empty_figure()
            st.plotly_chart(fig_s2, use_container_width=True,
                            config={"displayModeBar": False}, key="monthly_chart_donut2")

        # AI 인사이트 카드
        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
        st.markdown(f"""
        <div style="background:{TOKENS['surface']};border:1px solid {TOKENS['line']};
            border-radius:14px;padding:20px 24px;margin-bottom:8px;">
            <div style="display:flex;align-items:center;justify-content:space-between;">
                <div style="display:flex;align-items:center;gap:12px;">
                    <div style="width:32px;height:32px;border-radius:9px;
                        background:linear-gradient(160deg,{TOKENS['navy_2']},{TOKENS['navy']});
                        display:grid;place-items:center;color:{TOKENS['amber_2']};
                        font-size:14px;">✦</div>
                    <div>
                        <div style="font-size:14px;font-weight:600;color:{TOKENS['ink']};
                            letter-spacing:-0.005em;">AI 인사이트</div>
                        <div style="font-size:11.5px;color:{TOKENS['ink_3']};margin-top:2px;">
                            현재 월간 통계를 바탕으로 주요 인사이트와 정책 제언을 생성합니다.
                        </div>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if "ai_insight" not in st.session_state:
            st.session_state.ai_insight = None

        if st.button("AI 인사이트 생성", key="monthly_btn_ai"):
            with st.spinner("AI가 분석 중입니다..."):
                try:
                    import anthropic
                    client = anthropic.Anthropic()
                    prompt = f"""당신은 동물복지 정책 분석 전문가입니다.
아래 유실유기동물 월간 통계 데이터를 바탕으로 한국어로 간결한 인사이트를 작성해 주세요.

이번 달 총 접수: {current_total:,}건
전월 총 접수: {prev_total:,}건
입양: {current_adopt:,}건
안락사: {current_euth:,}건
보호중: {current_protected:,}건

시도별 월간 비교:
{sido_month_df.to_string(index=False)}

처리 상태:
{current_status.to_string(index=False) if not current_status.empty else '데이터 없음'}

작성 항목:
1. 핵심 요약 3개
2. 주목할 지역 또는 추세
3. 정책적 시사점
4. 다음 달 확인이 필요한 지표
"""
                    message = client.messages.create(
                        model="claude-opus-4-5",
                        max_tokens=1024,
                        messages=[{"role": "user", "content": prompt}],
                    )
                    st.session_state.ai_insight = message.content[0].text
                except Exception as e:
                    st.session_state.ai_insight = None
                    st.error(f"AI 인사이트 생성 중 오류가 발생했습니다: {type(e).__name__}: {e}")

        if st.session_state.ai_insight:
            st.markdown(f"""
            <div style="background:{TOKENS['surface_2']};
                border:1px solid {TOKENS['line']};
                border-left:3px solid {TOKENS['amber']};
                border-radius:12px;padding:18px 22px;margin-top:8px;">
                <div style="font-size:12px;font-weight:600;color:{TOKENS['amber']};
                    margin-bottom:10px;letter-spacing:0.04em;text-transform:uppercase;">
                    ✦ AI 분석 결과
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown(st.session_state.ai_insight)

            st.download_button(
                "↓  AI 인사이트 다운로드 (txt)",
                data=st.session_state.ai_insight.encode("utf-8"),
                file_name=f"AI_인사이트_{current_month_start:%Y년%m월}.txt",
                mime="text/plain",
                key="monthly_btn_ai_dl",
            )

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        csv_m = table_df.to_csv(index=False, encoding="utf-8-sig")
        st.download_button("↓  현재 필터 상세 데이터 다운로드",
                           data=csv_m.encode("utf-8-sig"),
                           file_name="유실유기동물_현재필터.csv",
                           mime="text/csv", key="monthly_btn_dl")
