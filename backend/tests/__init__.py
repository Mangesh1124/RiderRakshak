"""
RideRakshak Backend Tests

Tests cover:
  1. Sensor simulation (all scenarios)
  2. Preprocessing
  3. Feature extraction
  4. Accident detection
  5. Sensor fusion
  6. Severity calculation
  7. Accident ID generation
  8. GPS simulation
  9. Emergency alert generation
  10. False alert cancellation flow
  11. API endpoints
"""

import pytest
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
