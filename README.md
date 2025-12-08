# ACCESS Incentive & AI Optimization Demonstration Simulator

A visual, interactive simulation demonstrating how an AI-driven healthcare organization learns to maximize financial outcomes under ACCESS-style incentives.

## The Problem This Demonstrates

Even with **no malicious intent**, ACCESS-style incentive structures lead AI systems to:

- **Cherry-pick** the easiest patients
- **Lemon-drop** complex ones
- **Optimize metrics** rather than actual care
- **Improve outcomes** only for the enrolled subgroup
- **Leave the true high-cost population unchanged or worsening**

### Key Insight

The AI **cannot see** which patients are truly complex. It only learns through reward signals — and discovers that complex patients reduce its rewards. By selecting on observable proxies (engagement, digital literacy, chronic conditions), it learns to avoid complexity without ever "knowing" it's doing so.

## Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Running the Simulator

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`.

## Features

### Sidebar Controls

- **Population Settings**: Size, panel limits, simulation years
- **Financial Parameters**: PBPM, outcome bonus weight, cost per patient
- **Policy Thresholds**: Enrollment and drop criteria
- **AI Optimization**: Compare AI vs no-AI scenarios

### Visualizations

1. **Outcomes Over Time**: Track enrolled, dropped, and never-enrolled patient outcomes
2. **Panel Composition**: See how % complex patients changes by status group
3. **Financial Performance**: PBPM income, outcome bonuses, costs, and total reward
4. **Status Counts**: Stacked bars showing patient distribution
5. **Complexity Breakdown**: Easy vs complex patients in enrolled panel

### Comparison Mode

Run side-by-side simulations to see the difference between:
- A static policy (no AI optimization)
- An AI-optimized policy that learns to maximize reward

## Project Structure

```
access-denied/
├── app.py                 # Streamlit application
├── simulation/
│   ├── __init__.py
│   ├── config.py          # Configuration dataclass
│   ├── patient.py         # Patient model and generator
│   ├── environment.py     # Outcome and dropout simulation
│   ├── policy.py          # Enrollment/drop policies + optimization
│   ├── metrics.py         # Reward computation
│   └── simulator.py       # Main simulation orchestrator
├── visuals/
│   ├── __init__.py
│   └── plots.py           # Plotly visualization functions
├── requirements.txt
└── README.md
```

## How the Simulation Works

### Patient Model

Patients have:
- **Observable features**: Age, chronic conditions, engagement, digital literacy, etc.
- **Hidden complexity**: Either "easy" or "complex" (40% are complex)

Complex patients have lower engagement, lower digital literacy, and worse clinical baselines — but the AI never directly sees the complexity label.

### Environment Model

- **Enrolled patients**: Can improve (easy: ~60% chance, complex: ~20% chance)
- **Dropped/never enrolled**: Easy patients drift flat; complex patients decline

### Policy Model

The AI uses hill-climbing optimization to find policy thresholds that maximize reward:
- Minimum engagement score
- Maximum chronic conditions
- Minimum digital literacy
- Drop threshold (improvement below which patients are removed)

### Reward Model

```
Reward = PBPM Income + Outcome Bonus - Costs
```

Where:
- PBPM Income = pbpm × enrolled_count × 12
- Outcome Bonus = bonus_weight × avg_improvement × enrolled_count
- Costs = cost_per_patient × enrolled_count

**The incentive problem**: Dropping low-improvement patients increases average improvement, which increases the bonus while reducing costs.

## Key Takeaways

1. **Selection vs. Treatment**: High metrics for enrolled patients don't mean better care — they may just mean better selection.

2. **Proxy Discrimination**: By optimizing on observable features correlated with complexity, the AI effectively discriminates against complex patients without "intending" to.

3. **Goodhart's Law**: When a measure becomes a target, it ceases to be a good measure. Optimizing for average improvement incentivizes selection, not treatment.

4. **System-Level Thinking**: Individual organization rewards can conflict with population health goals.

## Disclaimer

This is a demonstration tool, not a prediction of real-world outcomes. It is designed to expose incentive structures, not simulate actual Medicare programs. No actual patient data is used.
