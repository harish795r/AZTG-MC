import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, classification_report

os.makedirs("models", exist_ok=True)
os.makedirs("paper", exist_ok=True)

print("=" * 75)
print("  AZTG-MC: Machine Learning Engine Training on Deep Multi-Cloud Data")
print("=" * 75)

# 1. Load the Deep Telemetry Dataset
dataset_path = "data/normalized/aztg_mc_deep_telemetry.csv"
df = pd.read_csv(dataset_path)
print(f"\n[+] Loaded Dataset: {dataset_path}")
print(f"    • Total Samples (Rows)   : {len(df):,}")
print(f"    • Total Columns Available: {df.shape[1]}")

# 2. Select Features for ML (Multi-Dimensional Feature Vector)
feature_cols = [
    "permission_utilization",
    "api_call_frequency",
    "latency_ms",
    "response_bytes",
    "entropy_score",
    "privilege_cardinality",
    "service_diversity_count",
    "hour_of_day",
    "day_of_week",
    "is_off_hours",
    "is_weekend",
    "is_ip_anomaly",
    "http_status"
]

# Convert categorical to numeric
df["is_aws"] = (df["cloud_provider"] == "AWS").astype(int)
feature_cols.append("is_aws")

X = df[feature_cols]
y = df["target_class"]

print(f"\n[+] Feature Matrix Built: {X.shape[1]} engineered features across {len(X):,} samples.")
print(f"    Features: {', '.join(feature_cols)}")

# 3. 80/20 Stratified Train-Test Split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, random_state=42, stratify=y
)
print(f"\n[+] Train Set: {len(X_train)} rows | Test Set: {len(X_test)} rows")

# 4. Train Models
print("\n[+] Training Classification Models...")

# Model 1: Random Forest
rf = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=42)
rf.fit(X_train, y_train)
rf_pred = rf.predict(X_test)

# Model 2: XGBoost (Proposed Primary)
xgb = XGBClassifier(n_estimators=100, max_depth=6, learning_rate=0.1, random_state=42, verbosity=0)
xgb.fit(X_train, y_train)
xgb_pred = xgb.predict(X_test)

# Model 3: Static Rule Baseline
st_pred = np.where(X_test["permission_utilization"] < 0.15, 2, np.where(X_test["permission_utilization"] < 0.45, 1, 0))

# 5. Evaluate Performance (Table I for Paper)
print("\n" + "=" * 75)
print(f"{'Model Architecture':<26} | {'Accuracy':<8} | {'Precision':<9} | {'Recall':<7} | {'F1-Score'}")
print("-" * 75)
for name, pred in [("Static Rule Baseline", st_pred), ("Random Forest", rf_pred), ("XGBoost (AZTG-MC)", xgb_pred)]:
    acc = accuracy_score(y_test, pred)
    prec = precision_score(y_test, pred, average="weighted")
    rec = recall_score(y_test, pred, average="weighted")
    f1 = f1_score(y_test, pred, average="weighted")
    print(f"{name:<26} | {acc:<8.4f} | {prec:<9.4f} | {rec:<7.4f} | {f1:.4f}")
print("=" * 75)

# 6. 5-Fold Cross Validation
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
rf_cv = cross_val_score(rf, X, y, cv=skf, scoring="f1_weighted")
xgb_cv = cross_val_score(xgb, X, y, cv=skf, scoring="f1_weighted")
print(f"\n[+] 5-Fold Cross-Validation (Weighted F1):")
print(f"    • Random Forest : {rf_cv.mean():.4f} (± {rf_cv.std():.4f})")
print(f"    • XGBoost       : {xgb_cv.mean():.4f} (± {xgb_cv.std():.4f})")

# 7. Generate Feature Importance Plot (Figure 2 for Paper)
importance = pd.DataFrame({
    "Feature": feature_cols,
    "Importance": xgb.feature_importances_
}).sort_values(by="Importance", ascending=False)

plt.figure(figsize=(9, 5))
sns.barplot(data=importance, x="Importance", y="Feature", palette="Blues_r")
plt.title("AZTG-MC: XGBoost Feature Importance Breakdown", fontsize=12, fontweight="bold")
plt.xlabel("Relative Importance Weight", fontsize=10)
plt.ylabel("Engineered Telemetry Feature", fontsize=10)
plt.tight_layout()
fig_path = "paper/feature_importance.png"
plt.savefig(fig_path, dpi=300)
print(f"\n[+] High-Resolution Plot Saved: {fig_path}")

# 8. Confusion Matrix Plot
cm = confusion_matrix(y_test, xgb_pred)
plt.figure(figsize=(6, 5))
sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=["Reader (0)", "Contrib (1)", "Owner (2)"], yticklabels=["Reader (0)", "Contrib (1)", "Owner (2)"])
plt.title("XGBoost Confusion Matrix", fontsize=11, fontweight="bold")
plt.xlabel("Predicted Class")
plt.ylabel("True Class")
plt.tight_layout()
cm_path = "paper/confusion_matrix.png"
plt.savefig(cm_path, dpi=300)
print(f"[+] Confusion Matrix Saved    : {cm_path}")

print("\n" + "=" * 75)
print("🎉 Model Training Complete! All figures & tables ready for submission.")
print("=" * 75)
