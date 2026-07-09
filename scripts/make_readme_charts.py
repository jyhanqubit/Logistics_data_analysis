"""README용 차트 4종 생성. outputs/ 산출물만 읽어 docs/img/에 저장한다."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import pandas as pd

for f in fm.fontManager.ttflist:
    if "Noto Sans CJK" in f.name:
        plt.rcParams["font.family"] = f.name
        break
plt.rcParams["axes.unicode_minus"] = False

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "img"
OUT.mkdir(parents=True, exist_ok=True)

C_MODEL, C_NAIVE, C_BLEND, C_BAND = "#2563eb", "#9ca3af", "#059669", "#bfdbfe"

# 1. fold별 WAPE: 모델 vs naive vs 운영(blend) -------------------------------
bt = pd.read_csv(ROOT / "outputs/forecasting/backtest_metrics.csv")
fig, ax = plt.subplots(figsize=(7, 4))
x = range(len(bt))
w = 0.26
ax.bar([i - w for i in x], bt["wape_naive"] * 100, w, label="Seasonal naive", color=C_NAIVE)
ax.bar(x, bt["wape_model"] * 100, w, label="GBM (recursive)", color=C_MODEL)
ax.bar([i + w for i in x], bt["wape_blend"] * 100, w, label="운영 예측 (h>14 naive 전환)", color=C_BLEND)
ax.set_xticks(list(x))
ax.set_xticklabels([f"Fold {r.fold}\n(origin {r.origin})" for r in bt.itertuples()], fontsize=9)
ax.set_ylabel("WAPE (%)")
ax.set_title("Rolling-origin backtest: 28일 horizon WAPE")
ax.legend(fontsize=9)
ax.grid(axis="y", alpha=0.3)
for i, r in enumerate(bt.itertuples()):
    ax.text(i + w, r.wape_blend * 100 + 0.15, f"{r.wape_blend*100:.1f}", ha="center", fontsize=8, color=C_BLEND)
fig.tight_layout()
fig.savefig(OUT / "backtest_wape.png", dpi=150)
plt.close(fig)

# 2. horizon별 WAPE와 전환점 --------------------------------------------------
hz = pd.read_csv(ROOT / "outputs/forecasting/backtest_by_horizon.csv")
hz_avg = hz.groupby("horizon", as_index=False)[["wape_model", "wape_naive"]].mean()
order = ["h01-07", "h08-14", "h15-28"]
hz_avg = hz_avg.set_index("horizon").loc[order].reset_index()
fig, ax = plt.subplots(figsize=(7, 4))
ax.plot(hz_avg["horizon"], hz_avg["wape_model"] * 100, "o-", label="GBM (recursive)", color=C_MODEL, lw=2)
ax.plot(hz_avg["horizon"], hz_avg["wape_naive"] * 100, "s--", label="Seasonal naive", color=C_NAIVE, lw=2)
ax.axvline(1.5, color=C_BLEND, ls=":", lw=2)
ax.text(1.55, ax.get_ylim()[1] * 0.55, "h=14 전환점\n(이후 naive 사용)", fontsize=9, color=C_BLEND)
ax.set_ylabel("WAPE (%)")
ax.set_xlabel("예측 horizon 구간")
ax.set_title("Horizon이 길수록 recursive 오차 누적으로 모델이 naive에 역전됨")
ax.legend(fontsize=9)
ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(OUT / "wape_by_horizon.png", dpi=150)
plt.close(fig)

# 3. 예측 fan chart (송파구, 카테고리 합) -------------------------------------
pred = pd.read_csv(ROOT / "outputs/forecasting/forecast_predictions.csv", parse_dates=["date_key"])
g = pred[pred["region_name"] == "송파구"].groupby("date_key", as_index=False)[
    ["inbound_volume", "prediction", "q10", "q90"]
].sum()
fig, ax = plt.subplots(figsize=(8, 4))
ax.fill_between(g["date_key"], g["q10"], g["q90"], color=C_BAND, alpha=0.7, label="q10–q90 구간")
ax.plot(g["date_key"], g["inbound_volume"], "k-", lw=1.5, label="실측")
ax.plot(g["date_key"], g["prediction"], color=C_MODEL, lw=2, label="운영 예측")
ax.set_ylabel("일 물동량 (건)")
ax.set_title("송파구 28일 예측 vs 실측 (최종 holdout, 카테고리 합)")
ax.legend(fontsize=9)
ax.grid(alpha=0.3)
fig.autofmt_xdate()
fig.tight_layout()
fig.savefig(OUT / "forecast_fan_songpa.png", dpi=150)
plt.close(fig)

# 4. 차량 배분: 무제약 newsvendor vs 총량 제약 MILP --------------------------
cap = pd.read_csv(ROOT / "outputs/capacity/capacity_plan.csv").head(12)
fig, ax = plt.subplots(figsize=(8, 4.5))
x = range(len(cap))
w = 0.38
ax.bar([i - w / 2 for i in x], cap["vehicles_unconstrained"], w, label="무제약 newsvendor", color=C_NAIVE)
ax.bar([i + w / 2 for i in x], cap["vehicles_milp"], w, label="총량 제약 MILP", color=C_MODEL)
cut = cap[cap["cut_by_constraint"] > 0]
for i, r in enumerate(cap.itertuples()):
    if r.cut_by_constraint > 0:
        ax.annotate("−1", (i + w / 2, r.vehicles_milp + 0.15), ha="center", fontsize=9, color="#dc2626", weight="bold")
ax.set_xticks(list(x))
ax.set_xticklabels(cap["region_name"], rotation=45, ha="right", fontsize=9)
ax.set_ylabel("배치 차량 (대)")
ax.set_title("권역별 차량 배분: 총량 제약이 분산 작은 권역부터 감축")
ax.legend(fontsize=9)
ax.grid(axis="y", alpha=0.3)
fig.tight_layout()
fig.savefig(OUT / "capacity_allocation.png", dpi=150)
plt.close(fig)

print("saved:", sorted(p.name for p in OUT.glob("*.png")))
