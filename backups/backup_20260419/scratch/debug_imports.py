import sys
print(f"Python: {sys.version}")
try:
    import streamlit as st
    print(f"Streamlit: {st.__version__}")
    import pandas as pd
    print("Pandas imported")
    import plotly.express as px
    print("Plotly imported")
    import crawler
    print("Crawler imported")
    print("ALL IMPORTS SUCCESSFUL")
except Exception as e:
    print(f"IMPORT ERROR: {e}")
    import traceback
    traceback.print_exc()
