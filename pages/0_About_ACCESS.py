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

# Display the PDF - full width, taller height for presentation mode
pdf_viewer("access.pdf", width="100%", height=800)
