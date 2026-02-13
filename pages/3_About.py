"""About the Author."""

import streamlit as st

st.title("About the Author")

st.markdown("""
### Graham Walker, MD

Emergency physician practicing in San Francisco. Co-director of Advanced Development
at The Permanente Medical Group, which delivers care for Kaiser Permanente's
4 million members in Northern California.
""")

st.markdown("""
As a clinical informaticist, Graham leads emergency and urgent care strategy for KP's
electronic medical record. He completed his residency training in emergency medicine
at St. Luke's-Roosevelt Hospital Center in Manhattan, and attended medical school
at the Stanford University School of Medicine.

Graham is also a software developer and entrepreneur. He created
[MDCalc](https://www.mdcalc.com) and [Offcall](https://www.offcall.com), two online
resources dedicated to helping physicians across the world.

In his free time Graham writes about the intersection of AI, technology, and medicine,
and created **The Physicians' Charter for Responsible AI**, a practical guide to
implementing safe, accurate, and fair AI in healthcare settings.
""")

st.markdown("""
#### Connect

- [Personal Website](https://www.drgrahamwalker.com/)
- [LinkedIn](https://www.linkedin.com/in/graham-walker-md/)
""")

st.divider()

st.subheader("About This Project")

st.markdown("""
ACCESS Denied is an open-source simulation tool built to illustrate the incentive
problems inherent in value-based care payment models.

**Key insights:**

1. **The math drives behavior** — Organizations don't need to be "bad actors" to
   cherry-pick patients. The payment structure mathematically rewards avoiding
   complex patients.

2. **Outcome thresholds punish complexity** — When payments depend on meeting
   targets, patients who are harder to treat become financial liabilities.

3. **Good intentions aren't enough** — Mission-driven organizations serving
   complex patients face the same financial pressures as everyone else.

**Built with:**
- Python + Streamlit
- Plotly for visualizations
- NumPy/Pandas for simulation

The simulation uses simplified models and assumptions. Real-world ACCESS programs
are more nuanced, but the underlying incentive dynamics remain.
""")

st.info("""
**Disclaimer:** This is an educational tool, not a prediction of actual outcomes.
The simulation parameters are illustrative and may not reflect real-world data.
""")
