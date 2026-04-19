import sys
import time
import importlib

modules = ["streamlit", "pandas", "plotly.express", "crawler"]

for mod in modules:
    print(f"Importing {mod}...", end="", flush=True)
    start = time.time()
    try:
        importlib.import_module(mod)
        print(f" OK ({(time.time() - start):.2f}s)")
    except Exception as e:
        print(f" FAILED: {e}")

print("All import tests done.")
