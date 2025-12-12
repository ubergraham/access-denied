"""About ACCESS - PDF Presentation.

Displays the ACCESS presentation explaining how incentives shape outcomes
in CMS's new tech-enabled chronic care model.
"""

import streamlit as st
from streamlit_pdf_viewer import pdf_viewer

st.title("About ACCESS")

st.markdown("""
This presentation explains **ACCESS** (Advancing Care Coordination and Engagement through
Supportive Services) — CMS's new tech-enabled chronic care model — and analyzes how its
incentive structure will shape real-world outcomes.

> *"Show me the incentive and I'll show you the outcome."* — Charlie Munger
""")

st.divider()

# Display the PDF
pdf_viewer("access.pdf", width=800)

st.divider()

st.markdown("""
### Key Concerns

1. **Cherry-picking** — Vendors will target "movable" patients who are younger, tech-ready, and easier to improve
2. **Lemon-dropping** — Complex, non-engaged patients will be dropped or never enrolled
3. **PCP Burden** — Coordination responsibilities shift to primary care for $80-100/year per patient
4. **Fragmented Care** — Patients may enroll in multiple condition-specific vendors with no integration
5. **TCOC Not Measured** — Success is measured by condition-specific metrics, not total cost of care

Use the simulators in this app to explore how these dynamics play out.
""")
