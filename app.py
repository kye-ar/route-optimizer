from fastapi import FastAPI, HTTPException
from optimizer.views import data_source_table_view, routes_table_view
from optimizer.optimize_routes import optimize_routes
import os


app = FastAPI(
    title="FastAPI Route Optimizer",
    docs_url="/docs"
)

@app.get("/optimize-route/")
async def optimize_route():
    """
    Endpoint for the route optimization process.
    """
    csv_file_path = os.path.join('data', 'customer-requests-testingLondon36.csv')
    
    try:
        # Run the route optimization
        routes = optimize_routes(csv_file_path)
        
        # Extract Google Maps URLs as a simple list
        map_links = [route['google_maps_url'] for route in routes]
        
        return {
            "map_links": map_links
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.get("/data-source")
async def data_source():
    """
    Endpoint for loading the source data, formatting and returning a HTML table.
    """

    return await data_source_table_view()


@app.get("/view-routes")
async def view_routes():
    """ 
    Endpoint to view the route summaries in csv format, complete with delivery windows and times.
    """
    
    return await routes_table_view()

