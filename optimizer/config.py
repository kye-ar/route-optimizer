# Route Constraints
max_distance_miles = 120
max_route_duration_minutes = 480  # 8 hours in minutes
max_drop_count = 20 # max number of drops per route

# Time Settings
estimated_delivery_time = 5 # minutes for delivery completion
default_start_time = "10:00:00"  # Majority of drop off windows begin at 10am

# Collection point (London central)
default_collection_point = (51.5074, -0.1278)

# Distance-based Speed Settings (mph)
speed_central_london = 4     # <= 1 mile: heavy congestion, traffic lights
speed_urban_london = 8     # 1-3 miles: moderate traffic  
speed_outer_london = 14       # 3-5 miles: outer London areas
speed_long_distance = 25      # > 5 miles: may include faster roads

# Distance Thresholds (miles)
distance_threshold_central = 1.0
distance_threshold_urban = 3.0  
distance_threshold_outer = 5.0

# Peak Hour Settings
peak_hours = ["08:00:00", "09:00:00", "17:00:00", "18:00:00", "19:00:00"]
peak_hour_speed_reduction = 0.7  # 30% speed reduction during peak hours

