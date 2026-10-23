import streamlit as st, latex2mathml.converter as c
st.html('<style>.f{font-size:1.15rem}</style><div class="f">'+c.convert(r'\mathrm{CDR}=\frac{D}{P}\times 1000')+'</div><details><summary>Formula +</summary>'+c.convert(r'\mathrm{TFR}=5\sum_{i=1}^{7}\frac{\mathrm{ASFR}_i}{1000}')+'</details>')
