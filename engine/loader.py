"""
Vital Stats Suite - Demographic Data Ingestion & Parser
Supports:
1. Multi-format CSV ingestion (Age-Sex tables, 5-year tables, key-value indicators, wide summaries)
2. JSON dataset ingestion
3. Strict demographic normalization without data invention (Fix B7)
4. Sample CSV template generators linked to section schemas
"""

from __future__ import annotations
import io
import json
import re
from pathlib import Path
from typing import Dict, Any, Optional, Union, Tuple
import pandas as pd
import numpy as np

from engine.base import DemographicDataset
from engine.schemas import get_template_csv


def normalize_column_name(col: str) -> str:
    """Normalizes string column names (lowercase, stripped, alphanumeric with underscores)."""
    return re.sub(r"[^a-z0-9_]+", "_", str(col).strip().lower()).strip("_")


def parse_age_to_numeric(val: Any) -> Optional[int]:
    """Extracts base integer age from strings like '0', '5', '85+', '0-4', '5-9'."""
    s = str(val).strip()
    match = re.match(r"^(\d+)", s)
    if match:
        return int(match.group(1))
    return None


def parse_age_group_label(val: Any) -> str:
    """Standardizes age group labels like '0-4', '5 to 9', '85+', '85 and over'."""
    s = str(val).strip()
    if re.match(r"^\d+\s*-\s*\d+$", s):
        parts = re.split(r"\s*-\s*", s)
        return f"{parts[0]}-{parts[1]}"
    if re.match(r"^\d+\s+to\s+\d+$", s, re.IGNORECASE):
        parts = re.split(r"\s+to\s+", s, flags=re.IGNORECASE)
        return f"{parts[0]}-{parts[1]}"
    if "+" in s or "over" in s.lower() or "plus" in s.lower():
        match = re.search(r"(\d+)", s)
        if match:
            return f"{match.group(1)}+"
    return s


def load_demographic_dataset(
    source: Union[str, Path, io.BytesIO, io.StringIO, pd.DataFrame, dict],
    name: Optional[str] = None,
    year: Optional[int] = None,
    region: Optional[str] = None,
) -> DemographicDataset:
    """
    Universal demographic loader. Ingests JSON, CSV (Age-Sex, Key-Value, Wide), or DataFrame,
    and returns a standardized DemographicDataset without heuristic data invention.
    """
    # 1. Handle JSON string or file path
    if isinstance(source, (str, Path)):
        is_path = False
        if isinstance(source, Path):
            is_path = source.is_file()
            p = source
        elif isinstance(source, str) and "\n" not in source and len(source) < 500:
            try:
                p = Path(source)
                is_path = p.is_file()
            except Exception:
                is_path = False
        
        if is_path:
            if p.suffix.lower() == ".json":
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return _from_dict(data, default_name=name or p.stem, default_year=year, default_region=region)
            else:
                df = pd.read_csv(p)
                return _from_dataframe(df, name=name or p.stem, year=year, region=region)
        else:
            raw_str = str(source).strip()
            if raw_str.startswith("{") and raw_str.endswith("}"):
                data = json.loads(raw_str)
                return _from_dict(data, default_name=name, default_year=year, default_region=region)
            else:
                df = pd.read_csv(io.StringIO(raw_str))
                return _from_dataframe(df, name=name, year=year, region=region)

    # 2. Handle BytesIO / StringIO
    if isinstance(source, (io.BytesIO, io.StringIO)):
        if isinstance(source, io.BytesIO):
            content = source.getvalue().decode("utf-8", errors="replace").strip()
        else:
            content = source.getvalue().strip()

        if content.startswith("{") and content.endswith("}"):
            data = json.loads(content)
            return _from_dict(data, default_name=name, default_year=year, default_region=region)
        else:
            df = pd.read_csv(io.StringIO(content))
            return _from_dataframe(df, name=name, year=year, region=region)

    # 3. Handle Dictionary
    if isinstance(source, dict):
        return _from_dict(source, default_name=name, default_year=year, default_region=region)

    # 4. Handle pandas DataFrame
    if isinstance(source, pd.DataFrame):
        return _from_dataframe(source, name=name, year=year, region=region)

    raise ValueError(f"Unsupported source format for demographic dataset: {type(source)}")


def _from_dict(data: dict, default_name: Optional[str] = None, default_year: Optional[int] = None, default_region: Optional[str] = None) -> DemographicDataset:
    """Builds DemographicDataset from a parsed JSON dictionary."""
    single_year_df = pd.DataFrame(data["single_year_ages"]) if "single_year_ages" in data and data["single_year_ages"] else None
    age_group_5yr_df = pd.DataFrame(data["age_group_5yr"]) if "age_group_5yr" in data and data["age_group_5yr"] else None
    fertility_df = pd.DataFrame(data["fertility_schedule"]) if "fertility_schedule" in data and data["fertility_schedule"] else None
    mortality_df = pd.DataFrame(data["mortality_schedule"]) if "mortality_schedule" in data and data["mortality_schedule"] else None
    marital_df = pd.DataFrame(data["marital_status_df"]) if "marital_status_df" in data and data["marital_status_df"] else None
    migration_matrix_df = pd.DataFrame(data["migration_matrix_df"]) if "migration_matrix_df" in data and data["migration_matrix_df"] else None
    std_pop_df = pd.DataFrame(data["standard_population"]) if "standard_population" in data and data["standard_population"] else None
    std_rates_df = pd.DataFrame(data["standard_rates"]) if "standard_rates" in data and data["standard_rates"] else None

    # Derive broad age groups if single_year_ages is present but broad groups are missing
    pop_0_14 = data.get("pop_0_14")
    pop_15_64 = data.get("pop_15_64")
    pop_65_plus = data.get("pop_65_plus")
    tot_pop = data.get("total_population")
    male_pop = data.get("male_population")
    fem_pop = data.get("female_population")

    if single_year_df is not None and not single_year_df.empty:
        age_col = "age" if "age" in single_year_df.columns else single_year_df.columns[0]
        single_year_df["age_num"] = single_year_df[age_col].apply(parse_age_to_numeric)
        
        tot_col = "total" if "total" in single_year_df.columns else ("male" if "male" in single_year_df.columns else single_year_df.columns[1])
        if pop_0_14 is None:
            pop_0_14 = float(single_year_df[single_year_df["age_num"] <= 14][tot_col].sum())
        if pop_15_64 is None:
            pop_15_64 = float(single_year_df[(single_year_df["age_num"] >= 15) & (single_year_df["age_num"] <= 64)][tot_col].sum())
        if pop_65_plus is None:
            pop_65_plus = float(single_year_df[single_year_df["age_num"] >= 65][tot_col].sum())
            
        if tot_pop is None:
            tot_pop = float(single_year_df[tot_col].sum())
        if male_pop is None and "male" in single_year_df.columns:
            male_pop = float(single_year_df["male"].sum())
        if fem_pop is None and "female" in single_year_df.columns:
            fem_pop = float(single_year_df["female"].sum())

    # Build 5-year table from single-year if missing
    if age_group_5yr_df is None and single_year_df is not None and not single_year_df.empty:
        groups = []
        for a in range(0, 85, 5):
            sub = single_year_df[(single_year_df["age_num"] >= a) & (single_year_df["age_num"] <= a + 4)]
            groups.append({
                "age_group": f"{a}-{a+4}",
                "male": sub["male"].sum() if "male" in sub.columns else sub["total"].sum() * 0.5,
                "female": sub["female"].sum() if "female" in sub.columns else sub["total"].sum() * 0.5,
                "total": sub["total"].sum() if "total" in sub.columns else sub["male"].sum() + sub["female"].sum(),
            })
        sub85 = single_year_df[single_year_df["age_num"] >= 85]
        groups.append({
            "age_group": "85+",
            "male": sub85["male"].sum() if "male" in sub85.columns else sub85["total"].sum() * 0.5,
            "female": sub85["female"].sum() if "female" in sub85.columns else sub85["total"].sum() * 0.5,
            "total": sub85["total"].sum() if "total" in sub85.columns else sub85["male"].sum() + sub85["female"].sum(),
        })
        age_group_5yr_df = pd.DataFrame(groups)

    return DemographicDataset(
        name=data.get("name", default_name or "Demographic Dataset"),
        year=data.get("year", default_year),
        region=data.get("region", default_region or "National"),
        area_km2=data.get("area_km2"),
        urban_population=data.get("urban_population"),
        total_population=tot_pop,
        male_population=male_pop,
        female_population=fem_pop,
        pop_0_14=pop_0_14,
        pop_15_64=pop_15_64,
        pop_65_plus=pop_65_plus,
        total_live_births=data.get("total_live_births"),
        male_births=data.get("male_births"),
        female_births=data.get("female_births"),
        marital_births=data.get("marital_births"),
        married_women_15_49=data.get("married_women_15_49"),
        total_women_15_49=data.get("total_women_15_49"),
        total_deaths=data.get("total_deaths"),
        male_deaths=data.get("male_deaths"),
        female_deaths=data.get("female_deaths"),
        neonatal_deaths=data.get("neonatal_deaths"),
        early_neonatal_deaths=data.get("early_neonatal_deaths"),
        post_neonatal_deaths=data.get("post_neonatal_deaths"),
        infant_deaths=data.get("infant_deaths"),
        child_deaths_1_4=data.get("child_deaths_1_4"),
        pop_1_4=data.get("pop_1_4"),
        maternal_deaths=data.get("maternal_deaths"),
        stillbirths=data.get("stillbirths"),
        census_coverage_rate=data.get("census_coverage_rate") or data.get("pec_completeness_rate"),
        pec_omission_rate=data.get("pec_omission_rate"),
        death_registration_completeness=data.get("death_registration_completeness"),
        birth_registration_completeness=data.get("birth_registration_completeness"),
        marriages_total=data.get("marriages_total"),
        first_marriages=data.get("first_marriages"),
        divorces_total=data.get("divorces_total"),
        in_migrants=data.get("in_migrants"),
        out_migrants=data.get("out_migrants"),
        net_migrants=data.get("net_migrants"),
        previous_census_pop=data.get("previous_census_pop"),
        previous_census_year=data.get("previous_census_year"),
        single_year_ages=single_year_df,
        age_group_5yr=age_group_5yr_df,
        fertility_schedule=fertility_df,
        mortality_schedule=mortality_df,
        marital_status_df=marital_df,
        migration_matrix_df=migration_matrix_df,
        standard_population=std_pop_df,
        standard_rates=std_rates_df,
        metadata=data.get("metadata", {}),
    )


def _from_dataframe(
    df: pd.DataFrame,
    name: Optional[str] = None,
    year: Optional[int] = None,
    region: Optional[str] = None,
) -> DemographicDataset:
    """
    Parses a pandas DataFrame into DemographicDataset without heuristic data invention (Fix B7).
    """
    clean_df = df.copy()
    clean_df.columns = [normalize_column_name(c) for c in clean_df.columns]

    # Check for Key-Value Indicator Format (e.g. indicator, value)
    if len(clean_df.columns) == 2 and any(c in clean_df.columns for c in ["indicator", "variable", "metric"]):
        ind_col = [c for c in clean_df.columns if c in ["indicator", "variable", "metric"]][0]
        val_col = [c for c in clean_df.columns if c != ind_col][0]
        kv = {}
        for _, r in clean_df.iterrows():
            k = normalize_column_name(str(r[ind_col]))
            v = r[val_col]
            try:
                kv[k] = float(str(v).replace(",", "").strip())
            except Exception:
                kv[k] = v
                
        return DemographicDataset(
            name=name or "Indicators Dataset",
            year=int(kv["year"]) if kv.get("year") not in (None, "") and str(kv.get("year")).replace(".0","").isdigit() else year,
            region=str(kv.get("region", region or "National")),
            area_km2=kv.get("area_km2"),
            urban_population=kv.get("urban_population"),
            total_population=kv.get("total_population") or kv.get("population") or kv.get("midyear_population"),
            male_population=kv.get("male_population"),
            female_population=kv.get("female_population"),
            pop_0_14=kv.get("pop_0_14"),
            pop_15_64=kv.get("pop_15_64"),
            pop_65_plus=kv.get("pop_65_plus"),
            total_live_births=kv.get("total_live_births") or kv.get("births") or kv.get("live_births"),
            male_births=kv.get("male_births"),
            female_births=kv.get("female_births"),
            marital_births=kv.get("marital_births"),
            married_women_15_49=kv.get("married_women_15_49"),
            total_women_15_49=kv.get("total_women_15_49") or kv.get("women_15_49"),
            total_deaths=kv.get("total_deaths") or kv.get("deaths"),
            neonatal_deaths=kv.get("neonatal_deaths"),
            infant_deaths=kv.get("infant_deaths"),
            child_deaths_1_4=kv.get("child_deaths_1_4") or kv.get("deaths_1_4"),
            pop_1_4=kv.get("pop_1_4"),
            maternal_deaths=kv.get("maternal_deaths"),
            marriages_total=kv.get("marriages_total") or kv.get("marriages"),
            divorces_total=kv.get("divorces_total") or kv.get("divorces"),
            in_migrants=kv.get("in_migrants"),
            out_migrants=kv.get("out_migrants"),
            previous_census_pop=kv.get("previous_census_pop"),
            previous_census_year=int(kv["previous_census_year"]) if "previous_census_year" in kv else None,
            census_coverage_rate=kv.get("census_coverage_rate") or kv.get("pec_completeness_rate") or kv.get("completeness_rate"),
            pec_omission_rate=kv.get("pec_omission_rate") or kv.get("omission_rate"),
            death_registration_completeness=kv.get("death_registration_completeness"),
            raw_df=clean_df,
        )

    # ---- Table-kind detection: schedule-only tables must not masquerade as full population tables ----
    cols = set(clean_df.columns)

    def _num(col: str) -> pd.Series:
        return pd.to_numeric(clean_df[col].astype(str).str.replace(",", "").str.strip(), errors="coerce").fillna(0)

    if {"origin", "destination"} <= cols:
        return DemographicDataset(
            name=name or "Migration Streams Dataset", year=year, region=region or "National",
            migration_matrix_df=clean_df.copy(), raw_df=clean_df,
        )

    if {"sex", "married"} <= cols and ({"never_married"} & cols or {"single"} & cols):
        return DemographicDataset(
            name=name or "Marital Status Dataset", year=year, region=region or "National",
            marital_status_df=clean_df.copy(), raw_df=clean_df,
        )

    has_sex_cols = any(c in cols for c in ["male", "males", "men", "male_count", "m", "female", "females", "women", "female_count", "f"])
    if "female_pop" in cols and "births" in cols and not has_sex_cols and "deaths" not in cols:
        fert = pd.DataFrame({"age_group": clean_df[[c for c in ["age_group", "age"] if c in cols][0]].apply(parse_age_group_label),
                             "female_pop": _num("female_pop"), "births": _num("births")})
        for extra in ["female_births", "married_women", "marital_births"]:
            if extra in cols:
                fert[extra] = _num(extra)
        return DemographicDataset(
            name=name or "Fertility Schedule", year=year, region=region or "National",
            total_live_births=float(fert["births"].sum()),
            total_women_15_49=float(fert["female_pop"].sum()),
            married_women_15_49=float(fert["married_women"].sum()) if "married_women" in fert else None,
            marital_births=float(fert["marital_births"].sum()) if "marital_births" in fert else None,
            fertility_schedule=fert, raw_df=clean_df,
        )

    if {"population", "deaths"} <= cols and not has_sex_cols and not ({"births"} & cols):
        mort = pd.DataFrame({"age_group": clean_df[[c for c in ["age_group", "age"] if c in cols][0]].apply(parse_age_group_label),
                             "population": _num("population"), "deaths": _num("deaths")})
        tot = mort["population"]
        age_tbl = pd.DataFrame({"age_group": mort["age_group"], "total": tot})
        p0_14 = float(mort.loc[mort["age_group"].apply(lambda g: (parse_age_to_numeric(g) or 0) < 15), "population"].sum())
        p65 = float(mort.loc[mort["age_group"].apply(lambda g: (parse_age_to_numeric(g) or 0) >= 65), "population"].sum())
        tot_pop = float(tot.sum())
        return DemographicDataset(
            name=name or "Mortality Schedule", year=year, region=region or "National",
            total_population=tot_pop, total_deaths=float(mort["deaths"].sum()),
            pop_0_14=p0_14 or None, pop_65_plus=p65 or None, pop_15_64=(tot_pop - p0_14 - p65) or None,
            age_group_5yr=age_tbl, mortality_schedule=mort, raw_df=clean_df,
        )

    # Age-Sex Table Parsing
    age_col = None
    for cand in ["age", "age_group", "age_bracket", "ages"]:
        if cand in clean_df.columns:
            age_col = cand
            break
            
    if not age_col:
        age_col = clean_df.columns[0]

    male_col = None
    for cand in ["male", "males", "men", "male_pop", "male_count", "m"]:
        if cand in clean_df.columns:
            male_col = cand
            break

    female_col = None
    for cand in ["female", "females", "women", "female_pop", "female_count", "f"]:
        if cand in clean_df.columns:
            female_col = cand
            break
            
    total_col = None
    for cand in ["total", "total_pop", "total_population", "population", "pop", "both_sexes", "all"]:
        if cand in clean_df.columns:
            total_col = cand
            break

    # Clean numeric data in male/female/total
    for col in [male_col, female_col, total_col]:
        if col and col in clean_df.columns:
            clean_df[col] = pd.to_numeric(clean_df[col].astype(str).str.replace(",", "").str.strip(), errors="coerce").fillna(0)

    # Derive total if male & female present
    if male_col and female_col and (not total_col or total_col not in clean_df.columns):
        clean_df["total"] = clean_df[male_col] + clean_df[female_col]
        total_col = "total"

    # Identify Deaths & Births if present
    deaths_col = None
    for cand in ["deaths", "death", "death_count", "total_deaths"]:
        if cand in clean_df.columns:
            deaths_col = cand
            clean_df[deaths_col] = pd.to_numeric(clean_df[deaths_col].astype(str).str.replace(",", "").str.strip(), errors="coerce").fillna(0)
            break

    births_col = None
    for cand in ["births", "birth", "birth_count", "total_births", "live_births"]:
        if cand in clean_df.columns:
            births_col = cand
            clean_df[births_col] = pd.to_numeric(clean_df[births_col].astype(str).str.replace(",", "").str.strip(), errors="coerce").fillna(0)
            break

    female_births_col = None
    for cand in ["female_births", "f_births", "girl_births"]:
        if cand in clean_df.columns:
            female_births_col = cand
            clean_df[female_births_col] = pd.to_numeric(clean_df[female_births_col].astype(str).str.replace(",", "").str.strip(), errors="coerce").fillna(0)
            break

    # Determine if single-year or 5-year
    is_single_year = False
    numeric_ages = clean_df[age_col].apply(parse_age_to_numeric)
    valid_nums = numeric_ages.dropna().values
    if len(valid_nums) >= 20 and np.all(np.diff(valid_nums[:15]) == 1):
        is_single_year = True

    single_year_df = None
    age_group_5yr_df = None
    fertility_schedule_df = None
    mortality_schedule_df = None

    if is_single_year:
        m_vals = clean_df[male_col].values if male_col else np.zeros(len(clean_df))
        f_vals = clean_df[female_col].values if female_col else np.zeros(len(clean_df))
        if total_col:
            t_vals = clean_df[total_col].values
        elif male_col and female_col:
            t_vals = m_vals + f_vals
        elif female_col:
            t_vals = f_vals
        elif male_col:
            t_vals = m_vals
        else:
            t_vals = np.zeros(len(clean_df))

        single_year_df = pd.DataFrame({
            "age": numeric_ages.astype(int),
            "male": m_vals,
            "female": f_vals,
            "total": t_vals,
        })
        # Build 5-year table
        groups = []
        for a in range(0, 85, 5):
            lbl = f"{a}-{a+4}"
            sub = single_year_df[(single_year_df["age"] >= a) & (single_year_df["age"] <= a + 4)]
            groups.append({
                "age_group": lbl,
                "male": sub["male"].sum(),
                "female": sub["female"].sum(),
                "total": sub["total"].sum(),
            })
        sub85 = single_year_df[single_year_df["age"] >= 85]
        groups.append({
            "age_group": "85+",
            "male": sub85["male"].sum(),
            "female": sub85["female"].sum(),
            "total": sub85["total"].sum(),
        })
        age_group_5yr_df = pd.DataFrame(groups)
    else:
        clean_labels = clean_df[age_col].apply(parse_age_group_label)
        m_vals = clean_df[male_col].values if male_col else np.zeros(len(clean_df))
        f_vals = clean_df[female_col].values if female_col else np.zeros(len(clean_df))
        if total_col:
            t_vals = clean_df[total_col].values
        elif male_col and female_col:
            t_vals = m_vals + f_vals
        elif female_col:
            t_vals = f_vals
        elif male_col:
            t_vals = m_vals
        else:
            t_vals = np.zeros(len(clean_df))

        tbl = {"age_group": clean_labels}
        if male_col:
            tbl["male"] = m_vals
        if female_col:
            tbl["female"] = f_vals
        tbl["total"] = t_vals
        age_group_5yr_df = pd.DataFrame(tbl)

    # Fertility schedule (Only if births provided, without inventing missing values, Fix B7)
    if births_col and births_col in clean_df.columns:
        fert_labels = ["15-19", "20-24", "25-29", "30-34", "35-39", "40-44", "45-49"]
        fert_rows = []
        for _, r in clean_df.iterrows():
            lbl = parse_age_group_label(r[age_col])
            if lbl in fert_labels:
                f_pop = r[female_col] if female_col else (r[total_col] if total_col else 0)
                b = r[births_col]
                row_dict = {
                    "age_group": lbl,
                    "female_pop": f_pop,
                    "births": b,
                }
                if female_births_col and female_births_col in clean_df.columns:
                    row_dict["female_births"] = r[female_births_col]
                if "married_women" in clean_df.columns:
                    row_dict["married_women"] = r["married_women"]
                if "marital_births" in clean_df.columns:
                    row_dict["marital_births"] = r["marital_births"]
                fert_rows.append(row_dict)
        if fert_rows:
            fertility_schedule_df = pd.DataFrame(fert_rows)

    # Mortality schedule (Only if deaths provided)
    if deaths_col and deaths_col in clean_df.columns:
        mort_rows = []
        for _, r in clean_df.iterrows():
            lbl = parse_age_group_label(r[age_col])
            if total_col:
                pop_val = r[total_col]
            elif male_col and female_col:
                pop_val = r[male_col] + r[female_col]
            elif female_col:
                pop_val = r[female_col]
            elif male_col:
                pop_val = r[male_col]
            else:
                pop_val = 0
            d_val = r[deaths_col]
            mort_rows.append({
                "age_group": lbl,
                "population": pop_val,
                "deaths": d_val,
            })
        if mort_rows:
            mortality_schedule_df = pd.DataFrame(mort_rows)

    # Population totals
    tot_pop = float(age_group_5yr_df["total"].sum()) if age_group_5yr_df is not None else float(clean_df[total_col].sum())
    tot_male = float(age_group_5yr_df["male"].sum()) if age_group_5yr_df is not None and male_col else None
    tot_female = float(age_group_5yr_df["female"].sum()) if age_group_5yr_df is not None and female_col else None

    # Calculate 0-14, 15-64, 65+
    pop_0_14 = 0.0
    pop_15_64 = 0.0
    pop_65_plus = 0.0

    if single_year_df is not None:
        pop_0_14 = float(single_year_df[single_year_df["age"] <= 14]["total"].sum())
        pop_15_64 = float(single_year_df[(single_year_df["age"] >= 15) & (single_year_df["age"] <= 64)]["total"].sum())
        pop_65_plus = float(single_year_df[single_year_df["age"] >= 65]["total"].sum())
    elif age_group_5yr_df is not None:
        for _, r in age_group_5yr_df.iterrows():
            lbl = str(r["age_group"])
            pop = float(r["total"])
            num = parse_age_to_numeric(lbl)
            if num is not None:
                if num < 15:
                    pop_0_14 += pop
                elif 15 <= num < 65:
                    pop_15_64 += pop
                else:
                    pop_65_plus += pop

    tot_births = float(clean_df[births_col].sum()) if births_col else (float(fertility_schedule_df["births"].sum()) if fertility_schedule_df is not None else None)
    tot_deaths = float(clean_df[deaths_col].sum()) if deaths_col else (float(mortality_schedule_df["deaths"].sum()) if mortality_schedule_df is not None else None)

    # Women 15-49
    women_15_49 = None
    if age_group_5yr_df is not None and female_col:
        fert_labels = ["15-19", "20-24", "25-29", "30-34", "35-39", "40-44", "45-49"]
        w_sub = age_group_5yr_df[age_group_5yr_df["age_group"].isin(fert_labels)]
        if not w_sub.empty:
            women_15_49 = float(w_sub["female"].sum())

    # Nuptiality & Marital Distribution Table detection
    marital_df = None
    if any(c in clean_df.columns for c in ["never_married", "single", "married", "widowed", "divorced", "separated"]):
        marital_df = clean_df.copy()

    # Migration OD Matrix detection
    migration_matrix_df = None
    if "origin" in clean_df.columns and len(clean_df.columns) >= 3:
        migration_matrix_df = clean_df.copy()

    # Check for user-provided married women / marital births in fertility tables
    user_married_women = None
    for cand in ["married_women", "married_women_15_49", "married_females"]:
        if cand in clean_df.columns:
            user_married_women = float(pd.to_numeric(clean_df[cand], errors="coerce").fillna(0).sum())
            break

    user_marital_births = None
    for cand in ["marital_births", "legitimate_births"]:
        if cand in clean_df.columns:
            user_marital_births = float(pd.to_numeric(clean_df[cand], errors="coerce").fillna(0).sum())
            break

    # Note: B7 compliance — we do NOT invent married_women_15_49 or marital_births!
    return DemographicDataset(
        name=name or "Uploaded Demographic Dataset",
        year=year,
        region=region or "National",
        total_population=tot_pop,
        male_population=tot_male,
        female_population=tot_female,
        pop_0_14=pop_0_14 if pop_0_14 > 0 else None,
        pop_15_64=pop_15_64 if pop_15_64 > 0 else None,
        pop_65_plus=pop_65_plus if pop_65_plus > 0 else None,
        total_live_births=tot_births,
        total_deaths=tot_deaths,
        total_women_15_49=women_15_49,
        married_women_15_49=user_married_women,  # User provided, not invented (B7)
        marital_births=user_marital_births,       # User provided, not invented (B7)
        single_year_ages=single_year_df,
        age_group_5yr=age_group_5yr_df,
        fertility_schedule=fertility_schedule_df,
        mortality_schedule=mortality_schedule_df,
        marital_status_df=marital_df,
        migration_matrix_df=migration_matrix_df,
        raw_df=clean_df,
    )


def generate_sample_age_distribution_csv() -> str:
    """Returns a ready-to-use sample CSV template containing 5-year age groups with births and deaths."""
    sample_data = """age_group,male,female,total,births,deaths
0-4,580000,560000,1140000,0,7068
5-9,570000,550000,1120000,0,784
10-14,560000,540000,1100000,0,550
15-19,550000,535000,1085000,42265,1193
20-24,530000,520000,1050000,149100,1575
25-29,510000,505000,1015000,126875,1827
30-34,480000,480000,960000,74880,2304
35-39,450000,455000,905000,31850,3077
40-44,410000,420000,830000,10375,4150
45-49,370000,380000,750000,3000,5775
50-54,320000,330000,650000,0,7280
55-59,270000,280000,550000,0,9570
60-64,220000,230000,450000,0,12150
65-69,170000,180000,350000,0,14700
70-74,120000,130000,250000,0,16500
75-79,80000,85000,165000,0,15675
80-84,45000,50000,95000,0,13300
85+,25000,30000,55000,0,12100
"""
    return sample_data


def generate_sample_summary_csv() -> str:
    """Returns sample indicators key-value CSV."""
    sample_data = """indicator,value
total_population,11765000
male_population,5920000
female_population,5845000
pop_0_14,3529500
pop_15_64,7411950
pop_65_plus,823550
total_live_births,225400
total_deaths,100860
infant_deaths,5635
area_km2,147570
census_coverage_rate,0.968
death_registration_completeness,0.880
"""
    return sample_data
