from fastapi import HTTPException
from fastapi.responses import HTMLResponse
import pandas as pd
import os

async def data_source_table_view():
    """
    Load CSV file, convert to HTML table, return as endpoint response.
    """
    # Load source customer data for display
    file_path = os.path.join('data', 'customer-requests-testingLondon36.csv')

    try:
        # Load CSV with pandas for easy manipulation
        df = pd.read_csv(file_path)

        # Convert DataFrame to HTML table without row indices
        html_table = df.to_html(index=False)

        # Return as HTML response for browser display
        return HTMLResponse(content=html_table)

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="CSV file not found")
    except pd.errors.EmptyDataError:
        raise HTTPException(status_code=400, detail="CSV file is empty")
    except pd.errors.ParserError:
        raise HTTPException(status_code=400, detail="CSV file format is invalid")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading CSV: {str(e)}")


async def routes_table_view():
    """
    Load optimized routes CSV file, convert to HTML table, return as endpoint response.
    """
    # Load generated route optimization results
    file_path = os.path.join('data', 'routes', 'optimized_routes.csv')

    try:
        # Load optimized routes CSV with pandas
        df = pd.read_csv(file_path)

        # Convert long Google Maps URLs to clickable links for better display
        if 'Google Maps URL' in df.columns:
            df['Google Maps URL'] = df['Google Maps URL'].apply(lambda x: f"<a href='{x}' target='_blank'>View Route</a>" if pd.notna(x) else '')

        # Simple CSS to make table more compact
        css_style = """
        <style>
        table { font-size: 12px; }
        th, td { padding: 2px 4px; }
        .route-break { border-top: 2px solid #ccc; }
        </style>
        """

        # Generate HTML table with clickable links enabled
        html_table = df.to_html(index=False, escape=False)
        
        # Add visual separators between different routes for clarity
        lines = html_table.split('\n')
        result_lines = []
        prev_route = None
        
        for line in lines:
            if '<td>Route ' in line:
                current_route = line.split('<td>Route ')[1].split('</td>')[0]
                if prev_route and current_route != prev_route:
                    # Insert empty row to visually separate routes
                    col_count = len(df.columns)
                    empty_row = f'    <tr class="route-break">{"<td>&nbsp;</td>" * col_count}</tr>'
                    result_lines.append(empty_row)
                prev_route = current_route
            result_lines.append(line)
        
        html_table = '\n'.join(result_lines)
        
        # Combine CSS styling with HTML table
        return HTMLResponse(content=css_style + html_table)

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Routes CSV file not found. Run route optimization first.")
    except pd.errors.EmptyDataError:
        raise HTTPException(status_code=400, detail="Routes CSV file is empty")
    except pd.errors.ParserError:
        raise HTTPException(status_code=400, detail="Routes CSV file format is invalid")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading routes CSV: {str(e)}")
