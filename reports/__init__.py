# reports package
import sys
import os
 
# Add repo root to path so utils.py and cycles.py are always importable
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)
 
# Also try cwd as fallback (Streamlit Cloud sets cwd to repo root)
_cwd = os.getcwd()
if _cwd not in sys.path:
    sys.path.insert(0, _cwd)
