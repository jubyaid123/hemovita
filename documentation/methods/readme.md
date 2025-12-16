# Evaluation Metrics for HemoVita AI

## Overview
The **Evaluation Metrics** subtask focuses on selecting and analyzing performance metrics to assess the effectiveness of machine learning models in detecting nutrient deficiencies from bloodwork data. Proper evaluation ensures that the model is **accurate, interpretable, and clinically reliable**, which is crucial for making **personalized supplement recommendations**.

## Existing Technologies and Methodologies

Different types of evaluation metrics are used based on the **model type and prediction task**. Below are three key categories:

### 1. **Classification Metrics** (For Deficiency Detection)
- **Accuracy**: Measures the overall correctness of the model.
- **Precision & Recall (Sensitivity/Specificity)**: Evaluates how well deficiencies are identified without misclassifications.
- **F1 Score**: Balances precision and recall, useful for imbalanced datasets.
- **AUROC (Area Under the Receiver Operating Characteristic Curve)**: Measures the ability to distinguish between deficient and non-deficient cases.


**References:**
- Sokolova, M., & Lapalme, G. (2009). *A systematic analysis of performance measures for classification tasks*. Information Processing & Management. [DOI:10.1016/j.ipm.2009.03.002](https://doi.org/10.1016/j.ipm.2009.03.002)

---

### 2. **Regression Metrics** (For Continuous Nutrient Level Predictions)
- **Mean Absolute Error (MAE)**: Measures average deviation between predicted and actual values.
- **Mean Squared Error (MSE) & Root Mean Squared Error (RMSE)**: Penalizes larger errors more heavily.
- **R² Score (Coefficient of Determination)**: Measures how well the model explains variance in blood nutrient levels.


**References:**
- Willmott, C. J., & Matsuura, K. (2005). *Advantages of the mean absolute error (MAE) over the root mean square error (RMSE) in assessing average model performance*. Climate Research. [DOI:10.3354/cr010079](https://doi.org/10.3354/cr010079)

---

### 3. **Explainability & Trust Metrics** (For Clinical Reliability)
- **SHAP (Shapley Additive Explanations)**: Interprets individual model predictions.
- **LIME (Local Interpretable Model-Agnostic Explanations)**: Provides local feature importance.
- **Calibration Metrics (Brier Score, Reliability Diagrams)**: Ensures the model’s confidence matches reality.


**References:**
- Ribeiro, M. T., Singh, S., & Guestrin, C. (2016). *"Why Should I Trust You?" Explaining the Predictions of Any Classifier*. Proceedings of the 22nd ACM SIGKDD. [DOI:10.1145/2939672.2939778](https://doi.org/10.1145/2939672.2939778)

---

## Sources

### Public Datasets:
1. **Vitamin and Mineral Nutrition Information System (WHO)** - Global micronutrient deficiencies data: [Link](https://www.who.int/data)
2. **MIMIC-III Clinical Database** - Real-world electronic health records: [Link](https://physionet.org/content/mimic3/)
3. **Blood Chemistry Dataset (Kaggle)** - Blood test records for AI model evaluation: [Link](https://www.kaggle.com/datasets)

---

## Evaluation of Existing Solutions

### Effectiveness of Existing Approaches:
- **Standard Classification & Regression Metrics:** Effective for basic performance assessment but may not capture medical relevance.
- **SHAP & LIME for Explainability:** Useful but require integration into clinical workflows.
- **Calibration Metrics:** Improve trust but are often overlooked in AI-driven diagnostics.

### Limitations & Potential Improvements:
- **Medical Context Awareness:** Many existing metrics do not account for **clinical impact** (e.g., missing a critical deficiency).
- **Handling Imbalanced Data:** Precision/Recall tradeoffs need to be optimized for rare deficiencies.

### Proposed Enhancements:
- **Clinical Impact-Driven Metrics:** Develop metrics incorporating **medical risks** of false positives/negatives.
- **Hybrid Model Evaluation:** Combine **traditional ML metrics + calibration + explainability tools**.


