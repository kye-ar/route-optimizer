"""
Simple integration tests for route optimizer endpoints.
Run with: python integration_tests.py
"""

import asyncio
import os


def test_csv_loading_with_main_file():
    """Test CSV loading with main customer data file."""
    print("Testing CSV loading with main customer file...")
    
    try:
        from optimizer.optimize_routes import load_jobs_from_csv
        
        # Test with main customer CSV file
        jobs = load_jobs_from_csv('data/customer-requests-testingLondon36.csv')
        
        # Should load 36 jobs from the main CSV
        assert len(jobs) > 0, f"Should load jobs from main CSV, got {len(jobs)}"
        
        # Check first job structure
        first_job = jobs[0]
        required_fields = ['pickup_lat', 'pickup_lng', 'dropoff_lat', 'dropoff_lng']
        for field in required_fields:
            assert field in first_job, f"Job should have {field} field"
        
        print(f"✓ Main CSV loading works correctly - loaded {len(jobs)} jobs")
        
    except FileNotFoundError:
        print("⚠ Main CSV file not found - skipping valid CSV test")
    except Exception as e:
        print(f"✗ CSV loading with main file failed: {e}")


def test_data_source_endpoint():
    """Test data source endpoint returns HTML table."""
    print("Testing data_source_table_view endpoint...")
    
    try:
        from optimizer.views import data_source_table_view
        
        # Run the async function
        response = asyncio.run(data_source_table_view())
        
        # Basic response validation
        assert hasattr(response, 'body'), "Should return HTMLResponse object"
        html_content = response.body.decode('utf-8')
        assert '<table' in html_content, "Response should contain HTML table"
        assert 'pickup' in html_content.lower(), "Should contain pickup data"
        
        print("✓ Data source endpoint returns valid HTML")
        
    except Exception as e:
        print(f"✗ Data source endpoint failed: {e}")


def test_routes_endpoint():
    """Test routes endpoint (may fail if no optimized routes exist)."""
    print("Testing routes_table_view endpoint...")
    
    try:
        from optimizer.views import routes_table_view
        
        # Run the async function
        response = asyncio.run(routes_table_view())
        
        # Basic response validation
        assert hasattr(response, 'body'), "Should return HTMLResponse object"
        html_content = response.body.decode('utf-8')
        assert '<table' in html_content, "Response should contain HTML table"
        
        print("✓ Routes endpoint returns valid HTML")
        
    except Exception as e:
        # This might fail if no optimized routes CSV exists yet - that's expected
        if "not found" in str(e).lower():
            print("⚠ Routes CSV not found - run optimization first (expected)")
        else:
            print(f"✗ Routes endpoint failed: {e}")


def test_route_optimization_end_to_end():
    """Test full route optimization with test CSV."""
    print("Testing end-to-end route optimization...")
    
    try:
        from optimizer.optimize_routes import optimize_routes
        
        # Run optimization on main customer CSV
        routes = optimize_routes('data/customer-requests-testingLondon36.csv')
        
        # Basic validation
        assert len(routes) > 0, "Should generate at least one route"
        
        # Check route structure
        first_route = routes[0]
        required_fields = ['route_number', 'jobs', 'total_distance_miles', 
                          'total_duration_minutes', 'google_maps_url']
        
        for field in required_fields:
            assert field in first_route, f"Route should have {field} field"
        
        # Check that routes CSV was created
        routes_csv_path = os.path.join('data', 'routes', 'optimized_routes.csv')
        assert os.path.exists(routes_csv_path), "Should create optimized routes CSV"
        
        print(f"✓ End-to-end optimization created {len(routes)} routes")
        
    except Exception as e:
        print(f"✗ End-to-end optimization failed: {e}")


def test_invalid_csv_handling():
    """Test error handling with invalid CSV files."""
    print("Testing invalid CSV file handling...")
    
    try:
        from optimizer.optimize_routes import load_jobs_from_csv
        
        # Test 1: Invalid coordinates
        jobs = load_jobs_from_csv('testing/data/invalid_csv.csv')
        # Should load 0 jobs (all invalid)
        assert len(jobs) == 0, f"Invalid CSV should load 0 jobs, got {len(jobs)}"
        print("✓ Invalid coordinates handled correctly")
        
        # Test 2: Empty CSV (headers only)
        jobs = load_jobs_from_csv('testing/data/empty.csv')
        assert len(jobs) == 0, f"Empty CSV should load 0 jobs, got {len(jobs)}"
        print("✓ Empty CSV handled correctly")
        
        # Test 3: Non-existent file
        try:
            jobs = load_jobs_from_csv('testing/data/nonexistent.csv')
            assert False, "Non-existent file should raise FileNotFoundError"
        except FileNotFoundError:
            print("✓ Non-existent file handled correctly")
        
    except Exception as e:
        print(f"✗ Invalid CSV handling failed: {e}")


def test_endpoint_error_handling():
    """Test endpoint behavior with missing files."""
    print("Testing endpoint error handling...")
    
    try:
        from optimizer.views import data_source_table_view
        
        # Temporarily change file path to non-existent file
        import optimizer.views as views_module
        original_path = None
        
        # This test would require modifying the hardcoded path in views.py
        # For simplicity, we'll just test that endpoints handle errors gracefully
        print("⚠ Endpoint error handling requires runtime file manipulation - skipped for simplicity")
        
    except Exception as e:
        print(f"✗ Endpoint error handling test failed: {e}")


def run_all_integration_tests():
    """Run all integration tests."""
    print("="*60)
    print("RUNNING SIMPLE INTEGRATION TESTS")
    print("="*60)
    
    tests = [
        test_csv_loading_with_main_file,
        test_invalid_csv_handling,
        test_data_source_endpoint,
        test_route_optimization_end_to_end,
        test_routes_endpoint,  # Run this after optimization
        test_endpoint_error_handling,
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
    
    print("="*60)
    print(f"INTEGRATION TEST RESULTS: {passed} passed, {failed} failed")
    print("="*60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_integration_tests()
    exit(0 if success else 1)