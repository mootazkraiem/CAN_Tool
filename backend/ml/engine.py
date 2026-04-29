from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from backend.data_processing.parser import CanLogParser, SUPPORTED_SUFFIXES
from backend.data_processing.feature_engineering import FEATURE_COLUMNS, FeatureEngineer

try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None

logger = logging.getLogger("can_ai_backend")

@dataclass
class ModelBundle:
    scaler: StandardScaler
    isolation_forest: IsolationForest
    kmeans: KMeans
    n_clusters: int
    trained_at: float

class VehicleAIDiagnosticEngine:
    def __init__(
        self,
        contamination: float = 0.01,
        n_clusters: int = 5,
        random_state: int = 42,
        model_path: str | Path = "models/isolation_forest.joblib",
    ):
        self.contamination = contamination
        self.n_clusters = n_clusters
        self.random_state = random_state
        self.model_path = Path(model_path)
        self.model_bundle: ModelBundle | None = None
        self.cluster_profiles: dict[int, dict[str, Any]] = {}
        self._load_model()

    def _determine_optimal_clusters(self, features_norm: np.ndarray, max_k: int = 8) -> int:
        if len(features_norm) < 10:
            return min(2, max(1, len(features_norm)))
        max_k = min(max_k, len(features_norm))
        inertias: list[float] = []
        k_values = list(range(2, max_k + 1))
        for k in k_values:
            km = KMeans(n_clusters=k, random_state=self.random_state, n_init=10)
            km.fit(features_norm)
            inertias.append(float(km.inertia_))
        if len(inertias) < 3:
            return k_values[0]
        second_diff = np.diff(np.diff(np.array(inertias)))
        elbow_idx = int(np.argmax(second_diff)) + 2
        return int(k_values[min(elbow_idx, len(k_values) - 1)])

    def fit(self, dataset: pd.DataFrame, auto_clusters: bool = True) -> None:
        if dataset.empty:
            raise ValueError("Cannot train with empty dataset.")
        features = dataset[FEATURE_COLUMNS].to_numpy(dtype=float)
        scaler = StandardScaler()
        features_norm = scaler.fit_transform(features)

        isolation_forest = IsolationForest(
            contamination=self.contamination,
            n_estimators=250,
            random_state=self.random_state,
            n_jobs=1,
        )
        isolation_forest.fit(features_norm)

        n_clusters = self._determine_optimal_clusters(features_norm) if auto_clusters else self.n_clusters
        n_clusters = max(2, int(n_clusters))
        kmeans = KMeans(n_clusters=n_clusters, random_state=self.random_state, n_init=15)
        kmeans.fit(features_norm)

        self.model_bundle = ModelBundle(
            scaler=scaler,
            isolation_forest=isolation_forest,
            kmeans=kmeans,
            n_clusters=n_clusters,
            trained_at=time.time(),
        )
        self._build_cluster_profiles(dataset, kmeans.labels_)
        self.save_model()

    def _build_cluster_profiles(self, dataset: pd.DataFrame, labels: np.ndarray) -> None:
        prof_df = dataset.copy()
        prof_df["cluster"] = labels
        profiles: dict[int, dict[str, Any]] = {}
        for cluster_id, grp in prof_df.groupby("cluster"):
            profiles[int(cluster_id)] = {
                "rows": int(len(grp)),
                "avg_can_id": round(float(grp["can_id"].mean()), 3),
                "avg_frequency": round(float(grp["message_frequency"].mean()), 6),
                "avg_entropy": round(float(grp["payload_entropy"].mean()), 6),
                "avg_timing": round(float(grp["time_diff"].mean()), 6),
            }
        self.cluster_profiles = profiles

    def predict(self, dataset: pd.DataFrame) -> pd.DataFrame:
        if dataset.empty:
            return dataset.copy()
        if self.model_bundle is None:
            self.fit(dataset)
        assert self.model_bundle is not None

        output = dataset.copy()
        features = output[FEATURE_COLUMNS].to_numpy(dtype=float)
        features_norm = self.model_bundle.scaler.transform(features)

        raw_score = self.model_bundle.isolation_forest.decision_function(features_norm)
        outlier_label = self.model_bundle.isolation_forest.predict(features_norm)
        severity = 1.0 / (1.0 + np.exp(8.0 * raw_score))

        output["anomaly"] = outlier_label
        output["cluster"] = self.model_bundle.kmeans.predict(features_norm)
        output["anomaly_score"] = raw_score
        output["severity"] = severity
        return output

    def save_model(self) -> None:
        if self.model_bundle is None:
            return
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "bundle": self.model_bundle,
            "cluster_profiles": self.cluster_profiles,
            "feature_columns": FEATURE_COLUMNS,
        }
        joblib.dump(payload, self.model_path)
        logger.info("Saved model bundle to %s", self.model_path)

    def _load_model(self) -> None:
        if not self.model_path.exists():
            return
        try:
            payload = joblib.load(self.model_path)
            self.model_bundle = payload.get("bundle")
            self.cluster_profiles = payload.get("cluster_profiles", {})
            logger.info("Loaded model bundle from %s", self.model_path)
        except Exception as exc:
            logger.warning("Failed to load model bundle: %s", exc)
            self.model_bundle = None
            self.cluster_profiles = {}

    def build_anomaly_context(self, enriched: pd.DataFrame) -> list[dict[str, Any]]:
        if enriched.empty:
            return []
        anomalies = enriched[enriched["anomaly"] == -1].copy()
        if anomalies.empty:
            return []

        byte_cols = [f"byte_{i}" for i in range(8)]
        global_byte_mean = float(enriched[byte_cols].stack().mean()) if len(enriched) else 0.0
        global_byte_std = float(enriched[byte_cols].stack().std()) if len(enriched) else 1.0
        global_byte_std = global_byte_std if global_byte_std > 1e-9 else 1.0

        per_id_freq = (
            enriched.groupby("can_id")["message_frequency"]
            .agg(["mean", "std"])
            .rename(columns={"mean": "freq_mean", "std": "freq_std"})
            .fillna(0.0)
        )
        per_id_timing = (
            enriched.groupby("can_id")["time_diff"]
            .agg(["mean", "std"])
            .rename(columns={"mean": "td_mean", "std": "td_std"})
            .fillna(0.0)
        )

        contexts: list[dict[str, Any]] = []
        for _, row in anomalies.iterrows():
            can_id = int(row["can_id"])
            can_hex = f"0x{can_id:X}"
            freq = float(row["message_frequency"])
            freq_mean = float(per_id_freq.loc[can_id, "freq_mean"]) if can_id in per_id_freq.index else freq
            freq_std = float(per_id_freq.loc[can_id, "freq_std"]) if can_id in per_id_freq.index else 0.0
            freq_z = 0.0 if freq_std <= 1e-9 else (freq - freq_mean) / freq_std

            tdiff = float(row["time_diff"])
            td_mean = float(per_id_timing.loc[can_id, "td_mean"]) if can_id in per_id_timing.index else tdiff
            td_std = float(per_id_timing.loc[can_id, "td_std"]) if can_id in per_id_timing.index else 0.0
            td_z = 0.0 if td_std <= 1e-9 else (tdiff - td_mean) / td_std

            unusual_bytes: list[dict[str, Any]] = []
            max_byte_z = 0.0
            for i in range(8):
                value = int(row[f"byte_{i}"])
                z = (value - global_byte_mean) / global_byte_std
                max_byte_z = max(max_byte_z, abs(z))
                if abs(z) >= 2.5:
                    unusual_bytes.append({"index": i, "value": value, "z_score": round(float(z), 3)})

            anomaly_type = classify_anomaly_type(freq_z=freq_z, td_z=td_z, byte_z=max_byte_z)
            confidence = "high" if float(row["severity"]) >= 0.85 else "medium" if float(row["severity"]) >= 0.6 else "low"
            cluster = int(row["cluster"])
            cluster_desc = self.cluster_profiles.get(cluster, {})

            contexts.append(
                {
                    "timestamp": float(row["timestamp"]),
                    "source_file": str(row.get("source_file", "")),
                    "can_id": can_hex,
                    "severity": round(float(row["severity"]), 4),
                    "type": anomaly_type,
                    "cluster": cluster,
                    "confidence": confidence,
                    "issue": anomaly_type.replace("_", " "),
                    "frequency": round(freq, 6),
                    "frequency_baseline": round(freq_mean, 6),
                    "frequency_deviation_z": round(freq_z, 3),
                    "timing_deviation_z": round(td_z, 3),
                    "unusual_bytes": unusual_bytes,
                    "anomaly_score": round(float(row["anomaly_score"]), 6),
                    "cluster_profile": cluster_desc,
                }
            )
        return contexts

def classify_anomaly_type(freq_z: float, td_z: float, byte_z: float) -> str:
    if abs(freq_z) >= 2.0:
        return "frequency_anomaly"
    if abs(td_z) >= 2.0:
        return "timing_anomaly"
    if byte_z >= 2.5:
        return "data_anomaly"
    return "pattern_anomaly"

class LLMExplainer:
    def __init__(self, model: str = "gpt-5.4-mini"):
        self.model = model

    def explain(self, context: dict[str, Any]) -> dict[str, str]:
        prompt = (
            "A CAN anomaly was detected in an EV system.\n\n"
            f"CAN ID: {context.get('can_id')}\n"
            f"Anomaly type: {context.get('type')}\n"
            f"Severity (0-1): {context.get('severity')}\n"
            f"Confidence: {context.get('confidence')}\n"
            f"Cluster: {context.get('cluster')}\n"
            f"Cluster profile: {json.dumps(context.get('cluster_profile', {}))}\n"
            f"Frequency deviation z-score: {context.get('frequency_deviation_z')}\n"
            f"Timing deviation z-score: {context.get('timing_deviation_z')}\n"
            f"Unusual bytes: {json.dumps(context.get('unusual_bytes', []))}\n\n"
            "Return strict JSON with keys: causes, risks, recommendations. "
            "Keep each value concise and actionable for automotive diagnostics."
        )

        if OpenAI is None:
            return {
                "causes": "OpenAI SDK unavailable.",
                "risks": "LLM explanation disabled; only statistical output available.",
                "recommendations": "Install OpenAI SDK and set OPENAI_API_KEY.",
            }

        try:
            client = OpenAI()
            response = client.responses.create(model=self.model, input=prompt, temperature=0.2)
            text = (response.output_text or "").strip()
            parsed = _extract_json_object(text)
            if parsed:
                return {
                    "causes": str(parsed.get("causes", "")),
                    "risks": str(parsed.get("risks", "")),
                    "recommendations": str(parsed.get("recommendations", "")),
                }
            return {
                "causes": text[:600] if text else "No response content.",
                "risks": "Model did not return strict JSON.",
                "recommendations": "Retry with stricter model/system settings.",
            }
        except Exception as exc:
            logger.warning("LLM explanation failed: %s", exc)
            return {
                "causes": f"LLM call failed: {exc}",
                "risks": "Narrative diagnosis unavailable.",
                "recommendations": "Verify OPENAI_API_KEY and network connectivity.",
            }

class FeedbackStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, item: dict[str, Any]) -> None:
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(item, ensure_ascii=True) + "\n")

class AnalyzeCache:
    def __init__(self) -> None:
        self._cache: dict[str, dict[str, Any]] = {}

    @staticmethod
    def fingerprint(content: bytes) -> str:
        return hashlib.sha256(content).hexdigest()

    def get(self, key: str) -> dict[str, Any] | None:
        return self._cache.get(key)

    def set(self, key: str, value: dict[str, Any]) -> None:
        self._cache[key] = value

def collect_can_logs_from_assets(
    root: str | Path,
    max_files: int = 50,
    max_lines_per_file: int = 5000,
) -> tuple[pd.DataFrame, dict[str, int]]:
    root_path = Path(root)
    if not root_path.exists():
        return pd.DataFrame(), {"files_seen": 0, "files_parsed": 0}

    candidates = [p for p in root_path.rglob("*") if p.suffix.lower() in SUPPORTED_SUFFIXES]
    candidates = sorted(candidates)[:max_files]

    all_parts: list[pd.DataFrame] = []
    files_parsed = 0
    for path in candidates:
        try:
            with path.open("r", encoding="utf-8", errors="ignore") as handle:
                parsed, _ = CanLogParser.parse_stream(handle, source_name=str(path.name), max_lines=max_lines_per_file)
            if not parsed.empty:
                all_parts.append(parsed)
                files_parsed += 1
        except Exception as exc:
            logger.warning("Failed to parse seed file %s: %s", path, exc)
            continue

    if not all_parts:
        return pd.DataFrame(), {"files_seen": len(candidates), "files_parsed": files_parsed}
    return pd.concat(all_parts, ignore_index=True), {"files_seen": len(candidates), "files_parsed": files_parsed}

def _extract_json_object(text: str) -> dict[str, Any] | None:
    raw = text.strip()
    if not raw:
        return None
    try:
        candidate = json.loads(raw)
        if isinstance(candidate, dict):
            return candidate
    except Exception:
        pass
    first = raw.find("{")
    last = raw.rfind("}")
    if first == -1 or last == -1 or last <= first:
        return None
    try:
        candidate = json.loads(raw[first : last + 1])
        return candidate if isinstance(candidate, dict) else None
    except Exception:
        return None
