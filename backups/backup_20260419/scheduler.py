import time
import datetime
import pandas as pd
import os
import crawler # crawler.py 임포트

CSV_PATH = "price_history.csv"
TIMESTAMP_PATH = "last_update.txt"
DEPLOY_DATA_PATH = "deploy_aircap/price_history.txt"
DEPLOY_TIMESTAMP_PATH = "deploy_aircap/last_update.txt"
INTERVAL_SECONDS = 3600 # 1시간

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

def load_data():
    if os.path.exists(CSV_PATH):
        df = pd.read_csv(CSV_PATH)
        # 컬럼 존재 확인 및 타입 강제 (app.py와 동일 로직)
        if "product_url" not in df.columns:
            df["product_url"] = ""
        else:
            df["product_url"] = df["product_url"].fillna("").astype(str)
        
        if "status" not in df.columns:
            df["status"] = "⚪ 수동"
            
        return df
    return pd.DataFrame()

def run_update():
    print(f"[{datetime.datetime.now()}] 백그라운드 크롤링 시작...")
    try:
        results = crawler.crawl_all()
        df_full = load_data()
        
        if df_full.empty:
            print("데이터 파일이 없습니다.")
            return False
            
        latest_date = df_full["date"].max()
        matched = 0
        total_items = 0
        
        for comp, items in results.items():
            total_items += len(items)
            for item in items:
                db_company = df_full["company"].astype(str).str.strip()
                mask = (df_full["date"] == latest_date) & \
                       (db_company == comp) & \
                       (df_full["width"] == item["width"]) & \
                       (df_full["height"] == item["height"])
                
                if mask.any():
                    df_full.loc[mask, "unit_price"] = item["unit_price"]
                    df_full.loc[mask, "qty_per_box"] = item["qty_per_box"]
                    df_full.loc[mask, "status"] = "🟢 수집"
                    matched += 1
        
        df_full.to_csv(CSV_PATH, index=False)
        
        # [NEW] 배포용 TXT 파일 자동 생성 (카페24 확장자 제한 우회)
        if not os.path.exists("deploy_aircap"):
            os.makedirs("deploy_aircap")
        df_full.to_csv(DEPLOY_DATA_PATH, index=False)
        
        now = datetime.datetime.now()
        save_last_update(now)
        # 배포용 타임스탬프도 별도로 저장
        with open(DEPLOY_TIMESTAMP_PATH, "w", encoding="utf-8") as f:
            f.write(now.strftime("%Y-%m-%d %H:%M:%S"))
            
        print(f"[{now}] 업데이트 완료: {matched}건 / 전체 {total_items}건")
        print(f"[{now}] 배포용 파일 생성 완료: {DEPLOY_DATA_PATH}")
        return True
    except Exception as e:
        print(f"오류 발생: {e}")
        return False

def main():
    print("=== 에어캡 단가 모니터링 스케줄러 실행 중 (1시간 주기) ===")
    while True:
        last_dt = get_last_update()
        now = datetime.datetime.now()
        
        should_update = False
        if last_dt is None:
            should_update = True
        else:
            diff = (now - last_dt).total_seconds()
            if diff >= INTERVAL_SECONDS:
                should_update = True
        
        if should_update:
            run_update()
        else:
            # 남은 시간 출력
            remain = INTERVAL_SECONDS - (now - last_dt).total_seconds()
            print(f"[{now}] 다음 업데이트까지 {int(remain//60)}분 남음...", end="\r")
            
        time.sleep(60) # 1분마다 체크

if __name__ == "__main__":
    main()
