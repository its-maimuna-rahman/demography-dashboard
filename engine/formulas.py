"""
LaTeX formulas for every measure, and a renderer that turns them into SVG images.

Browsers cannot render math inside Streamlit's sanitised HTML, so each formula is drawn once with
matplotlib's mathtext (Computer Modern fonts, text converted to paths so no font is needed) and
embedded as a data-URI image. Results are cached. If a formula ever fails to render, the plain-text
formula is shown instead, so a card can never break.
"""

from __future__ import annotations
import base64
import html
import io
from functools import lru_cache
from typing import Dict

# Notation: P population, B births, D deaths, W women, M marriages, I / O in- and out-migrants,
# l_x, L_x, T_x life-table functions, subscripts give age ranges.
LATEX: Dict[str, str] = {
    # ---- Composition and age structure
    "MP": r"\mathrm{MP}=\frac{P_m}{P_t}\times 100",
    "SR": r"\mathrm{SR}=\frac{P_m}{P_f}\times 100",
    "SRB": r"\mathrm{SRB}=\frac{B_m}{B_f}\times 100",
    "EXCESS_M": r"\mathrm{Excess}_{M}=P_m-P_f",
    "ACR": r"\mathrm{ACR}=\frac{P_{15-64}}{P_t}\times 100",
    "TDR": r"\mathrm{TDR}=\frac{P_{0-14}+P_{65+}}{P_{15-64}}\times 100",
    "CDR_CHILD": r"\mathrm{CDR}_{\mathrm{child}}=\frac{P_{0-14}}{P_{15-64}}\times 100",
    "OADR": r"\mathrm{OADR}=\frac{P_{65+}}{P_{15-64}}\times 100",
    "AI": r"\mathrm{AI}=\frac{P_{65+}}{P_{0-14}}\times 100",
    "PSR": r"\mathrm{PSR}=\frac{P_{15-64}}{P_{65+}}",
    "MEDIAN_AGE": r"\mathrm{Median}=L_m+\frac{N/2-F_{m-1}}{f_m}\,w",
    "CWR": r"\mathrm{CWR}=\frac{P_{0-4}}{W_{15-49}}\times 1000",
    "DENSITY": r"\mathrm{PD}=\frac{P}{A}",
    "GROWTH_RATE": r"r=\frac{\ln\left(P_2/P_1\right)}{t}\times 100",
    "PCT_0_14": r"\%P_{0-14}=\frac{P_{0-14}}{P_t}\times 100",
    "PCT_15_64": r"\%P_{15-64}=\frac{P_{15-64}}{P_t}\times 100",
    "PCT_65P": r"\%P_{65+}=\frac{P_{65+}}{P_t}\times 100",
    "PCT_CHANGE": r"\%\Delta=\frac{\mathrm{New}-\mathrm{Old}}{\mathrm{Old}}\times 100",
    "IRD": r"\mathrm{IRD}=\left|\frac{r_2}{r_1}\times 100-100\right|",
    "ID": r"\mathrm{ID}=\frac{1}{2}\sum\left|r_2-r_1\right|",
    # ---- Fertility
    "CBR": r"\mathrm{CBR}=\frac{B}{P}\times 1000",
    "GFR": r"\mathrm{GFR}=\frac{B}{W_{15-49}}\times 1000",
    "ASFR": r"\mathrm{ASFR}_i=\frac{B_i}{W_i}\times 1000",
    "TFR": r"\mathrm{TFR}=5\sum_{i=1}^{7}\frac{\mathrm{ASFR}_i}{1000}",
    "GRR": r"\mathrm{GRR}=\mathrm{TFR}\times\frac{B_f}{B}",
    "NRR": r"\mathrm{NRR}=5\,\frac{B_f}{B}\sum_{i=1}^{7}\frac{B_i}{P_i}\cdot\frac{{}_5L_x}{l_0}",
    "MBR": r"\mathrm{GMFR}=\frac{B^{m}}{W^{m}_{15-49}}\times 1000",
    "MAC": r"\mathrm{MAC}=\frac{\sum\left(x+n/2\right)\mathrm{ASFR}_x}{\sum\mathrm{ASFR}_x}",
    "RSOB": r"\mathrm{RSOB}=\frac{B_i}{P^{f}_{15-44}}\times 1000",
    "DSFR": r"\mathrm{DSFR}_t=\frac{B^{m}_t}{P^{f,m}_{15-44,t}}\times 1000",
    "AABR_D": r"\mathrm{AABR}=\frac{\sum f_a\,P^{f}_a}{P}\times 1000",
    "AABR_I": r"\mathrm{AABR}_{\mathrm{ind}}=\frac{b}{\sum F_a\,P^{f}_a}\times F",
    "PROP_FEMALE_BIRTHS": r"\frac{B_f}{B}",
    "GRR_SHORT": r"\mathrm{GRR}=0.488\times\mathrm{TFR}",
    # ---- Mortality
    "CDR": r"\mathrm{CDR}=\frac{D}{P}\times 1000",
    "CORRECTED_CDR": r"\mathrm{CDR}_{\mathrm{corr}}=\frac{D/C_d}{P/C_p}\times 1000",
    "CDR_AVG_V1": r"\overline{\mathrm{CDR}}=\frac{1}{n}\sum_{k=1}^{n}\frac{D_k}{P_k}\times 1000",
    "CDR_AVG_V2": r"\overline{\mathrm{CDR}}=\frac{\frac{1}{n}\sum D_k}{\frac{1}{n}\sum P_k}\times 1000",
    "CDR_AVG_V3": r"\overline{\mathrm{CDR}}=\frac{\frac{1}{n}\sum D_k}{P_{\mathrm{mid}}}\times 1000",
    "MONTHLY_DR": r"\frac{365}{n_m}\cdot\frac{D_m}{P_m}\times 1000",
    "ASDR": r"M_a=\frac{D_a}{P_a}\times 1000",
    "ASDR_SEX": r"M^{f}_a=\frac{D^{f}_a}{P^{f}_a}\times 1000",
    "CSDR": r"\frac{D_c}{P}\times 100000",
    "DEATH_RATIO": r"\frac{D_c}{D}\times 100",
    "ENDO_DR": r"\frac{D_{en}}{P}\times 1000",
    "EXO_DR": r"\frac{D_{ex}}{P}\times 1000",
    "NMR": r"\mathrm{NMR}=\frac{D_{<28d}}{B}\times 1000",
    "ENMR": r"\mathrm{ENMR}=\frac{D_{<7d}}{B}\times 1000",
    "PNMR": r"\mathrm{PNMR}=\frac{D_{28d-1y}}{B}\times 1000",
    "IMR": r"\mathrm{IMR}=\frac{D_{<1}}{B}\times 1000",
    "CMR": r"{}_4m_1=\frac{D_{1-4}}{P_{1-4}}\times 1000",
    "U5MR": r"\mathrm{U5MR}=\frac{D_{0-4}}{B}\times 1000",
    "CS_IMR": r"\frac{D^{c}_0}{B}\times 100000",
    "CSIMR_EN": r"\mathrm{CSIMR}_{en}=\frac{D^{en}_0}{B}\times 1000",
    "CSIMR_EX": r"\mathrm{CSIMR}_{ex}=\frac{D^{ex}_0}{B}\times 1000",
    "AIMR_A": r"\frac{D'_y+D''_{y+1}}{B_y}\times 1000",
    "AIMR_B": r"\left(\frac{D'_y}{B_y}+\frac{D''_y}{B_{y-1}}\right)\times 1000",
    "AIMR_C": r"\frac{D_y}{f'B_y+\left(1-f'\right)B_{y-1}}\times 1000",
    "SEP_FACTOR": r"f'=\frac{D'_y}{D'_y+D''_y}",
    "PM_RATIO": r"\frac{D_f+D_z}{B}\times 1000",
    "PM_RATE": r"\frac{D_f+D_z}{D_f+B}\times 1000",
    "FD_RATIO": r"\frac{D_f}{B}\times 1000",
    "FD_RATE": r"\frac{D_f}{D_f+B}\times 1000",
    "MMR": r"\mathrm{MMR}=\frac{D_p}{B}\times 100000",
    "MMRATE_NOTES": r"\mathrm{MMR}=\frac{D_p}{B}\times 1000",
    "DSDR": r"\mathrm{DSDR}=\frac{\sum M_a\,P^{s}_a}{\sum P^{s}_a}",
    "SMR": r"\mathrm{SMR}=\frac{D_{\mathrm{obs}}}{\sum M^{s}_a\,P_a}",
    "ISDR": r"\mathrm{ISDR}=\mathrm{SMR}\times\mathrm{CDR}^{s}",
    # ---- Life table
    "E0": r"\mathring{e}_0=\frac{T_0}{l_0}",
    "E65": r"\mathring{e}_{65}=\frac{T_{65}}{l_{65}}",
    "45Q15": r"{}_{45}q_{15}=1-\frac{l_{60}}{l_{15}}",
    "RM_L0": r"L_0=0.276\,l_0+0.724\,l_1",
    "RM_4L1": r"{}_4L_1=0.034\,l_0+1.184\,l_1+2.782\,l_5",
    "RM_L1": r"L_1=0.410\,l_1+0.590\,l_2",
    "RM_3L2": r"{}_3L_2=-0.021\,l_0+1.384\,l_2+1.637\,l_5",
    "RM_5L5": r"{}_5L_5=-0.003\,l_0+2.242\,l_5+2.761\,l_{10}",
    # ---- Nuptiality
    "SMAM_MALE": r"\mathrm{SMAM}=\frac{15+5\sum S_i-50\,S_{50}}{1-S_{50}}",
    "SMAM_FEMALE": r"\mathrm{SMAM}=\frac{15+5\sum S_i-50\,S_{50}}{1-S_{50}}",
    "SPOUSAL_GAP": r"\mathrm{SAG}=\mathrm{SMAM}_m-\mathrm{SMAM}_f",
    "CELIBACY": r"\mathrm{CR}=S_{50}\times 100",
    "CMRG": r"\mathrm{CMR}=\frac{M}{P}\times 1000",
    "CDVR": r"\mathrm{CDvR}=\frac{\mathrm{Div}}{P}\times 1000",
    "GDVR": r"\mathrm{GDvR}=\frac{\mathrm{Div}}{P_{\mathrm{married}}}\times 1000",
    "GMR": r"\mathrm{GMR}=\frac{M}{P^{f}_{15+}}\times 1000",
    "ASMR": r"\mathrm{ASMR}=\frac{M_{\mathrm{age}}}{P_{\mathrm{age}}}\times 1000",
    "ASDVR": r"\mathrm{ASDvR}=\frac{\mathrm{Div}_{\mathrm{age}}}{P_{\mathrm{age}}}\times 1000",
    "FMR": r"\frac{M_1}{P^{nm}_{15+}}\times 1000",
    "REMARRIAGE_RATE": r"\frac{M_2}{P_{M+D}}\times 1000",
    "AOSMR": r"\frac{M^{f,1}_{20-24}}{P^{f,nm,15+}_{20-24}}\times 1000",
    "TMR": r"\mathrm{TMR}=\sum_{a}\frac{M^{f}_a}{P^{f}_a}\times 1000",
    "TFMR": r"\mathrm{TFMR}=\sum_{a}\frac{M^{f,1}_a}{P^{f}_a}\times 1000",
    "RDR": r"\mathrm{RDR}=\frac{\mathrm{Div}}{P^{f}_{m}}\times 1000",
    "DIV_DUR": r"\frac{\mathrm{Div}_i}{P_{m,i}}\times 1000",
    "MEDIAN_AGE_MARRIAGE": r"\mathrm{Median\ age}:\ S(x)=\frac{1+S_{50}}{2}",
    # ---- Migration
    "NMRG": r"\mathrm{NMR}=\frac{I-O}{P}\times 1000",
    "IMRG": r"\mathrm{IMR}=\frac{I}{P}\times 1000",
    "OMRG": r"\mathrm{OMR}=\frac{O}{P}\times 1000",
    "GROSS_MIG": r"\mathrm{Gross}=I+O",
    "NET_MIG": r"\mathrm{Net}=I-O",
    "MER": r"\mathrm{MER}=\frac{\left|I-O\right|}{I+O}\times 100",
    "MER_SIGNED": r"\mathrm{M.E.}=\frac{I-O}{I+O}\times 100",
    # ---- Stable population
    "LOTKA_R": r"\int_{15}^{49}e^{-rn}f(n)\,p(n)\,dn=1",
    "INTRINSIC_B": r"b=\frac{1}{\int_{0}^{\infty}e^{-rn}p(n)\,dn}",
    "INTRINSIC_D": r"d=b-r",
    "GEN_LEN": r"T=\frac{\ln R_0}{r}",
    "R1": r"R_1=\int x\,p(x)\,f(x)\,dx",
    "R2": r"R_2=\int x^{2}\,p(x)\,f(x)\,dx",
    "ALPHA": r"\alpha=\frac{R_1}{R_0}",
    "BETA": r"\beta=\left(\frac{R_1}{R_0}\right)^{2}-\frac{R_2}{R_0}",
    "R_QUAD": r"r=\frac{-\alpha+\sqrt{\alpha^{2}+2\beta\ln R_0}}{\beta}",
    "T_QUAD": r"T=\alpha+\frac{1}{2}\beta r",
    "MU": r"\mu=\frac{R_1}{R_0}",
}


@lru_cache(maxsize=512)
def render_formula_svg(latex: str, size: float = 18.0, color: str = "#4B5E52") -> str:
    """Render LaTeX to an SVG string. Raises ValueError if the formula cannot be rendered."""
    import matplotlib
    from matplotlib.figure import Figure
    with matplotlib.rc_context({"svg.fonttype": "path", "mathtext.fontset": "cm"}):
        fig = Figure(figsize=(0.1, 0.1))
        fig.text(0, 0, f"${latex}$", fontsize=size, color=color)
        buf = io.StringIO()
        try:
            fig.savefig(buf, format="svg", bbox_inches="tight", pad_inches=0.03, transparent=True)
        except Exception as exc:  # mathtext parse errors surface here
            raise ValueError(f"Could not render LaTeX: {latex!r} ({exc})") from exc
    return buf.getvalue()


@lru_cache(maxsize=512)
def formula_img_html(latex: str, plain: str = "", size: float = 18.0) -> str:
    """HTML for a formula: an inline SVG image with the LaTeX as alt text; plain text if rendering fails."""
    try:
        svg = render_formula_svg(latex, size)
    except Exception:
        return f'<span class="vs-formula-fallback">{html.escape(plain or latex)}</span>'
    b64 = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f'<img class="vs-math" alt="{html.escape(latex, quote=True)}" src="data:image/svg+xml;base64,{b64}"/>'


def latex_for(code: str) -> str:
    return LATEX.get(code.upper(), "")
