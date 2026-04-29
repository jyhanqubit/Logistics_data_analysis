from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score


def run_classification_analysis(feature_df: pd.DataFrame, out_dir: Path) -> dict[str, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    df = feature_df.sort_values("date_key").copy()

    threshold = df["inbound_volume"].quantile(0.9)
    df["peak_demand_risk"] = (df["inbound_volume"] >= threshold).astype(int)
    df["stockout_risk"] = (df["inbound_volume"] > (df.get("rolling_mean_28", 0) + df.get("rolling_std_14", 0))).astype(int)
    df["late_delivery_risk"] = (df.get("demand_spike_score", 0) > 1.0).astype(int)

    X = df[[c for c in df.columns if np.issubdtype(df[c].dtype, np.number) and c not in {"peak_demand_risk", "stockout_risk", "late_delivery_risk"}]].fillna(0)
    cut = int(len(df) * 0.8)
    X_train, X_test = X.iloc[:cut], X.iloc[cut:]

    tasks = ["peak_demand_risk", "stockout_risk", "late_delivery_risk"]
    models = {
        "LogisticRegression": LogisticRegression(max_iter=300),
        "RandomForestClassifier": RandomForestClassifier(n_estimators=120, random_state=42),
        "GradientBoostingClassifier": GradientBoostingClassifier(random_state=42),
        "HistGradientBoostingClassifier": HistGradientBoostingClassifier(random_state=42),
    }

    metric_rows: list[dict] = []
    pred_rows: list[dict] = []
    cm_rows: list[dict] = []
    fi_rows: list[dict] = []

    for task in tasks:
        y = df[task]
        y_train, y_test = y.iloc[:cut], y.iloc[cut:]
        for name, model in models.items():
            model.fit(X_train, y_train)
            pred = model.predict(X_test)
            prob = model.predict_proba(X_test)[:, 1] if hasattr(model, "predict_proba") else pred.astype(float)
            metric_rows.append(
                {
                    "task": task,
                    "model": name,
                    "accuracy": accuracy_score(y_test, pred),
                    "precision": precision_score(y_test, pred, zero_division=0),
                    "recall": recall_score(y_test, pred, zero_division=0),
                    "f1": f1_score(y_test, pred, zero_division=0),
                    "roc_auc": roc_auc_score(y_test, prob) if len(np.unique(y_test)) > 1 else np.nan,
                    "pr_auc": np.nan,
                    "positive_rate": float(np.mean(pred)),
                }
            )
            tn, fp, fn, tp = confusion_matrix(y_test, pred, labels=[0, 1]).ravel()
            cm_rows.append({"task": task, "model": name, "tn": tn, "fp": fp, "fn": fn, "tp": tp})

            for i, idx in enumerate(X_test.index[:200]):
                pred_rows.append({"task": task, "model": name, "index": int(idx), "y_true": int(y_test.loc[idx]), "y_pred": int(pred[i]), "prob": float(prob[i])})

            if hasattr(model, "feature_importances_"):
                imp = model.feature_importances_
            elif hasattr(model, "coef_"):
                imp = np.abs(np.ravel(model.coef_))
            else:
                imp = np.zeros(X_train.shape[1])
            top_idx = np.argsort(imp)[::-1][:20]
            for ti in top_idx:
                fi_rows.append({"task": task, "model": name, "feature": X_train.columns[ti], "importance": float(imp[ti])})

    metrics_path = out_dir / "classification_model_metrics.csv"
    pred_path = out_dir / "classification_predictions.csv"
    cm_path = out_dir / "confusion_matrix.csv"
    fi_path = out_dir / "classification_feature_importance.csv"
    summary_path = out_dir / "classification_summary.md"

    pd.DataFrame(metric_rows).to_csv(metrics_path, index=False, encoding="utf-8-sig")
    pd.DataFrame(pred_rows).to_csv(pred_path, index=False, encoding="utf-8-sig")
    pd.DataFrame(cm_rows).to_csv(cm_path, index=False, encoding="utf-8-sig")
    pd.DataFrame(fi_rows).to_csv(fi_path, index=False, encoding="utf-8-sig")
    summary_path.write_text("# Classification Summary\n\n고위험 class 탐지 중심 분석입니다.\n", encoding="utf-8")

    return {"metrics": metrics_path, "predictions": pred_path, "confusion": cm_path, "feature_importance": fi_path, "summary": summary_path}
