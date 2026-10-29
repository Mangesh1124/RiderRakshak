"""
ML Detector Module.

Provides ML-based accident detection as a complement to the threshold detector.

CURRENT STATUS:
  No real IMU/accident dataset is available.
  The full ML pipeline STRUCTURE is implemented and ready.
  Model training requires a labeled dataset.

  DO NOT claim any model accuracy without running actual training.

Supported models:
  - Random Forest (default)
  - SVM
  - Logistic Regression

Feature vector schema (must match feature_extraction.py):
  [acceleration_magnitude, gyro_magnitude, tilt_angle,
   peak_acceleration, peak_gyro, angular_velocity,
   deceleration, speed, alcohol]
"""

import logging
import os
import numpy as np
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from app.accident.features import Features

logger = logging.getLogger(__name__)

FEATURE_COLUMNS = [
    "acceleration_magnitude",
    "gyro_magnitude",
    "tilt_angle",
    "peak_acceleration",
    "peak_gyro",
    "angular_velocity",
    "deceleration",
    "speed",
    "alcohol",
]

MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "ml", "models")


@dataclass
class MLPrediction:
    """Prediction from the ML model."""
    label: str          # "ACCIDENT" or "NORMAL"
    confidence: float   # 0.0–1.0
    model_name: str
    available: bool     # False if no trained model


def features_to_vector(features: Features) -> np.ndarray:
    """Convert Features to numpy array for ML inference."""
    return np.array([[
        features.acceleration_magnitude,
        features.gyro_magnitude,
        features.tilt_angle,
        features.peak_acceleration,
        features.peak_gyro,
        features.angular_velocity,
        features.deceleration,
        features.speed,
        features.alcohol,
    ]])


class MLAccidentDetector:
    """
    ML-based accident detector.

    Usage:
      1. Train: train(X, y)
      2. Save: save_model()
      3. Load: load_model()
      4. Predict: predict(features)

    The feature schema is shared with the threshold detector so
    the same ESP32 pipeline can feed either system.
    """

    def __init__(self, model_type: str = "random_forest"):
        self.model_type = model_type
        self.model = None
        self.is_trained = False

    def _build_model(self):
        """Build the ML model based on model_type."""
        if self.model_type == "random_forest":
            from sklearn.ensemble import RandomForestClassifier
            return RandomForestClassifier(n_estimators=100, random_state=42)
        elif self.model_type == "svm":
            from sklearn.svm import SVC
            return SVC(probability=True, random_state=42)
        elif self.model_type == "logistic_regression":
            from sklearn.linear_model import LogisticRegression
            return LogisticRegression(random_state=42, max_iter=1000)
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")

    def train(self, X: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
        """
        Train the ML model.

        Args:
            X: Feature matrix (n_samples, n_features)
               Columns must match FEATURE_COLUMNS
            y: Labels array (0=NORMAL, 1=ACCIDENT)

        Returns:
            Training metadata dict (NOT performance metrics — use evaluate() for that)
        """
        from sklearn.model_selection import train_test_split
        from sklearn.preprocessing import StandardScaler

        logger.info("Training ML model: %s on %d samples", self.model_type, len(X))

        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)

        self.model = self._build_model()
        self.model.fit(X_scaled, y)
        self.is_trained = True

        return {
            "model_type": self.model_type,
            "n_samples": len(X),
            "n_features": X.shape[1],
            "feature_columns": FEATURE_COLUMNS,
            "status": "trained",
            "note": "Run evaluate() on a held-out test set to get actual metrics.",
        }

    def evaluate(self, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, Any]:
        """
        Evaluate the trained model on held-out test data.

        Returns REAL metrics only — no fabricated values.
        """
        if not self.is_trained:
            raise RuntimeError("Model not trained. Call train() first.")

        from sklearn.metrics import (
            accuracy_score, precision_score, recall_score,
            f1_score, confusion_matrix
        )

        X_scaled = self.scaler.transform(X_test)
        y_pred = self.model.predict(X_scaled)

        return {
            "accuracy": float(accuracy_score(y_test, y_pred)),
            "precision": float(precision_score(y_test, y_pred, zero_division=0)),
            "recall": float(recall_score(y_test, y_pred, zero_division=0)),
            "f1_score": float(f1_score(y_test, y_pred, zero_division=0)),
            "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
            "n_test_samples": len(y_test),
            "model_type": self.model_type,
        }

    def predict(self, features: Features) -> MLPrediction:
        """
        Run inference on extracted features.

        Returns MLPrediction with availability flag.
        If model is not trained, returns a 'not available' placeholder.
        """
        if not self.is_trained or self.model is None:
            return MLPrediction(
                label="UNAVAILABLE",
                confidence=0.0,
                model_name=self.model_type,
                available=False,
            )

        X = features_to_vector(features)
        X_scaled = self.scaler.transform(X)
        proba = self.model.predict_proba(X_scaled)[0]
        label = "ACCIDENT" if proba[1] >= 0.5 else "NORMAL"

        return MLPrediction(
            label=label,
            confidence=float(max(proba)),
            model_name=self.model_type,
            available=True,
        )

    def save_model(self, path: Optional[str] = None) -> str:
        """Save model to disk."""
        import joblib
        os.makedirs(MODEL_DIR, exist_ok=True)
        save_path = path or os.path.join(MODEL_DIR, f"{self.model_type}_model.pkl")
        joblib.dump({"model": self.model, "scaler": self.scaler}, save_path)
        logger.info("Model saved: %s", save_path)
        return save_path

    def load_model(self, path: Optional[str] = None) -> bool:
        """Load model from disk. Returns True if successful."""
        import joblib
        load_path = path or os.path.join(MODEL_DIR, f"{self.model_type}_model.pkl")
        if not os.path.exists(load_path):
            logger.warning("No trained model found at: %s", load_path)
            return False
        data = joblib.load(load_path)
        self.model = data["model"]
        self.scaler = data["scaler"]
        self.is_trained = True
        logger.info("Model loaded: %s", load_path)
        return True
