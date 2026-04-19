import requests
from bs4 import BeautifulSoup
import urllib3
import urllib.request
import ssl
import re

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def check_structure():
    url = "https://www.boxmall.net/product/product_list.php?code=000038&WonjiType=A"
    ctx = ssl._create_unverified_context()
    ctx.set_ciphers('DEFAULT@SECLEVEL=0')
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    res = urllib.request.urlopen(req, context=ctx, timeout=15)
    html_data = res.read()
    
    soup = BeautifulSoup(html_data, "html.parser", from_encoding="euc-kr")
    product_list = soup.find("div", id="product_list")
    if product_list:
        uls = product_list.find_all("ul")
        for i, ul in enumerate(uls):
            li11 = ul.find("li", class_="line11")
            text11 = li11.get_text(strip=True) if li11 else ""
            
            # Find one that doesn't say "일시품절"
            if "일시품절" not in text11:
                print(f"--- Product {i} (Likely Available) ---")
                for li in ul.find_all("li"):
                    print(f"Class: {li.get('class')}, HTML: {str(li)[:150]}")
                break

if __name__ == "__main__":
    check_structure()
