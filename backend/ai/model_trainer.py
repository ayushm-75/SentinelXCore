# backend/ai/model_trainer.py
"""
Standalone model trainer helper.
Used by both the background anomaly detector and the manual training script.
"""
import time
import numpy as np
import joblib
from typing import List, Optional
from pathlib import Path
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from backend.core.logger import get_logger
from backend.utils.constants import MODEL_PATH, SCALER_PATH

log = get_logger("model_trainer")


class ModelTrainer:

    def __init__(
        self,
        n_estimators:  int   = 100,
        contamination: float = 0.05,
        random_state:  int   = 42,
    ):
        self.n_estimators  = n_estimators
        self.contamination = contamination
        self.random_state  = random_state

    def train(
        self,
        samples: List[np.ndarray],
        save: bool = True,
    ) -> tuple:
        """
        Train IsolationForest on collected feature samples.
        Returns (model, scaler).
        """
        if len(samples) < 10:
            raise ValueError(f"Need at least 10 samples, got {len(samples)}")

        X = np.array(samples, dtype=np.float32)
        log.info(f"Training on {len(X)} samples, {X.shape[1]} features")

        start  = time.time()
        scaler = StandardScaler()
        X_sc   = scaler.fit_transform(X)

        model = IsolationForest(
            n_estimators=  self.n_estimators,
            max_samples=   "auto",
            contamination= self.contamination,
            random_state=  self.random_state,
            n_jobs=        1,       # Single thread — low CPU
            warm_start=    False,
        )
        model.fit(X_sc)

        elapsed = time.time() - start
        log.info(f"Training complete in {elapsed:.2f}s")

        if save:
            self._save(model, scaler)

        return model, scaler

    def _save(self, model: IsolationForest, scaler: StandardScaler) -> None:
        MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(model,  MODEL_PATH,  compress=3)
        joblib.dump(scaler, SCALER_PATH, compress=3)
        log.info(f"Model saved → {MODEL_PATH}")

    def load(self) -> Optional[tuple]:
        """Load model + scaler from disk. Returns (model, scaler) or None."""
        if MODEL_PATH.exists() and SCALER_PATH.exists():
            try:
                model  = joblib.load(MODEL_PATH)
                scaler = joblib.load(SCALER_PATH)
                log.info("Model loaded from disk.")
                return model, scaler
            except Exception as e:
                log.error(f"Model load failed: {e}")
        return None

    def evaluate(
        self,
        model: IsolationForest,
        scaler: StandardScaler,
        sample: np.ndarray,
    ) -> float:
        """Score a single sample. Returns [0,1] where 1 = most anomalous."""
        X     = sample.reshape(1, -1)
        X_sc  = scaler.transform(X)
        raw   = model.decision_function(X_sc)[0]
        score = float(1.0 / (1.0 + np.exp(raw * 2)))
        return round(score, 4)