"""Shared dataset selection for the section pages: template download, upload, bundled presets."""

from __future__ import annotations
from pathlib import Path
from typing import Dict, Optional, Tuple

import pandas as pd
import streamlit as st

from engine.base import DemographicDataset
from engine.loader import load_demographic_dataset

SAMPLE_DIR = Path(__file__).resolve().parent.parent / "sample_data"


def load_sample(filename: str, name: Optional[str] = None) -> DemographicDataset:
    path = SAMPLE_DIR / filename
    if not path.is_file():
        st.error(f"Bundled dataset '{filename}' is missing. Run `python sample_data/generate_samples.py` to regenerate it.")
        st.stop()
    return load_demographic_dataset(path, name=name or path.stem)


def read_sample_csv(filename: str) -> pd.DataFrame:
    path = SAMPLE_DIR / filename
    if not path.is_file():
        st.error(f"Bundled dataset '{filename}' is missing. Run `python sample_data/generate_samples.py` to regenerate it.")
        st.stop()
    return pd.read_csv(path)


def sidebar_dataset(
    key: str,
    schema,
    presets: Dict[str, Tuple[str, str]],
    note: str = "",
) -> Tuple[DemographicDataset, str]:
    """
    Draws the sidebar controls and returns (dataset, source description).
    ``presets`` maps a menu label to (file name in sample_data, display name). The first entry is the default.
    """
    with st.sidebar:
        st.markdown("**Data**")
        st.download_button("Download CSV template", data=schema.generate_template_csv(), file_name=schema.file_name,
                           mime="text/csv", key=f"{key}_tpl")
        up = st.file_uploader(f"Upload {schema.file_name}", type=["csv", "json"], key=f"{key}_up",
                              help="Your file replaces the bundled dataset below.")
        choice = st.selectbox("Bundled dataset", list(presets.keys()), key=f"{key}_preset", disabled=up is not None)

    if up is not None:
        try:
            ds = load_demographic_dataset(up, name=up.name.rsplit(".", 1)[0])
        except Exception as exc:  # surface a readable message instead of a traceback
            st.error(f"Could not read '{up.name}': {exc}. Check the columns against the template in the sidebar.")
            st.stop()
        return ds, f"Uploaded file: {up.name}"
    fname, disp = presets[choice]
    return load_sample(fname, disp), (note or f"Bundled dataset: {choice}")


def default_projection_inputs() -> Dict[str, pd.DataFrame]:
    """Age-sex, fertility and mortality tables from the bundled 2022 files."""
    return {
        "age_sex": read_sample_csv("bbs_census_2022_age_sex.csv"),
        "fertility": read_sample_csv("bbs_svrs_2022_fertility.csv"),
        "mortality": read_sample_csv("bbs_svrs_2022_mortality.csv"),
    }
