"""
Vital Stats Suite: entry point and navigation.

Run with:  streamlit run app.py      (or:  python app.py)
"""

import sys
from pathlib import Path

import streamlit as st

if __name__ == "__main__" and not st.runtime.exists():  # `python app.py` convenience launcher
    from streamlit.web import cli as stcli
    sys.argv = ["streamlit", "run", str(Path(__file__).resolve())] + sys.argv[1:]
    sys.exit(stcli.main())

SECTIONS = [
    ("pages/1_Composition_and_Growth.py", "Composition & Growth", ":material/groups:"),
    ("pages/2_Data_Quality.py", "Data Quality", ":material/fact_check:"),
    ("pages/3_Fertility.py", "Fertility", ":material/child_care:"),
    ("pages/4_Mortality.py", "Mortality", ":material/monitor_heart:"),
    ("pages/5_Life_Tables.py", "Life Tables", ":material/timeline:"),
    ("pages/6_Nuptiality.py", "Nuptiality", ":material/favorite:"),
    ("pages/7_Migration.py", "Migration", ":material/route:"),
    ("pages/8_Graduation.py", "Graduation", ":material/stacked_line_chart:"),
    ("pages/9_Stable_Population.py", "Stable Population", ":material/balance:"),
    ("pages/10_Projections.py", "Projections", ":material/trending_up:"),
]

navigation = st.navigation({
    "Dashboard": [st.Page("home.py", title="Overview", icon=":material/home:", default=True)],
    "Sections": [st.Page(path, title=title, icon=icon, url_path=Path(path).stem.split("_", 1)[1].lower()) for path, title, icon in SECTIONS],
})
navigation.run()
