# backend/app/schema.py
from typing import Dict, List, Optional
from pydantic import BaseModel
from typing_extensions import Literal

class PatientPayload(BaseModel):
    age: int
    sex: Literal["female", "male"]
    country: Optional[str] = None
    notes: Optional[str] = None
    pregnant: Optional[bool] = None
    # OPTIONAL: if you want population from the UI
    population: Optional[str] = None


class ReportRequest(BaseModel):
    labs: Dict[str, float]
    patient: PatientPayload
    diet_filter: Optional[str] = None


class FoodItem(BaseModel):
    name: str
    serving_g: Optional[float] = None
    category: Optional[str] = None


class RiskMicronutrient(BaseModel):
    micronutrient: str
    predicted_risk: float  # 0–1


class RiskMeta(BaseModel):
    country: Optional[str] = None
    population: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[float] = None

    # optional extra fields from risk.py
    country_known: Optional[bool] = None
    fallback_used: Optional[bool] = None
    fallback_level: Optional[str] = None


class RiskProfile(BaseModel):
    overall_risk: float
    risk_bucket: Literal["low", "moderate", "high"]
    high_risk_micronutrients: List[RiskMicronutrient]
    micronutrient_risks: List[RiskMicronutrient]
    summary_text: str
    meta: RiskMeta


class ReportResponse(BaseModel):
    labels: Dict[str, str]
    supplement_plan: Dict[str, List[str]]
    foods: Dict[str, List[FoodItem]]
    network_notes: List[str]
    report_text: str

    # risk stuff
    risk_profile: Optional[RiskProfile] = None
    micronutrient_risks: Optional[List[Dict]] = None
    risk_summary_text: Optional[str] = None


class RiskProfileInput(BaseModel):
    country: str
    population: str
    gender: str
    age: float

# from typing import Dict, List, Optional
# from pydantic import BaseModel, Field
# from typing_extensions import Literal

# class PatientPayload(BaseModel):
#     age: int
#     sex: str
#     country: Optional[str] = None
#     notes: Optional[str] = None
#     pregnant: Optional[bool] = None


# class ReportRequest(BaseModel):
#     labs: Dict[str, float]
#     patient: PatientPayload
#     diet_filter: Optional[str] = None  # you can wire this into suggest_foods later


# class FoodItem(BaseModel):
#     name: str
#     serving_g: Optional[float] = None
#     category: Optional[str] = None


# class RiskMicronutrient(BaseModel):
#     micronutrient: str
#     predicted_risk: float  # 0–1


# class RiskMeta(BaseModel):
#     country: Optional[str] = None
#     population: Optional[str] = None
#     gender: Optional[str] = None
#     age: Optional[float] = None


# class RiskProfile(BaseModel):
#     overall_risk: float
#     risk_bucket: str  # "low" | "moderate" | "high"
#     high_risk_micronutrients: List[RiskMicronutrient]
#     micronutrient_risks: List[RiskMicronutrient]
#     summary_text: str
#     meta: RiskMeta


# class ReportResponse(BaseModel):
#     labels: Dict[str, str]
#     supplement_plan: Dict[str, List[str]]
#     foods: Dict[str, List[FoodItem]]
#     network_notes: List[str]
#     report_text: str

#     # NEW: optional field for demographics-based risk
#     risk_profile: Optional[RiskProfile] = None