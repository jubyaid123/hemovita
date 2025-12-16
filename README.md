# HemoVita – AI-driven Micronutrient Guidance

HemoVita turns lab results into clear deficiency flags and follow-up suggestions. It pairs a Next.js app for data entry and visualization with a small Python toolkit for exploring nutrient interaction graphs.
---

## 💡 Why HemoVita?  
Micronutrient deficiencies—especially in Iron, B12, and Vitamin D—are common, underdiagnosed, and difficult for non-experts to interpret. HemoVita transforms raw blood test data into clear, personalized health recommendations using AI.  

Built for accessibility, HemoVita empowers users to understand their nutrient status and take action—without needing a clinician to decode lab reports.  

---

## 👩‍💻 Meet the Team  
**Project Manager & Developer** – *Selma Doganata*  
📧 sdogana000@citymail.cuny.edu  
Oversees technical development and system design.

**Machine Learning Engineer** – *Jubyaid Uddin*  
📧 juddin002@citymail.cuny.edu  
Develops ML models for nutrient deficiency classification and interpretability.

**Researcher & Data Analyst** – *Rahat Rahman*  
📧 rrahman008@citymail.cuny.edu  
Curates datasets, establishes clinical thresholds, and supports validation.

---
## What’s inside
- Lab intake & validation: guided form with unit hints and Zod validation for iron, B12, vitamin D, and other key markers.
- Rule-based recommendations: `/api/recommend` classifies each marker against reference ranges and returns a prioritized follow-up schedule.
- Nutrient interaction network: `/api/network/graph` builds a force-directed graph from `cleaned_data/network_relationships.csv` and `Hemovita_Micronutrients.xlsx`; rendered in the 3D graph view.
- Auth + storage: credential-based NextAuth with Prisma + SQLite; password hashing via bcrypt.
- Python utilities: reusable loader for the nutrient graph (`network/hemovita_network_loader.py`) and a demo query script.

## 🔬 Scientific Foundation  
Deficiencies are detected using a hybrid method:  

- **Rule-Based Thresholding**  
  - *Iron*: Ferritin < 30 µg/L, MCV < 80 fL  
  - *B12*: B12 < 200 ng/L  
  - *Vitamin D*: 25-OH Vit D < 20 ng/mL  

- **Machine Learning Classification**  
  - Triggered for overlapping or borderline cases using tabular lab data and XGBoost.

---
## Repository layout
- `frontend/` – Next.js 14 app (App Router), UI components, API routes, Prisma schema.
- `cleaned_data/` – micronutrient reference workbook and edge list CSV used by the graph API.
- `network/` – Python graph loader, demo script, and saved XGBoost JSON.
- `code/` – notebooks (EDA, feature engineering, reproduction), model/method notes, deployment stubs.
- `documentation/` – project write-ups (methods, data sources, references).
- `data_visuals/` – network visuals and notebooks.
- `references/` – paper summaries and source texts.


## 🔄 System Pipeline  

1. **Data Upload & Extraction**  
   Users submit PDFs or CSVs of blood tests. The system uses structured parsing and, soon, OCR to extract lab values such as Ferritin, MCV, RDW, B12, and Vitamin D.

2. **Preprocessing & Normalization**  
   Extracted values are cleaned, converted to standard units, and mapped to expected input formats. Missing data is handled via imputation or flagged for user review.

3. **Deficiency Detection**  
   A hybrid approach is applied:  
   - **Threshold-based rules** identify deficiencies in clear cases.  
   - **XGBoost classifier** is used for nuanced or conflicting signals, combining features like RDW, MCV, and B12.

4. **Nutrient Interaction Modeling**  
   Once a deficiency is detected, the system evaluates nutrient interdependencies using a **knowledge graph** derived from clinical literature (e.g., Iron-B12 synergy, B12–Folate overlap).  
   This modeling ensures:  
   - No redundant supplementation  
   - Improved recommendations when multiple deficiencies co-occur

5. **Recommendation Engine**  
   Personalized supplement suggestions are generated based on the detected deficiencies and their interactions. Outputs are filtered through dosage safety checks and linked to common clinical guidelines.

6. **Interpretability & Transparency**  
   With SHAP values, users can see which biomarkers contributed most to the model’s decision—making results understandable and trustworthy.

7. **Results Interface** *(in development)*  
   A clean dashboard will visualize current results, previous uploads, and improvement over time—powered by Streamlit or Power BI.

---

## 🛠️ Tech Stack  

## Backend (Python + data assets)
- Graph loader: `network/hemovita_network_loader.py` validates `cleaned_data/network_relationships.csv` against `Hemovita_Micronutrients.xlsx`, builds a directed graph with attributes (effect, confidence, notes), and offers path queries.
- Demo script: `network/demo_load_and_query.py` is a quick sanity check—loads the graph, prints a summary, and runs sample path queries (requires `pandas` and `networkx`).
- Model artifacts: `network/hemovita_xgb.json` (saved XGBoost) and evaluation notebooks in `code/` support future API integration.
- Data files: `cleaned_data/` holds the authoritative CSV/XLSX; `data_visuals/network/*.json|csv` contains derived interaction files for plotting.
- Future API stub: `code/deployment/fastapi_server.py` is currently empty; intended for a FastAPI service that would expose model inference and network queries.

### Frontend  
- **Next.js** – Web framework  
- **Tailwind CSS** – Styling  
- **Axios** – API calls
## Frontend setup (Next.js)
1) `cd frontend`
2) Copy env: `cp .env.example .env` and set `NEXTAUTH_SECRET`; adjust `NEXTAUTH_URL` if not `http://localhost:3000`.
3) Install: `npm install`
4) Prisma client + schema: `npm run prisma:generate && npm run prisma:push` (uses SQLite at `DATABASE_URL`).
5) Dev server: `npm run dev` (defaults to `http://localhost:3000`).

### Database  
- **SQLite** (initial) → **PostgreSQL** (scalable)

