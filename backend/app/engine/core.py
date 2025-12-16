from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Set, List, Tuple, Optional

import numpy as np
import pandas as pd
import math


SCRIPT_DIR = Path(__file__).resolve().parent          # backend/app/engine
DATA_DIR = SCRIPT_DIR.parent.parent / "data"          # backend/data

CUTOFF_CSV = DATA_DIR / "micronutrient_cutoffs_structured.csv"
FOOD_CSV_DEFAULT = DATA_DIR / "foods_usda.csv"
EDGES = DATA_DIR / "network_relationships.csv"

# -------------------------------------------------------------------
# 0. Nutrient interaction network (Graph)
# -------------------------------------------------------------------
try:
    import networkx as nx

    if EDGES.exists():
        edges_df = pd.read_csv(EDGES)

        def build_graph_from_edges(df: pd.DataFrame):
            G = nx.DiGraph()
            for _, r in df.iterrows():
                G.add_edge(
                    str(r["source"]).strip(),
                    str(r["target"]).strip(),
                    effect=str(r.get("effect", "")).strip(),
                    confidence=str(r.get("confidence", "")).strip(),
                    notes=str(r.get("notes", "")).strip(),
                )
            return G

        G_NETWORK = build_graph_from_edges(edges_df)
    else:
        edges_df = None
        G_NETWORK = None

except ImportError:
    edges_df = None
    G_NETWORK = None


def low_items(labels: Dict[str, str]) -> List[str]:
    """Return markers that are flagged low in the classification."""
    return [k for k, v in labels.items() if v == "low"]


def multihop_explanations(
    G: "nx.DiGraph",
    low_targets: List[str],
    max_hops: int = 2,
) -> Dict[str, List[str]]:
    """
    For each low target node, find all simple paths of length <= max_hops
    from any source node to that target, and format them as readable strings.
    """
    import networkx as nx  # local import to avoid issues if not installed

    out: Dict[str, List[str]] = {}
    for T in low_targets:
        if T not in G.nodes:
            continue

        paths: List[str] = []
        for S in G.nodes:
            if S == T:
                continue
            if not nx.has_path(G, S, T):
                continue

            for p in nx.all_simple_paths(G, S, T, cutoff=max_hops):
                effs = []
                for u, v in zip(p[:-1], p[1:]):
                    e = G[u][v]
                    effs.append(f"{u} —{e.get('effect', '')}→ {v}")
                paths.append(" → ".join(p) + "   [" + "; ".join(effs) + "]")

        if paths:
            out[T] = sorted(set(paths))

    return out


@dataclass
class PatientInfo:
    age: Optional[float] = None           # years
    sex: Optional[str] = None             # "male" / "female" / None
    pregnant: Optional[bool] = None       # True / False / None
    country: Optional[str] = None
    notes: Optional[str] = None


# -------------------------------------------------------------------
# 1. Load structured cutoffs & build REF / REF_TIERS
# -------------------------------------------------------------------

cutoffs = pd.read_csv(CUTOFF_CSV)

# Marker names here should match keys you use in the labs dict
# (e.g., labs["Hemoglobin"], labs["ferritin"], labs["vitamin_B12"], ...)
MARKER_MAP = {
    # anemia & RBC indices
    "Hemoglobin": {
        "micronutrient": "iron_related_anemia",
        "biomarker": "hemoglobin",
        # we pick WHO nonpregnant_women threshold as "low"
        "population_group": "nonpregnant_women",
        "low_type": "anemia",
        "unit": "g/dL",
    },
    "MCV": {
        "micronutrient": "iron_related_anemia",
        "biomarker": "MCV",
        "population_group": "adults",
        "low_type": "microcytosis",
        "high_type": "macrocytosis",
        "unit": "fL",
    },

    # iron status
    "ferritin": {
        "micronutrient": "iron",
        "biomarker": "serum_ferritin",
        "population_group": "nonpregnant_adults",
        "low_type": "deficiency",
        "unit": "µg/L",
    },

    # B12 / folate
    "vitamin_B12": {
        "micronutrient": "vitamin_B12",
        "biomarker": "serum_B12",
        "population_group": "adults",
        "low_type": "deficiency",
        # many labs report pg/mL; we set that here
        "unit": "pg/mL",
    },
    "folate_plasma": {
        "micronutrient": "folate",
        "biomarker": "plasma_or_serum_folate",
        "population_group": "adults",
        "low_type": "deficiency",
        "unit": "nmol/L",
    },

    # fat-soluble vitamins
    "vitamin_D": {
        "micronutrient": "vitamin_D",
        "biomarker": "serum_25OHD",
        "population_group": "general",
        "low_type": "deficiency",
        "unit": "nmol/L",   # switch to "ng/mL" if your labs use that
    },
    "vitamin_A": {
        "micronutrient": "vitamin_A",
        "biomarker": "serum_retinol",
        "population_group": "children_and_adults_nonpregnant",
        "low_type": "deficiency",
        "unit": "µmol/L",
    },
    "vitamin_E": {
        "micronutrient": "vitamin_E",
        "biomarker": "plasma_alpha_tocopherol",
        "population_group": "adults",
        "low_type": "deficiency",
        "unit": "µmol/L",
    },

    # water-soluble vitamins
    "vitamin_C": {
        "micronutrient": "vitamin_C",
        "biomarker": "plasma_vitamin_C",
        "population_group": "adults",
        "low_type": "deficiency",
        "unit": "µmol/L",
    },
    "vitamin_B6": {
        "micronutrient": "vitamin_B6",
        "biomarker": "plasma_PLP",
        "population_group": "adults",
        "low_type": "deficiency",
        "unit": "nmol/L",
    },

    # minerals
    "magnesium": {
        "micronutrient": "magnesium",
        "biomarker": "serum_magnesium",
        "population_group": "adults",
        "low_type": "deficiency",
        "unit": "mmol/L",
    },
    "calcium": {
        "micronutrient": "calcium",
        "biomarker": "serum_total_calcium",
        "population_group": "adults",
        "low_type": "low",
        "unit": "mmol/L",
    },
    "zinc": {
        "micronutrient": "zinc",
        "biomarker": "plasma_or_serum_zinc",
        "population_group": "females_over_10",
        "low_type": "deficiency",
        "unit": "µg/dL",
    },

    # homocysteine (functional B12/folate marker)
    "homocysteine": {
        "micronutrient": "homocysteine_related",
        "biomarker": "plasma_homocysteine",
        "population_group": "adults",
        "high_type": "high_mild",  # >15 µmol/L
        "unit": "µmol/L",
    },
}


def _select_rows_for_marker(marker_name: str) -> pd.DataFrame:
    """
    Return subset of the cutoffs table relevant for this marker.
    """
    spec = MARKER_MAP.get(marker_name, {})
    micronutrient = spec.get("micronutrient")
    biomarker = spec.get("biomarker")
    if not micronutrient or not biomarker:
        return cutoffs.iloc[0:0]

    df = cutoffs[
        (cutoffs["micronutrient"] == micronutrient)
        & (cutoffs["biomarker"] == biomarker)
    ].copy()

    pg = spec.get("population_group")
    if pg is not None:
        df = df[df["population_group"] == pg]

    unit = spec.get("unit")
    if unit is not None:
        df = df[df["unit"] == unit]

    return df


def build_ref_from_cutoffs() -> Tuple[Dict[str, Dict[str, float]], Dict[str, Dict[str, float]]]:
    """
    Build:
      REF[marker]      = {"low": value?, "high": value?}
      REF_TIERS[marker] = {"deficiency": val, "severe_deficiency": val, ...}
    from the structured CSV.
    """
    REF: Dict[str, Dict[str, float]] = {}
    REF_TIERS: Dict[str, Dict[str, float]] = {}

    for marker in MARKER_MAP.keys():
        df = _select_rows_for_marker(marker)
        if df.empty:
            continue

        tiers: Dict[str, float] = {}
        for _, row in df.iterrows():
            ctype = str(row["cutoff_type"])
            val = float(row["cutoff_value"])
            tiers[ctype] = val

        REF_TIERS[marker] = tiers

        spec = MARKER_MAP.get(marker, {})
        low_type = spec.get("low_type")
        high_type = spec.get("high_type")

        low_val = None
        high_val = None

        # Low
        if low_type and low_type in tiers:
            low_val = tiers[low_type]
        else:
            for k in tiers.keys():
                if (
                    "deficiency" in k
                    or "anemia" in k
                    or "micro" in k
                    or "ntd_insufficient" in k
                ):
                    low_val = tiers[k]
                    break

        # High
        if high_type and high_type in tiers:
            high_val = tiers[high_type]
        else:
            for k in tiers.keys():
                if "high" in k or "macro" in k:
                    high_val = tiers[k]
                    break

        if low_val is not None or high_val is not None:
            REF[marker] = {}
            if low_val is not None:
                REF[marker]["low"] = low_val
            if high_val is not None:
                REF[marker]["high"] = high_val

    return REF, REF_TIERS


REF, REF_TIERS = build_ref_from_cutoffs()

# -------------------------------------------------------------------
# 2. Classification helpers
# -------------------------------------------------------------------

def classify_panel(labs: Dict[str, float]) -> Dict[str, str]:
    """
    Given a dict of labs {marker: value}, return {marker: label}
    using classify_value and the global REF/REF_TIERS.
    """
    labels: Dict[str, str] = {}
    for marker, val in labs.items():
        labels[marker] = classify_value(marker, val)
    return labels


def classify_value(marker: str, value: Optional[float]) -> str:
    """
    Classify a lab value using REF + REF_TIERS:
    - "low", "high", "normal", "unknown"
    (you can extend with "severe_low", "marginal" if you wire in REF_TIERS details)
    """
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "unknown"

    rng = REF.get(marker)
    if not rng:
        return "unknown"

    low = rng.get("low")
    high = rng.get("high")

    # Low side
    if low is not None and value < low:
        return "low"

    # High side
    if high is not None and value > high:
        return "high"

    return "normal"


# -------------------------------------------------------------------
# 3. Supplement scheduling (conflict-aware)
# -------------------------------------------------------------------

# Time slots in a day
SLOTS = ["morning", "midday", "evening"]  # cheap & simple

# Map lab markers -> actual supplement key we schedule
# (anemia markers should NOT appear as "supplements" in the plan)
SUPPLEMENT_PROXY = {
    "Hemoglobin": "iron",
    "MCV": "iron",
    "ferritin": "iron",
    "Serum ferritin": "iron",  # just in case you ever use this label
}


def marker_to_supplement(marker: str) -> str:
    """
    Convert a lab marker name to the supplement key we actually schedule.
    For example:
        Hemoglobin, MCV, ferritin, Serum ferritin -> "iron"
    Everything else defaults to itself (vitamin_B12, vitamin_D, etc.).
    """
    return SUPPLEMENT_PROXY.get(marker, marker)


# Map network nodes → supplement keys we actually schedule
# (everything else maps to itself)
NETWORK_TO_PLAN_KEY = {
    # All iron-status biomarkers / constructs → "iron"
    "indicator_iron_serum": "iron",
    "Hemoglobin": "iron",
    "ferritin": "iron",
    "total_iron_binding_capacity": "iron",
    "transferrin": "iron",
    "iron_deficiency_anemia": "iron",
}


def _network_node_to_plan_key(node: str) -> str:
    """
    Map a node name from network_relationships.csv into the supplement key
    that appears in the plan (e.g., indicator_iron_serum → "iron").
    Everything else just passes through unchanged.
    """
    node = str(node).strip()
    return NETWORK_TO_PLAN_KEY.get(node, node)


def build_interaction_rules_from_network(edges_df: Optional[pd.DataFrame] = None):
    """
    Build BOOSTERS / ANTAGONISTS purely from network_relationships.csv.

    - BOOSTERS:
        For every row where effect == "boosts":
            source --boosts--> target
        we treat `source` as a co-dosed booster for the supplement bundle
        corresponding to `target`.

    - ANTAGONISTS:
        For every row where effect == "inhibits":
            source --inhibits--> target
        we treat source/target as a pair that should NOT share the same slot.
        (We make this symmetric so either direction counts as a conflict.)
    """
    boosters: Dict[str, Dict[str, List[str]]] = {}
    antagonists_raw: Dict[str, Set[str]] = {}

    if edges_df is None or edges_df.empty:
        # No network → no cofactors, no conflict rules
        return boosters, {}

    df = edges_df.copy()
    df["effect_norm"] = df["effect"].astype(str).str.lower().str.strip()
    df["target_norm"] = df["target"].astype(str).str.strip()
    df["source_norm"] = df["source"].astype(str).str.strip()

    # ---------- 1) BOOSTERS: source --boosts--> target ----------
    boost_df = df[df["effect_norm"] == "boosts"]

    for _, row in boost_df.iterrows():
        raw_target = row["target_norm"]
        raw_source = row["source_norm"]

        target_key = _network_node_to_plan_key(raw_target)
        source_key = _network_node_to_plan_key(raw_source)

        if not target_key or not source_key:
            continue
        if target_key == source_key:
            continue  # e.g. iron_status nodes collapsing to "iron"

        bundle = boosters.setdefault(
            target_key,
            {"targets": [target_key], "boosters": []},
        )
        if source_key not in bundle["boosters"]:
            bundle["boosters"].append(source_key)

    # ---------- 2) ANTAGONISTS: source --inhibits--> target ----------
    inhib_df = df[df["effect_norm"] == "inhibits"]

    for _, row in inhib_df.iterrows():
        raw_target = row["target_norm"]
        raw_source = row["source_norm"]

        a = _network_node_to_plan_key(raw_source)
        b = _network_node_to_plan_key(raw_target)

        if not a or not b:
            continue
        if a == b:
            continue  # ignore self-loops after bundling

        # Treat inhibition as "these two should not share a slot" (symmetric)
        antagonists_raw.setdefault(a, set()).add(b)
        antagonists_raw.setdefault(b, set()).add(a)

    # Convert sets → {"avoid_with": [...]}
    antagonists: Dict[str, Dict[str, List[str]]] = {}
    for nutrient, avoid_set in antagonists_raw.items():
        antagonists[nutrient] = {"avoid_with": sorted(avoid_set)}

    return boosters, antagonists


# Instantiate BOOSTERS / ANTAGONISTS using the nutrient network if present
if "edges_df" in globals():
    BOOSTERS, ANTAGONISTS = build_interaction_rules_from_network(edges_df)
else:
    BOOSTERS, ANTAGONISTS = build_interaction_rules_from_network(None)

print("BOOSTERS:", BOOSTERS)
print("ANTAGONISTS:", ANTAGONISTS)


def build_supplement_plan(labels: Dict[str, str]) -> Dict[str, List[str]]:
    """
    Given classification labels, decide which supplements to schedule.

    - We map anemia markers (Hemoglobin, MCV, ferritin, Serum ferritin)
      to a single "iron" supplement key.
    - We only schedule markers that are "low".
    - We use ANTAGONISTS / BOOSTERS (derived from the network) to place
      nutrients away from their antagonists and co-dose network boosters.
    """
    # 1) Find low markers
    raw_deficient_markers = [m for m, lab in labels.items() if lab == "low"]

    # 2) Map lab markers -> supplement keys and dedupe (order-preserving)
    deficient: List[str] = []
    for m in raw_deficient_markers:
        supp = marker_to_supplement(m)
        if supp not in deficient:
            deficient.append(supp)

    # 3) Initialize empty plan
    plan: Dict[str, List[str]] = {slot: [] for slot in SLOTS}

    def can_place(nutrient: str, slot: str) -> bool:
        """
        General conflict logic using ANTAGONISTS from the network:

        For any nutrient already in the slot, if:
          - nutrient is in ANTAGONISTS[other]["avoid_with"], OR
          - other is in ANTAGONISTS[nutrient]["avoid_with"]
        then they should NOT share the slot.
        """
        for already in plan[slot]:
            avoid_for_new = set(ANTAGONISTS.get(nutrient, {}).get("avoid_with", []))
            avoid_for_already = set(ANTAGONISTS.get(already, {}).get("avoid_with", []))

            if already in avoid_for_new or nutrient in avoid_for_already:
                return False

        return True

    # 4) First pass: place primary supplements (deficient ones)
    for nutrient in deficient:
        placed = False
        for slot in SLOTS:
            if can_place(nutrient, slot):
                plan[slot].append(nutrient)
                placed = True
                break
        if not placed:
            # If nowhere is conflict-free, just put it in the last slot
            plan[SLOTS[-1]].append(nutrient)

    # 5) Second pass: align boosters (from the nutrient network)
    for bundle in BOOSTERS.values():
        # "targets" are supplement keys (e.g., "iron", "vitamin_D")
        targets = [t for t in bundle["targets"] if t in deficient]

        # Use ALL known boosters from the network, not only when they are low
        boosters = bundle["boosters"]

        for t in targets:
            # Find the slot where the target ended up
            target_slot = None
            for slot, nutrients in plan.items():
                if t in nutrients:
                    target_slot = slot
                    break
            if not target_slot:
                continue

            # Try to co-locate boosters in the same slot
            for b in boosters:
                supp_b = marker_to_supplement(b)
                # don’t duplicate
                if supp_b in plan[target_slot]:
                    continue
                if can_place(supp_b, target_slot):
                    plan[target_slot].append(supp_b)
    return plan


def _pretty_nutrient(key: str) -> str:
    """
    Human-friendly label for nutrients/supplements.
    Prefer HUMAN_LABEL; fall back to title-cased key.
    """
    return HUMAN_LABEL.get(key, key.replace("_", " ").title())


def _slots_to_phrase(slots: Set[str]) -> str:
    slots = sorted(slots)
    if not slots:
        return ""
    if len(slots) == 1:
        return slots[0]
    if len(slots) == 2:
        return f"{slots[0]} and {slots[1]}"
    return ", ".join(slots[:-1]) + f", and {slots[-1]}"


def build_network_notes_for_plan(plan: Dict[str, List[str]]) -> List[str]:
    """
    Use network_relationships.csv to explain:
      - why some nutrients are co-dosed (effect == "boosts")
      - why some are separated into different time slots (effect == "inhibits")

    Logic:
      - For each "boosts" edge where both nodes appear in the same slot:
          → explain co-dosing using the `notes` column.
      - For each "inhibits" edge where both nodes appear in the plan
        BUT never share a slot:
          → explain separation using the `notes` column.
    """
    notes: List[str] = []

    if not EDGES.exists():
        return [
            "Supplement timing uses an internal nutrient interaction network, "
            "but the relationships file (network_relationships.csv) was not found."
        ]

    df = pd.read_csv(EDGES)
    if df.empty:
        return [
            "Supplement timing uses an internal nutrient interaction network, "
            "but no relationships were found in network_relationships.csv."
        ]

    # Normalize effect strings
    df["effect_norm"] = df["effect"].astype(str).str.lower().str.strip()

    # --- 1) Build slot → nutrients and nutrient → slots maps (from the plan) ---
    slot_to_nutrients: Dict[str, Set[str]] = {}
    nutrient_to_slots: Dict[str, Set[str]] = {}

    for slot, items in plan.items():
        norm_slot = str(slot).strip()
        nutrients_here: Set[str] = set()
        for raw in items:
            if not raw:
                continue
            key = str(raw).strip()
            nutrients_here.add(key)
            nutrient_to_slots.setdefault(key, set()).add(norm_slot)
        slot_to_nutrients[norm_slot] = nutrients_here

    # For quick membership
    all_plan_nutrients = set(nutrient_to_slots.keys())

    # Helper to avoid duplicate notes
    seen_notes = set()

    # --- 2) Co-dosed boosters: effect == "boosts", same slot ---
    mask_boosts = df["effect_norm"] == "boosts"
    for _, row in df.loc[mask_boosts].iterrows():
        src_raw = row["source"]
        tgt_raw = row["target"]
        edge_notes = str(row.get("notes", "")).strip()
        confidence = str(row.get("confidence", "")).strip()

        src_key = _network_node_to_plan_key(src_raw)
        tgt_key = _network_node_to_plan_key(tgt_raw)

        if src_key == tgt_key:
            continue

        # Only care if both show up in the plan
        if src_key not in all_plan_nutrients or tgt_key not in all_plan_nutrients:
            continue

        for slot, nutrients in slot_to_nutrients.items():
            if src_key in nutrients and tgt_key in nutrients:
                pretty_src = _pretty_nutrient(src_key)
                pretty_tgt = _pretty_nutrient(tgt_key)
                snippet = edge_notes or f"{pretty_src} helps the effectiveness of {pretty_tgt}."
                suffix = f" (evidence: {confidence})" if confidence else ""

                key = ("boost", slot, tuple(sorted([src_key, tgt_key])))
                if key in seen_notes:
                    continue
                seen_notes.add(key)

                notes.append(
                    f"{pretty_src} and {pretty_tgt} are scheduled together in the {slot} slot because {snippet}{suffix}."
                )

    # --- 3) Separated antagonists: effect == "inhibits", different slots ---
    mask_inhibits = df["effect_norm"] == "inhibits"
    for _, row in df.loc[mask_inhibits].iterrows():
        src_raw = row["source"]
        tgt_raw = row["target"]
        edge_notes = str(row.get("notes", "")).strip()
        confidence = str(row.get("confidence", "")).strip()

        src_key = _network_node_to_plan_key(src_raw)
        tgt_key = _network_node_to_plan_key(tgt_raw)

        if src_key not in all_plan_nutrients or tgt_key not in all_plan_nutrients:
            continue

        slots_src = nutrient_to_slots.get(src_key, set())
        slots_tgt = nutrient_to_slots.get(tgt_key, set())

        # If there is ANY overlapping slot, we are *not* separating them.
        if not slots_src or not slots_tgt or not slots_src.isdisjoint(slots_tgt):
            continue

        pretty_src = _pretty_nutrient(src_key)
        pretty_tgt = _pretty_nutrient(tgt_key)
        snippet = edge_notes or f"{pretty_tgt} can reduce the absorption or effect of {pretty_src} when taken together."
        suffix = f" (evidence: {confidence})" if confidence else ""

        src_phrase = _slots_to_phrase(slots_src)
        tgt_phrase = _slots_to_phrase(slots_tgt)

        key = ("inhibit", tuple(sorted([src_key, tgt_key])))
        if key in seen_notes:
            continue
        seen_notes.add(key)

        notes.append(
            f"{pretty_src} is kept in the {src_phrase} slot and {pretty_tgt} in the {tgt_phrase} slot to avoid interaction: {snippet}{suffix}."
        )

    if not notes:
        notes.append(
            "Supplement timing groups compatible nutrients and separates antagonistic ones "
            "based on the nutrient interaction network (network_relationships.csv)."
        )

    return notes


# -------------------------------------------------------------------
# 4. Food suggestions (using foods_usda.csv)
# -------------------------------------------------------------------

def load_food_data(path: Path) -> pd.DataFrame:
    """
    Load curated USDA-based food data.

    Expected columns in foods_usda.csv:
    - Food: human-readable food name (e.g. "Beef liver")
    - Category: broad food group (Meat, Legume, Vegetable, etc.)
    - Bundle: nutrient this food is a top source for
              (e.g. "iron", "vitamin_B12", "folate", "magnesium", ...)
    - Typical_serve_g: approximate grams per typical serving
    - Diet_tag: simple diet tag (vegan, omnivore, pescatarian/omnivore, ...)
    - FDC_ID, Description, DataType: metadata (not strictly required)
    """
    df = pd.read_csv(path)

    # Basic cleanup
    for col in ["Food", "Category", "Bundle"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    if "Diet_tag" in df.columns:
        df["Diet_tag"] = df["Diet_tag"].astype(str).str.strip()
    else:
        df["Diet_tag"] = ""

    return df


# Map lab markers -> base nutrient "bundle" used in foods_usda.csv
FOOD_BASE_MAP = {
    # Anemia cluster → iron bundle (single tab)
    "Hemoglobin": "iron",
    "MCV": "iron",
    "ferritin": "iron",
    "Serum ferritin": "iron",

    # One-to-one lab ↔ bundle
    "vitamin_B12": "vitamin_B12",
    "folate_plasma": "folate",
    "vitamin_D": "vitamin_D",
    "vitamin_C": "vitamin_C",
    "vitamin_E": "vitamin_E",
    "vitamin_A": "vitamin_A",
    "vitamin_B6": "vitamin_B6",
    "magnesium": "magnesium",
    "calcium": "calcium",
    "zinc": "zinc",

    # High homocysteine → treat as B12-driven
    "homocysteine": "vitamin_B12",
}


def suggest_foods(
    labels: Dict[str, str],
    food_df: pd.DataFrame,
    top_n: int = 5,
    diet_filter: Optional[str] = None,
) -> Dict[str, List[Tuple[str, float, str]]]:
    """
    For each flagged deficiency, return top foods using foods_usda.csv.

    - For most markers, we use "low" as the trigger.
    - For homocysteine, we use "high" as the trigger.
    - Anemia markers (Hemoglobin, MCV, ferritin, Serum ferritin)
      are all mapped into a single "iron" bundle → one iron foods tab.

    Returns:
        base_nutrient -> list of (Food, Typical_serve_g, Category)
    """
    out: Dict[str, List[Tuple[str, float, str]]] = {}

    # 1) Decide which base bundles we need food recs for
    base_needed: List[str] = []
    for marker, status in labels.items():
        if marker == "homocysteine":
            # only care when high
            if status != "high":
                continue
        else:
            # deficiencies only
            if status != "low":
                continue

        base = FOOD_BASE_MAP.get(marker)
        if not base:
            continue

        if base not in base_needed:
            base_needed.append(base)

    # 2) For each base bundle, pull top foods from foods_usda.csv
    for base in base_needed:
        sub = food_df[food_df["Bundle"] == base]

        if diet_filter:
            sub = sub[sub["Diet_tag"].str.contains(diet_filter, case=False, na=False)]

        if sub.empty:
            continue

        # Avoid repeating the same base food within a bundle
        # (e.g. multiple rows for "Beef liver" → keep one)
        sub = sub.drop_duplicates(subset=["Food"])

        # Keep the first top_n as curated in the CSV
        sub = sub.head(top_n)

        # Store: (Food name, typical serving grams, category)
        foods_list: List[Tuple[str, float, str]] = []
        for _, row in sub.iterrows():
            food_name = str(row.get("Food", "")).strip()
            category = str(row.get("Category", "")).strip()
            try:
                serving = float(row.get("Typical_serve_g", float("nan")))
            except Exception:
                serving = float("nan")
            foods_list.append((food_name, serving, category))

        if foods_list:
            out[base] = foods_list

    return out


# -------------------------------------------------------------------
# 5. Report generator
# -------------------------------------------------------------------

HUMAN_LABEL = {
    "Hemoglobin": "Hemoglobin",
    "MCV": "Mean corpuscular volume (MCV)",
    "ferritin": "Serum ferritin",

    # NEW: actual supplement we schedule for anemia markers
    "iron": "Iron",

    "vitamin_B12": "Vitamin B12",
    "folate_plasma": "Folic Acid",
    "folate": "Folate",
    "vitamin_D": "Vitamin D (25(OH)D)",
    "vitamin_C": "Vitamin C",
    "vitamin_E": "Vitamin E",
    "vitamin_A": "Vitamin A (retinol)",
    "vitamin_B6": "Vitamin B6 (PLP)",
    "magnesium": "Magnesium",
    "calcium": "Calcium",
    "zinc": "Zinc",
    "homocysteine": "Homocysteine",
}


def _format_lab_block(labs: Dict[str, float], labels: Dict[str, str]) -> str:
    lines = []
    for marker, val in labs.items():
        label = labels.get(marker, "unknown")
        pretty = HUMAN_LABEL.get(marker, marker)
        lines.append(f"- {pretty}: {val} → {label}")
    return "\n".join(lines)


def _format_supplement_block(plan: Dict[str, List[str]]) -> str:
    lines = []
    for slot in SLOTS:
        nutrients = plan.get(slot, [])
        if not nutrients:
            continue
        pretty_nutrients = [HUMAN_LABEL.get(n, n) for n in nutrients]
        lines.append(f"- {slot.capitalize()}: {', '.join(pretty_nutrients)}")
    if not lines:
        return "No supplements recommended based on current labs."
    return "\n".join(lines)


def _format_food_block(food_suggestions: Dict[str, List[Tuple[str, float, str]]]) -> str:
    if not food_suggestions:
        return "No specific food suggestions (no matching entries for the flagged deficiencies)."

    chunks: List[str] = []
    for key, foods in food_suggestions.items():
        if not foods:
            continue

        header = HUMAN_LABEL.get(key, key)
        lines = [f"{header} – suggested food sources:"]

        for name, serving_g, cat in foods:
            cat_str = f" [{cat}]" if cat else ""
            if isinstance(serving_g, float) and math.isnan(serving_g):
                amount_str = ""
            else:
                amount_str = f" – typical serving ~{serving_g:g} g"

            lines.append(f"  • {name}{cat_str}{amount_str}")

        chunks.append("\n".join(lines))

    return "\n\n".join(chunks)


def generate_report(
    labs: Dict[str, float],
    patient: PatientInfo,
    food_path: Optional[Path] = FOOD_CSV_DEFAULT,
) -> str:
    """
    Main entry point.

    labs: dict of marker -> numeric value (e.g., {"Hemoglobin": 11.2, "ferritin": 8.0, ...})
    patient: PatientInfo dataclass
    food_path: path to food CSV for food suggestions (Path or str or None)
    """
    # 1. Classify labs
    labels = classify_panel(labs)

    # 2. Build supplement schedule
    plan = build_supplement_plan(labels)

    # 3. Load food data & suggest foods for low markers
    food_df = None
    if food_path:
        # allow both str and Path
        if isinstance(food_path, (str, bytes)):
            food_path = Path(food_path)
        if isinstance(food_path, Path) and food_path.exists():
            food_df = load_food_data(food_path)

    food_suggestions = {}
    if food_df is not None:
        food_suggestions = suggest_foods(labels, food_df)

    # 4. Network-based explanations (optional)
    if G_NETWORK is not None:
        low_set = low_items(labels)
        multihop = multihop_explanations(G_NETWORK, low_set, max_hops=2)
        if multihop:
            lines = []
            for tgt, chains in multihop.items():
                pretty_tgt = HUMAN_LABEL.get(tgt, tgt)
                lines.append(f"{pretty_tgt}:")
                for ch in chains[:3]:  # show at most 3 chains per target
                    lines.append(f"  • {ch}")
            network_block = "\n".join(lines)
        else:
            network_block = "No network-based causal chains found for the flagged deficiencies."
    else:
        network_block = "Nutrient interaction network not available (missing file or networkx)."

    # 5. Build narrative report
    header = [
        "HemoVita – Personalized Micronutrient Report",
        "===========================================",
        "",
        "Patient summary:",
        f"- Age: {patient.age if patient.age is not None else 'N/A'}",
        f"- Sex: {patient.sex or 'N/A'}",
        f"- Pregnant: {patient.pregnant if patient.pregnant is not None else 'N/A'}",
        f"- Country: {patient.country or 'N/A'}",
    ]
    if patient.notes:
        header.append(f"- Notes: {patient.notes}")

    labs_block = _format_lab_block(labs, labels)
    supp_block = _format_supplement_block(plan)
    food_block = _format_food_block(food_suggestions)

    report_parts = [
        "\n".join(header),
        "",
        "1. Lab overview",
        "---------------",
        labs_block or "No labs provided.",
        "",
        "2. Supplement plan (prototype)",
        "------------------------------",
        supp_block,
        "",
        "3. Food suggestions (per 100 g, highest nutrient density first)",
        "----------------------------------------------------------------",
        food_block,
        "",
        "4. Notes on cutoffs",
        "--------------------",
        "All low/normal/high classifications are derived from a unified cutoff table ",
        "(`micronutrient_cutoffs_structured.csv`) built from WHO guidelines, IZiNCG ",
        "zinc thresholds, and widely used clinical consensus cutoffs. This table can ",
        "be updated independently of the code to reflect new evidence.",
        "",
        "5. Network-based nutrient interactions",
        "--------------------------------------",
        network_block,
    ]

    return "\n".join(report_parts)
