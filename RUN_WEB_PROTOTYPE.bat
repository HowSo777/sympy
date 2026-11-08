@echo off
cd /d "%~dp0"
echo ========================================================
echo Launching Match Zero SymPy Web Dashboard (Streamlit)...
echo ========================================================
py -m streamlit run app_prototype.py
pause
