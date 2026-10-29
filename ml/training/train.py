"""
ML Pipeline — Dataset Training Script

Usage:
  python train.py --model random_forest --dataset path/to/dataset.csv

IMPORTANT:
  No real IMU/accident dataset is bundled with this repository.
  This script implements the FULL pipeline structure.
  Training requires a labeled dataset with the columns listed in FEATURE_COLUMNS.

  DO NOT claim model accuracy without running actual training.
"""

import argparse
import os
import sys
import pandas as pd
import numpy as np

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.accident.ml_detector import MLAccidentDetector, FEATURE_COLUMNS

LABEL_COLUMN = "label"   # 0 = NORMAL, 1 = ACCIDENT


def inspect_dataset(df: pd.DataFrame):
    """Inspect dataset structure before training."""
    print("\n" + "="*60)
    print("DATASET INSPECTION")
    print("="*60)
    print(f"Shape: {df.shape}")
    print(f"\nColumns: {list(df.columns)}")
    print(f"\nLabel distribution:")
    if LABEL_COLUMN in df.columns:
        print(df[LABEL_COLUMN].value_counts())
    print(f"\nMissing values:")
    print(df.isnull().sum())
    print(f"\nFirst rows:")
    print(df.head(3))
    print("="*60)


def train(dataset_path: str, model_type: str = "random_forest", test_size: float = 0.2):
    """
    Train the accident detection ML model.

    Args:
        dataset_path: Path to CSV dataset
        model_type: 'random_forest', 'svm', or 'logistic_regression'
        test_size: Fraction for test split
    """
    print(f"\nLoading dataset: {dataset_path}")
    df = pd.read_csv(dataset_path)

    inspect_dataset(df)

    # Check required columns
    missing_features = [c for c in FEATURE_COLUMNS if c not in df.columns]
    if missing_features:
        print(f"\nERROR: Missing feature columns: {missing_features}")
        print(f"Expected: {FEATURE_COLUMNS}")
        print(f"Got: {list(df.columns)}")
        print("\nYou may need to preprocess your dataset to match the feature schema.")
        return

    if LABEL_COLUMN not in df.columns:
        print(f"\nERROR: Label column '{LABEL_COLUMN}' not found.")
        print("Add a binary label column (0=NORMAL, 1=ACCIDENT) to your dataset.")
        return

    # Clean
    df = df.dropna(subset=FEATURE_COLUMNS + [LABEL_COLUMN])
    print(f"\nRows after dropping NaN: {len(df)}")

    X = df[FEATURE_COLUMNS].values
    y = df[LABEL_COLUMN].values

    # Train/test split
    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42, stratify=y
    )
    print(f"Train: {len(X_train)} | Test: {len(X_test)}")

    # Train
    detector = MLAccidentDetector(model_type=model_type)
    meta = detector.train(X_train, y_train)
    print(f"\nTraining complete: {meta}")

    # Evaluate on held-out test set
    print("\nEvaluating on test set...")
    metrics = detector.evaluate(X_test, y_test)
    print("\n" + "="*60)
    print("REAL TEST SET METRICS (not fabricated)")
    print("="*60)
    print(f"Accuracy:  {metrics['accuracy']:.4f}")
    print(f"Precision: {metrics['precision']:.4f}")
    print(f"Recall:    {metrics['recall']:.4f}")
    print(f"F1 Score:  {metrics['f1_score']:.4f}")
    print(f"Confusion Matrix:\n{np.array(metrics['confusion_matrix'])}")
    print("="*60)

    # Save model
    save_path = detector.save_model()
    print(f"\nModel saved: {save_path}")
    print("\nTo use with the FastAPI backend, the model will be loaded automatically.")
    print("NOTE: These are real metrics from a real test set, not fabricated values.")


def generate_synthetic_demo_dataset(output_path: str, n_samples: int = 1000):
    """
    Generate a synthetic demonstration dataset using the simulator.
    
    WARNING: This dataset uses SIMULATED values, not real hardware readings.
    DO NOT use this for claiming real-world model performance.
    Results from training on this dataset are SOFTWARE DEMONSTRATION ONLY.
    """
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

    from app.sensors.simulator import SimulatedSensorProvider, VALID_SCENARIOS
    from app.accident.preprocessing import preprocess_reading
    from app.accident.features import extract_features

    print(f"\nGenerating SYNTHETIC demo dataset ({n_samples} samples)...")
    print("WARNING: SIMULATED DATA — not validated real-world readings")

    sim = SimulatedSensorProvider()
    rows = []

    # ACCIDENT scenarios → label 1
    accident_scenarios = ["ACCIDENT", "FALL", "HIGH_TILT"]
    # NORMAL scenarios → label 0
    normal_scenarios = ["NORMAL", "HARD_BRAKING", "SUDDEN_ACCELERATION", "ALCOHOL_DETECTED"]

    per_acc = n_samples // (2 * len(accident_scenarios))
    per_norm = n_samples // (2 * len(normal_scenarios))

    for scenario in accident_scenarios:
        for _ in range(per_acc):
            clean = preprocess_reading(sim.get_reading(scenario)).reading
            f = extract_features(clean)
            row = {**f.to_dict(), LABEL_COLUMN: 1}
            row.pop("scenario")
            rows.append(row)

    for scenario in normal_scenarios:
        for _ in range(per_norm):
            clean = preprocess_reading(sim.get_reading(scenario)).reading
            f = extract_features(clean)
            row = {**f.to_dict(), LABEL_COLUMN: 0}
            row.pop("scenario")
            rows.append(row)

    df = pd.DataFrame(rows)
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Synthetic dataset saved: {output_path}")
    print(f"Shape: {df.shape}")
    print(f"Label distribution:\n{df[LABEL_COLUMN].value_counts()}")
    print("\nDO NOT use this for claiming real model performance.")
    return output_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RideRakshak ML Training Pipeline")
    parser.add_argument("--model", default="random_forest", choices=["random_forest", "svm", "logistic_regression"])
    parser.add_argument("--dataset", default=None, help="Path to CSV dataset")
    parser.add_argument("--generate-demo", action="store_true", help="Generate synthetic demo dataset and train on it")
    parser.add_argument("--test-size", type=float, default=0.2)
    args = parser.parse_args()

    if args.generate_demo:
        demo_path = os.path.join(os.path.dirname(__file__), "datasets", "synthetic_demo.csv")
        dataset_path = generate_synthetic_demo_dataset(demo_path)
        print("\n⚠️  Training on SYNTHETIC data — for pipeline demonstration only.")
        print("Do NOT claim these metrics are real-world validated.\n")
        train(dataset_path, args.model, args.test_size)
    elif args.dataset:
        train(args.dataset, args.model, args.test_size)
    else:
        print("Usage:")
        print("  python train.py --dataset /path/to/real_dataset.csv --model random_forest")
        print("  python train.py --generate-demo  # synthetic demo only")
        print("\nNo dataset provided. Exiting.")
