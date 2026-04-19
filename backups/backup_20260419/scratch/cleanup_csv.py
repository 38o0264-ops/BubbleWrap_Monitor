import pandas as pd
import os

csv_path = 'price_history.csv'
if os.path.exists(csv_path):
    df = pd.read_csv(csv_path)
    
    # 박스몰: 상위 3개
    df_box = df[df['company'] == '박스몰'].head(3)
    
    # 비닐닷컴: 상위 2개
    df_vinyl = df[df['company'] == '비닐닷컴'].head(2)
    
    # 포장몰: '에어캡봉투' 키워드 포함 품목
    # '에어캡봉투' 또는 '에어캡비닐안전봉투' 등을 포함하는지 확인
    df_pojang = df[(df['company'] == '포장몰') & (df['product'].str.contains('에어캡봉투|에어캡비닐안전봉투'))]
    
    # 합치기
    df_new = pd.concat([df_box, df_vinyl, df_pojang], ignore_index=True)
    
    # 저장
    df_new.to_csv(csv_path, index=False)
    print(f"Original items: {len(df)}")
    print(f"Remaining items: {len(df_new)}")
    print(df_new[['company', 'product']])
else:
    print("CSV not found")
