"""
Test: Sensor Simulation
"""

import pytest
import math
from app.sensors.simulator import SimulatedSensorProvider, VALID_SCENARIOS
from app.sensors.base import SensorReading


@pytest.fixture
def simulator():
    return SimulatedSensorProvider(seed=42)


def test_all_scenarios_produce_readings(simulator):
    """Every scenario must produce a valid SensorReading."""
    for scenario in VALID_SCENARIOS:
        reading = simulator.get_reading(scenario)
        assert isinstance(reading, SensorReading)
        assert reading.scenario == scenario


def test_invalid_scenario_raises(simulator):
    """Invalid scenario name must raise ValueError."""
    with pytest.raises(ValueError, match="Unknown scenario"):
        simulator.get_reading("FLYING_CAR")


def test_normal_scenario_values(simulator):
    """Normal scenario should produce near-gravity Z values."""
    reading = simulator.get_reading("NORMAL")
    # Z should be close to gravity (9.81 m/s²)
    assert 8.0 < reading.accelerometer.z < 12.0, (
        f"Normal Z={reading.accelerometer.z} expected near 9.81"
    )


def test_accident_scenario_high_acceleration(simulator):
    """Accident scenario must produce high acceleration magnitude."""
    # Use multiple readings to account for Gaussian variability
    magnitudes = []
    for _ in range(5):
        reading = simulator.get_reading("ACCIDENT")
        ax, ay, az = reading.accelerometer.x, reading.accelerometer.y, reading.accelerometer.z
        mag = math.sqrt(ax**2 + ay**2 + az**2)
        magnitudes.append(mag)

    avg_mag = sum(magnitudes) / len(magnitudes)
    assert avg_mag > 20.0, f"Accident avg magnitude {avg_mag:.2f} should be > 20 m/s²"


def test_alcohol_scenario_above_threshold(simulator):
    """Alcohol scenario must produce alcohol value above legal threshold."""
    from app.config import settings
    readings = [simulator.get_reading("ALCOHOL_DETECTED") for _ in range(5)]
    avg_alcohol = sum(r.alcohol for r in readings) / len(readings)
    assert avg_alcohol > settings.ALCOHOL_THRESHOLD, (
        f"Alcohol avg={avg_alcohol:.3f} should be > {settings.ALCOHOL_THRESHOLD}"
    )


def test_reading_has_gps(simulator):
    """All readings must have GPS coordinates."""
    for scenario in VALID_SCENARIOS:
        reading = simulator.get_reading(scenario)
        assert reading.gps.latitude is not None
        assert reading.gps.longitude is not None
        assert -90 <= reading.gps.latitude <= 90
        assert -180 <= reading.gps.longitude <= 180


def test_reading_has_timestamp(simulator):
    """All readings must have a timestamp."""
    from datetime import datetime
    reading = simulator.get_reading("NORMAL")
    assert isinstance(reading.timestamp, datetime)


def test_simulator_name():
    sim = SimulatedSensorProvider()
    assert "Simulated" in sim.get_name()


def test_valid_scenarios_list():
    assert "NORMAL" in VALID_SCENARIOS
    assert "ACCIDENT" in VALID_SCENARIOS
    assert "FALL" in VALID_SCENARIOS
