"""
에어캡 시장 단가 자동 수집 모듈 (Placeholder)

이 파일은 추후 Selenium / BeautifulSoup를 활용하여
각 업체 사이트에서 에어캡 단가를 자동 크롤링하기 위한 스켈레톤입니다.

사용법:
    1. 각 함수 안에 크롤링 로직을 구현합니다.
    2. 함수는 list[dict] 형태로 상품 정보를 반환해야 합니다.
    3. 반환 dict 키: product, width, height, unit_price, qty_per_box, shipping_per_box
"""

# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from bs4 import BeautifulSoup
# import requests
# import time


import requests
from bs4 import BeautifulSoup
import re
import urllib3
import urllib.request
import ssl

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def crawl_boxmall() -> list[dict]:
    """
    박스몰(boxmall.net) 에어캡 단가 크롤링
    """
    url = "https://www.boxmall.net/product/product_list.php?code=000038&WonjiType=A"
    
    try:
        # TLS handshake 오류(dh key too small) 우회를 위해 urllib와 ssl context 활용
        ctx = ssl._create_unverified_context()
        ctx.set_ciphers('DEFAULT@SECLEVEL=0')
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        res = urllib.request.urlopen(req, context=ctx, timeout=15)
        html_data = res.read()
    except Exception as e:
        print(f"[박스몰] 사이트 접속 실패: {e}")
        return []

    # 파싱
    soup = BeautifulSoup(html_data, "html.parser", from_encoding="euc-kr")
    
    results = []
    
    product_list = soup.find("div", id="product_list")
    if not product_list:
        print("[박스몰] 상품 리스트(product_list) 요소를 찾을 수 없습니다.")
        return []
        
    for ul in product_list.find_all("ul"):
        size_li = ul.find("li", class_="line2_c")
        price_li = ul.find("li", class_="line7")
        qty_li = ul.find("li", class_="line6")
        
        if not (size_li and price_li and qty_li):
            continue
            
        size_text = size_li.get_text(strip=True)
        m = re.search(r"(\d+)\s*[xX\*]\s*(\d+)", size_text)
        if not m:
            continue
            
        width = int(m.group(1))
        height = int(m.group(2))
        
        price_str = re.sub(r"[^\d.]", "", price_li.get_text(strip=True))
        qty_str = re.sub(r"[^\d]", "", qty_li.get_text(strip=True))
        
        if price_str and qty_str:
            unit_price = float(price_str)
            qty = int(qty_str)
            
            # 실제 홈페이지 배송비 규정에 따라 추후 로직 보완 가능 (여기서는 5300원으로 고정)
            shipping_fee = 5300
            
            # 판매여부 확인: 'line11' 클래스 셀에 체크박스가 있으면 판매중 (일시품절 시 체크박스 없음)
            check_cell = ul.find("li", class_="line11")
            is_available = False
            if check_cell and check_cell.find("input", {"type": "checkbox"}):
                is_available = True
            
            product_url = ""
            a_tag = size_li.find("a")
            if a_tag and "href" in a_tag.attrs:
                product_url = "https://www.boxmall.net/product/" + a_tag["href"]

            results.append({
                "product": f"에어캡 {width}x{height}",
                "width": width,
                "height": height,
                "unit_price": unit_price,
                "qty_per_box": qty,
                "shipping_per_box": shipping_fee,
                "availability": "판매중" if is_available else "품절",
                "product_url": product_url
            })

    print(f"[박스몰] {len(results)}개 상품 크롤링 완료")
    return results


def crawl_vinyl_com() -> list[dict]:
    """
    비닐닷컴 에어캡 단가 크롤링
    
    구현 로직:
        1. 비닐닷컴 에어캡봉투 카테고리(105)에서 상품 목록 파싱
        2. 상품명에서 가로/세로(mm) 및 입수량(매) 추출
        3. 판매가(박스당 가격)를 바탕으로 단가 역산
    """
    products = []
    shipping_fee = 0 # UI 수동입력으로 처리
    
    try:
        url = "https://xn--ij1bycz62bkyq.com/category/%EC%97%90%EC%96%B4%EC%BA%A1%EB%B4%89%ED%88%AC%EB%B9%84%EC%A0%91%EC%B0%A9%EC%8B%9D/105/"
        
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        ctx.set_ciphers('DEFAULT@SECLEVEL=0')
        
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, context=ctx) as response:
            html = response.read().decode('utf-8')
            
        soup = BeautifulSoup(html, 'html.parser')
        items = soup.select('.item')
        
        for item in items:
            name_el = item.select_one('.name strong a')
            if not name_el:
                continue
            name_text = name_el.text.strip()
            
            price_text = ""
            for span in item.select('.info span'):
                t = span.text.strip()
                if '원' in t and ',' in t:
                    price_text = t
                    break
                    
            if not price_text:
                continue
                
            s = re.search(r'(\d+)\*(\d+)', name_text)
            q = re.search(r'(\d+)매', name_text)
            p = re.search(r'([\d,]+)', price_text)
            
            if s and q and p:
                width_cm = int(s.group(1)) / 10.0
                height_cm = int(s.group(2)) / 10.0
                qty = int(q.group(1))
                box_price = int(p.group(1).replace(',', ''))
                
                # 역산 단가 계산
                unit_price = box_price / qty
                
                # 불필요한 접두어 제거
                clean_name = name_text
                if " :" in clean_name:
                    clean_name = clean_name.split(" :")[-1].strip()
                
                product_url = ""
                if name_el.has_attr('href'):
                    product_url = "https://xn--ij1bycz62bkyq.com" + name_el['href']

                products.append({
                    "product": clean_name,
                    "width": width_cm,
                    "height": height_cm,
                    "unit_price": unit_price,
                    "qty_per_box": qty,
                    "shipping_per_box": shipping_fee,
                    "availability": "품절" if item.select_one('img[alt="품절"]') else "판매중",
                    "product_url": product_url
                })
        print(f"[비닐닷컴] {len(products)}개 상품 크롤링 완료")
        
    except Exception as e:
        print(f"[비닐닷컴] 크롤링 오류: {e}")
        
    return products


def crawl_pojangmall() -> list[dict]:
    """
    포장몰(pojangmall.co.kr) 에어캡 단가 크롤링
    
    구현 로직:
        1. 포장몰 비닐안전봉투 카테고리(75)에서 상품 목록 파싱
        2. 상품명에서 가로x세로(mm) 및 입수량(매) 추출
        3. 판매가(박스당 가격)를 바탕으로 단가 역산
    """
    products = []
    shipping_fee = 0 # UI 수동입력 연동
    url = "https://pojangmall.co.kr/product/list.html?cate_no=75"
    
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        ctx.set_ciphers('DEFAULT@SECLEVEL=0')
        
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, context=ctx, timeout=15) as response:
            html = response.read().decode('utf-8')
            
        soup = BeautifulSoup(html, 'html.parser')
        # Cafe24 기반 쇼핑몰 구조: li.item
        items = soup.select('li.item')
        
        for item in items:
            # 상품명 추출
            name_el = item.select_one('.name a')
            if not name_el:
                name_el = item.select_one('.name span')
            
            if not name_el:
                continue
            name_text = name_el.get_text(strip=True)
            
            # 가격 추출 (판매가 항목 찾기)
            price_text = ""
            # Cafe24 특유의 span 구조 대응
            for li in item.select('ul.xans-product-listitem li'):
                li_text = li.get_text(strip=True)
                if '판매가' in li_text:
                    price_text = li_text
                    break
            
            if not price_text:
                # 대안: span.price 등
                price_el = item.select_one('span.price') or item.select_one('.price span')
                if price_el:
                    price_text = price_el.get_text(strip=True)
            
            if not price_text:
                continue
                
            # 규격 및 입수량 파싱
            s = re.search(r'(\d+)\s*[xX]\s*(\d+)', name_text)
            q = re.search(r'(\d+)매', name_text)
            p = re.search(r'([\d,]{2,})', price_text) # 최소 2자리 숫자 (쉼표 포함)
            
            if s and q and p:
                # mm -> cm 변환
                width_cm = float(s.group(1)) / 10.0
                height_cm = float(s.group(2)) / 10.0
                qty = int(q.group(1))
                box_price = int(p.group(1).replace(',', ''))
                
                # 역산 단가 계산
                unit_price = box_price / qty
                
                product_url = ""
                if name_el.name == 'a' and name_el.has_attr('href'):
                    product_url = "https://pojangmall.co.kr" + name_el['href']
                elif name_el.find('a'):
                    a_tag = name_el.find('a')
                    product_url = "https://pojangmall.co.kr" + a_tag['href']

                products.append({
                    "product": name_text,
                    "width": width_cm,
                    "height": height_cm,
                    "unit_price": unit_price,
                    "qty_per_box": qty,
                    "shipping_per_box": shipping_fee,
                    "availability": "품절" if item.select_one('.sold img') else "판매중",
                    "product_url": product_url
                })
        print(f"[포장몰] {len(products)}개 상품 크롤링 완료")
        
    except Exception as e:
        print(f"[포장몰] 크롤링 오류: {e}")
        
    return products


def crawl_dalin() -> list[dict]:
    """
    달인 패키지(dalinweb.cafe24.com) 에어캡 단가 크롤링
    
    구현 로직:
        1. 지정된 아이템 페이지에서 테이블 파싱
        2. 규격(20*30, 25*35) 필터링
        3. '단가'와 '판매단위' 추출
    """
    products = []
    url = "https://dalinweb.cafe24.com/shop/item_list.php?it_id=1703025293"
    
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        ctx.set_ciphers('DEFAULT@SECLEVEL=0')
        
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, context=ctx, timeout=15) as response:
            html = response.read().decode('utf-8')
            
        soup = BeautifulSoup(html, 'html.parser')
        
        # 테이블 찾기 (클래스 sit_item_list 내부의 table)
        table = soup.select_one('.sit_item_list table')
        if not table:
            print("[달인 패키지] 테이블을 찾을 수 없습니다.")
            return []
            
        rows = table.find_all('tr')
        for row in rows:
            cols = row.find_all('td')
            if len(cols) < 5:
                continue
                
            size_text = cols[0].get_text(strip=True) # 외경사이즈(cm)
            price_text = cols[3].get_text(strip=True) # 단가
            qty_text = cols[4].get_text(strip=True) # 판매단위
            
            # 모든 사이즈 수집하도록 필터 제거
            if True:
                # 숫자만 추출
                unit_price = float(re.sub(r'[^\d]', '', price_text))
                qty = int(re.sub(r'[^\d]', '', qty_text))
                
                product_url = ""
                # 첫 번째 a 태그 검색
                a_tag = row.find('a')
                if a_tag and a_tag.has_attr('href'):
                    product_url = "https://dalinweb.cafe24.com" + a_tag['href']

                products.append({
                    "product": f"에어캡봉투 {size_text}",
                    "width": float(size_text.split('*')[0]),
                    "height": float(size_text.split('*')[1]),
                    "unit_price": unit_price,
                    "qty_per_box": qty,
                    "shipping_per_box": 0, # 확인 필요 시 수동 조정
                    "availability": "품절" if "전화문의" in price_text else "판매중",
                    "product_url": product_url
                })
                
        print(f"[달인 패키지] {len(products)}개 상품 크롤링 완료")
        
    except Exception as e:
        print(f"[달인 패키지] 크롤링 오류: {e}")
        
    return products


def crawl_all() -> dict[str, list[dict]]:
    """
    모든 업체의 크롤링을 실행하고 결과를 통합 반환합니다.

    Returns:
        dict[str, list[dict]]: {업체명: [상품 정보 리스트]}
        예시: {
            "박스몰": [...],
            "업체B": [...],
            "업체C": [...]
        }
    """
    results = {
        "박스몰": crawl_boxmall(),
        "비닐닷컴": crawl_vinyl_com(),
        "포장몰": crawl_pojangmall(),
        "달인 패키지": crawl_dalin(),
    }

    total = sum(len(v) for v in results.values())
    print(f"[크롤링 완료] 총 {total}개 상품 수집됨")

    return results
