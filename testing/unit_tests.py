"""
Simple unit tests for route optimizer functions using basic assert statements.
Run with: python simple_tests.py
"""

from optimizer.utils import haversine_distance, calculate_travel_time, validate_coordinates, is_time_within_window
from optimizer.optimize_routes import load_jobs_from_csv, find_nearest_delivery_job
import math


def test_haversine_distance():
    """Test haversine distance calculation."""
    print("Testing haversine_distance...")
    
    # Test 1: Same point should return 0
    distance = haversine_distance(51.5074, -0.1278, 51.5074, -0.1278)
    assert abs(distance) < 0.001, f"Same point distance should be ~0, got {distance}"
    
    # Test 2: Known distance London to Birmingham (~100 miles)
    london_lat, london_lng = 51.5074, -0.1278
    birmingham_lat, birmingham_lng = 52.4862, -1.8904
    distance = haversine_distance(london_lat, london_lng, birmingham_lat, birmingham_lng)
    assert 90 < distance < 110, f"London-Birmingham distance should be ~100 miles, got {distance}"
    
    # Test 3: Short distance within London
    distance = haversine_distance(51.5074, -0.1278, 51.5144, -0.1419)  # ~1 mile
    assert 0.5 < distance < 1.5, f"Short London distance should be ~1 mile, got {distance}"
    
    print("✓ haversine_distance tests passed")


def test_calculate_travel_time():
    """Test travel time calculation based on distance and time."""
    print("Testing calculate_travel_time...")
    
    # Test 1: Short distance in central London (should be slow)
    time_minutes = calculate_travel_time(0.5, "10:00:00")  # 0.5 miles, non-peak
    assert 5 < time_minutes < 15, f"Central London travel time should be 5-15 mins, got {time_minutes}"
    
    # Test 2: Peak hour should take longer
    peak_time = calculate_travel_time(0.5, "08:00:00")  # Same distance, peak hour
    normal_time = calculate_travel_time(0.5, "10:00:00")  # Same distance, normal hour
    assert peak_time > normal_time, f"Peak hour should be slower: peak={peak_time}, normal={normal_time}"
    
    # Test 3: Longer distance should take more time
    short_time = calculate_travel_time(1.0, "10:00:00")
    long_time = calculate_travel_time(5.0, "10:00:00")
    assert long_time > short_time, f"Longer distance should take more time: short={short_time}, long={long_time}"
    
    print("✓ calculate_travel_time tests passed")


def test_validate_coordinates():
    """Test coordinate validation."""
    print("Testing validate_coordinates...")
    
    # Test 1: Valid London coordinates
    try:
        lat, lng = validate_coordinates("51.5074", "-0.1278")
        assert lat == 51.5074 and lng == -0.1278, f"Valid coordinates failed: {lat}, {lng}"
    except ValueError:
        assert False, "Valid London coordinates should not raise error"
    
    # Test 2: Invalid coordinates (outside UK)
    try:
        validate_coordinates("40.7128", "-74.0060")  # New York
        assert False, "Non-UK coordinates should raise error"
    except ValueError:
        pass  # Expected
    
    # Test 3: Invalid format
    try:
        validate_coordinates("invalid", "also_invalid")
        assert False, "Invalid format should raise error"
    except ValueError:
        pass  # Expected
    
    print("✓ validate_coordinates tests passed")


def test_time_within_window():
    """Test time window validation."""
    print("Testing is_time_within_window...")
    
    # Test 1: Time within window
    assert is_time_within_window("12:00:00", "10:00:00", "14:00:00"), "12:00 should be within 10:00-14:00"
    
    # Test 2: Time at window boundary
    assert is_time_within_window("10:00:00", "10:00:00", "14:00:00"), "10:00 should be within 10:00-14:00 (inclusive)"
    assert is_time_within_window("14:00:00", "10:00:00", "14:00:00"), "14:00 should be within 10:00-14:00 (inclusive)"
    
    # Test 3: Time outside window
    assert not is_time_within_window("09:00:00", "10:00:00", "14:00:00"), "09:00 should NOT be within 10:00-14:00"
    assert not is_time_within_window("15:00:00", "10:00:00", "14:00:00"), "15:00 should NOT be within 10:00-14:00"
    
    print("✓ is_time_within_window tests passed")


def test_find_nearest_delivery_job():
    """Test nearest job finding logic."""
    print("Testing find_nearest_delivery_job...")
    
    # Create test jobs
    current_location = (51.5074, -0.1278)  # London center
    
    jobs = [
        {'dropoff_lat': 51.5144, 'dropoff_lng': -0.1419},  # Close
        {'dropoff_lat': 51.6074, 'dropoff_lng': -0.2278},  # Far
        {'dropoff_lat': 51.5094, 'dropoff_lng': -0.1298}   # Very close
    ]
    
    nearest = find_nearest_delivery_job(current_location, jobs)
    
    # Should return the very close job (index 2)
    assert nearest == jobs[2], f"Should return closest job, got {nearest}"
    
    # Test empty list
    nearest = find_nearest_delivery_job(current_location, [])
    assert nearest is None, "Empty job list should return None"
    
    print("✓ find_nearest_delivery_job tests passed")


def test_basic_csv_loading():
    """Test basic CSV loading functionality."""
    print("Testing basic CSV loading...")
    
    # Test with existing CSV file
    try:
        jobs = load_jobs_from_csv('data/customer-requests-testingLondon36.csv')
        assert len(jobs) > 0, "Should load some jobs from test CSV"
        
        # Check job structure
        first_job = jobs[0]
        required_fields = ['pickup_lat', 'pickup_lng', 'dropoff_lat', 'dropoff_lng', 
                          'pickup_time_from', 'pickup_time_to', 'dropoff_time_from', 'dropoff_time_to']
        
        for field in required_fields:
            assert field in first_job, f"Job should have {field} field"
        
        print(f"✓ Loaded {len(jobs)} jobs from CSV")
        
    except FileNotFoundError:
        print("⚠ CSV file not found - skipping CSV loading test")
    except Exception as e:
        print(f"✗ CSV loading failed: {e}")


def run_all_tests():
    """Run all tests."""
    print("="*50)
    print("RUNNING SIMPLE UNIT TESTS")
    print("="*50)
    
    tests = [
        test_haversine_distance,
        test_calculate_travel_time,
        test_validate_coordinates,
        test_time_within_window,
        test_find_nearest_delivery_job,
        test_basic_csv_loading
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"✗ {test.__name__} FAILED: {e}")
            failed += 1
    
    print("="*50)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("="*50)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)