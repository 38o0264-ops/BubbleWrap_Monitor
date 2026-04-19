import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crawler import crawl_all

def verify():
    print("Running crawl_all()...")
    results = crawl_all()
    
    for company, items in results.items():
        print(f"\n--- {company} ---")
        if items:
            sample = items[0]
            print(f"Product: {sample['product']}")
            print(f"URL: {sample.get('product_url', 'MISSING')}")
        else:
            print("No items found.")

if __name__ == "__main__":
    verify()
