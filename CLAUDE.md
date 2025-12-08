# CLAUDE.md
# ACCESS Incentive & AI Optimization Demonstration Simulator
### A Specification for Building a Visual, Interactive Simulation of Incentive-Driven Patient Selection Under the ACCESS Model

## PURPOSE
Create a **visual, interactive simulation** demonstrating how an AI-driven “ACCESS organization” learns to maximize financial outcomes under ACCESS-style incentives.  
The simulator should show how even well-intentioned actors — with **no malicious intent** — end up:
- cherry-picking the easiest patients,
- lemon-dropping complex ones,
- optimizing metrics rather than care,
- improving outcomes only for the enrolled subgroup,
- while leaving the true high-cost population unchanged or worsening.

The simulator must run in **Streamlit** for easy live screen-sharing.

---

## TECH STACK

**Language:** Python 3.11+  
**Packages (required):**
- numpy
- pandas
- plotly
- streamlit
- scikit-learn (optional)

requirements.txt:

```
numpy>=1.26
pandas>=2.0
plotly>=5.0
streamlit>=1.37
scikit-learn>=1.4
```

---

## PROJECT STRUCTURE

```
access-sim/
  app.py
  simulation/
    __init__.py
    config.py
    patient.py
    environment.py
    policy.py
    simulator.py
    metrics.py
  visuals/
    plots.py
  requirements.txt
  README.md
```

---

## SYSTEM OVERVIEW

### Layers

1. Patient Layer  
2. Environment Layer  
3. Policy / AI Layer  
4. Simulation Orchestrator  
5. Visualization Layer (Streamlit + Plotly)

---

## 1. PATIENT MODEL (patient.py)

### Patient dataclass

```
id: int
true_complexity: int

age: int
num_chronic_conditions: int
has_ckd: int
has_copd: int
has_hf: int
has_depression: int

baseline_bp: float
baseline_a1c: float

engagement_score: float
prior_no_show_rate: float
device_sync_rate: float

housing_stability: float
broadband_score: float
english_proficiency: float

digital_literacy: float

status: str
current_outcome: float
```

### Patient generator

Rules:
- ~40% are complex
- Complex patients: older, lower literacy, lower engagement, worse baselines
- Easy patients: younger, higher literacy, higher engagement

---

## 2. ENVIRONMENT MODEL (environment.py)

### simulate_outcome_change(patient)
If enrolled:
- Easy improvement probability ~0.6  
- Complex ~0.2  
- Modified by engagement + literacy  
- Improvement magnitude:
  - Easy: +0.1 to +0.2  
  - Complex: +0.02 to +0.08  

If dropped or never enrolled:
- Easy drift: ~flat  
- Complex drift: slight decline  

### simulate_spontaneous_dropout(patient)
Higher dropout risk if:
- low engagement
- low digital literacy
- high complexity

---

## 3. POLICY / AI MODEL (policy.py)

### Policy parameters

```
min_engagement: float
max_num_conditions: int
min_digital_literacy: float
drop_threshold_delta: float
```

### Enrollment rule
Enroll if:
- engagement ≥ min_engagement
- num_conditions ≤ max_num_conditions
- literacy ≥ min_digital_literacy
- status == "never_enrolled"
- panel not full

### Drop rule
Drop if:
- outcome_delta < drop_threshold_delta

### Policy optimization
Use hill-climbing:
- mutate policy
- rerun simulation
- keep whichever policy yields higher reward

No deep RL required.

---

## 4. REWARD MODEL (metrics.py)

### compute_year_reward
Reward = enrollment income + improvement bonus – cost.

Components:
- pbpm_income = pbpm * enrolled_count * 12
- avg_improvement = mean(outcome_delta)
- outcome_bonus = outcome_bonus_weight * avg_improvement * enrolled_count
- cost = cost_per_patient * enrolled_count
- reward = pbpm_income + outcome_bonus - cost

Key effect:
Dropping low-improvement patients increases average improvement → higher reward.

This is the incentive problem.

---

## 5. SIMULATOR (simulator.py)

### run_simulation()

For each year:
1. Select patients to enroll  
2. Store previous outcomes  
3. Simulate new outcomes  
4. Simulate spontaneous dropouts  
5. Apply AI drop rules  
6. Compute yearly reward  
7. Log metrics:
   - outcomes by group (enrolled/dropped/never enrolled/all)
   - % complex enrolled vs dropped
   - reward trajectory

Return:
- DataFrame of yearly metrics
- final policy
- optimized policy if applicable

---

## 6. VISUALIZATION (plots.py)

Required plots:
1. Outcomes over time (enrolled, dropped, never enrolled, total)  
2. Panel composition over time (% complex in each group)  
3. Reward over time  
4. Optional stacked bars for status counts

Charts should be interactive Plotly charts.

---

## 7. STREAMLIT APP (app.py)

### Sidebar controls
- Population size  
- Number of years (default: 10)  
- Policy thresholds  
- PBPM, bonus weight, cost per patient  
- AI optimization toggle + iteration count  

### Main panel
- "Run Simulation" button  
- Plots  
- Policy summary  
- Table of key metrics  

### Notes
Clarify:
- AI **cannot see true complexity**  
- It only learns via reward  
- Complex patients lower reward → get dropped  

---

## NON-GOALS
Not production ready.  
No auth, persistence, scaling.  
Does not simulate actual Medicare.  
Designed to expose incentives, not predict real data.

---

## STRETCH GOALS
- Toggle AI vs no-AI  
- Animation slider  
- Export CSV  
- Scenario presets  

---

## CORE DEMO PRINCIPLE
The AI learns to avoid complex patients even though:
- It is never told who is complex  
- It only sees feature vectors  
- It only wants to maximize reward  

Reward → selection → exclusion.

This is the ACCESS unintended consequence illustrated.

