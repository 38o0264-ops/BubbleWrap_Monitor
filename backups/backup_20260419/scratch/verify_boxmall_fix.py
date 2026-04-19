import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crawler import crawl_boxmall

def verify():
    print("Running crawl_boxmall()...")
    results = crawl_boxmall()
    print(f"Total products found: {len(results)}")
    
    sold_out = [r for r in results if r['availability'] == '품절']
    available = [r for r in results if r['availability'] == '판매중']
    
    print(f"Available: {len(available)}")
    print(f"Sold Out: {len(sold_out)}")
    
    if len(results) > 0:
        print("\nSample results:")
        for r in results[:10]:
            print(f"- {r['product']}: {r['availability']} (Qty: {r['qty_per_box']})")

if __name__ == "__main__":
    verify()
