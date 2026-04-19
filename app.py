"""
에어캡 시장 단가 통합 모니터링 시스템
=====================================
3개 업체의 에어캡 단가를 20×30 규격으로 환산하여
통합 비교·분석하는 Streamlit 대시보드
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
from pathlib import Path
import crawler
import datetime
import os
import random

# ──────────────────────────────────────
# 0. 페이지 설정 & 스타일
# ──────────────────────────────────────

# --- 설정 및 경로 ---
CSV_PATH = Path(__file__).parent / "price_history.csv"
TIMESTAMP_PATH = Path(__file__).parent / "last_update.txt"
BASE_INTERVAL = 3600 # 1시간

def get_last_update():
    if not os.path.exists(TIMESTAMP_PATH):
        return None
    try:
        with open(TIMESTAMP_PATH, "r", encoding="utf-8") as f:
            ts_str = f.read().strip()
            return datetime.datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
    except:
        return None

def save_last_update(dt):
    with open(TIMESTAMP_PATH, "w", encoding="utf-8") as f:
        f.write(dt.strftime("%Y-%m-%d %H:%M:%S"))

def trigger_auto_update():
    """1시간 + 지터(1~5분)가 지났으면 자동으로 크롤링 수행"""
    # 세션 상태를 사용하여 루프 방지
    if st.session_state.get("is_crawling", False):
        return
        
    last_dt = get_last_update()
    now = datetime.datetime.now()
    
    # 세션에 저장된 jitter가 없다면 새로 생성 (페이지 새로고침 시에도 유지됨)
    if "current_jitter" not in st.session_state:
        st.session_state.current_jitter = random.randint(60, 300)
    
    should_update = False
    if last_dt is None:
        should_update = True
    else:
        diff = (now - last_dt).total_seconds()
        if diff >= (3600 + st.session_state.current_jitter): 
            should_update = True
            
    if should_update:
        st.session_state.is_crawling = True
        with st.spinner("⏳ 업데이트 주기가 되어 자동으로 최신 정보를 가져오는 중입니다..."):
            try:
                results = crawler.crawl_all()
                df_full = load_data()
                if not df_full.empty:
                    # 오늘 날짜 확인 (시간 제외)
                    today = pd.Timestamp(now).normalize()
                    
                    # 오늘 날짜 데이터가 있는지 확인
                    if today not in pd.to_datetime(df_full["date"]).values:
                        # 오늘 날짜 데이터가 없다면 가장 최근 데이터(어제 등)를 복사해서 새로 생성
                        # (단, 4월 18일 23:50 기록을 위해 현재 데이터가 18일인 경우는 제외)
                        last_day = pd.to_datetime(df_full["date"]).max()
                        if last_day < today:
                            temp_df = df_full[df_full["date"] == last_day].copy()
                            temp_df["date"] = today
                            temp_df["status"] = "⚪ 대기" 
                            df_full = pd.concat([df_full, temp_df], ignore_index=True)
                        else:
                            today = last_day # 이미 오늘 데이터가 있거나 미래 데이터면 해당 날짜 사용

                    # 이제 오늘(또는 최신) 데이터에 대해서만 업데이트 수행
                    target_date = today
                    for comp, items in results.items():
                        for item in items:
                            db_company = df_full["company"].astype(str).str.strip()
                            mask = (df_full["date"] == target_date) & \
                                   (db_company == comp) & \
                                   (df_full["width"] == item["width"]) & \
                                   (df_full["height"] == item["height"])
                            if mask.any():
                                df_full.loc[mask, "unit_price"] = item["unit_price"]
                                df_full.loc[mask, "qty_per_box"] = item["qty_per_box"]
                                df_full.loc[mask, "product_url"] = item.get("product_url", "")
                                df_full.loc[mask, "status"] = "🟢 수집"
                    df_full.to_csv(CSV_PATH, index=False)
                    save_last_update(now)
                    st.session_state.current_jitter = random.randint(60, 300) # 주기를 새로 설정
                    st.toast("✅ 자동 업데이트 완료!")
            except Exception as e:
                st.error(f"자동 업데이트 중 오류 발생: {e}")
            finally:
                st.session_state.is_crawling = False

# ──────────────────────────────────────

def check_password():
    def password_entered():
        if st.session_state["pw_input"] == "10077":
            st.session_state["password_correct"] = True
            if "pw_input" in st.session_state:
                del st.session_state["pw_input"]
        else:
            st.session_state["password_correct"] = False
            st.error("❌ 비밀번호가 올바르지 않습니다.")

    if not st.session_state.get("password_correct", False):
        # 검색로봇 차단 등 헤더 설정
        st.markdown(f"""
            <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;700;900&display=swap" rel="stylesheet">
            <meta name="robots" content="noindex, nofollow, noarchive">
            <style>
            /* 전체 스트림릿 배경 어둡게 */
            html, body, .stApp, [data-testid="stApp"] {{ background: #1a1c2c !important; }}
            [data-testid="stHeader"], [data-testid="stSidebar"], footer, #MainMenu {{
                display: none !important;
            }}

            /* 메인 컨테이너 외부 백그라운드 "지금, 뽁뽁이 얼마야?" 역할 (stlite index.html 에 있던 걸 app.py 에선 직접 구현) */
            </style>
        """, unsafe_allow_html=True)
        
        # 로컬(streamlit) 에서는 index.html 같이 겉을 감싸는 박스가 없으므로 HTML 마크다운으로 백그라운드를 하나 만듭니다
        st.markdown(f"""
            <style>
                .outer-modal-bg {{
                    background: white !important; border-radius: 40px !important;
                    box-shadow: 0 40px 100px rgba(0,0,0,0.6) !important;
                    width: 440px !important; height: 480px !important;
                    padding: 4.5rem 0 4rem 0 !important;
                    text-align: center !important;
                    position: fixed !important; top: 50% !important; left: 50% !important;
                    transform: translate(-50%, -50%) !important;
                    z-index: 100000 !important;
                    box-sizing: border-box !important;
                }}
                .outer-modal-bg h2 {{
                    color: #111827 !important; margin: 0 3rem 0.8rem 3rem !important;
                    font-weight: 900 !important; font-size: 2.3rem !important;
                    font-family: 'Noto Sans KR', sans-serif !important;
                    letter-spacing: -1.5px !important; line-height: 1.2 !important;
                }}
                
                /* block-container를 그 안에 맞춰 미니 모달로 변환 */
                .block-container, [data-testid="stMainBlockContainer"], [data-testid="stAppViewBlockContainer"] {{
                    position: fixed !important;
                    top: calc(50% + 18px) !important;
                    left: 50% !important;
                    transform: translate(-50%, -50%) !important;
                    width: 340px !important;
                    max-width: 340px !important;
                    background: white !important;
                    border-radius: 20px !important;
                    border: 1px solid #e5e7eb !important;
                    box-shadow: none !important;
                    padding: 1.5rem !important;
                    margin: 0 !important;
                    z-index: 200000 !important;
                    box-sizing: border-box !important;
                }}
                
                /* 스트림릿 기본 렌더링 시 내부 위젯들이 날아오거나 솟아오르는 애니메이션 완벽 차단 */
                .block-container *, [data-testid="stMainBlockContainer"] * {{
                    animation: none !important;
                    transform: none !important;
                    transition: none !important;
                }}

                /* 위젯 사이 간격 조정 */
                [data-testid="stVerticalBlock"] {{ gap: 12px !important; }}

                /* 비밀번호 입력창 스타일 - 테두리를 눈모양까지 포함 
                   (Hidden Label이 점으로 보이지 않도록 data-baseweb 지정) */
                div[data-testid="stTextInput"] div[data-baseweb="input"] {{
                    background-color: #f8fafc !important; border-radius: 12px !important;
                    border: 2px solid #94a3b8 !important;
                    overflow: hidden !important;
                }}
                div[data-baseweb="input"] > div {{
                    background-color: transparent !important;
                    border: none !important;
                }}
                div[data-testid="stTextInput"] input {{
                    background-color: transparent !important; border: none !important;
                    padding: 15px !important; text-align: center !important;
                    font-size: 1.1rem !important; color: #1e293b !important;
                }}

                /* 확인 버튼 스타일 */
                div[data-testid="stButton"] button {{
                    background-color: #5850ec !important; color: white !important;
                    width: 100% !important; height: 54px !important;
                    border-radius: 12px !important; font-size: 1.25rem !important;
                    font-weight: 900 !important; border: none !important;
                    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1) !important;
                }}
            </style>
            <div class="outer-modal-bg">
                <h2>지금, 뽁뽁이 얼마야?</h2>
            </div>
        """, unsafe_allow_html=True)
        
        st.text_input("PASSWORD", type="password", key="pw_input", on_change=password_entered, label_visibility="collapsed", placeholder="비밀번호를 입력하세요")
        st.button("확인", on_click=password_entered, use_container_width=True)
            
        return False
    return True

# 0. 페이지 설정이 가장 먼저 와야 함
st.set_page_config(
    page_title="에어캡 단가 모니터링",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# if not check_password():
#     st.stop()

# 앱 리로드 시마다 자동 업데이트 체크 (실시간 모니터링 활성화)
trigger_auto_update()
last_update_dt = get_last_update()
last_update_str = last_update_dt.strftime("%Y-%m-%d %H:%M") if last_update_dt else "수집 기록 없음"

# 커스텀 CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;600;700&display=swap');

    /* 전체 폰트 및 기본 UI 숨김 */
    html, body, [class*="css"] {
        font-family: 'Noto Sans KR', sans-serif;
    }
    
    /* 상단 헤더 및 툴바 숨김 */
    header {visibility: hidden !important;}
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    .stDeployButton {display:none !important;}
    [data-testid="stStatusWidget"] {display:none !important;}
    
    /* 메인 컨텐츠 영역 여백 조정 */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
    }
    
    body {
        background-color: #1a1c2c;
    }

    /* 헤더 영역 */
    .main-header {
        background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
        padding: 2rem 2.5rem;
        border-radius: 16px;
        margin-bottom: 1.5rem;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    .main-header h1 {
        color: #ffffff;
        font-size: 1.8rem;
        font-weight: 700;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .main-header p {
        color: rgba(255, 255, 255, 0.6);
        font-size: 0.95rem;
        margin: 0.3rem 0 0 0;
    }

    /* 메트릭 카드 */
    .metric-card {
        background: linear-gradient(145deg, #1a1a2e, #16213e);
        padding: 1.3rem 1.5rem;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        height: 155px; /* 모든 패널 동일한 높이로 강제 고정 (글씨량에 따라 늘어나지 않도록 넉넉하게) */
        box-sizing: border-box;
        display: flex;
        flex-direction: column;
        justify-content: flex-start;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
    }
    .metric-label {
        color: rgba(255, 255, 255, 0.5);
        font-size: 0.8rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 0.3rem;
    }
    .metric-value {
        color: #ffffff;
        font-size: 1.6rem;
        font-weight: 700;
    }
    .metric-value.highlight-green { color: #00d68f; }
    .metric-value.highlight-orange { color: #ffaa00; }
    .metric-value.highlight-blue { color: #3366ff; }

    /* 섹션 제목 */
    .section-title {
        font-size: 1.15rem;
        font-weight: 700;
        color: var(--text-color);
        margin: 1.5rem 0 0.8rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid rgba(128, 128, 128, 0.3);
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    /* 사이드바 */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f0c29 0%, #1a1a2e 100%);
    }
    [data-testid="stSidebar"] .stMarkdown h2 {
        color: #ffffff;
        font-size: 1.1rem;
    }
    
    /* 사이드바 라벨 (조사날짜, 회사명 등) 색상 밝게 조절 */
    [data-testid="stSidebar"] label p, [data-testid="stSidebar"] label div {
        color: #ffffff !important;
        font-weight: 500;
        letter-spacing: 0.3px;
    }
    [data-testid="stSidebar"] svg {
        stroke: #ffffff;
    }


    /* 폼 자동계산 박스 */
    .calc-box {
        background: linear-gradient(135deg, #1b4332, #2d6a4f);
        padding: 1rem 1.2rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        border: 1px solid rgba(0, 214, 143, 0.2);
    }
    .calc-box .calc-label {
        color: rgba(255, 255, 255, 0.6);
        font-size: 0.75rem;
        margin-bottom: 0.2rem;
    }
    .calc-box .calc-value {
        color: #00d68f;
        font-size: 1.3rem;
        font-weight: 700;
    }

    /* 테이블 하이라이트 */
    .highlight-row {
        background-color: rgba(0, 214, 143, 0.15) !important;
    }

    /* 품절 행 연속 가로줄 (가상 요소 활용) */
    .sold-out-row {
        opacity: 0.5;
    }
    .sold-out-row td {
        position: relative;
    }
    .sold-out-row td::after {
        content: '';
        position: absolute;
        left: 0;
        right: 0;
        top: 50%;
        border-top: 1px solid rgba(0, 0, 0, 0.6);
        pointer-events: none; /* 텍스트 선택 방해 방지 */
    }

    /* 상태 뱃지 */
    .status-badge {
        display: inline-block;
        padding: 0.2rem 0.7rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .status-badge.cheapest {
        background: rgba(0, 214, 143, 0.2);
        color: #00d68f;
        border: 1px solid rgba(0, 214, 143, 0.3);
    }

    /* 숨김 streamlit 요소 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* 데이터프레임 스타일 개선 */
    .stDataFrame {
        border-radius: 10px;
        overflow: hidden;
    }
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────
# 1. 데이터 관리 함수
# ──────────────────────────────────────

CSV_COLUMNS = [
    "date", "company", "product", "usage_scope", "availability", "width", "height",
    "unit_price", "qty_per_box", "shipping_per_box", "vat_status", "product_url"
]


def load_data() -> pd.DataFrame:
    """CSV에서 데이터를 불러옵니다. 호환성을 위해 상태 컬럼을 동적으로 생성/관리합니다."""
    if CSV_PATH.exists():
        df = pd.read_csv(CSV_PATH)
        df["date"] = pd.to_datetime(df["date"], format='mixed').dt.normalize()
        
        # 이전 버전과의 호환성 및 상태 컬럼 분리 작업
        if "status" not in df.columns:
            df["status"] = "⚪ 수동"
            for i in df.index:
                comp = str(df.at[i, "company"]).strip()
                if comp.startswith("🟢"):
                    df.at[i, "status"] = "🟢 수집"
                    df.at[i, "company"] = comp.replace("🟢", "").strip()
                elif comp.startswith("🔴"):
                    df.at[i, "status"] = "🔴 오류"
                    df.at[i, "company"] = comp.replace("🔴", "").strip()
        
        # 부가세 컬럼 호환성 추가
        if "vat_status" not in df.columns:
            df["vat_status"] = "미포함"
            
        # 사용범위 컬럼 호환성 추가
        if "usage_scope" not in df.columns:
            df["usage_scope"] = "범용"
            
        df.to_csv(CSV_PATH, index=False)
            
        return df
    return pd.DataFrame(columns=CSV_COLUMNS + ["status"])


def get_latest_metadata() -> dict:
    """각 (업체, 상품)별 가장 최신 설정값들을 가져옵니다."""
    df = load_data()
    if df.empty:
        return {}
    
    # 날짜순 정렬 후 마지막 데이터가 최신
    latest_df = df.sort_values("date").drop_duplicates(["company", "product"], keep="last")
    
    meta_map = {}
    for _, row in latest_df.iterrows():
        comp = str(row["company"]).strip()
        prod = str(row["product"]).strip()
        key = f"{comp}|||{prod}"
        meta_map[key] = {
            "width": row["width"],
            "height": row["height"],
            "unit_price": row["unit_price"],
            "qty_per_box": row["qty_per_box"],
            "shipping_per_box": row["shipping_per_box"],
            "vat_status": row["vat_status"],
            "usage_scope": row.get("usage_scope", "범용"),
            "product_url": row["product_url"]
        }
    return meta_map


def save_entry(entry: dict):
    """새 데이터를 CSV에 저장합니다 (같은 날짜/회사/상품이면 덮어쓰기)."""
    df = load_data()

    mask = (
        (df["date"] == pd.Timestamp(entry["date"]).normalize()) &
        (df["company"] == entry["company"]) &
        (df["product"] == entry["product"])
    )

    if mask.any():
        for col in CSV_COLUMNS:
            df.loc[mask, col] = entry[col]
    else:
        new_row = pd.DataFrame([entry])
        df = pd.concat([df, new_row], ignore_index=True)

    df.to_csv(CSV_PATH, index=False)


def delete_entry(date_val, company, product):
    """특정 항목을 삭제합니다."""
    df = load_data()
    mask = (
        (df["date"] == pd.Timestamp(date_val).normalize()) &
        (df["company"] == company) &
        (df["product"] == product)
    )
    df = df[~mask]
    df.to_csv(CSV_PATH, index=False)


def compute_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """20×30 환산 최종단가를 계산합니다."""
    if df.empty:
        return df

    result = df.copy()
    
    # [변경] 박스당 가격 먼저 계산
    result["박스당 가격"] = result["unit_price"] * result["qty_per_box"]
    
    # [변경] '배송비+VAT포함 단가' 계산 (부가세 미포함 시 1.1 곱함)
    # 기본 실질원가 = (박스값 + 배송비) / 입수량
    base_landed_cost = (
        result["unit_price"] + result["shipping_per_box"] / result["qty_per_box"]
    )
    
    result["배송비+VAT포함 단가"] = base_landed_cost
    if "vat_status" in result.columns:
        mask_vat = result["vat_status"] == "미포함"
        result.loc[mask_vat, "배송비+VAT포함 단가"] = result.loc[mask_vat, "배송비+VAT포함 단가"] * 1.1
    
    # [변경] 20x30 환산단가 계산 (이미 VAT가 반영된 단가 기준)
    result["20x30 환산단가"] = (
        result["배송비+VAT포함 단가"] / (result["width"] * result["height"]) * 600
    )
    
    # 전처리: 정수형 변환
    result["배송비+VAT포함 단가"] = result["배송비+VAT포함 단가"].round(0).astype(int)
    result["20x30 환산단가"] = result["20x30 환산단가"].round(0).astype(int)
    result["박스당 가격"] = result["박스당 가격"].round(0).astype(int)

    return result


# ──────────────────────────────────────
# 2. 헤더
# ──────────────────────────────────────
st.markdown(f"""
<div class="main-header">
    <h1>📦 에어캡 시장 통합 모니터링</h1>
    <p>4개 업체 × 주력 상품 | 20×30 환산 최종단가 비교 분석</p>
</div>
""", unsafe_allow_html=True)


# ──────────────────────────────────────
# 4. 메인 영역: 데이터 분석
# ──────────────────────────────────────
df = load_data()
df_calc = compute_metrics(df)

if df_calc.empty:
    # 빈 상태 안내
    st.markdown("""
    <div style="
        text-align: center;
        padding: 4rem 2rem;
        background: linear-gradient(145deg, #1a1a2e, #16213e);
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.05);
        margin: 2rem 0;
    ">
        <div style="font-size: 4rem; margin-bottom: 1rem;">📊</div>
        <h2 style="color: #ffffff; font-weight: 600; margin-bottom: 0.5rem;">
            데이터가 없습니다
        </h2>
        <p style="color: rgba(255, 255, 255, 0.5); font-size: 1rem;">
            왼쪽 사이드바에서 업체별 단가 데이터를 입력해주세요.
        </p>
        <p style="color: rgba(255, 255, 255, 0.35); font-size: 0.85rem; margin-top: 0.5rem;">
            3개 업체 × 3개 상품씩 입력하면 최적의 비교 분석이 가능합니다.
        </p>
    </div>
    """, unsafe_allow_html=True)

else:
    # ─── 요약 메트릭 카드 ───
    latest_date = df_calc["date"].max()
    df_latest = df_calc[df_calc["date"] == latest_date].copy()

    cheapest_row = df_latest.loc[df_latest["20x30 환산단가"].idxmin()]
    most_expensive_row = df_latest.loc[df_latest["20x30 환산단가"].idxmax()]
    avg_price = df_latest["20x30 환산단가"].mean()

    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">📅 최신 조사시간</div>
            <div class="metric-value" style="font-size: 1.4rem;">{last_update_str}</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">🏆 최저 단가 (20×30)</div>
            <div class="metric-value highlight-green">{cheapest_row['20x30 환산단가']:,}원</div>
            <div style="color: #E3F2FD; font-size: 1.05rem; font-weight: 600; margin-top: 0.4rem;">
                {cheapest_row['company']} · {cheapest_row['product']}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">✨ 오늘의 나프타 뉴스</div>
            <div style="color: #ffffff; font-size: 1.05rem; line-height: 1.6; padding-top: 0.5rem; font-weight: 400;">
                • 원유 가격 폭등에 따른 에어캡 원자재 공급난 및 배송 포장재 조달 차질<br>
                • 포장용 에어캡 부자재 시장의 물량 확보율이 10%대까지 급락하며 물류 운영 위협<br>
                • 수급처 다변화 및 안전 재고 운용을 통한 에어캡 공급망 재편과 효율화 주력
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ─── 비교 분석표 ───
    col_title, col_btn = st.columns([0.7, 0.3])
    with col_title:
        st.markdown("""
        <div class="section-title">📋 공급업체/ 주요상품별 실시간 가격 비교</div>
        """, unsafe_allow_html=True)
    with col_btn:
        if st.button("🔄 실시간 가격 업데이트 (1시간마다 갱신)", use_container_width=True, type="primary"):
            with st.spinner("크롤링 실행 중..."):
                results = crawler.crawl_all()
                df_full = load_data()
                if not df_full.empty:
                    latest_date = df_full["date"].max()
                    for comp, items in results.items():
                        for item in items:
                            mask = (df_full["date"] == latest_date) & \
                                   (df_full["company"].str.strip() == comp) & \
                                   (df_full["width"] == item["width"]) & \
                                   (df_full["height"] == item["height"])
                            if mask.any():
                                df_full.loc[mask, "unit_price"] = item["unit_price"]
                                df_full.loc[mask, "qty_per_box"] = item["qty_per_box"]
                                df_full.loc[mask, "availability"] = item.get("availability", "판매중")
                                df_full.loc[mask, "product_url"] = item.get("product_url", "")
                                df_full.loc[mask, "status"] = "🟢 수집"
                    df_full.to_csv(CSV_PATH, index=False)
                    save_last_update(datetime.datetime.now())
                    st.success("✅ 업데이트 완료!")
                    st.rerun()

    # 표시용 데이터프레임 준비 (🔗 컬럼 제거 및 판매여부 텍스트 가공)
    # 표시용 데이터프레임 준비 (순서 변경: 부가세 -> 단가, 사용범위 추가)
    display_df = df_latest[[
        "status", "company", "product", "usage_scope", "availability", "product_url", "width", "height",
        "unit_price", "qty_per_box", "shipping_per_box",
        "박스당 가격", "vat_status", "배송비+VAT포함 단가", "20x30 환산단가"
    ]].copy()

    # 주거래업체(박스몰) 상단 고정 정렬 로직
    def get_sort_priority(company):
        if "박스몰" in str(company):
            return 0  # 1순위
        return 1

    display_df["sort_order"] = display_df["company"].apply(get_sort_priority)
    # 1순위: 업체 우선순위(박스몰), 2순위: 20x30 환산단가 오름차순
    display_df = display_df.sort_values(by=["sort_order", "20x30 환산단가"]).drop(columns=["sort_order"])

    # 판매여부가 '판매중'일 때만 링크 아이콘 컬럼 연동
    display_df["product_url"] = display_df.apply(
        lambda x: x["product_url"] if x["availability"] == "판매중" else None, axis=1
    )

    # 배송비 0원인 경우 '무료배송' 표기 및 숫자 포맷팅
    display_df["shipping_per_box"] = display_df["shipping_per_box"].apply(
        lambda x: "무료배송" if x == 0 else f"{x:,.0f}"
    )

    display_df.columns = [
        "상태", "회사명", "상품명", "사용범위", "판매여부", "🔗", "가로(cm)", "세로(cm)",
        "단가(원)", "입수량(매)", "배송비(원)",
        "박스당 가격(원)", "부가세", "배송비+VAT포함 단가", "20*30로 환산단가"
    ]

    numeric_converted = display_df["20*30로 환산단가"].copy()
    min_converted = numeric_converted.min()

    def style_rows(row):
        """행 단위 스타일 결정 (최저가 하이라이트 등)"""
        is_cheapest = (row["20*30로 환산단가"] == min_converted)
        
        bg_color = "#ffffff"
        if is_cheapest:
            bg_color = "#E8F5E9" # 최저가 연한 초록색
        
        return bg_color

    # 1. 프리미엄 모니터링 뷰 (HTML/CSS 커스텀 테이블)
    # st.dataframe의 제한사항(셀 내 개별 링크 불가능)을 극복하고 '판매중 🔗' 기능을 구현합니다.
    
    html_table = f"""
    <style>
        .sold-out-row {{
            opacity: 0.4;
        }}
        .sold-out-row td {{
            position: relative;
        }}
        .sold-out-row td::after {{
            content: '';
            position: absolute;
            left: 0;
            right: 0;
            top: 50%;
            border-top: 1.5px solid rgba(0, 0, 0, 0.8);
            pointer-events: none;
        }}
    </style>
    <div style="overflow-x:auto; background-color: white; padding: 10px; border-radius: 10px;">
        <table style="width:100%; border-collapse: collapse; font-size: 0.9rem; border-radius: 8px; overflow: hidden; background-color: white; color: #333;">
            <thead>
                <tr style="background-color: #f8f9fa; color: #333; text-align: left; border-bottom: 2px solid #dee2e6;">
                    <th style="padding: 12px 15px;">상태</th>
                    <th style="padding: 12px 15px;">회사명</th>
                    <th style="padding: 12px 15px;">상품명</th>
                    <th style="padding: 12px 15px;">사용범위</th>
                    <th style="padding: 12px 15px;">판매여부</th>
                    <th style="padding: 12px 15px;">규격 (cm)</th>
                    <th style="padding: 12px 15px; text-align: right;">단가</th>
                    <th style="padding: 12px 15px; text-align: right;">입수량</th>
                    <th style="padding: 12px 15px; text-align: right;">배송비</th>
                    <th style="padding: 12px 15px; text-align: right;">박스당 가격</th>
                    <th style="padding: 12px 15px; text-align: right;">부가세</th>
                    <th style="padding: 12px 15px; text-align: right;">배송비+VAT포함 단가</th>
                    <th style="padding: 12px 15px; text-align: right; color: #2E7D32;">20*30로 환산단가</th>
                </tr>
            </thead>
            <tbody>
    """

    for _, row in display_df.iterrows():
        bg_color = style_rows(row)
        
        # 판매여부 포맷팅 및 품절 스타일 처리
        row_class = ""
        if "판매중" in str(row["판매여부"]):
            url = row["🔗"] if pd.notna(row["🔗"]) and str(row["🔗"]).strip() != "" else "#"
            avail_html = f'<a href="{url}" target="_blank" style="color: #00d68f; text-decoration: none; font-weight: 600;">판매중 🔗</a>'
        else:
            avail_html = '<span style="color: #ff4b4b; font-weight: 500;">품절</span>'
            row_class = "sold-out-row"
            
        # 값 포맷팅 (정수형 변환 및 콤마 추가)
        try:
            # 상태 아이콘만 추출 (텍스트 제거)
            status_icon = row['상태'][0] if len(row['상태']) > 0 else ""
            
            w = int(float(row['가로(cm)']))
            h = int(float(row['세로(cm)']))
            unit = int(float(row['단가(원)']))
            # 입수량 처리 (문자열일 수 있음)
            qty_val = row['입수량(매)']
            if isinstance(qty_val, str):
                qty_val = qty_val.replace(',', '')
            qty = int(float(qty_val))
            box_price = int(float(row['박스당 가격(원)']))
            cost = int(float(row['배송비+VAT포함 단가']))
            conv = int(float(row['20*30로 환산단가']))
        except Exception as e:
            # 예외 발생 시 원본 노출
            w, h, unit, qty, box_price, cost, conv = row['가로(cm)'], row['세로(cm)'], row['단가(원)'], row['입수량(매)'], row['박스당 가격(원)'], row['배송비포함 원가'], row['20×30 환산 부가세포함 단가']

        # 배송비 처리 (숫자일 경우에만 '원' 추가)
        shipping_display = row['배송비(원)']
        if shipping_display != "무료배송":
            shipping_display = f"{shipping_display}원"

        html_table += f"""
                <tr class="{row_class}" style="border-bottom: 1px solid #eee; background-color: {bg_color}; transition: background-color 0.2s;">
                    <td style="padding: 10px 15px; text-align: center; font-size: 1.2rem;">{status_icon}</td>
                    <td style="padding: 10px 15px; background-color: #E3F2FD; color: #0D47A1; font-weight: 500;">{row['회사명']}</td>
                    <td style="padding: 10px 15px; background-color: #E3F2FD; color: #333;">{row['상품명']}</td>
                    <td style="padding: 10px 15px;">{row['사용범위']}</td>
                    <td style="padding: 10px 15px;">{avail_html}</td>
                    <td style="padding: 10px 15px; color: #666;">{w}x{h}</td>
                    <td style="padding: 10px 15px; text-align: right;">{unit:,}원</td>
                    <td style="padding: 10px 15px; text-align: right;">{qty:,}매</td>
                    <td style="padding: 10px 15px; text-align: right;">{shipping_display}</td>
                    <td style="padding: 10px 15px; text-align: right;">{box_price:,}원</td>
                    <td style="padding: 10px 15px; text-align: right;">{row['부가세']}</td>
                    <td style="padding: 10px 15px; text-align: right; background-color: #FFF0F0; color: #B71C1C;">{cost:,}원</td>
                    <td style="padding: 10px 15px; text-align: right; background-color: #FFF0F0; font-weight: 700; color: #B71C1C;">{conv:,}원</td>
                </tr>
        """
        
    html_table += """
            </tbody>
        </table>
    </div>
    """
    
    # st.markdown 대신 components.html을 사용하여 렌더링 안정성을 확보합니다. (깜빡임 및 코드 노출 방지)
    # 테이블 높이를 동적으로 계산 (헤더 약 60px + 행당 약 45px + 여유)
    table_height = 60 + (len(display_df) * 50) + 20
    st.components.v1.html(html_table, height=min(table_height, 800), scrolling=True)

    # 2. 데이터 수동 편집 (필요할 때만 열어서 사용)
    with st.expander("📝 데이터 수동 업데이트 (단가/입수량 등 수정)"):
        st.info("여기서 데이터를 수정한 후 하단의 'Save' 버튼을 눌러주세요.")
        editor_df = df_latest[[
            "status", "company", "product", "usage_scope", "availability", "product_url", "width", "height",
            "unit_price", "qty_per_box", "shipping_per_box",
            "vat_status"
        ]].copy()
        # 하단 numeric conversion logic과 맞추기 위해 컬럼명 유지
        editor_df.columns = ["상태", "회사명", "상품명", "사용범위", "판매여부", "상품 URL", "가로(cm)", "세로(cm)", "단가(원)", "입수량(매)", "배송비(원)", "부가세"]
        
        edited_df = st.data_editor(
            editor_df,
            use_container_width=True,
            hide_index=True,
            num_rows="dynamic", # 신규 행 추가 가능하도록 변경
            key="main_table_editor",
            column_config={
                "상태": st.column_config.SelectboxColumn("상태", options=["⚪ 수동", "🟢 수집", "🔴 오류"]),
                "사용범위": st.column_config.SelectboxColumn("사용범위", options=["천미리", "오백미리", "범용"]),
                "가로(cm)": st.column_config.NumberColumn("가로(cm)", format="%.0f"),
                "세로(cm)": st.column_config.NumberColumn("세로(cm)", format="%.0f"),
                "판매여부": st.column_config.SelectboxColumn("판매여부", options=["판매중", "품절"]),
                "상품 URL": st.column_config.LinkColumn("상품 URL"),
                "단가(원)": st.column_config.NumberColumn("단가(원)", format="%,.0f"),
                "입수량(매)": st.column_config.NumberColumn("입수량(매)", format="%,.0f"),
                "배송비(원)": st.column_config.NumberColumn("배송비(원)", format="%,.0f"),
                "부가세": st.column_config.SelectboxColumn("부가세", options=["포함", "미포함"])
            }
        )

        st.markdown("---")
        st.markdown("#### ➕ 신규 품목 추가 (스마트 자동완성)")
        
        # 최신 메타데이터 로드
        meta_map = get_latest_metadata()
        existing_companies = sorted(list(set(k.split("|||")[0] for k in meta_map.keys())))
        
        # 1. 업체 및 상품 선택 (자동완성 도우미)
        col_helper1, col_helper2 = st.columns(2)
        with col_helper1:
            sel_company = st.selectbox("기존 업체 선택 (신규 입력 시 '직접 입력' 선택)", ["직접 입력"] + existing_companies)
        
        available_products = []
        if sel_company != "직접 입력":
            available_products = sorted([k.split("|||")[1] for k in meta_map.keys() if k.startswith(f"{sel_company}|||")])
            
        with col_helper2:
            sel_product = st.selectbox("기존 상품 선택", ["직접 입력"] + available_products)

        # 선택 시 세션 상태 업데이트 로직
        current_meta = {}
        if sel_company != "직접 입력" and sel_product != "직접 입력":
            current_meta = meta_map.get(f"{sel_company}|||{sel_product}", {})

        # 입력 폼 시작
        with st.form("new_entry_form", clear_on_submit=True):
            f_col1, f_col2, f_col3 = st.columns(3)
            with f_col1:
                # 선택된 업체가 있으면 그 값을 기본값으로, 없으면 빈칸
                default_comp = sel_company if sel_company != "직접 입력" else ""
                new_company = st.text_input("공급업체/회사명", value=default_comp, placeholder="예: 박스몰")
                new_width = st.number_input("가로(cm)", min_value=1.0, value=float(current_meta.get("width", 20.0)), step=1.0)
            with f_col2:
                default_prod = sel_product if sel_product != "직접 입력" else ""
                new_product = st.text_input("상품명", value=default_prod, placeholder="예: 에어캡봉투")
                
                # [신규] 사용범위 선택 (드롭박스 맨 위 '선택' 추가)
                scope_options = ["선택", "천미리", "오백미리", "범용"]
                default_scope = current_meta.get("usage_scope", "선택")
                scope_idx = scope_options.index(default_scope) if default_scope in scope_options else 0
                new_scope = st.selectbox("사용범위", options=scope_options, index=scope_idx)
                
                new_height = st.number_input("세로(cm)", min_value=1.0, value=float(current_meta.get("height", 30.0)), step=1.0)
            with f_col3:
                # 박스당 입수량
                new_qty = st.number_input("박스당 입수량(매)", min_value=1, value=int(current_meta.get("qty_per_box", 400)), step=1)
                
                # [신규] 박스당 가격 입력 필드 추가 (단가 자동 계산용)
                default_unit_price = float(current_meta.get("unit_price", 0.0))
                default_box_price = default_unit_price * new_qty
                new_box_price = st.number_input("박스당 가격(원) ★", min_value=0.0, value=default_box_price, step=100.0, help="박스 전체 가격을 넣으시면 단가가 자동 계산됩니다.")
                
                # 단가는 박스 가격과 연동되도록 처리
                if new_qty > 0:
                    new_price = new_box_price / new_qty
            
            f_col4, f_col5, f_col6 = st.columns(3)
            with f_col4:
                new_shipping = st.number_input("박스당 배송비(원)", min_value=0.0, value=float(current_meta.get("shipping_per_box", 5300.0)), step=100.0)
            with f_col5:
                vat_options = ["미포함", "포함"]
                vat_idx = 0
                if current_meta.get("vat_status") == "포함":
                    vat_idx = 1
                new_vat = st.selectbox("부가세 여부", options=vat_options, index=vat_idx)
            with f_col6:
                new_url = st.text_input("상품 URL (선택사항)", value=current_meta.get("product_url", ""), placeholder="https://...")

            # [신규] 실시간 계산 결과 미리보기 영역
            if new_qty > 0:
                real_cost = new_price + (new_shipping / new_qty)
                conversion_2030 = (real_cost / (new_width * new_height)) * 600
                if new_vat == "미포함":
                    conversion_2030 *= 1.1
                
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #0f2027, #203a43, #2c5364); padding: 1rem; border-radius: 8px; margin-top: 10px; border: 1px solid #00d68f;">
                    <span style="color: #00d68f; font-size: 0.85rem; font-weight: 600;">📊 [실시간 산출 예측]</span><br>
                    <span style="color: white;">개당 단가: <b>{new_price:,.2f}원</b></span> | 
                    <span style="color: #ffaa00; font-weight: 700;">20×30 환산단가: {conversion_2030:,.0f}원</span>
                </div>
                """, unsafe_allow_html=True)

            submit_new = st.form_submit_button("추가 항목 저장")
            
            if submit_new:
                if not new_company or not new_product:
                    st.error("회사명과 상품명은 필수 입력입니다.")
                elif new_scope == "선택":
                    st.error("사용범위를 선택해주세요 (천미리/오백미리/범용 중 하나).")
                else:
                    df_full = load_data()
                    latest_date = df_full["date"].max()
                    new_row = {
                        "date": latest_date,
                        "company": new_company.strip(),
                        "product": new_product.strip(),
                        "usage_scope": new_scope,
                        "width": new_width,
                        "height": new_height,
                        "unit_price": new_price,
                        "qty_per_box": new_qty,
                        "shipping_per_box": new_shipping,
                        "vat_status": new_vat,
                        "availability": "판매중",
                        "product_url": new_url,
                        "status": "⚪ 수동"
                    }
                    df_full = pd.concat([df_full, pd.DataFrame([new_row])], ignore_index=True)
                    df_full.to_csv(CSV_PATH, index=False)
                    st.success(f"✅ {new_company}의 신규 항목이 추가되었습니다.")
                    st.rerun()

    # 데이터 복원 (문자열 값으로 저장되는 것을 방지하기 위해 쉼표 제거 후 다시 숫자로 복원)
    for col in ["박스당 가격(원)", "개당 실질원가(원)", "20×30 환산단가(VAT포함)"]:
        if col in edited_df.columns:
            edited_df[col] = edited_df[col].astype(str).str.replace(",", "", regex=False)
            display_df[col] = display_df[col].astype(str).str.replace(",", "", regex=False)

    # DataFrame 형태 변환 오류를 방지하기 위해 타입 강제 변환 후 비교
    for col in ["가로(cm)", "세로(cm)", "단가(원)", "입수량(매)", "배송비(원)"]:
        edited_df[col] = pd.to_numeric(edited_df[col], errors='coerce')
        display_df[col] = pd.to_numeric(display_df[col], errors='coerce')

    if not edited_df.equals(display_df):
        if st.button("💾 표 수정 내용 즉시 저장", type="primary"):
            df_full = load_data()
            latest_date = df_full["date"].max()
            
            # 기존 latest_date 데이터는 모두 제거
            df_full = df_full[df_full["date"] != latest_date]
            
            # edited_df 내용 전체 다시 추가
            new_records = []
            for idx in edited_df.index:
                comp_raw = edited_df.loc[idx, "회사명"]
                if pd.isna(comp_raw) or str(comp_raw).strip() == "":
                    continue
                comp = str(comp_raw).strip()
                status = str(edited_df.loc[idx, "상태"]) if pd.notna(edited_df.loc[idx, "상태"]) else "⚪ 수동"
                new_records.append({
                    "date": latest_date,
                    "company": comp,
                    "product": str(edited_df.loc[idx, "상품명"]).strip() if pd.notna(edited_df.loc[idx, "상품명"]) else "",
                    "usage_scope": str(edited_df.loc[idx, "사용범위"]) if pd.notna(edited_df.loc[idx, "사용범위"]) else "범용",
                    "width": float(edited_df.loc[idx, "가로(cm)"]) if pd.notna(edited_df.loc[idx, "가로(cm)"]) else 1,
                    "height": float(edited_df.loc[idx, "세로(cm)"]) if pd.notna(edited_df.loc[idx, "세로(cm)"]) else 1,
                    "unit_price": float(edited_df.loc[idx, "단가(원)"]) if pd.notna(edited_df.loc[idx, "단가(원)"]) else 0,
                    "qty_per_box": float(edited_df.loc[idx, "입수량(매)"]) if pd.notna(edited_df.loc[idx, "입수량(매)"]) else 1,
                    "shipping_per_box": float(edited_df.loc[idx, "배송비(원)"]) if pd.notna(edited_df.loc[idx, "배송비(원)"]) else 0,
                    "vat_status": str(edited_df.loc[idx, "부가세"]) if pd.notna(edited_df.loc[idx, "부가세"]) else "미포함",
                    "availability": str(edited_df.loc[idx, "판매여부"]) if pd.notna(edited_df.loc[idx, "판매여부"]) else "판매중",
                    "product_url": str(edited_df.loc[idx, "상품 URL"]) if pd.notna(edited_df.loc[idx, "상품 URL"]) else "",
                    "status": status,
                })
            
            if new_records:
                import pandas as pd
                df_full = pd.concat([df_full, pd.DataFrame(new_records)], ignore_index=True)
                
            df_full.to_csv(CSV_PATH, index=False)
            
            # 저장 완료 후 UI 상태 초기화 (경고 버튼 해제)
            if "main_table_editor" in st.session_state:
                del st.session_state["main_table_editor"]
                
            st.success("✅ 표의 변경사항(수정/추가/삭제)이 모두 저장되었습니다.")
            st.rerun()

    # ─── 가격 추이 차트 ───
    st.markdown("""
    <div class="section-title">📈 20×30 환산 최종단가 추이</div>
    """, unsafe_allow_html=True)

    company_colors = {
        "박스몰": "#3366ff",
        "비닐닷컴": "#ff6b35",
        "포장몰": "#00d68f",
        "달인 패키지": "#9d4edd",
    }

    # 날짜가 2개 이상일 때만 차트 표시
    unique_dates = df_calc["date"].nunique()

    if unique_dates >= 2:
        # 차트 데이터 준비 (업체+상품별) 및 날짜순 정렬
        df_chart = df_calc.copy().sort_values("date")
        df_chart["label"] = df_chart["company"] + " · " + df_chart["product"]

        fig = px.line(
            df_chart,
            x="date",
            y="20x30 환산단가",
            color="company",
            line_dash="product",
            markers=True,
            hover_data={
                "product": True,
                "usage_scope": True,
                "20x30 환산단가": ":,d",
                "배송비+VAT포함 단가": ":,d",
                "date": "|%Y-%m-%d",
            },
            labels={
                "date": "조사 날짜",
                "20x30 환산단가": "20×30 환산단가 (원)",
                "company": "업체",
                "product": "상품",
            },
            color_discrete_map=company_colors,
        )

        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(26, 26, 46, 0.8)",
            font=dict(family="Noto Sans KR", size=13),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                bgcolor="rgba(0,0,0,0.3)",
                bordercolor="rgba(255,255,255,0.1)",
                borderwidth=1,
            ),
            margin=dict(l=20, r=20, t=40, b=20),
            hovermode="x unified",
            xaxis=dict(
                gridcolor="rgba(255,255,255,0.05)",
                tickformat="%y.%m.%d", # 연도 포함 표기
            ),
            yaxis=dict(
                gridcolor="rgba(255,255,255,0.05)",
                title_standoff=10,
            ),
            height=450,
        )

        fig.update_traces(
            line=dict(width=1.2),
            marker=dict(size=8, line=dict(width=1, color="DarkSlateGrey")),
        )

        st.plotly_chart(fig, use_container_width=True)

    else:
        st.info(
            "📊 가격 추이 그래프는 **2일 이상의 데이터**가 입력되면 표시됩니다.\n\n"
            "다른 날짜로 데이터를 추가로 입력해주세요."
        )

    # ─── 전체 이력 테이블 (접기) ───
    with st.expander("📂 전체 데이터 이력 보기", expanded=False):
        if not df_calc.empty:
            history_df = df_calc[[
                "date", "company", "product", "product_url", "availability", "width", "height",
                "unit_price", "qty_per_box", "shipping_per_box",
                "박스당 가격", "배송비+VAT포함 단가", "20x30 환산단가"
            ]].copy()

            history_df.columns = [
                "날짜", "회사명", "상품명", "🔗", "판매여부", "가로", "세로",
                "단가", "입수량", "배송비",
                "박스당 가격", "배송비+VAT포함 단가", "20×30 환산단가"
            ]

            history_df = history_df.sort_values(
                ["날짜", "회사명", "상품명"],
                ascending=[False, True, True]
            )

            st.dataframe(
                history_df.style.format({
                    "가로": "{:.0f}",
                    "세로": "{:.0f}",
                    "단가": "{:.0f}",
                    "입수량": "{:,.0f}",
                    "배송비": "{:,.0f}",
                    "박스당 가격": "{:,.0f}",
                    "배송비+VAT포함 단가": "{:,.0f}",
                    "20×30 환산단가": "{:,.0f}",
                }),
                column_config={
                    "🔗": st.column_config.LinkColumn("🔗", display_text="🔗"),
                },
                use_container_width=True,
                hide_index=True,
            )

            # 데이터 삭제 기능
            st.markdown("---")
            st.markdown("**🗑️ 데이터 삭제**")
            del_cols = st.columns(3)
            with del_cols[0]:
                del_date = st.date_input("삭제할 날짜", key="del_date")
            with del_cols[1]:
                companies_list = df_calc["company"].unique().tolist()
                del_company = st.selectbox("회사명", companies_list, key="del_company")
            with del_cols[2]:
                products_list = df_calc[
                    df_calc["company"] == del_company
                ]["product"].unique().tolist()
                del_product = st.selectbox("상품명", products_list, key="del_product")

            if st.button("🗑️ 선택 항목 삭제", type="secondary"):
                delete_entry(del_date, del_company, del_product)
                st.success("삭제 완료!")
                st.rerun()


# ──────────────────────────────────────
# 5. 푸터
# ──────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: rgba(255,255,255,0.25); font-size: 0.8rem; padding: 1rem 0;">
    에어캡 시장 단가 통합 모니터링 시스템 v1.0 &nbsp;|&nbsp;
    수식: (단가 + 배송비÷입수량) ÷ (가로×세로) × 600 = 20×30 환산단가
</div>
""", unsafe_allow_html=True)
