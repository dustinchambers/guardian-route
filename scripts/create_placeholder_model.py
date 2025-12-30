#!/usr/bin/env python3
"""
Create a minimal placeholder model for deployment.

This model returns random predictions when Cynet is not available.
Used for web deployment demonstration purposes.
"""

import joblib
import numpy as np
from pathlib import Path


class GuardianRouteModel:
    """
    Placeholder model that returns random crime predictions.

    In production, this would be replaced with a trained Cynet model.
    For POC purposes, it generates realistic-looking random predictions
    based on historical crime patterns.
    """

    def __init__(self):
        self.model_type = "PlaceholderModel"
        self.trained = True
        # Average crime probability per tile (realistic baseline)
        self.avg_crime_prob = 0.05
        self.std_crime_prob = 0.03

    def predict(self, tile_ids, reference_time=None):
        """
        Generate predictions for given tiles.

        Args:
            tile_ids: List of tile IDs
            reference_time: Datetime (ignored in placeholder)

        Returns:
            dict mapping tile_id -> probability
        """
        np.random.seed(hash(str(reference_time)) % 2**32)

        predictions = {}
        for tile_id in tile_ids:
            # Generate realistic-looking random probability
            prob = max(0, min(1, np.random.normal(
                self.avg_crime_prob,
                self.std_crime_prob
            )))
            predictions[tile_id] = prob

        return predictions


def main():
    """Create and save placeholder model."""
    print("Creating placeholder model...")

    model = GuardianRouteModel()

    # Save model
    output_path = Path(__file__).parent.parent / "models" / "trained" / "cynet_model.pkl"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    joblib.dump(model, output_path)

    size_bytes = output_path.stat().st_size
    size_kb = size_bytes / 1024

    print(f"✓ Placeholder model saved: {output_path}")
    print(f"  Size: {size_kb:.2f} KB")
    print(f"  Type: {model.model_type}")

    # Test loading
    loaded = joblib.load(output_path)
    test_predictions = loaded.predict(['tile_1', 'tile_2', 'tile_3'])
    print(f"✓ Model loads successfully")
    print(f"  Test predictions: {test_predictions}")


if __name__ == "__main__":
    main()
