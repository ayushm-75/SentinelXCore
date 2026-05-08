# Standalone model trainer script
# scripts/train_model.py
"""
Standalone model trainer.
Runs for 5 minutes collecting baseline system stats, then trains.
Run: python scripts/train_model.py
"""
import asyncio
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.ai.anomaly_detector import AnomalyDetector
from backend.ai.feature_extractor import FeatureExtractor
from backend.core.logger import setup_logger

setup_logger()


async def collect_and_train():
    print("Collecting baseline samples for 5 minutes...")
    print("Please use the system normally during this time.")

    extractor = FeatureExtractor()
    detector  = AnomalyDetector()
    samples   = []

    for i in range(60):  # 60 samples × 5 seconds = 5 minutes
        features = extractor.extract()
        if features is not None:
            samples.append(features)
            print(f"Sample {len(samples)}/60 collected", end="\r")
        await asyncio.sleep(5.0)

    print(f"\nCollected {len(samples)} samples. Training model...")

    import numpy as np
    import joblib
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler
    from backend.utils.constants import MODEL_PATH, SCALER_PATH

    X = np.array(samples, dtype=float)

    scaler = StandardScaler()
    X_sc   = scaler.fit_transform(X)

    model = IsolationForest(n_estimators=100, contamination=0.05, random_state=42, n_jobs=1)
    model.fit(X_sc)

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model,  MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)

    print(f"Model saved to {MODEL_PATH}")
    print("Done!")


if __name__ == "__main__":
    asyncio.run(collect_and_train())