@echo off
echo === AI Flood Risk Mapping setup ===
python -m venv venv
call venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
echo === REAL training pipeline (Sen1Floods11 + NASA POWER + SRTM) ===
python scripts\run_real_pipeline.py
echo === Whole-India grid + map ===
python scripts\run_india_pipeline.py
echo === DEMO fallback pipeline (simulated) ===
python scripts\run_pipeline.py
echo === Tests ===
python -m pytest tests/ -v
echo === Done. Dashboard: python -m streamlit run dashboard/app.py ===
echo === Report: python scripts/generate_report.py ===
