import csv
from typing import List, Tuple, Dict, Optional

try:
    from .utils import (haversine_distance, generate_google_maps_url, add_minutes_to_time, 
                       subtract_minutes_from_time, time_difference_minutes, 
                       is_time_within_window, calculate_travel_time, validate_coordinates,
                       normalize_coordinates, import_config)
except ImportError:
    from utils import (haversine_distance, generate_google_maps_url, add_minutes_to_time, 
                      subtract_minutes_from_time, time_difference_minutes, 
                      is_time_within_window, calculate_travel_time, validate_coordinates,
                      normalize_coordinates, import_config)


def optimize_routes(csv_file_path: str) -> List[Dict]:
    """Main route optimization using nearest neighbor algorithm."""
    # Load configuration parameters
    (max_distance_miles, max_route_duration_minutes, estimated_delivery_time, 
     default_collection_point, default_start_time, max_drop_count) = import_config(
        'max_distance_miles', 'max_route_duration_minutes', 'estimated_delivery_time',
        'default_collection_point', 'default_start_time', 'max_drop_count')
    
    # Load and validate all jobs from CSV
    jobs = load_jobs_from_csv(csv_file_path)
    unassigned_jobs = jobs.copy()
    routes = []
    
    # Build routes iteratively until all jobs assigned or no more feasible routes
    while unassigned_jobs:
        # Attempt to build a single optimized route from remaining jobs
        route = build_single_route(
            unassigned_jobs=unassigned_jobs,
            depot_location=default_collection_point,
            start_time=default_start_time,
            max_distance=max_distance_miles,
            max_duration=max_route_duration_minutes,
            delivery_time=estimated_delivery_time,
            max_drops=max_drop_count
        )
        
        # Stop if no jobs could be assigned to this route
        if not route['jobs']:
            break
            
        routes.append(route)
        
        # Remove assigned jobs from unassigned list using unique identifiers
        assigned_job_ids = [f"{job_info['job']['pickup_address']}->{job_info['job']['dropoff_address']}" 
                           for job_info in route['jobs']]
        
        unassigned_jobs = [job for job in unassigned_jobs 
                          if f"{job['pickup_address']}->{job['dropoff_address']}" not in assigned_job_ids]
    
    # Assign sequential route numbers
    for i, route in enumerate(routes, 1):
        route['route_number'] = i
    
    # Save optimized routes to CSV file
    save_routes_to_csv(routes, 'optimized_routes.csv')
    
    return routes


def load_jobs_from_csv(csv_file_path: str) -> List[Dict]:
    """Load and validate job data from CSV file."""
    jobs = []
    failed_jobs = []
    
    with open(csv_file_path, 'r') as file:
        reader = csv.DictReader(file)
        for row_num, row in enumerate(reader, start=2):
            try:
                pickup_lat, pickup_lng = validate_coordinates(row['pickup_lat'], row['pickup_lng'])
                dropoff_lat, dropoff_lng = validate_coordinates(row['dropoff_lat'], row['dropoff_lng'])
                
                job = {
                    'pickup_lat': pickup_lat,
                    'pickup_lng': pickup_lng,
                    'pickup_time_from': row['pickup_time_from'],
                    'pickup_time_to': row['pickup_time_to'],
                    'dropoff_lat': dropoff_lat,
                    'dropoff_lng': dropoff_lng,
                    'dropoff_time_from': row['dropoff_time_from'],
                    'dropoff_time_to': row['dropoff_time_to'],
                    'pickup_address': row['pickup_address_line_1'],
                    'dropoff_address': row['dropoff_address_line_1']
                }
                jobs.append(job)
                
            except ValueError as e:
                failed_jobs.append({
                    'row_number': row_num,
                    'pickup_address': row.get('pickup_address_line_1', 'unknown'),
                    'dropoff_address': row.get('dropoff_address_line_1', 'unknown'),
                    'error': str(e)
                })
                print(f"ERROR: Row {row_num} - {str(e)}")
    
    print(f"CSV Loading: {len(jobs)} loaded, {len(failed_jobs)} failed")
    
    return jobs


def build_single_route(unassigned_jobs: List[Dict], depot_location: Tuple[float, float], 
                      start_time: str, max_distance: float, max_duration: int, 
                      delivery_time: int, max_drops: int) -> Dict:
    """Build single route using nearest neighbor algorithm for delivery-only operations."""
    # Initialize route tracking variables
    current_time = start_time
    route_jobs = []
    total_distance_miles = 0.0
    route_start_time = current_time
    current_location = depot_location
    available_jobs = unassigned_jobs.copy()
    
    # Greedy nearest neighbor: keep adding closest valid jobs until constraints violated
    while available_jobs:
        # Filter jobs where current time allows delivery within their window
        valid_jobs = get_jobs_within_dropoff_window(available_jobs, current_time)
        if not valid_jobs:
            break
        
        # Select nearest job by straight-line distance to dropoff location
        nearest_job = find_nearest_delivery_job(current_location, valid_jobs)
        if not nearest_job:
            break
        
        # Calculate travel time and arrival estimates
        delivery_timing = calculate_delivery_timing(current_location, current_time, nearest_job, delivery_time)
        new_distance = total_distance_miles + delivery_timing['travel_distance']
        new_duration = time_difference_minutes(route_start_time, delivery_timing['completion_time'])
        
        # Check all constraints: distance, duration, drop count, and delivery window
        if (new_distance <= max_distance and 
            new_duration <= max_duration and
            len(route_jobs) < max_drops and
            is_time_within_window(delivery_timing['arrival_time'], 
                                nearest_job['dropoff_time_from'], 
                                nearest_job['dropoff_time_to'])):
            
            # Add job to route and update tracking variables
            route_jobs.append({
                'job': nearest_job,
                'pickup_arrival_time': route_start_time,
                'dropoff_arrival_time': delivery_timing['arrival_time'],
                'completion_time': delivery_timing['completion_time']
            })
            
            # Update current position and time for next iteration
            available_jobs.remove(nearest_job)
            current_location = (nearest_job['dropoff_lat'], nearest_job['dropoff_lng'])
            current_time = delivery_timing['completion_time']
            total_distance_miles = new_distance
        else:
            # Cannot add this job without violating constraints
            break
    
    # Build route coordinate list for Google Maps URL generation
    route_points = [depot_location] + [(job_info['job']['dropoff_lat'], job_info['job']['dropoff_lng']) 
                                      for job_info in route_jobs]
    
    return {
        'route_number': 0,
        'jobs': route_jobs,
        'total_distance_miles': round(total_distance_miles, 2),
        'total_duration_minutes': time_difference_minutes(route_start_time, current_time) if route_jobs else 0,
        'start_time': route_start_time,
        'end_time': current_time if route_jobs else route_start_time,
        'google_maps_url': generate_google_maps_url(route_points)
    }


def get_jobs_within_dropoff_window(jobs: List[Dict], current_time: str) -> List[Dict]:
    """Filter jobs where current time is within dropoff window."""
    return [job for job in jobs 
            if is_time_within_window(current_time, job['dropoff_time_from'], job['dropoff_time_to'])]


def find_nearest_delivery_job(current_location: Tuple[float, float], valid_jobs: List[Dict]) -> Optional[Dict]:
    """Find closest delivery location using nearest neighbor algorithm."""
    # Return job with minimum straight-line distance to dropoff point
    if not valid_jobs:
        return None
    
    return min(valid_jobs, 
              key=lambda job: haversine_distance(current_location[0], current_location[1],
                                                job['dropoff_lat'], job['dropoff_lng']))


def calculate_delivery_timing(current_location: Tuple[float, float], current_time: str, 
                            job: Dict, delivery_time: int) -> Dict:
    """Calculate timing information for delivery operation."""
    # Calculate travel distance and time-adjusted travel duration
    travel_distance = haversine_distance(current_location[0], current_location[1],
                                        job['dropoff_lat'], job['dropoff_lng'])
    travel_time = calculate_travel_time(travel_distance, current_time)
    arrival_time = add_minutes_to_time(current_time, travel_time)
    completion_time = add_minutes_to_time(arrival_time, delivery_time)
    
    return {
        'travel_distance': travel_distance,
        'arrival_time': arrival_time,
        'completion_time': completion_time
    }


def save_routes_to_csv(routes: List[Dict], output_file: str) -> str:
    import os
    # Ensure the routes directory exists
    routes_dir = os.path.join('data', 'routes')
    os.makedirs(routes_dir, exist_ok=True)
    
    # Update output file path to be in routes folder
    if not output_file.startswith(routes_dir):
        output_file = os.path.join(routes_dir, os.path.basename(output_file))
    
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        
        writer.writerow([
            'Route Number', 'Job Number', 'Pickup Address', 'Pickup Lat', 'Pickup Lng', 
            'Pickup Arrival Time', 'Dropoff Address', 'Dropoff Lat', 'Dropoff Lng',
            'Drop-off Window Start', 'Drop-off Window End', 'Estimated Arrival Window Start',
            'Estimated Arrival Window End', 'Dropoff Arrival Time', 'Completion Time',
            'Route Distance (Miles)', 'Route Duration (Minutes)', 'Google Maps URL'
        ])
        
        for route in routes:
            for i, job_info in enumerate(route['jobs'], 1):
                job = job_info['job']
                
                # Calculate estimated arrival window (5 minutes either side of arrival time)
                arrival_time = job_info['dropoff_arrival_time']
                estimated_window_start = subtract_minutes_from_time(arrival_time, 5)
                estimated_window_end = add_minutes_to_time(arrival_time, 5)
                
                writer.writerow([
                    f"Route {route['route_number']}",
                    i,
                    job['pickup_address'],
                    job['pickup_lat'],
                    job['pickup_lng'],
                    job_info['pickup_arrival_time'],
                    job['dropoff_address'],
                    job['dropoff_lat'],
                    job['dropoff_lng'],
                    job['dropoff_time_from'],
                    job['dropoff_time_to'],
                    estimated_window_start,
                    estimated_window_end,
                    job_info['dropoff_arrival_time'],
                    job_info['completion_time'],
                    route['total_distance_miles'],
                    route['total_duration_minutes'],
                    route['google_maps_url']
                ])
    
    return output_file


