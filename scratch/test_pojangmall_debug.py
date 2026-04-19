import requests
from bs4 import BeautifulSoup
import re
import urllib.request
import ssl

def test_pojangmall():
    url = "https://pojangmall.co.kr/product/list.html?cate_no=75"
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    ctx.set_ciphers('DEFAULT@SECLEVEL=0')
    
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'})
    with urllib.request.urlopen(req, context=ctx, timeout=15) as response:
        content = response.read()
        # Try to detect encoding
        html = content.decode('utf-8', errors='replace')
        
    soup = BeautifulSoup(html, 'html.parser')
    
    # Try different selectors
    selectors = [
        'li.item',
        'li.xans-record-',
        '.prdList li',
        '.name'
    ]
    
    for s in selectors:
        found = soup.select(s)
        print(f"Selector '{s}' found {len(found)} elements")
        if found and len(found) > 0:
            try:
                text = found[0].get_text(strip=True)
                # Print safely for Windows console
                print(f"First element text sample (encoded): {text[:50].encode('ascii', 'ignore')}")
                
                # Check name and price inside the first item
                if s == 'li.item':
                    name = found[0].select_one('.name span')
                    price = found[0].select_one('li.xans-record- span:nth-child(2)') # Cafe24 often uses nth-child
                    if not price:
                        price = found[0].select_one('span.price')
                    if not price:
                        # Try to find text with '원'
                        price = found[0].find(string=re.compile(r'[\d,]+원'))
                    
                    name_txt = name.get_text(strip=True) if name else "NOT FOUND"
                    price_txt = price.get_text(strip=True) if price else (price if isinstance(price, str) else "NOT FOUND")
                    print(f"  Name found: {'YES' if name else 'NO'}")
                    print(f"  Price found: {'YES' if price else 'NO'}")
                    if name: print(f"  Name sample: {name_txt[:20].encode('ascii', 'ignore')}")
                    if price: print(f"  Price sample: {str(price)[:20].encode('ascii', 'ignore')}")

            except Exception as e:
                print(f"  Error printing sample: {e}")

if __name__ == "__main__":
    test_pojangmall()
