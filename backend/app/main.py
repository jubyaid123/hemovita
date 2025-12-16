# backend/app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .schema import (
    ReportRequest,
    ReportResponse,
    FoodItem,
    RiskProfileInput,
)
from .engine import (
    PatientInfo,
    classify_panel,
    build_supplement_plan,
    load_food_data,
    suggest_foods,
    generate_report,
    FOOD_CSV_DEFAULT,
    build_network_notes_for_plan,
)
from . import risk  # risk.py lives in app/engine

app = FastAPI(title="HemoVita API", version="0.1.0")

# CORS so localhost:3000 can talk to localhost:8000
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # you can restrict later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------------------------------------------------
# 1) Standalone risk endpoint (useful for testing/debugging)
# -------------------------------------------------------------------
@app.post("/api/risk-profile")
async def micronutrient_risk_route(profile: RiskProfileInput):
    """
    Given age/sex/country/population, return the raw risk model output
    (bandit + fallback baselines).
    """
    result = risk.get_micronutrient_risk_profile(profile.dict())
    return result


# -------------------------------------------------------------------
# 2) Main report endpoint used by the frontend proxy (/api/report)
# -------------------------------------------------------------------
@app.post("/api/report", response_model=ReportResponse)
def api_report(payload: ReportRequest):
    # -----------------------
    # 1) Build patient object
    # -----------------------
    patient = PatientInfo(
        age=payload.patient.age,
        sex=payload.patient.sex,
        pregnant=payload.patient.pregnant,
        country=payload.patient.country,
        notes=payload.patient.notes,
    )

    # -----------------------
    # 2) Generate narrative report text
    # -----------------------
    report_text = generate_report(
        payload.labs,
        patient,
        FOOD_CSV_DEFAULT,
    )

    # -----------------------
    # 3) Structured extras (labels, supplement plan, foods)
    # -----------------------
    labels = classify_panel(payload.labs)
    supp_plan = build_supplement_plan(labels)

    foods: dict[str, list[FoodItem]] = {}
    if FOOD_CSV_DEFAULT.exists():
        food_df = load_food_data(FOOD_CSV_DEFAULT)
        # wire in diet_filter if you want to use it
        foods_raw = suggest_foods(
            labels,
            food_df,
            top_n=5,
            diet_filter=payload.diet_filter,
        )
        for key, lst in foods_raw.items():
            foods[key] = [
                FoodItem(name=name, serving_g=serv_g, category=cat)
                for (name, serv_g, cat) in lst
            ]

    # -----------------------
    # 4) Dynamic network notes from core.py (no hardcoding)
    # -----------------------
    network_notes = build_network_notes_for_plan(supp_plan)

    # -----------------------
    # 5) Risk profile (uses risk.get_micronutrient_risk_profile)
    # -----------------------

    risk_profile = None
    micronutrient_risks = None
    risk_summary_text = None

    try:
        sex_lower = (patient.sex or "").lower()
        if sex_lower == "female":
            default_population = "Pregnant women" if patient.pregnant else "Women"
            gender = "Female"
        elif sex_lower == "male":
            default_population = "Men"
            gender = "Male"
        else:
            default_population = "Adults"
            gender = "All"

        # 🟢 Prefer explicit population from the UI if provided
        explicit_population = payload.patient.population
        population = explicit_population or default_population

        rp_input = {
            "country": patient.country or "",
            "population": population,
            "gender": gender,
            "age": patient.age,
        }

        raw = risk.get_micronutrient_risk_profile(rp_input)
        micronutrient_risks = raw.get("micronutrient_risks", [])
        summary_text = raw.get("summary_text", "")
        disclaimer = raw.get("disclaimer", "")
        meta = raw.get("meta", {})

        if micronutrient_risks:
            overall_risk = max(m["predicted_risk"] for m in micronutrient_risks)
        else:
            overall_risk = 0.0

        if overall_risk < 0.33:
            bucket = "low"
        elif overall_risk < 0.66:
            bucket = "moderate"
        else:
            bucket = "high"

        high_risk = [
            m for m in micronutrient_risks
            if m["predicted_risk"] >= 0.66
        ]

        if disclaimer:
            risk_summary_text = summary_text + " " + disclaimer
        else:
            risk_summary_text = summary_text

        risk_profile = {
            "overall_risk": overall_risk,
            "risk_bucket": bucket,
            "high_risk_micronutrients": high_risk,
            "micronutrient_risks": micronutrient_risks,
            "summary_text": summary_text,
            "meta": meta,
        }

    except Exception as e:
        print("Risk model failed:", e)
        risk_profile = None
        micronutrient_risks = None
        risk_summary_text = None


    # -----------------------
    # 6) Final response
    # -----------------------
    return ReportResponse(
        labels=labels,
        supplement_plan=supp_plan,
        foods=foods,
        network_notes=network_notes,
        report_text=report_text,
        micronutrient_risks=micronutrient_risks,
        risk_summary_text=risk_summary_text,
        risk_profile=risk_profile,
    )


# # backend/app/main.py

# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware

# from .schema import (
#     ReportRequest,
#     ReportResponse,
#     FoodItem,
    
# )
# from .engine import (
#     PatientInfo,
#     classify_panel,
#     build_supplement_plan,
#     load_food_data,
#     suggest_foods,
#     generate_report,
#     FOOD_CSV_DEFAULT,
# )
# from . import risk  # module with get_micronutrient_risk_profile

# app = FastAPI(title="HemoVita API", version="0.1.0")

# # CORS so localhost:3000 can talk to localhost:8000
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # you can restrict later
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


# # -------------------------------------------------------------------
# # 1) Standalone risk endpoint (optional)
# # -------------------------------------------------------------------
# # @app.post("/api/risk-profile")
# # async def micronutrient_risk_route(profile: RiskProfileInput):
# #     """
# #     Optional endpoint: given age/sex/country/population, returns
# #     the raw risk model output.
# #     """
# #     result = risk.get_micronutrient_risk_profile(profile.dict())
# #     return result


# # -------------------------------------------------------------------
# # 2) Main report endpoint used by the frontend proxy (/api/report)
# # -------------------------------------------------------------------
# @app.post("/api/report", response_model=ReportResponse)
# def api_report(payload: ReportRequest):
#     # -----------------------
#     # 1) Build patient object
#     # -----------------------
#     patient = PatientInfo(
#         age=payload.patient.age,
#         sex=payload.patient.sex,
#         pregnant=payload.patient.pregnant,
#         country=payload.patient.country,
#         notes=payload.patient.notes,
#     )

#     # -----------------------
#     # 2) Generate narrative report
#     # -----------------------
#     report_text = generate_report(
#         payload.labs,
#         patient,
#         FOOD_CSV_DEFAULT,
#     )

#     # -----------------------
#     # 3) Structured extras
#     # -----------------------
#     labels = classify_panel(payload.labs)
#     supp_plan = build_supplement_plan(labels)

#     foods: dict[str, list[FoodItem]] = {}
#     if FOOD_CSV_DEFAULT.exists():
#         food_df = load_food_data(FOOD_CSV_DEFAULT)
#         foods_raw = suggest_foods(labels, food_df, top_n=5)
#         for key, lst in foods_raw.items():
#             foods[key] = [
#                 FoodItem(name=name, serving_g=serv_g, category=cat)
#                 for (name, serv_g, cat) in lst
#             ]

#     network_notes = [
#         "Iron is scheduled away from calcium/zinc based on the nutrient interaction network.",
#         "Vitamin C / D are co-dosed with iron when possible to boost absorption.",
#     ]

#     # -----------------------
#     # 4) Risk profile
#     # -----------------------
#     risk_profile = None
#     try:
#         sex_lower = (patient.sex or "").lower()
#         if sex_lower == "female":
#             population = "Pregnant women" if patient.pregnant else "Women"
#             gender = "Female"
#         elif sex_lower == "male":
#             population = "Men"
#             gender = "Male"
#         else:
#             population = "All"
#             gender = "All"

#         rp_input = {
#             "country": patient.country or "",
#             "population": population,
#             "gender": gender,
#             "age": patient.age,
#         }

#         raw = risk.get_micronutrient_risk_profile(rp_input)
#         micronutrient_risks = raw.get("micronutrient_risks", [])
#         meta = raw.get("meta", {})
#         summary_text = raw.get("summary_text", "")

#         if micronutrient_risks:
#             overall_risk = max(m["predicted_risk"] for m in micronutrient_risks)
#         else:
#             overall_risk = 0.0

#         if overall_risk < 0.33:
#             bucket = "low"
#         elif overall_risk < 0.66:
#             bucket = "moderate"
#         else:
#             bucket = "high"

#         high_risk = [m for m in micronutrient_risks if m["predicted_risk"] >= 0.66]

#         risk_profile = {
#             "overall_risk": overall_risk,
#             "risk_bucket": bucket,
#             "high_risk_micronutrients": high_risk,
#             "micronutrient_risks": micronutrient_risks,
#             "summary_text": summary_text,
#             "meta": meta,
#         }
#     except Exception as e:
#         print("Risk model failed:", e)
#         risk_profile = None

#     # -----------------------
#     # 5) Final response
#     # -----------------------
#     return ReportResponse(
#         labels=labels,
#         supplement_plan=supp_plan,  # ✅ use the real variable name
#         foods=foods,
#         network_notes=network_notes,
#         report_text=report_text,
#         risk_profile=risk_profile,
#     )
