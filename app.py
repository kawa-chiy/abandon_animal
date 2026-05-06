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

ALL_OPTION = "전체 (미선택 시 전체 표시)"

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
# 커스텀 CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Noto Sans KR', sans-serif !important;
}

.stApp {
    background: oklch(97.5% 0.006 220);
}

[data-testid="stSidebar"] {
    background: #151f32 !important;
    border-right: 1px solid rgba(255,255,255,0.07);
}
[data-testid="stSidebar"] * {
    color: #e2e8f0 !important;
}
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stDateInput label,
[data-testid="stSidebar"] .stMarkdown p {
    color: #94a3b8 !important;
    font-size: 12px !important;
}
[data-testid="stSidebar"] [data-testid="stSelectbox"] > div > div {
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    border-radius: 8px !important;
    color: #e2e8f0 !important;
}
[data-testid="stSidebar"] [data-testid="stDateInput"] input {
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    color: #e2e8f0 !important;
    border-radius: 8px !important;
}

.stTabs [data-baseweb="tab-list"] {
    background: #f1f5f9;
    border-radius: 10px;
    padding: 4px;
    gap: 2px;
    border: none;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 7px;
    padding: 8px 18px;
    font-size: 13px;
    font-weight: 500;
    color: #64748b;
    background: transparent;
    border: none;
}
.stTabs [aria-selected="true"] {
    background: #ffffff !important;
    color: #0f172a !important;
    font-weight: 600;
    box-shadow: 0 1px 3px rgba(15,23,42,0.08);
}
.stTabs [data-baseweb="tab-highlight"],
.stTabs [data-baseweb="tab-border"] {
    display: none;
}

[data-testid="stMetric"] {
    background: #ffffff;
    border-radius: 12px;
    padding: 18px 20px !important;
    box-shadow: 0 1px 3px rgba(15,23,42,0.06), 0 1px 2px rgba(15,23,42,0.04);
}
[data-testid="stMetricLabel"] {
    font-size: 12px !important;
    color: #64748b !important;
    font-weight: 500;
}
[data-testid="stMetricValue"] {
    font-size: 28px !important;
    font-weight: 700 !important;
    color: #0f172a !important;
    letter-spacing: -0.03em;
}
[data-testid="stMetricDelta"] {
    font-size: 12px !important;
    font-weight: 500 !important;
}

hr {
    border-color: rgba(255,255,255,0.07) !important;
    margin: 12px 0 !important;
}

[data-testid="stDataFrame"] {
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 1px 3px rgba(15,23,42,0.06);
}

.stDownloadButton > button {
    background: #ffffff !important;
    border: 1px solid #e8edf2 !important;
    border-radius: 8px !important;
    color: #0f172a !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    padding: 8px 18px !important;
    transition: all 0.15s !important;
    font-family: 'Noto Sans KR', sans-serif !important;
    width: 100%;
}
.stDownloadButton > button:hover {
    border-color: #0d9488 !important;
    color: #0d9488 !important;
}

.stButton > button {
    background: linear-gradient(135deg, #6366f1, #0d9488) !important;
    border: none !important;
    border-radius: 9px !important;
    color: white !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    padding: 10px 22px !important;
    font-family: 'Noto Sans KR', sans-serif !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.15);
}
.stButton > button:hover {
    opacity: 0.9;
    box-shadow: 0 4px 16px rgba(0,0,0,0.2);
}

[data-testid="stSidebar"] .stButton > button {
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    color: #94a3b8 !important;
    box-shadow: none !important;
    width: 100%;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(255,255,255,0.1) !important;
    color: #e2e8f0 !important;
}

.section-header {
    font-size: 13px;
    font-weight: 600;
    color: #0f172a;
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 0 2px 8px;
    border-bottom: 1px solid #e8edf2;
    margin-bottom: 4px;
}

.modebar { display: none !important; }
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
            '<div style="text-align:center;margin-bottom:8px;">'
            '<div style="width:60px;height:60px;border-radius:16px;'
            'background:linear-gradient(135deg,#0d9488,#6366f1);'
            'display:flex;align-items:center;justify-content:center;'
            'font-size:28px;margin:0 auto 16px;">🐾</div></div>'
            '<h2 style="text-align:center;margin-bottom:4px;font-size:20px;'
            'font-weight:700;color:#0f172a;">유실유기동물 현황 대시보드</h2>'
            '<p style="text-align:center;color:#64748b;margin-bottom:32px;font-size:13px;">'
            '동물자유연대 구성원 전용입니다.</p>',
            unsafe_allow_html=True,
        )
        if "oauth_state" not in st.session_state:
            st.session_state["oauth_state"] = secrets.token_hex(16)
        st.link_button(
            "🔐 Google 계정으로 로그인",
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
    job_config = bigquery.QueryJobConfig(
        query_parameters=params or []
    )
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
        SELECT
          happen_date AS dt,
          COUNT(*) AS cnt
        FROM {TABLE_NAME}
        WHERE {where_sql}
        GROUP BY happen_date
        ORDER BY happen_date
    """

    status_query = f"""
        SELECT
          COALESCE(process_state, '미상') AS status_name,
          COUNT(*) AS cnt
        FROM {TABLE_NAME}
        WHERE {where_sql}
        GROUP BY 1
        ORDER BY 2 DESC
    """

    sido_query = f"""
        SELECT
          COALESCE(sido, '미상') AS region,
          COUNT(*) AS cnt
        FROM {TABLE_NAME}
        WHERE {where_sql}
        GROUP BY 1
        ORDER BY 2 DESC
    """

    breed_query = f"""
        SELECT
          CONCAT(COALESCE(breed, '미상'), '(', COALESCE(animal_type, '미상'), ')') AS breed_name,
          COUNT(*) AS cnt
        FROM {TABLE_NAME}
        WHERE {where_sql}
        GROUP BY 1
        ORDER BY 2 DESC
        LIMIT 12
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
        FROM {TABLE_NAME}
        WHERE {where_sql}
        ORDER BY happen_date DESC, notice_no DESC
        LIMIT 500
    """

    monthly_daily_query = f"""
        SELECT
          CAST(EXTRACT(DAY FROM happen_date) AS STRING) AS day_num,
          COUNT(*) AS cnt
        FROM {TABLE_NAME}
        WHERE {where_sql}
        GROUP BY 1
        ORDER BY CAST(day_num AS INT64)
    """

    kpi_query = f"""
        SELECT
          COUNT(*) AS total_count,
          COUNTIF(process_state = '입양') AS adoption_count,
          COUNTIF(process_state = '안락사') AS euthanasia_count,
          COUNTIF(process_state = '보호중') AS protected_count,
          MAX(happen_date) AS latest_date
        FROM {TABLE_NAME}
        WHERE {where_sql}
    """

    animal_type_query = f"""
        SELECT
          COALESCE(animal_type, '미상') AS animal_type_name,
          COUNT(*) AS cnt
        FROM {TABLE_NAME}
        WHERE {where_sql}
        GROUP BY 1
        ORDER BY 2 DESC
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
    monthly_daily_raw = run_bq_query(monthly_daily_query, params)
    monthly_daily_raw["day_num"] = monthly_daily_raw["day_num"] + "일"
    monthly_daily_df = monthly_daily_raw.rename(columns={"day_num": "일", "cnt": "건수"})
    kpi_df = run_bq_query(kpi_query, params)
    animal_type_df = run_bq_query(animal_type_query, params).rename(columns={"animal_type_name": "축종", "cnt": "건수"})

    return {
        "daily_df": daily_df,
        "status_df": status_df,
        "sido_df": sido_df,
        "breed_df": breed_df,
        "table_df": table_df,
        "monthly_daily_df": monthly_daily_df,
        "kpi_df": kpi_df,
        "animal_type_df": animal_type_df,
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
        SELECT
          happen_date,
          COUNT(*) AS total_count,
          COUNTIF(process_state = '입양') AS adoption_count,
          COUNTIF(process_state = '안락사') AS euthanasia_count,
          COUNTIF(process_state = '보호중') AS protected_count
        FROM {TABLE_NAME}
        WHERE {where_sql}
        GROUP BY happen_date
    """

    sido_compare_query = f"""
        SELECT
          COALESCE(sido, '미상') AS region,
          SUM(IF(happen_date = @prev_date, 1, 0)) AS prev_cnt,
          SUM(IF(happen_date = @target_date, 1, 0)) AS target_cnt
        FROM {TABLE_NAME}
        WHERE {where_sql}
        GROUP BY 1
        ORDER BY 3 DESC, 2 DESC
        LIMIT 10
    """

    animal_compare_query = f"""
        SELECT
          COALESCE(animal_type, '미상') AS animal_name,
          SUM(IF(happen_date = @prev_date, 1, 0)) AS prev_cnt,
          SUM(IF(happen_date = @target_date, 1, 0)) AS target_cnt
        FROM {TABLE_NAME}
        WHERE {where_sql}
        GROUP BY 1
        ORDER BY 3 DESC, 2 DESC
    """

    detail_query = f"""
        SELECT
          notice_no AS col_notice_no,
          FORMAT_DATE('%Y.%m.%d', happen_date) AS col_happen_date,
          happen_place AS col_happen_place,
          animal_type AS col_animal_type,
          breed AS col_breed,
          age AS col_age,
          process_state AS col_process_state,
          special_mark AS col_special,
          care_name AS col_care_name,
          org_name AS col_org_name
        FROM {TABLE_NAME}
        WHERE happen_date = @target_date
        ORDER BY notice_no DESC
        LIMIT 300
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
        "target_date": target_date,
        "prev_date": prev_date,
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
        SELECT
          IF(happen_date < @current_month_start, 'prev', 'current') AS period,
          COUNT(*) AS total_count,
          COUNTIF(process_state = '입양') AS adoption_count,
          COUNTIF(process_state = '안락사') AS euthanasia_count,
          COUNTIF(process_state = '보호중') AS protected_count
        FROM {TABLE_NAME}
        WHERE {where_sql}
        GROUP BY 1
    """

    sido_month_query = f"""
        SELECT
          COALESCE(sido, '미상') AS region,
          SUM(IF(happen_date < @current_month_start, 1, 0)) AS prev_cnt,
          SUM(IF(happen_date >= @current_month_start, 1, 0)) AS cur_cnt
        FROM {TABLE_NAME}
        WHERE {where_sql}
        GROUP BY 1
        ORDER BY 3 DESC, 2 DESC
        LIMIT 10
    """

    month_daily_query = f"""
        SELECT
          CAST(EXTRACT(DAY FROM happen_date) AS STRING) AS day_num,
          COUNT(*) AS cnt
        FROM {TABLE_NAME}
        WHERE happen_date BETWEEN @current_month_start AND @date_to
        GROUP BY 1
        ORDER BY CAST(day_num AS INT64)
    """

    status_month_query = f"""
        SELECT
          IF(happen_date < @current_month_start, 'prev', 'current') AS period,
          COALESCE(process_state, '미상') AS status_name,
          COUNT(*) AS cnt
        FROM {TABLE_NAME}
        WHERE {where_sql}
        GROUP BY 1, 2
        ORDER BY 1, 3 DESC
    """

    sido_month_df = run_bq_query(sido_month_query, params).rename(columns={
        "region": "지역", "prev_cnt": "전월", "cur_cnt": "이번월"
    })
    month_daily_raw = run_bq_query(month_daily_query, params)
    month_daily_raw["day_num"] = month_daily_raw["day_num"] + "일"
    month_daily_df = month_daily_raw.rename(columns={"day_num": "일", "cnt": "건수"})
    status_month_raw = run_bq_query(status_month_query, params)
    # period 값을 한글로 변환하여 기존 코드와 호환
    status_month_raw["period"] = status_month_raw["period"].map({"prev": "전월", "current": "이번월"})
    status_month_df = status_month_raw.rename(columns={"status_name": "상태", "cnt": "건수"})

    return {
        "monthly_kpi_df": run_bq_query(monthly_kpi_query, params),
        "sido_month_df": sido_month_df,
        "month_daily_df": month_daily_df,
        "status_month_df": status_month_df,
        "current_month_start": current_month_start,
        "prev_month_start": prev_month_start,
        "prev_month_end": prev_month_end,
    }

# ─────────────────────────────────────────────
# 색상 테마
# ─────────────────────────────────────────────
COLORS = {
    "primary": "#0d9488",
    "primary_light": "#5eead4",
    "secondary": "#f59e0b",
    "indigo": "#6366f1",
    "rose": "#f87171",
    "green": "#10b981",
    "blue": "#3b82f6",
    "gray": "#94a3b8",
    "bg": "#f8fafc",
    "surface": "#ffffff",
    "text": "#0f172a",
    "text2": "#64748b",
}

STATUS_COLORS = {
    "보호중": "#3b82f6",
    "입양":   "#10b981",
    "자연사": "#94a3b8",
    "안락사": "#f87171",
    "반환":   "#f59e0b",
    "기증":   "#a78bfa",
    "방사":   "#34d399",
    "미상":   "#cbd5e1",
}

PLOTLY_LAYOUT = dict(
    font=dict(family="Noto Sans KR, sans-serif", size=12, color=COLORS["text2"]),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(t=16, b=8, l=8, r=8),
    legend=dict(
        bgcolor="rgba(0,0,0,0)",
        bordercolor="rgba(0,0,0,0)",
        font=dict(size=12),
        orientation="h",
        y=-0.15,
    ),
    xaxis=dict(showgrid=False, showline=False, zeroline=False, tickfont=dict(size=11)),
    yaxis=dict(gridcolor="#f1f5f9", showline=False, zeroline=False, tickfont=dict(size=11)),
    hoverlabel=dict(
        bgcolor=COLORS["surface"],
        bordercolor=COLORS["gray"],
        font=dict(family="Noto Sans KR", size=12, color=COLORS["text"]),
    ),
)

# ─────────────────────────────────────────────
# 차트 헬퍼
# ─────────────────────────────────────────────
def empty_figure(message="표시할 데이터가 없습니다"):
    fig = go.Figure()
    layout = {k: v for k, v in PLOTLY_LAYOUT.items() if k not in ("xaxis", "yaxis")}
    layout.update(
        height=240,
        annotations=[dict(text=message, x=0.5, y=0.5, showarrow=False, font=dict(size=13, color=COLORS["text2"]))],
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
    )
    fig.update_layout(**layout)
    return fig


def apply_layout(fig, **kwargs):
    base = dict(**PLOTLY_LAYOUT)
    base.update(kwargs)
    fig.update_layout(**base)
    return fig


def chart_area(df, x_col, y_col, color=None):
    if df.empty:
        return empty_figure()
    color = color or COLORS["primary"]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df[x_col], y=df[y_col],
        mode="lines",
        line=dict(color=color, width=2.5, shape="spline"),
        fill="tozeroy",
        fillcolor=f"rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:7],16)},0.08)",
        hovertemplate="%{x}<br>%{y:,}건<extra></extra>",
    ))
    apply_layout(
        fig,
        xaxis=dict(showgrid=False, showline=False, zeroline=False, tickfont=dict(size=10), tickangle=-30, nticks=10),
        yaxis=dict(gridcolor="#f1f5f9", showline=False, zeroline=False, tickfont=dict(size=10)),
        height=240,
    )
    return fig


def chart_donut(labels, values, colors=None):
    if len(labels) == 0 or sum(values) == 0:
        return empty_figure()
    colors = colors or [STATUS_COLORS.get(str(label), COLORS["primary"]) for label in labels]
    fig = go.Figure(go.Pie(
        labels=labels,
        values=values,
        hole=0.52,
        marker=dict(colors=colors, line=dict(color="#ffffff", width=2)),
        textfont=dict(size=11, family="Noto Sans KR"),
        hovertemplate="%{label}: %{value:,}건 (%{percent})<extra></extra>",
    ))
    total = sum(values)
    layout_args = {k: v for k, v in PLOTLY_LAYOUT.items() if k not in ["xaxis", "yaxis", "legend", "margin"]}
    fig.update_layout(
        **layout_args,
        annotations=[dict(text=f"<b>{total:,}건</b>", x=0.5, y=0.5, font=dict(size=14, color=COLORS["text"]), showarrow=False)],
        legend=dict(orientation="h", y=-0.12, font=dict(size=11), bgcolor="rgba(0,0,0,0)"),
        height=290,
        margin=dict(t=10, b=30, l=10, r=10),
    )
    return fig


def chart_hbar(labels, values, color=None):
    if len(labels) == 0:
        return empty_figure()
    color = color or COLORS["primary"]
    fig = go.Figure(go.Bar(
        y=labels,
        x=values,
        orientation="h",
        marker=dict(
            color=values,
            colorscale=[[0, f"rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:7],16)},0.35)"], [1, color]],
            showscale=False,
        ),
        text=[f"{int(v):,}" for v in values],
        textposition="outside",
        textfont=dict(size=11, color=COLORS["text2"]),
        hovertemplate="%{y}: %{x:,}건<extra></extra>",
    ))
    apply_layout(
        fig,
        xaxis=dict(showgrid=True, gridcolor="#f1f5f9", showline=False, zeroline=False, tickfont=dict(size=10)),
        yaxis=dict(showgrid=False, showline=False, zeroline=False, tickfont=dict(size=11), autorange="reversed"),
        height=380,
        margin=dict(t=10, b=8, l=8, r=50),
    )
    return fig


def chart_grouped_bar(categories, series, colors=None):
    if len(categories) == 0:
        return empty_figure()
    colors = colors or [COLORS["gray"], COLORS["primary"]]
    fig = go.Figure()
    for i, (name, data) in enumerate(series):
        fig.add_trace(go.Bar(
            name=name,
            x=categories,
            y=data,
            marker=dict(color=colors[i % len(colors)]),
            hovertemplate=f"{name}<br>%{{x}}: %{{y:,}}건<extra></extra>",
        ))
    apply_layout(
        fig,
        barmode="group",
        bargap=0.25,
        bargroupgap=0.06,
        xaxis=dict(showgrid=False, showline=False, zeroline=False, tickfont=dict(size=11), tickangle=-30),
        yaxis=dict(gridcolor="#f1f5f9", showline=False, zeroline=False, tickfont=dict(size=10)),
        height=260,
        legend=dict(orientation="h", y=-0.2, font=dict(size=12), bgcolor="rgba(0,0,0,0)"),
    )
    return fig


def chart_treemap(labels, values):
    if len(labels) == 0:
        return empty_figure()
    fig = go.Figure(go.Treemap(
        labels=labels,
        values=values,
        parents=[""] * len(labels),
        marker=dict(
            colorscale=[[0,"#99f6e4"],[0.3,"#2dd4bf"],[0.6,"#0d9488"],[1,"#0f766e"]],
            cmin=min(values),
            cmax=max(values),
            showscale=False,
        ),
        textfont=dict(size=11, family="Noto Sans KR"),
        hovertemplate="%{label}: %{value:,}건<extra></extra>",
        tiling=dict(pad=2),
        texttemplate="%{label}<br>%{value:,}건",
    ))
    apply_layout(fig, height=240, margin=dict(t=4, b=4, l=4, r=4))
    return fig


def chart_vbar(categories, values, color=None):
    if len(categories) == 0:
        return empty_figure()
    color = color or COLORS["indigo"]
    fig = go.Figure(go.Bar(
        x=categories,
        y=values,
        marker=dict(color=color, opacity=0.85),
        hovertemplate="%{x}: %{y:,}건<extra></extra>",
    ))
    apply_layout(
        fig,
        xaxis=dict(showgrid=False, showline=False, zeroline=False, tickfont=dict(size=10), tickangle=-45, nticks=10),
        yaxis=dict(gridcolor="#f1f5f9", showline=False, zeroline=False, tickfont=dict(size=10)),
        height=260,
        margin=dict(t=10, b=10, l=8, r=8),
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


def kpi_card(label, value, delta, delta_type="neutral", border_color="#0d9488"):
    if delta_type == "up":
        delta_style = "color:#0f766e; background:#ccfbf1;"
        arrow = "▲ "
    elif delta_type == "down":
        delta_style = "color:#e11d48; background:#fee2e2;"
        arrow = "▼ "
    else:
        delta_style = "color:#64748b; background:#f1f5f9;"
        arrow = ""
    return f"""
    <div style="
        background:#ffffff;
        border-radius:12px;
        padding:18px 20px;
        box-shadow:0 1px 3px rgba(15,23,42,0.06);
        border-left:3px solid {border_color};
        min-height:110px;
    ">
        <div style="font-size:12px;font-weight:500;color:#64748b;margin-bottom:10px;">{label}</div>
        <div style="font-size:26px;font-weight:700;color:#0f172a;letter-spacing:-0.03em;line-height:1;margin-bottom:10px;">{value}</div>
        <span style="{delta_style} display:inline-block;padding:2px 9px;border-radius:99px;font-size:11px;font-weight:500;">{arrow}{delta}</span>
    </div>"""


def section_title(icon, text):
    st.markdown(f"""
    <div class="section-header">
        {icon} {text}
    </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 사이드바
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding:4px 0 12px;">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:4px;">
            <div style="width:34px;height:34px;border-radius:10px;background:#0d9488;display:flex;align-items:center;justify-content:center;font-size:16px;">🐾</div>
            <div>
                <div style="color:#ffffff;font-weight:600;font-size:13px;">유실유기동물</div>
                <div style="color:#94a3b8;font-size:11px;">현황 대시보드</div>
            </div>
        </div>
    </div>
    <hr>
    """, unsafe_allow_html=True)

    name    = st.session_state.get("user_name", "사용자")
    email   = st.session_state.get("user_email", "")
    picture = st.session_state.get("user_picture", "")
    initial = name[0] if name else "?"

    avatar = (
        f"<img src='{picture}' style='width:34px;height:34px;border-radius:50%;object-fit:cover;'>"
        if picture else
        f"<div style='width:34px;height:34px;border-radius:50%;font-size:13px;"
        f"background:linear-gradient(135deg,#0d9488,#6366f1);font-weight:600;"
        f"display:flex;align-items:center;justify-content:center;color:white;flex-shrink:0;'>{initial}</div>"
    )

    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:10px;padding:4px 0 12px;">
        {avatar}
        <div style="flex:1;min-width:0;">
            <div style="color:#f1f5f9;font-size:12.5px;font-weight:500;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{name} 님 환영합니다 👋</div>
            <div style="color:#64748b;font-size:11px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{email}</div>
        </div>
    </div>
    <hr>
    """, unsafe_allow_html=True)

    st.markdown('<div style="color:#475569;font-size:10px;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;margin-bottom:10px;">필터</div>', unsafe_allow_html=True)

    st.markdown('<div style="color:#94a3b8;font-size:11px;font-weight:500;margin-bottom:4px;">시/도 (지역)</div>', unsafe_allow_html=True)
    sido_options = [
        ALL_OPTION,
        "서울특별시",
        "경기도",
        "부산광역시",
        "인천광역시",
        "대구광역시",
        "광주광역시",
        "대전광역시",
        "울산광역시",
        "세종특별자치시",
        "경상남도",
        "경상북도",
        "전라남도",
        "전북특별자치도",
        "충청남도",
        "충청북도",
        "강원특별자치도",
        "제주특별자치도",
    ]
    sido_sel = st.selectbox("시도 선택", sido_options, label_visibility="collapsed")

    st.markdown('<div style="color:#94a3b8;font-size:11px;font-weight:500;margin:10px 0 4px;">처리 상태</div>', unsafe_allow_html=True)
    status_options = [ALL_OPTION, "보호중", "입양", "자연사", "안락사", "반환", "기증", "방사"]
    status_sel = st.selectbox("상태 선택", status_options, label_visibility="collapsed")

    st.markdown('<div style="color:#94a3b8;font-size:11px;font-weight:500;margin:10px 0 4px;">접수일 범위</div>', unsafe_allow_html=True)
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        date_from = st.date_input("시작일", value=date(2026, 1, 1), label_visibility="collapsed")
    with col_d2:
        date_to = st.date_input("종료일", value=date.today(), label_visibility="collapsed")

    if date_from > date_to:
        st.error("시작일은 종료일보다 늦을 수 없습니다.")
        st.stop()

    st.markdown('<hr>', unsafe_allow_html=True)
    st.markdown(f"""
    <div style="color:#475569;font-size:10.5px;line-height:1.6;padding-bottom:12px;">
        데이터 출처: BigQuery<br>
        테이블: {DATASET_ID}.{TABLE_ID}<br>
        캐시: 1시간
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

daily_df = dashboard_data["daily_df"]
status_df = dashboard_data["status_df"]
sido_df = dashboard_data["sido_df"]
breed_df = dashboard_data["breed_df"]
table_df = dashboard_data["table_df"]
monthly_daily_df = dashboard_data["monthly_daily_df"]
kpi_df = dashboard_data["kpi_df"]
animal_type_df = dashboard_data["animal_type_df"]

kpi = kpi_df.iloc[0].to_dict() if not kpi_df.empty else {}
total_count = int(kpi.get("total_count") or 0)
adoption_count = int(kpi.get("adoption_count") or 0)
euthanasia_count = int(kpi.get("euthanasia_count") or 0)
protected_count = int(kpi.get("protected_count") or 0)
latest_date = kpi.get("latest_date")

# ─────────────────────────────────────────────
# 상단 헤더
# ─────────────────────────────────────────────
latest_text = latest_date.strftime("%Y-%m-%d") if pd.notna(latest_date) else "데이터 없음"
st.markdown(f"""
<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:20px;">
    <div>
        <h1 style="font-size:20px;font-weight:700;color:#0f172a;margin:0;display:flex;align-items:center;gap:8px;">
            🐾 유실유기동물 현황 대시보드
        </h1>
        <p style="font-size:12px;color:#94a3b8;margin:4px 0 0;">
            데이터 출처: BigQuery · 마지막 데이터 기준일: {latest_text}
        </p>
    </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 탭
# ─────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📊  대시보드", "📅  일간 보고서", "📆  월간 보고서"])

# ══════════════════════════════════════════════
# TAB 1 — 대시보드
# ══════════════════════════════════════════════
with tab1:
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(kpi_card("총 발생 건수", f"{fmt_int(total_count)}건", "선택 기간 기준", "neutral", "#0d9488"), unsafe_allow_html=True)
    with k2:
        st.markdown(kpi_card("입양률", pct(adoption_count, total_count), f"입양 {fmt_int(adoption_count)}건", "up", "#d97706"), unsafe_allow_html=True)
    with k3:
        st.markdown(kpi_card("안락사율", pct(euthanasia_count, total_count), f"안락사 {fmt_int(euthanasia_count)}건", "neutral", "#e11d48"), unsafe_allow_html=True)
    with k4:
        st.markdown(kpi_card("현재 보호중", f"{fmt_int(protected_count)}건", "선택 기간 기준", "neutral", "#6366f1"), unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    c1, c2 = st.columns([3, 2])
    with c1:
        section_title("📈", "일별 유기동물 발생 추이")
        fig = chart_area(daily_df, "날짜", "건수")
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, key="dash_chart_area")

    with c2:
        section_title("🌿", "축종·품종별 비율 (상위 12)")
        fig2 = chart_treemap(breed_df["품종"].tolist(), breed_df["건수"].tolist()) if not breed_df.empty else empty_figure()
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False}, key="dash_chart_tree")

    c3, c4 = st.columns(2)
    with c3:
        section_title("🔄", "처리 상태 비율")
        fig3 = chart_donut(status_df["상태"].tolist(), status_df["건수"].tolist()) if not status_df.empty else empty_figure()
        st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False}, key="dash_chart_donut")

    with c4:
        section_title("📍", "시/도별 접수 건수")
        fig4 = chart_hbar(sido_df["지역"].tolist(), sido_df["건수"].tolist()) if not sido_df.empty else empty_figure()
        st.plotly_chart(fig4, use_container_width=True, config={"displayModeBar": False}, key="dash_chart_hbar")

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    section_title("📋", "상세 데이터")
    st.dataframe(table_df, use_container_width=True, hide_index=True, height=280)

    csv = table_df.to_csv(index=False, encoding="utf-8-sig")
    st.download_button("↓  CSV 다운로드", data=csv.encode("utf-8-sig"), file_name="유실유기동물_상세데이터.csv", mime="text/csv", key="dash_btn_dl")

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
        prev_date = daily_report["prev_date"]
        target_date = daily_report["target_date"]
        summary_df = daily_report["summary_df"]
        target_row = summary_df[summary_df["happen_date"] == pd.to_datetime(target_date)]
        prev_row = summary_df[summary_df["happen_date"] == pd.to_datetime(prev_date)]

        target_total = int(target_row["total_count"].iloc[0]) if not target_row.empty else 0
        prev_total = int(prev_row["total_count"].iloc[0]) if not prev_row.empty else 0
        target_adopt = int(target_row["adoption_count"].iloc[0]) if not target_row.empty else 0
        target_euth = int(target_row["euthanasia_count"].iloc[0]) if not target_row.empty else 0
        target_protected = int(target_row["protected_count"].iloc[0]) if not target_row.empty else 0
        delta_total = target_total - prev_total

        st.markdown(f"""
        <div style="display:inline-flex;align-items:center;gap:8px;padding:6px 16px;
            background:#ccfbf1;border-radius:8px;font-size:12px;font-weight:500;
            color:#0f766e;margin-bottom:20px;">
            📅 기준일: {target_date:%Y년 %m월 %d일} vs {prev_date:%Y년 %m월 %d일}
        </div>
        """, unsafe_allow_html=True)

        d1, d2, d3, d4 = st.columns(4)
        with d1:
            st.markdown(kpi_card("기준일 접수", f"{fmt_int(target_total)}건", f"전일 대비 {delta_total:+,}건", "up" if delta_total >= 0 else "down", "#0d9488"), unsafe_allow_html=True)
        with d2:
            st.markdown(kpi_card("입양률", pct(target_adopt, target_total), f"입양 {fmt_int(target_adopt)}건", "neutral", "#d97706"), unsafe_allow_html=True)
        with d3:
            st.markdown(kpi_card("안락사율", pct(target_euth, target_total), f"안락사 {fmt_int(target_euth)}건", "neutral", "#e11d48"), unsafe_allow_html=True)
        with d4:
            st.markdown(kpi_card("보호중", f"{fmt_int(target_protected)}건", "기준일 기준", "neutral", "#6366f1"), unsafe_allow_html=True)

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

        dc1, dc2 = st.columns(2)
        sido_compare = daily_report["sido_compare_df"]
        animal_compare = daily_report["animal_compare_df"]
        with dc1:
            section_title("📍", "시/도별 접수 건수 비교")
            fig_d1 = chart_grouped_bar(
                sido_compare["지역"].tolist(),
                [(f"{prev_date:%m/%d}", sido_compare["전일"].tolist()), (f"{target_date:%m/%d}", sido_compare["기준일"].tolist())],
                colors=[COLORS["gray"], COLORS["primary"]],
            ) if not sido_compare.empty else empty_figure()
            st.plotly_chart(fig_d1, use_container_width=True, config={"displayModeBar": False}, key="daily_chart_bar1")

        with dc2:
            section_title("🐾", "축종별 접수 건수 비교")
            fig_d2 = chart_grouped_bar(
                animal_compare["축종"].tolist(),
                [(f"{prev_date:%m/%d}", animal_compare["전일"].tolist()), (f"{target_date:%m/%d}", animal_compare["기준일"].tolist())],
                colors=[COLORS["gray"], COLORS["secondary"]],
            ) if not animal_compare.empty else empty_figure()
            st.plotly_chart(fig_d2, use_container_width=True, config={"displayModeBar": False}, key="daily_chart_bar2")

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        section_title("📋", f"상세 데이터 ({target_date:%m/%d})")
        daily_detail_df = daily_report["detail_df"]
        st.dataframe(daily_detail_df, use_container_width=True, hide_index=True, height=220)

        csv_d = daily_detail_df.to_csv(index=False, encoding="utf-8-sig")
        st.download_button("↓  일간 데이터 다운로드", data=csv_d.encode("utf-8-sig"), file_name=f"유실유기동물_{target_date:%Y%m%d}.csv", mime="text/csv", key="daily_btn_dl")

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
        prev_month_start = monthly_report["prev_month_start"]
        prev_month_end = monthly_report["prev_month_end"]

        st.markdown(f"""
        <div style="display:inline-flex;align-items:center;gap:8px;padding:6px 16px;
            background:#e0e7ff;border-radius:8px;font-size:12px;font-weight:500;
            color:#4338ca;margin-bottom:20px;">
            📆 비교 기간: {prev_month_start:%Y년 %m월} → {current_month_start:%Y년 %m월}
        </div>
        """, unsafe_allow_html=True)

        monthly_kpi_df = monthly_report["monthly_kpi_df"]
        current_kpi = monthly_kpi_df[monthly_kpi_df["period"] == "current"].iloc[0].to_dict() if not monthly_kpi_df[monthly_kpi_df["period"] == "current"].empty else {}
        prev_kpi = monthly_kpi_df[monthly_kpi_df["period"] == "prev"].iloc[0].to_dict() if not monthly_kpi_df[monthly_kpi_df["period"] == "prev"].empty else {}

        current_total = int(current_kpi.get("total_count") or 0)
        prev_total = int(prev_kpi.get("total_count") or 0)
        current_adopt = int(current_kpi.get("adoption_count") or 0)
        current_euth = int(current_kpi.get("euthanasia_count") or 0)
        current_protected = int(current_kpi.get("protected_count") or 0)
        month_delta = current_total - prev_total
        month_delta_pct = f"{(month_delta / prev_total * 100):+.1f}%" if prev_total else "비교 불가"

        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.markdown(kpi_card("이번 달 접수", f"{fmt_int(current_total)}건", f"전월 대비 {month_delta:+,}건 ({month_delta_pct})", "up" if month_delta >= 0 else "down", "#6366f1"), unsafe_allow_html=True)
        with m2:
            st.markdown(kpi_card("입양률", pct(current_adopt, current_total), f"입양 {fmt_int(current_adopt)}건", "neutral", "#d97706"), unsafe_allow_html=True)
        with m3:
            st.markdown(kpi_card("안락사율", pct(current_euth, current_total), f"안락사 {fmt_int(current_euth)}건", "neutral", "#e11d48"), unsafe_allow_html=True)
        with m4:
            st.markdown(kpi_card("보호중", f"{fmt_int(current_protected)}건", "이번 달 기준", "neutral", "#0d9488"), unsafe_allow_html=True)

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

        mc1, mc2 = st.columns(2)
        sido_month_df = monthly_report["sido_month_df"]
        month_daily_df = monthly_report["month_daily_df"]
        with mc1:
            section_title("📍", "시/도별 월간 접수 건수 비교 (상위 10)")
            fig_m1 = chart_grouped_bar(
                sido_month_df["지역"].tolist(),
                [(f"{prev_month_start:%Y년 %m월}", sido_month_df["전월"].tolist()), (f"{current_month_start:%Y년 %m월}", sido_month_df["이번월"].tolist())],
                colors=[COLORS["gray"], COLORS["indigo"]],
            ) if not sido_month_df.empty else empty_figure()
            st.plotly_chart(fig_m1, use_container_width=True, config={"displayModeBar": False}, key="monthly_chart_bar1")

        with mc2:
            section_title("📈", f"{current_month_start:%Y년 %m월} 일별 발생 건수")
            fig_m2 = chart_vbar(month_daily_df["일"].tolist(), month_daily_df["건수"].tolist(), color=COLORS["indigo"]) if not month_daily_df.empty else empty_figure()
            st.plotly_chart(fig_m2, use_container_width=True, config={"displayModeBar": False}, key="monthly_chart_vbar")

        status_month_df = monthly_report["status_month_df"]
        md1, md2 = st.columns(2)
        with md1:
            section_title("🔄", f"처리 상태 — {prev_month_start:%Y년 %m월}")
            prev_status = status_month_df[status_month_df["period"] == "전월"] if not status_month_df.empty else pd.DataFrame()
            fig_s1 = chart_donut(prev_status["상태"].tolist(), prev_status["건수"].tolist()) if not prev_status.empty else empty_figure()
            st.plotly_chart(fig_s1, use_container_width=True, config={"displayModeBar": False}, key="monthly_chart_donut1")

        with md2:
            section_title("🔄", f"처리 상태 — {current_month_start:%Y년 %m월}")
            current_status = status_month_df[status_month_df["period"] == "이번월"] if not status_month_df.empty else pd.DataFrame()
            fig_s2 = chart_donut(current_status["상태"].tolist(), current_status["건수"].tolist()) if not current_status.empty else empty_figure()
            st.plotly_chart(fig_s2, use_container_width=True, config={"displayModeBar": False}, key="monthly_chart_donut2")

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        st.markdown("""
        <div style="background:#ffffff;border-radius:12px;padding:20px 24px;
            box-shadow:0 1px 3px rgba(15,23,42,0.06);margin-bottom:8px;">
            <div style="display:flex;align-items:center;gap:10px;margin-bottom:6px;">
                <span style="font-size:18px;">🤖</span>
                <div>
                    <div style="font-size:14px;font-weight:700;color:#0f172a;">AI 인사이트</div>
                    <div style="font-size:12px;color:#94a3b8;">
                        버튼을 클릭하면 현재 월간 통계를 바탕으로 주요 인사이트와 정책 제언을 생성합니다.
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if "ai_insight" not in st.session_state:
            st.session_state.ai_insight = None

        if st.button("🔍  AI 인사이트 생성", key="monthly_btn_ai"):
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
            <div style="background:linear-gradient(135deg,oklch(97% 0.01 280),oklch(97% 0.01 200));
                border:1px solid oklch(90% 0.04 260);border-radius:12px;padding:20px 24px;margin-top:8px;">
                <div style="font-size:13px;font-weight:600;color:#4338ca;margin-bottom:14px;display:flex;align-items:center;gap:7px;">
                    ✨ AI 분석 결과
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
        st.download_button("↓  현재 필터 상세 데이터 다운로드", data=csv_m.encode("utf-8-sig"), file_name="유실유기동물_현재필터.csv", mime="text/csv", key="monthly_btn_dl")
