# Isolation Forest model
# backend/ai/anomaly_detector.py
"""
Lightweight anomaly detector using Isolation Forest.
- Runs in <50MB RAM
- No GPU required
- Trains on first 100 samples of "normal" behavior
- Re-trains periodically with accumulated data
- AI is SECONDARY to heuristics — raises soft alerts only
"""
import asyncio
import time
import numpy as np
import joblib
from pathlib import Path
from collections import deque
from typing import Optional, List

from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from backend.core.logger import get_logger
from backend.core.state import state, AlertEntry
from backend.core.event_bus import bus
from backend.ai.feature_extractor import FeatureExtractor, FEATURE_DIM
from backend.utils.helpers import generate_alert_id
from backend.utils.constants import (
    MODEL_PATH, SCALER_PATH, FEATURE_WINDOW_SIZE,
    MIN_TRAIN_SAMPLES, MODEL_RETRAIN_INTERVAL_SEC,
    SEV_MEDIUM
)

log = get_logger("anomaly_detector")


class AnomalyDetector:

    def __init__(self):
        self.extractor     = FeatureExtractor()
        self.model: Optional[IsolationForest] = None
        self.scaler: Optional[StandardScaler] = None
        self._trained      = False
        self._sample_buffer: deque = deque(maxlen=FEATURE_WINDOW_SIZE * 3)
        self._last_retrain = 0.0
        self._anomaly_cooldown: dict = {}   # feature_hash → last_alert_time

    async def load_or_train(self) -> None:
        """Load existing model or defer training until enough samples collected."""
        if MODEL_PATH.exists() and SCALER_PATH.exists():
            try:
                loop = asyncio.get_event_loop()
                self.model, self.scaler = await loop.run_in_executor(
                    None, self._load_model
                )
                self._trained = True
                state.model_trained = True
                log.info("Anomaly model loaded from disk.")
                return
            except Exception as e:
                log.warning(f"Failed to load model: {e}. Will retrain.")

        log.info(f"Anomaly model will train after {MIN_TRAIN_SAMPLES} samples.")

    def _load_model(self):
        model  = joblib.load(MODEL_PATH)
        scaler = joblib.load(SCALER_PATH)
        return model, scaler

    async def run(self) -> None:
        log.info("Anomaly detector started.")
        while True:
            try:
                await self._tick()
                await asyncio.sleep(5.0)   # Sample every 5 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                log.error(f"Anomaly detector error: {e}")
                await asyncio.sleep(10)

    async def _tick(self) -> None:
        features = self.extractor.extract()
        if features is None:
            return

        self._sample_buffer.append(features)

        # Train if not yet trained and have enough samples
        if not self._trained and len(self._sample_buffer) >= MIN_TRAIN_SAMPLES:
            await self._train()

        # Periodic retrain
        if (
            self._trained and
            time.time() - self._last_retrain > MODEL_RETRAIN_INTERVAL_SEC and
            len(self._sample_buffer) >= MIN_TRAIN_SAMPLES
        ):
            await self._train()

        # Score current sample
        if self._trained:
            score = await self._score(features)
            if score is not None:
                await self._evaluate_score(score, features)

    async def _train(self) -> None:
        log.info(f"Training anomaly model on {len(self._sample_buffer)} samples...")
        loop = asyncio.get_event_loop()

        try:
            await loop.run_in_executor(None, self._blocking_train)
            self._trained       = True
            state.model_trained = True
            self._last_retrain  = time.time()
            log.info("Anomaly model trained and saved.")
        except Exception as e:
            log.error(f"Training failed: {e}")

    def _blocking_train(self) -> None:
        X = np.array(list(self._sample_buffer), dtype=np.float32)

        self.scaler = StandardScaler()
        X_scaled    = self.scaler.fit_transform(X)

        self.model  = IsolationForest(
            n_estimators=100,       # Lightweight
            max_samples="auto",
            contamination=0.05,    # Expect 5% anomalies in training data
            random_state=42,
            n_jobs=1,              # Single thread — low CPU
        )
        self.model.fit(X_scaled)

        # Persist
        MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.model,  MODEL_PATH)
        joblib.dump(self.scaler, SCALER_PATH)

    async def _score(self, features: np.ndarray) -> Optional[float]:
        """Return anomaly score [0, 1]. Higher = more anomalous."""
        try:
            loop  = asyncio.get_event_loop()
            score = await loop.run_in_executor(
                None, lambda: self._blocking_score(features)
            )
            return score
        except Exception as e:
            log.debug(f"Score error: {e}")
            return None

    def _blocking_score(self, features: np.ndarray) -> float:
        X        = features.reshape(1, -1)
        X_scaled = self.scaler.transform(X)
        # decision_function: negative = anomaly, positive = normal
        raw_score = self.model.decision_function(X_scaled)[0]
        # Normalize to [0,1]: 0=normal, 1=anomaly
        normalized = 1.0 / (1.0 + np.exp(raw_score * 2))
        return float(normalized)

    async def _evaluate_score(self, score: float, features: np.ndarray) -> None:
        from backend.core.settings import get_settings
        threshold = get_settings().anomaly_threshold

        if score < threshold:
            return

        state.anomalies_detected += 1

        # Dedup by feature fingerprint
        key = f"anomaly_{int(score * 10)}"
        now = time.time()
        if now - self._anomaly_cooldown.get(key, 0) < 60:
            return
        self._anomaly_cooldown[key] = now

        # Find most anomalous features
        top_features = self._explain(features)

        alert = AlertEntry(
            alert_id=  generate_alert_id(),
            severity=  SEV_MEDIUM,
            category=  "ai",
            title=     f"AI Anomaly Detected (score: {score:.2f})",
            detail=    f"Unusual system behavior. Top indicators: {top_features}",
        )
        await state.add_alert(alert)
        await bus.publish("ai.anomaly", {
            "score":        score,
            "threshold":    threshold,
            "top_features": top_features,
            "timestamp":    now,
        })
        log.warning(f"AI anomaly: score={score:.3f} | {top_features}")

    def _explain(self, features: np.ndarray) -> str:
        """Identify which features are most anomalous (simple z-score)."""
        names    = self.extractor.feature_names
        try:
            X_scaled = self.scaler.transform(features.reshape(1, -1))[0]
            ranked   = sorted(
                zip(names, np.abs(X_scaled)),
                key=lambda x: x[1],
                reverse=True
            )
            top      = ranked[:3]
            return ", ".join(f"{n}={v:.1f}σ" for n, v in top)
        except Exception:
            return "unknown"