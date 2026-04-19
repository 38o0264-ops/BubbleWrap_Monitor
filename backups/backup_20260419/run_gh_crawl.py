import crawler
import pandas as pd
import datetime
import os

CSV_PATH = "price_history.txt"
TIMESTAMP_PATH = "last_update.txt"

def load_data():
    if os.path.exists(CSV_PATH):
        try:
            df = pd.read_csv(CSV_PATH)
            df["date"] = pd.to_datetime(df["date"], format='mixed').dt.normalize()
            return df
        except Exception as e:
            print(f"데이터 로드 오류: {e}")
    return pd.DataFrame()

def run_update():
    print(f"[{datetime.datetime.now()}] 클라우드 크롤링 시작...")
    try:
        results = crawler.crawl_all()
        df_full = load_data()
        
        if df_full.empty:
            print("기존 데이터가 없습니다. 신규 데이터를 생성할 수 없으므로 종료합니다. (수동 데이터 필요)")
            return
            
        now = datetime.datetime.now()
        today = pd.Timestamp(now).normalize()
        
        # 오늘 날짜 데이터 확보 로직 (app.py와 동일)
        if today not in pd.to_datetime(df_full["date"]).values:
            last_day = pd.to_datetime(df_full["date"]).max()
            if last_day < today:
                temp_df = df_full[df_full["date"] == last_day].copy()
                temp_df["date"] = today
                temp_df["status"] = "⚪ 대기" 
                df_full = pd.concat([df_full, temp_df], ignore_index=True)
            else:
                today = last_day

        target_date = today
        matched = 0
        total_items = 0
        
        for comp, items in results.items():
            total_items += len(items)
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
                    df_full.loc[mask, "availability"] = item.get("availability", "판매중")
                    df_full.loc[mask, "status"] = "🟢 수집"
                    matched += 1
        
        # 저장
        df_full.to_csv(CSV_PATH, index=False)
        with open(TIMESTAMP_PATH, "w", encoding="utf-8") as f:
            f.write(now.strftime("%Y-%m-%d %H:%M:%S"))
            
        print(f"[{now}] 업데이트 완료: {matched}건 / 전체 {total_items}건")
        
    except Exception as e:
        print(f"크롤링 중 오류 발생: {e}")

if __name__ == "__main__":
    run_update()
