
import os
from pathlib import Path
from typing import Dict, Any, List

import numpy as np
import pandas as pd

# -----------------------------
# 0. DATA PATH RESOLUTION
# -----------------------------

DATA_PATH_ENV = "HEMOVITA_RISK_DATA"
DEFAULT_DATA_FILENAME = "micronutrient_data.csv"


def _resolve_data_path() -> Path:
    ...
    # 2) Default: backend/data/micronutrient_data.csv
    here = Path(__file__).resolve()
    # risk.py = backend/app/risk.py
    backend_root = here.parents[1]              # -> backend/
    default_path = backend_root / "data" / DEFAULT_DATA_FILENAME

    print(f"[risk] trying data path: {default_path}")
    if default_path.exists():
        print(f"[risk] resolved data path: {default_path}")
        return default_path

    raise FileNotFoundError(
        f"micronutrient_data.csv not found at: {default_path}\n"
        f"Place it at backend/data/micronutrient_data.csv "
        f"or set {DATA_PATH_ENV}."
    )


    # 2) Default: backend/data/micronutrient_data.csv
    here = Path(__file__).resolve()
    # risk.py = backend/app/engine/risk.py
    backend_root = here.parents[2]              # -> backend/
    default_path = backend_root / "data" / DEFAULT_DATA_FILENAME

    print(f"[risk] trying data path: {default_path}")
    if default_path.exists():
        print(f"[risk] resolved data path: {default_path}")
        return default_path

    raise FileNotFoundError(
        f"micronutrient_data.csv not found at: {default_path}\n"
        f"Place it at backend/data/micronutrient_data.csv "
        f"or set {DATA_PATH_ENV}."
    )


DATA_PATH = _resolve_data_path()
print(f"[risk] loading risk data from: {DATA_PATH}")
df = pd.read_csv(DATA_PATH)



# Rename target and drop rows without primary deficiency probability
df = df.rename(columns={"P_Deficiency_Primary": "True_Risk"})
df = df[~df["True_Risk"].isna()].copy()

# Scale risk from % to 0..1 if needed
if df["True_Risk"].max() > 1.0:
    df["True_Risk"] = df["True_Risk"] / 100.0

# Ensure Age exists
if "Age" not in df.columns:
    df["Age"] = np.nan
df["Age"] = df["Age"].fillna(15.0)

# Keep essential columns
df = df[["Country", "Population", "Gender", "Micronutrient", "Age", "True_Risk"]].copy()

# Strip whitespace in categoricals
CATEGORICAL_CONTEXT_COLS = ["Country", "Population", "Gender"]
for col in CATEGORICAL_CONTEXT_COLS + ["Micronutrient"]:
    df[col] = df[col].astype(str).str.strip()

# -----------------------------
# 1b. BASELINE TABLES (FALLBACKS)
# -----------------------------

# Population + Gender baseline (ignores Country)
baseline_pop_gender = (
    df.groupby(["Population", "Gender", "Micronutrient"], observed=False)["True_Risk"]
      .mean()
      .reset_index()
)

# Global baseline per micronutrient
baseline_global = (
    df.groupby(["Micronutrient"], observed=False)["True_Risk"]
      .mean()
      .reset_index()
)


# -----------------------------
# 2. ENCODING FOR CONTEXT
# -----------------------------

# Build manual maps for context columns (NOT micronutrients — those are actions)
cat_maps: Dict[str, Dict[str, int]] = {}
for col in CATEGORICAL_CONTEXT_COLS:
    cats = sorted(df[col].dropna().unique())
    cat_maps[col] = {val: i for i, val in enumerate(cats)}

def encode_context(country: str, population: str, gender: str, age: float) -> np.ndarray:
    """
    Encode a context (Country, Population, Gender, Age) into a numeric feature vector.
    """
    vals = {
        "Country": str(country).strip(),
        "Population": str(population).strip(),
        "Gender": str(gender).strip(),
    }
    codes: List[float] = []
    for col in CATEGORICAL_CONTEXT_COLS:
        mapping = cat_maps[col]
        v = vals[col]
        # unseen value -> -1
        codes.append(mapping.get(v, -1))
    # normalize age a bit (roughly 0-1 scale)
    age_scaled = float(age) / 100.0
    codes.append(age_scaled)
    return np.array(codes, dtype=float)

CONTEXT_DIM = len(CATEGORICAL_CONTEXT_COLS) + 1  # + Age

# -----------------------------
# 3. BUILD ENVIRONMENT FROM DATA
# -----------------------------

# We aggregate by (Country, Population, Gender, Age, Micronutrient)
# to get a "true" risk for each (context, action).
grouped = (
    df
    .groupby(["Country", "Population", "Gender", "Age", "Micronutrient"], observed=False)["True_Risk"]
    .mean()
    .reset_index()
)

# All unique micronutrients = ACTIONS
MICRONUTRIENTS = sorted(grouped["Micronutrient"].unique())
N_ACTIONS = len(MICRONUTRIENTS)
action_index = {m: i for i, m in enumerate(MICRONUTRIENTS)}

# Map (context, micronutrient) -> True_Risk
risk_lookup: Dict[tuple, float] = {}
# Map context -> list of available actions for that context
avail_actions: Dict[tuple, List[str]] = {}

for _, row in grouped.iterrows():
    ctx_key = (
        row["Country"],
        row["Population"],
        row["Gender"],
        float(row["Age"]),
    )
    m = row["Micronutrient"]
    r = float(row["True_Risk"])  # already in 0..1

    risk_lookup[(ctx_key, m)] = r
    if ctx_key not in avail_actions:
        avail_actions[ctx_key] = []
    avail_actions[ctx_key].append(m)

# List of all contexts for sampling
CONTEXT_KEYS = list(avail_actions.keys())

print(f"[micronutrient_risk_model] #contexts: {len(CONTEXT_KEYS)}, "
      f"#actions (micronutrients): {N_ACTIONS}")

# -----------------------------
# 4. LINUCB CONTEXTUAL BANDIT
# -----------------------------

# For each action a, we keep:
#   A_a (d x d), b_a (d)
# and learn theta_a = A_a^{-1} b_a

alpha = 1.0  # exploration strength
d = CONTEXT_DIM

A = [np.eye(d) for _ in range(N_ACTIONS)]
b = [np.zeros(d) for _ in range(N_ACTIONS)]

def choose_action_linucb(x: np.ndarray, allowed_micronutrients: List[str]) -> str:
    """
    Given context feature vector x and the list of allowed micronutrients
    for that context, pick an action using LinUCB.
    """
    x = x.reshape(-1, 1)  # column vector (d x 1)
    best_p = -1e9
    best_micronutrient = None
    for m in allowed_micronutrients:
        a_idx = action_index[m]
        A_a = A[a_idx]
        b_a = b[a_idx]
        A_inv = np.linalg.inv(A_a)
        theta_a = A_inv @ b_a  # (d,)
        # UCB score
        mean_reward = float(theta_a @ x[:, 0])
        # exploration term
        var_term = float(np.sqrt(x.T @ A_inv @ x))
        p = mean_reward + alpha * var_term
        if p > best_p:
            best_p = p
            best_micronutrient = m
    return best_micronutrient  # type: ignore[return-value]

def linucb_update(micronutrient: str, x: np.ndarray, reward: float) -> None:
    """
    Online update for LinUCB.
    """
    a_idx = action_index[micronutrient]
    x = x.reshape(-1, 1)  # (d x 1)
    A[a_idx] += x @ x.T
    b[a_idx] += reward * x[:, 0]

# -----------------------------
# 5. TRAINING LOOP (TRUE RL STYLE)
# -----------------------------

def train_bandit(num_steps: int = 50000, seed: int = 42):
    """
    True contextual-bandit training:
      - Sample a context from the dataset
      - Bandit chooses an action (micronutrient)
      - Environment returns a reward based on True_Risk
      - Update parameters online
    """
    rng = np.random.default_rng(seed)
    rewards_history: List[float] = []

    if not CONTEXT_KEYS:
        print("[micronutrient_risk_model] No contexts found; skipping training.")
        return rewards_history

    for t in range(1, num_steps + 1):
        # 1) Sample a random context from our data-derived environment
        ctx_key = CONTEXT_KEYS[rng.integers(0, len(CONTEXT_KEYS))]
        country, population, gender, age = ctx_key
        allowed_actions = avail_actions[ctx_key]

        # 2) Encode context
        x = encode_context(country, population, gender, age)

        # 3) Choose action using LinUCB
        chosen_m = choose_action_linucb(x, allowed_actions)

        # 4) Get underlying deficiency probability
        true_p = risk_lookup[(ctx_key, chosen_m)]  # in [0, 1]

        # 5) Sample a Bernoulli reward (1 = deficient, 0 = not)
        reward = rng.binomial(1, true_p)
        rewards_history.append(reward)

        # 6) Update bandit parameters
        linucb_update(chosen_m, x, reward)

        # Optional: small progress print
        if t % 10000 == 0:
            avg_r = np.mean(rewards_history[-1000:])
            print(
                f"[micronutrient_risk_model] Step {t}/{num_steps} "
                f"| recent avg reward (last 1000): {avg_r:.3f}"
            )

    print("[micronutrient_risk_model] Training complete.")
    return rewards_history

# Train once at import so the FastAPI app can use the learned parameters
rewards_history = train_bandit(num_steps=30000)

# -----------------------------
# 6. PREDICTION + PUBLIC API
# -----------------------------

def bandit_predict_deficiency_risk(
    country: str,
    population: str,
    gender: str,
    age: float,
):
    """
    Use the trained LinUCB parameters to estimate deficiency probability
    for ALL micronutrients for a given profile.

    Returns sorted list of:
        { 'micronutrient': str, 'predicted_risk': float }
    """
    x = encode_context(country, population, gender, age)  # (d,)
    results = []

    for m in MICRONUTRIENTS:
        a_idx = action_index[m]
        A_a = A[a_idx]
        b_a = b[a_idx]
        A_inv = np.linalg.inv(A_a)
        theta_a = A_inv @ b_a  # (d,)
        r_hat = float(theta_a @ x)  # can be outside [0,1]; clamp
        r_hat = max(0.0, min(1.0, r_hat))
        results.append({
            "micronutrient": m,
            "predicted_risk": r_hat,
        })

    # sort by predicted risk descending
    results.sort(key=lambda r: r["predicted_risk"], reverse=True)
    return results

#FALLBACK LOGIC 
def _fallback_risks_by_pop_gender(population: str, gender: str) -> List[Dict[str, float]]:
    """
    Fallback when country is unknown / not in training data.
    Use average risk per micronutrient for matching (Population, Gender),
    and if that fails, fall back to global averages.
    """
    pop = str(population).strip()
    gen = str(gender).strip()

    sub = baseline_pop_gender[
        (baseline_pop_gender["Population"] == pop)
        & (baseline_pop_gender["Gender"] == gen)
    ]

    if sub.empty:
        sub = baseline_global.copy()
    else:
        sub = sub.copy()

    results: List[Dict[str, float]] = []
    for _, row in sub.iterrows():
        results.append({
            "micronutrient": row["Micronutrient"],
            "predicted_risk": float(row["True_Risk"]),
        })

    results.sort(key=lambda r: r["predicted_risk"], reverse=True)
    return results

def _summarize_risks(risks: List[Dict[str, float]], top_n: int = 3) -> str:
    """
    Simple text summary for UI / report.
    """
    if not risks:
        return "No micronutrient risks could be estimated from demographic profile."

    # focus on higher risks
    sorted_risks = sorted(risks, key=lambda r: r["predicted_risk"], reverse=True)
    top = [r for r in sorted_risks if r["predicted_risk"] >= 0.15][:top_n]

    if not top:
        return "No major micronutrient risks predicted from demographics alone."

    parts = [
        f"{r['micronutrient']} (~{r['predicted_risk'] * 100:.1f}%)"
        for r in top
    ]
    return (
        "Highest predicted deficiency risks from demographics alone: "
        + ", ".join(parts)
        + "."
    )

# FALLBACK MODEL DISCLAIMER
def _fallback_disclaimer(fallback_level: str, population: str, gender: str) -> str:
    """
    Produce a readable disclaimer for when country-specific data is unavailable.
    """
    if fallback_level == "population_gender_or_global":
        return (
            "Country-specific data was not available for this profile. "
            "Risk estimates are based on global patterns for individuals "
            f"in the same population group ({population}, {gender})."
        )
    return ""


def get_micronutrient_risk_profile(profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Public API used by FastAPI.
    Expects keys: country, population, gender, age
    """
    country = profile.get("country", "") or ""
    population = profile.get("population", "") or "All"
    gender = profile.get("gender", "") or "All"
    age = float(profile.get("age", 15.0))

    # Do we know this country from the training data?
    country_clean = country.strip()
    country_known = country_clean in cat_maps.get("Country", {})

    if country_known:
        # Use full bandit model with country
        risks = bandit_predict_deficiency_risk(
            country=country,
            population=population,
            gender=gender,
            age=age,
        )
        fallback_used = False
        fallback_level = None
    else:
        # Fallback: ignore country, use Population+Gender baseline or global
        risks = _fallback_risks_by_pop_gender(population, gender)
        fallback_used = True
        fallback_level = "population_gender_or_global"

    summary = _summarize_risks(risks)

    disclaimer = ""
    if fallback_used:
        disclaimer = _fallback_disclaimer(
            fallback_level=fallback_level,
            population=population,
            gender=gender,
        )

    return {
        "micronutrient_risks": risks,
        "summary_text": summary,
        "disclaimer": disclaimer,
        "meta": {
            "country": country,
            "population": population,
            "gender": gender,
            "age": age,
            "country_known": country_known,
            "fallback_used": fallback_used,
            "fallback_level": fallback_level,
        },
    }

if __name__ == "__main__":
    # quick manual test
    demo_profile = {
        "country": "Pakistan",
        "population": "Women",
        "gender": "Female",
        "age": 15.0,
    }
    out = get_micronutrient_risk_profile(demo_profile)
    print(out["summary_text"])
    print("Disclaimer:", out.get("disclaimer", ""))
    print(out["micronutrient_risks"][:5])





















# import os
# from pathlib import Path
# from typing import Dict, Any, List

# import numpy as np
# import pandas as pd

# # -----------------------------
# # 0. DATA PATH RESOLUTION
# # -----------------------------

# DATA_PATH_ENV = "HEMOVITA_RISK_DATA"
# DEFAULT_DATA_FILENAME = "micronutrient_data.csv"


# def _resolve_data_path() -> Path:
#     ...
#     # 2) Default: backend/data/micronutrient_data.csv
#     here = Path(__file__).resolve()
#     # risk.py = backend/app/risk.py
#     backend_root = here.parents[1]              # -> backend/
#     default_path = backend_root / "data" / DEFAULT_DATA_FILENAME

#     print(f"[risk] trying data path: {default_path}")
#     if default_path.exists():
#         print(f"[risk] resolved data path: {default_path}")
#         return default_path

#     raise FileNotFoundError(
#         f"micronutrient_data.csv not found at: {default_path}\n"
#         f"Place it at backend/data/micronutrient_data.csv "
#         f"or set {DATA_PATH_ENV}."
#     )


#     # 2) Default: backend/data/micronutrient_data.csv
#     here = Path(__file__).resolve()
#     # risk.py = backend/app/engine/risk.py
#     backend_root = here.parents[2]              # -> backend/
#     default_path = backend_root / "data" / DEFAULT_DATA_FILENAME

#     print(f"[risk] trying data path: {default_path}")
#     if default_path.exists():
#         print(f"[risk] resolved data path: {default_path}")
#         return default_path

#     raise FileNotFoundError(
#         f"micronutrient_data.csv not found at: {default_path}\n"
#         f"Place it at backend/data/micronutrient_data.csv "
#         f"or set {DATA_PATH_ENV}."
#     )


# DATA_PATH = _resolve_data_path()
# print(f"[risk] loading risk data from: {DATA_PATH}")
# df = pd.read_csv(DATA_PATH)



# # Rename target and drop rows without primary deficiency probability
# df = df.rename(columns={"P_Deficiency_Primary": "True_Risk"})
# df = df[~df["True_Risk"].isna()].copy()

# # Scale risk from % to 0..1 if needed
# if df["True_Risk"].max() > 1.0:
#     df["True_Risk"] = df["True_Risk"] / 100.0

# # Ensure Age exists
# if "Age" not in df.columns:
#     df["Age"] = np.nan
# df["Age"] = df["Age"].fillna(15.0)

# # Keep essential columns
# df = df[["Country", "Population", "Gender", "Micronutrient", "Age", "True_Risk"]].copy()

# # Strip whitespace in categoricals
# CATEGORICAL_CONTEXT_COLS = ["Country", "Population", "Gender"]
# for col in CATEGORICAL_CONTEXT_COLS + ["Micronutrient"]:
#     df[col] = df[col].astype(str).str.strip()

# # -----------------------------
# # 2. ENCODING FOR CONTEXT
# # -----------------------------

# # Build manual maps for context columns (NOT micronutrients — those are actions)
# cat_maps: Dict[str, Dict[str, int]] = {}
# for col in CATEGORICAL_CONTEXT_COLS:
#     cats = sorted(df[col].dropna().unique())
#     cat_maps[col] = {val: i for i, val in enumerate(cats)}

# def encode_context(country: str, population: str, gender: str, age: float) -> np.ndarray:
#     """
#     Encode a context (Country, Population, Gender, Age) into a numeric feature vector.
#     """
#     vals = {
#         "Country": str(country).strip(),
#         "Population": str(population).strip(),
#         "Gender": str(gender).strip(),
#     }
#     codes: List[float] = []
#     for col in CATEGORICAL_CONTEXT_COLS:
#         mapping = cat_maps[col]
#         v = vals[col]
#         # unseen value -> -1
#         codes.append(mapping.get(v, -1))
#     # normalize age a bit (roughly 0-1 scale)
#     age_scaled = float(age) / 100.0
#     codes.append(age_scaled)
#     return np.array(codes, dtype=float)

# CONTEXT_DIM = len(CATEGORICAL_CONTEXT_COLS) + 1  # + Age

# # -----------------------------
# # 3. BUILD ENVIRONMENT FROM DATA
# # -----------------------------

# # We aggregate by (Country, Population, Gender, Age, Micronutrient)
# # to get a "true" risk for each (context, action).
# grouped = (
#     df
#     .groupby(["Country", "Population", "Gender", "Age", "Micronutrient"], observed=False)["True_Risk"]
#     .mean()
#     .reset_index()
# )

# # All unique micronutrients = ACTIONS
# MICRONUTRIENTS = sorted(grouped["Micronutrient"].unique())
# N_ACTIONS = len(MICRONUTRIENTS)
# action_index = {m: i for i, m in enumerate(MICRONUTRIENTS)}

# # Map (context, micronutrient) -> True_Risk
# risk_lookup: Dict[tuple, float] = {}
# # Map context -> list of available actions for that context
# avail_actions: Dict[tuple, List[str]] = {}

# for _, row in grouped.iterrows():
#     ctx_key = (
#         row["Country"],
#         row["Population"],
#         row["Gender"],
#         float(row["Age"]),
#     )
#     m = row["Micronutrient"]
#     r = float(row["True_Risk"])  # already in 0..1

#     risk_lookup[(ctx_key, m)] = r
#     if ctx_key not in avail_actions:
#         avail_actions[ctx_key] = []
#     avail_actions[ctx_key].append(m)

# # List of all contexts for sampling
# CONTEXT_KEYS = list(avail_actions.keys())

# print(f"[micronutrient_risk_model] #contexts: {len(CONTEXT_KEYS)}, "
#       f"#actions (micronutrients): {N_ACTIONS}")

# # -----------------------------
# # 4. LINUCB CONTEXTUAL BANDIT
# # -----------------------------

# # For each action a, we keep:
# #   A_a (d x d), b_a (d)
# # and learn theta_a = A_a^{-1} b_a

# alpha = 1.0  # exploration strength
# d = CONTEXT_DIM

# A = [np.eye(d) for _ in range(N_ACTIONS)]
# b = [np.zeros(d) for _ in range(N_ACTIONS)]

# def choose_action_linucb(x: np.ndarray, allowed_micronutrients: List[str]) -> str:
#     """
#     Given context feature vector x and the list of allowed micronutrients
#     for that context, pick an action using LinUCB.
#     """
#     x = x.reshape(-1, 1)  # column vector (d x 1)
#     best_p = -1e9
#     best_micronutrient = None
#     for m in allowed_micronutrients:
#         a_idx = action_index[m]
#         A_a = A[a_idx]
#         b_a = b[a_idx]
#         A_inv = np.linalg.inv(A_a)
#         theta_a = A_inv @ b_a  # (d,)
#         # UCB score
#         mean_reward = float(theta_a @ x[:, 0])
#         # exploration term
#         var_term = float(np.sqrt(x.T @ A_inv @ x))
#         p = mean_reward + alpha * var_term
#         if p > best_p:
#             best_p = p
#             best_micronutrient = m
#     return best_micronutrient  # type: ignore[return-value]

# def linucb_update(micronutrient: str, x: np.ndarray, reward: float) -> None:
#     """
#     Online update for LinUCB.
#     """
#     a_idx = action_index[micronutrient]
#     x = x.reshape(-1, 1)  # (d x 1)
#     A[a_idx] += x @ x.T
#     b[a_idx] += reward * x[:, 0]

# # -----------------------------
# # 5. TRAINING LOOP (TRUE RL STYLE)
# # -----------------------------

# def train_bandit(num_steps: int = 50000, seed: int = 42):
#     """
#     True contextual-bandit training:
#       - Sample a context from the dataset
#       - Bandit chooses an action (micronutrient)
#       - Environment returns a reward based on True_Risk
#       - Update parameters online
#     """
#     rng = np.random.default_rng(seed)
#     rewards_history: List[float] = []

#     if not CONTEXT_KEYS:
#         print("[micronutrient_risk_model] No contexts found; skipping training.")
#         return rewards_history

#     for t in range(1, num_steps + 1):
#         # 1) Sample a random context from our data-derived environment
#         ctx_key = CONTEXT_KEYS[rng.integers(0, len(CONTEXT_KEYS))]
#         country, population, gender, age = ctx_key
#         allowed_actions = avail_actions[ctx_key]

#         # 2) Encode context
#         x = encode_context(country, population, gender, age)

#         # 3) Choose action using LinUCB
#         chosen_m = choose_action_linucb(x, allowed_actions)

#         # 4) Get underlying deficiency probability
#         true_p = risk_lookup[(ctx_key, chosen_m)]  # in [0, 1]

#         # 5) Sample a Bernoulli reward (1 = deficient, 0 = not)
#         reward = rng.binomial(1, true_p)
#         rewards_history.append(reward)

#         # 6) Update bandit parameters
#         linucb_update(chosen_m, x, reward)

#         # Optional: small progress print
#         if t % 10000 == 0:
#             avg_r = np.mean(rewards_history[-1000:])
#             print(
#                 f"[micronutrient_risk_model] Step {t}/{num_steps} "
#                 f"| recent avg reward (last 1000): {avg_r:.3f}"
#             )

#     print("[micronutrient_risk_model] Training complete.")
#     return rewards_history

# # Train once at import so the FastAPI app can use the learned parameters
# rewards_history = train_bandit(num_steps=30000)

# # -----------------------------
# # 6. PREDICTION + PUBLIC API
# # -----------------------------

# def bandit_predict_deficiency_risk(
#     country: str,
#     population: str,
#     gender: str,
#     age: float,
# ):
#     """
#     Use the trained LinUCB parameters to estimate deficiency probability
#     for ALL micronutrients for a given profile.

#     Returns sorted list of:
#         { 'micronutrient': str, 'predicted_risk': float }
#     """
#     x = encode_context(country, population, gender, age)  # (d,)
#     results = []

#     for m in MICRONUTRIENTS:
#         a_idx = action_index[m]
#         A_a = A[a_idx]
#         b_a = b[a_idx]
#         A_inv = np.linalg.inv(A_a)
#         theta_a = A_inv @ b_a  # (d,)
#         r_hat = float(theta_a @ x)  # can be outside [0,1]; clamp
#         r_hat = max(0.0, min(1.0, r_hat))
#         results.append({
#             "micronutrient": m,
#             "predicted_risk": r_hat,
#         })

#     # sort by predicted risk descending
#     results.sort(key=lambda r: r["predicted_risk"], reverse=True)
#     return results

# def _summarize_risks(risks: List[Dict[str, float]], top_n: int = 3) -> str:
#     """
#     Simple text summary for UI / report.
#     """
#     if not risks:
#         return "No micronutrient risks could be estimated from demographic profile."

#     # focus on higher risks
#     sorted_risks = sorted(risks, key=lambda r: r["predicted_risk"], reverse=True)
#     top = [r for r in sorted_risks if r["predicted_risk"] >= 0.15][:top_n]

#     if not top:
#         return "No major micronutrient risks predicted from demographics alone."

#     parts = [
#         f"{r['micronutrient']} (~{r['predicted_risk'] * 100:.1f}%)"
#         for r in top
#     ]
#     return (
#         "Highest predicted deficiency risks from demographics alone: "
#         + ", ".join(parts)
#         + "."
#     )

# def get_micronutrient_risk_profile(profile: Dict[str, Any]) -> Dict[str, Any]:
#     """
#     Public API used by FastAPI.
#     Expects keys: country, population, gender, age
#     """
#     country = profile.get("country", "") or ""
#     population = profile.get("population", "") or "All"
#     gender = profile.get("gender", "") or "All"
#     age = float(profile.get("age", 15.0))

#     risks = bandit_predict_deficiency_risk(
#         country=country,
#         population=population,
#         gender=gender,
#         age=age,
#     )
#     summary = _summarize_risks(risks)

#     return {
#         "micronutrient_risks": risks,
#         "summary_text": summary,
#         "meta": {
#             "country": country,
#             "population": population,
#             "gender": gender,
#             "age": age,
#         },
#     }

# if __name__ == "__main__":
#     # quick manual test
#     demo_profile = {
#         "country": "Pakistan",
#         "population": "Women",
#         "gender": "Female",
#         "age": 15.0,
#     }
#     out = get_micronutrient_risk_profile(demo_profile)
#     print(out["summary_text"])
#     print(out["micronutrient_risks"][:5])
