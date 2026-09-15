"""Deterministic legacy baselines used to establish a credible floor."""

from __future__ import annotations

import platform
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import HistGradientBoostingClassifier

from league_ews import __version__
from league_ews.constants import EVENTS, FEATURE_POLICY_VERSION, LABEL_POLICY_VERSION
from league_ews.events import evaluate_operating_point, select_operating_threshold
from league_ews.features import (
    causal_feature_columns,
    history_feature_columns,
    legacy_post_match_feature_columns,
)
from league_ews.io import load_legacy_csv, sha256_file
from league_ews.metrics import probabilistic_metrics
from league_ews.provenance import source_provenance
from league_ews.splits import apply_split, chronological_match_split

BaselineName = Literal["time", "history", "causal", "postmatch_leak"]


@dataclass(frozen=True)
class BaselineSpec:
    name: BaselineName
    max_iter: int = 100
    learning_rate: float = 0.08
    max_leaf_nodes: int = 15
    min_samples_leaf: int = 100
    l2_regularization: float = 1.0
    random_state: int = 20260915


def _feature_columns(frame: pd.DataFrame, name: BaselineName) -> list[str]:
    if name == "time":
        return ["t"]
    if name == "history":
        return history_feature_columns(frame)
    if name == "causal":
        return causal_feature_columns(frame)
    if name == "postmatch_leak":
        return legacy_post_match_feature_columns(frame)
    raise ValueError(f"Unsupported baseline: {name}")


def _matrix(frame: pd.DataFrame, features: list[str]) -> np.ndarray:
    values = frame[features].replace([np.inf, -np.inf], np.nan).to_numpy(dtype=np.float32)
    return values


def _fit_predict(
    train: pd.DataFrame,
    validation: pd.DataFrame,
    test: pd.DataFrame,
    *,
    label: str,
    features: list[str],
    spec: BaselineSpec,
) -> tuple[np.ndarray, np.ndarray, float]:
    model = HistGradientBoostingClassifier(
        loss="log_loss",
        learning_rate=spec.learning_rate,
        max_iter=spec.max_iter,
        max_leaf_nodes=spec.max_leaf_nodes,
        min_samples_leaf=spec.min_samples_leaf,
        l2_regularization=spec.l2_regularization,
        class_weight="balanced",
        random_state=spec.random_state,
    )
    started = time.perf_counter()
    model.fit(_matrix(train, features), train[label].to_numpy(dtype=np.int8))
    elapsed = time.perf_counter() - started
    validation_probability = np.asarray(
        model.predict_proba(_matrix(validation, features))[:, 1], dtype=np.float64
    )
    test_probability = np.asarray(
        model.predict_proba(_matrix(test, features))[:, 1], dtype=np.float64
    )
    return validation_probability, test_probability, elapsed


def run_legacy_benchmark(
    csv_path: str | Path,
    *,
    baselines: tuple[BaselineName, ...] = ("time", "history", "causal"),
    max_matches: int | None = None,
    max_iter: int = 100,
    threshold_candidates: int = 31,
) -> dict[str, object]:
    """Run match-disjoint 30-second baselines and operational evaluation."""

    frame = load_legacy_csv(csv_path)
    frame["match_id"] = frame["match_id"].astype(str)
    if max_matches is not None:
        if max_matches < 3:
            raise ValueError("max_matches must be at least three")
        selected = sorted(frame["match_id"].unique())[:max_matches]
        frame = frame.loc[frame["match_id"].isin(selected)].copy()

    split = chronological_match_split(frame["match_id"])
    partitions = apply_split(frame, split)
    results: list[dict[str, object]] = []

    for baseline_name in baselines:
        spec = BaselineSpec(name=baseline_name, max_iter=max_iter)
        features = _feature_columns(frame, baseline_name)
        if not features:
            raise ValueError(f"No features available for {baseline_name} baseline")
        for event in EVENTS:
            label = f"y_{event}_30"
            validation_probability, test_probability, training_seconds = _fit_predict(
                partitions["train"],
                partitions["validation"],
                partitions["test"],
                label=label,
                features=features,
                spec=spec,
            )
            threshold, validation_operational = select_operating_threshold(
                partitions["validation"],
                validation_probability,
                event=event,
                candidates=threshold_candidates,
            )
            test_operational = evaluate_operating_point(
                partitions["test"],
                test_probability,
                event=event,
                threshold=threshold,
            )
            results.append(
                {
                    "baseline": baseline_name,
                    "event": event,
                    "label": label,
                    "feature_count": len(features),
                    "features": features,
                    "training_seconds": training_seconds,
                    "validation": {
                        "row_metrics": probabilistic_metrics(
                            partitions["validation"][label].to_numpy(), validation_probability
                        ),
                        "operational": validation_operational.to_dict(),
                    },
                    "test": {
                        "row_metrics": probabilistic_metrics(
                            partitions["test"][label].to_numpy(), test_probability
                        ),
                        "operational": test_operational.to_dict(),
                    },
                }
            )

    return {
        "schema_version": "legacy-benchmark-v1",
        "software_version": __version__,
        "source": source_provenance(),
        "dataset": {
            "path_name": Path(csv_path).name,
            "sha256": sha256_file(csv_path),
            "rows": len(frame),
            "matches": int(frame["match_id"].nunique()),
        },
        "policies": {
            "features": FEATURE_POLICY_VERSION,
            "labels": LABEL_POLICY_VERSION,
            "split": split.policy_version,
            "split_sha256": split.digest,
        },
        "partitions": {
            name: {
                "matches": int(partition["match_id"].nunique()),
                "rows": len(partition),
            }
            for name, partition in partitions.items()
        },
        "runtime": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scikit_learn": sklearn.__version__,
        },
        "configuration": {
            "baselines": list(baselines),
            "max_iter": max_iter,
            "threshold_candidates": threshold_candidates,
            "threshold_selection": "maximum event-level F1 on validation only",
            "alert_policy": "upward threshold crossing, 60s cooldown, one-to-one 30s match",
        },
        "results": results,
    }
