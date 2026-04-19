import requests
from bs4 import BeautifulSoup
import urllib3
import urllib.request
import ssl
import re

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def verify_links():
    ctx = ssl._create_unverified_context()
    ctx.set_ciphers('DEFAULT@SECLEVEL=0')
    
    # 1. BoxMall
    print("--- BoxMall ---")
    url = "https://www.boxmall.net/product/product_list.php?code=000038&WonjiType=A"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    res = urllib.request.urlopen(req, context=ctx, timeout=15)
    html = res.read()
    soup = BeautifulSoup(html, "html.parser", from_encoding="euc-kr")
    pl = soup.find("div", id="product_list")
    if pl:
        ul = pl.find("ul")
        if ul:
            a = ul.find("li", class_="line2_c").find("a")
            if a:
                print(f"Link: {a['href']}")
    
    # 2. Vinyl.com
    print("\n--- Vinyl.com ---")
    url = "https://xn--ij1bycz62bkyq.com/category/%EC%97%90%EC%96%B4%EC%BA%A1%EB%B4%89%ED%88%AC%EB%B9%84%EC%A0%91%EC%B0%A9%EC%8B%9D/105/"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    res = urllib.request.urlopen(req, context=ctx, timeout=15)
    html = res.read().decode('utf-8')
    soup = BeautifulSoup(html, "html.parser")
    item = soup.select_one('.item')
    if item:
        a = item.select_one('.name strong a')
        if a:
            print(f"Link: {a['href']}")

    # 3. Pojangmall
    print("\n--- Pojangmall ---")
    url = "https://pojangmall.co.kr/product/list.html?cate_no=75"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    res = urllib.request.urlopen(req, context=ctx, timeout=15)
    html = res.read().decode('utf-8')
    soup = BeautifulSoup(html, "html.parser")
    item = soup.select_one('li.item')
    if item:
        a = item.select_one('.name a')
        if a:
            print(f"Link: {a['href']}")

    # 4. Dalin Package
    print("\n--- Dalin Package ---")
    url = "https://dalinweb.cafe24.com/shop/item_list.php?it_id=1703025293"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    res = urllib.request.urlopen(req, context=ctx, timeout=15)
    html = res.read().decode('utf-8')
    soup = BeautifulSoup(html, "html.parser")
    table = soup.select_one('.sit_item_list table')
    if table:
        rows = table.find_all('tr')
        if len(rows) > 1:
            cols = rows[1].find_all('td')
            if cols:
                print(f"First row cols count: {len(cols)}")
                # Check for links in any column
                for i, col in enumerate(cols):
                    a = col.find('a')
                    if a:
                        print(f"Col {i} has link: {a['href']}")

if __name__ == "__main__":
    verify_links()
