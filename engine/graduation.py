"""
Section 8: Graduation & Age Distribution Smoothing

Splits 5-year age groups into single years while preserving every group total.

Methods
1. Sprague osculatory interpolation (published multipliers; group totals are conserved by the
   multipliers themselves, so no corrective rescaling is needed beyond clipping rare negatives).
2. Karup-King-type interpolation: a cubic through the cumulative counts at four neighbouring
   group boundaries (uses three groups). Multipliers are derived, not looked up.
3. Beers-type interpolation: a monotone cubic Hermite (Fritsch-Carlson) through the cumulative
   counts at all group boundaries. Cumulative counts never decrease, so single-year values are
   never negative, and each group re-sums exactly. This is NOT the published Beers coefficient table.
4. 1-2-1 weighted moving-average smoothing of the 5-year groups (total-preserving).

Open-ended last group (for example "85+"): pass ``open_last_group=True`` and it is kept as a
single open interval instead of being spread over five invented single years.

References
- Sprague, T. B. (1880). Explanation of a new formula for interpolation. JIA 22.
- Shryock, H. S., & Siegel, J. S. (1976). The Methods and Materials of Demography, Ch. 22.
- Fritsch, F. N., & Carlson, R. E. (1980). Monotone piecewise cubic interpolation. SIAM J. Numer. Anal. 17(2).
"""

from __future__ import annotations
from typing import Dict, Any, Tuple, List
import numpy as np
import pandas as pd


# --- Sprague multipliers (Shryock & Siegel 1976; column sums are exactly [0,...,1,...,0]) -------
# First panel: single years of group 1 from groups [W1, W2, W3, W4]
SPRAGUE_FIRST_PANEL = np.array([
    [ 0.3616, -0.2768,  0.1488, -0.0336],
    [ 0.2640, -0.0960,  0.0400, -0.0080],
    [ 0.1840,  0.0400, -0.0320,  0.0080],
    [ 0.1200,  0.1360, -0.0720,  0.0160],
    [ 0.0704,  0.1968, -0.0848,  0.0176],
])

# Second panel: single years of group 2 from groups [W1 .. W5]
SPRAGUE_SECOND_PANEL = np.array([
    [ 0.0336,  0.2272, -0.0752,  0.0160, -0.0016],
    [ 0.0080,  0.2320, -0.0480,  0.0080,  0.0000],
    [-0.0080,  0.2160, -0.0080,  0.0000,  0.0000],
    [-0.0160,  0.1840,  0.0400, -0.0080,  0.0000],
    [-0.0176,  0.1408,  0.0912, -0.0160,  0.0016],
])

# Middle panel: single years of group i from groups [W(i-2) .. W(i+2)]
SPRAGUE_MIDDLE_PANEL = np.array([
    [-0.0128,  0.0848,  0.1504, -0.0240,  0.0016],
    [-0.0016,  0.0144,  0.2224, -0.0416,  0.0064],
    [ 0.0064, -0.0336,  0.2544, -0.0336,  0.0064],
    [ 0.0064, -0.0416,  0.2224,  0.0144, -0.0016],
    [ 0.0016, -0.0240,  0.1504,  0.0848, -0.0128],
])


def _split_open_group(counts: List[float], open_last_group: bool) -> Tuple[List[float], float | None]:
    w = [float(x) for x in counts]
    if open_last_group and len(w) >= 2:
        return w[:-1], w[-1]
    return w, None


def _prorate_to_groups(values: np.ndarray, w: List[float]) -> np.ndarray:
    """Clip negatives, then rescale each block of five so it re-sums to its group total exactly."""
    out = np.clip(values.astype(float), 0.0, None)
    for i, orig in enumerate(w):
        chunk = out[i * 5:(i + 1) * 5]
        s = chunk.sum()
        out[i * 5:(i + 1) * 5] = chunk * (orig / s) if s > 0 else orig / 5.0
    return out


def _finish(values: np.ndarray, w: List[float], open_total: float | None, start_age: int,
            method: str, note: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    values = _prorate_to_groups(values, w)
    ages = list(range(start_age, start_age + len(values)))
    df = pd.DataFrame({"age": ages, "graduated_population": values})
    original_sum = float(sum(w))
    graduated_sum = float(values.sum())
    err = abs(graduated_sum - original_sum)
    group_err = max(abs(values[i * 5:(i + 1) * 5].sum() - w[i]) for i in range(len(w)))
    diag = {
        "original_5yr_groups_count": len(w),
        "single_year_estimates_count": len(values),
        "original_total_sum": original_sum,
        "graduated_total_sum": graduated_sum,
        "absolute_re_sum_difference": err,
        "max_group_re_sum_difference": float(group_err),
        "re_sum_verified": bool(group_err < 0.01),
        "open_interval_total": open_total,
        "method": method,
        "interpretation": (
            f"{note} {len(w)} five-year groups became {len(values)} single-year ages. "
            f"Every group re-sums to its input within {group_err:.4f} persons."
            + (f" The open-ended last group ({open_total:,.0f} persons) was kept as one interval." if open_total is not None else "")
        ),
    }
    return df, diag


def _sprague_raw(w: List[float]) -> np.ndarray:
    m = len(w)
    out: List[float] = []
    out += list(SPRAGUE_FIRST_PANEL @ np.array(w[:4]))
    out += list(SPRAGUE_SECOND_PANEL @ np.array(w[:5]))
    for i in range(2, m - 2):
        out += list(SPRAGUE_MIDDLE_PANEL @ np.array(w[i - 2:i + 3]))
    out += list((SPRAGUE_SECOND_PANEL @ np.array(w[m - 5:m])[::-1])[::-1])
    out += list((SPRAGUE_FIRST_PANEL @ np.array(w[m - 4:m])[::-1])[::-1])
    return np.array(out, dtype=float)


def graduate_5yr_to_single_year_sprague(
    five_year_counts: List[float],
    start_age: int = 0,
    open_last_group: bool = False,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Sprague osculatory graduation of closed 5-year groups into single years."""
    w, open_total = _split_open_group(five_year_counts, open_last_group)
    if len(w) < 5:
        raise ValueError("Sprague graduation requires at least 5 closed 5-year age groups.")
    return _finish(_sprague_raw(w), w, open_total, start_age,
                   "Sprague Osculatory Interpolation", "Sprague's osculatory interpolation (published multipliers).")


def _cumulative(w: List[float]) -> np.ndarray:
    return np.concatenate([[0.0], np.cumsum(w)])


def _pchip_slopes(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Fritsch-Carlson slopes for monotone cubic Hermite interpolation."""
    h = np.diff(x)
    delta = np.diff(y) / h
    n = len(x)
    d = np.zeros(n)
    if n == 2:
        d[:] = delta[0]
        return d
    for k in range(1, n - 1):
        if delta[k - 1] * delta[k] > 0:
            w1 = 2 * h[k] + h[k - 1]
            w2 = h[k] + 2 * h[k - 1]
            d[k] = (w1 + w2) / (w1 / delta[k - 1] + w2 / delta[k])
    def end(h0, h1, d0, d1):
        s = ((2 * h0 + h1) * d0 - h0 * d1) / (h0 + h1)
        if np.sign(s) != np.sign(d0):
            return 0.0
        if np.sign(d0) != np.sign(d1) and abs(s) > 3 * abs(d0):
            return 3 * d0
        return s
    d[0] = end(h[0], h[1], delta[0], delta[1])
    d[-1] = end(h[-1], h[-2], delta[-1], delta[-2])
    return d


def _hermite(x: np.ndarray, y: np.ndarray, d: np.ndarray, xq: np.ndarray) -> np.ndarray:
    idx = np.clip(np.searchsorted(x, xq, side="right") - 1, 0, len(x) - 2)
    h = x[idx + 1] - x[idx]
    t = (xq - x[idx]) / h
    h00 = 2 * t**3 - 3 * t**2 + 1
    h10 = t**3 - 2 * t**2 + t
    h01 = -2 * t**3 + 3 * t**2
    h11 = t**3 - t**2
    return h00 * y[idx] + h10 * h * d[idx] + h01 * y[idx + 1] + h11 * h * d[idx + 1]


def graduate_5yr_to_single_year_beers(
    five_year_counts: List[float],
    start_age: int = 0,
    open_last_group: bool = False,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Beers-type graduation: monotone cubic through cumulative counts (see module docstring).
    Single-year values are never negative and each 5-year group re-sums exactly.
    """
    w, open_total = _split_open_group(five_year_counts, open_last_group)
    if len(w) < 3:
        raise ValueError("Graduation requires at least 3 closed 5-year age groups.")
    x = np.arange(0, 5 * len(w) + 1, 5, dtype=float)
    cum = _cumulative(w)
    d = _pchip_slopes(x, cum)
    grid = np.arange(0, 5 * len(w) + 1, dtype=float)
    cum_single = _hermite(x, cum, d, grid)
    vals = np.diff(cum_single)
    return _finish(vals, w, open_total, start_age, "Beers-type Monotone Cumulative Interpolation",
                   "Monotone cubic interpolation of cumulative counts (Beers-type; not the published Beers table).")


def _lagrange_weights(nodes: np.ndarray, x: float) -> np.ndarray:
    out = []
    for i in range(len(nodes)):
        p = 1.0
        for j in range(len(nodes)):
            if i != j:
                p *= (x - nodes[j]) / (nodes[i] - nodes[j])
        out.append(p)
    return np.array(out)


def graduate_karup_king(
    five_year_counts: List[float],
    start_age: int = 0,
    open_last_group: bool = False,
) -> pd.DataFrame:
    """
    Karup-King-type graduation: for each group, a cubic through the cumulative counts at four
    neighbouring boundaries (previous, own start, own end, next). End groups use the nearest four
    boundaries. Returns the single-year estimates; use :func:`graduate_karup_king_with_diagnostics`
    for diagnostics.
    """
    return graduate_karup_king_with_diagnostics(five_year_counts, start_age, open_last_group)[0]


def graduate_karup_king_with_diagnostics(
    five_year_counts: List[float],
    start_age: int = 0,
    open_last_group: bool = False,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    w, open_total = _split_open_group(five_year_counts, open_last_group)
    m = len(w)
    if m < 3:
        raise ValueError("Karup-King graduation requires at least 3 closed 5-year age groups.")
    cum = _cumulative(w)
    bounds = np.arange(0, 5 * m + 1, 5, dtype=float)
    out: List[float] = []
    for i in range(m):
        lo = min(max(i - 1, 0), m - 3)  # first of four consecutive boundaries
        idx = [lo, lo + 1, lo + 2, lo + 3]
        nodes, ys = bounds[idx], cum[idx]
        for k in range(5):
            a, b = 5 * i + k, 5 * i + k + 1
            out.append(float(_lagrange_weights(nodes, b) @ ys - _lagrange_weights(nodes, a) @ ys))
    return _finish(np.array(out), w, open_total, start_age, "Karup-King-type Cumulative Cubic Interpolation",
                   "Cubic interpolation through four cumulative boundaries (Karup-King-type).")


def carrier_farrag_smoothing(five_year_counts: List[float]) -> List[float]:
    """
    1-2-1 weighted moving average over neighbouring 5-year groups, rescaled so the total is unchanged.
    S_i = (W_{i-1} + 2 W_i + W_{i+1}) / 4 for interior groups; the first and last groups are kept.
    (This is a simple heaping-smoother, not the UN Carrier-Farrag ratio procedure.)
    """
    w = [float(x) for x in five_year_counts]
    if len(w) < 3:
        return w
    sm = [w[0]] + [(w[i - 1] + 2.0 * w[i] + w[i + 1]) / 4.0 for i in range(1, len(w) - 1)] + [w[-1]]
    s_new, s_old = sum(sm), sum(w)
    return [v * (s_old / s_new) for v in sm] if s_new > 0 else sm
