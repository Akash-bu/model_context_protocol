from typing import Any 
import httpx 
from mcp.server.fastmcp import FastMCP 

mcp = FastMCP("weather") 

api_base = "https://api.weather.gov"
user_agent = "weather-app/1.0"

#Helper functions 

async def make_new_request(url: str) -> dict[str, Any] | None:
    """Make a request to the NWS API with proper error handling."""
    headers = {
        "User-Agent": user_agent,
        "Accept": "application/geo+json"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers = headers, timeout=40.0)
            response.raise_for_status() 
            print(response.status_code())
            return response.json()
        except Exception:
            return None 

def format_alert(feature: dict) -> str:
    """Format an alert feature into a readable string."""

    prop = feature["properties"]
    return f"""
Event: {prop.get('event', 'unknown')}
Area: {prop.get('areaDesc', 'Unknown')}
Severity: {prop.get('severity', 'Unknown')}
Description: {prop.get('description', 'No description avaliable')}
Instructions: {prop.get('instruction', 'No specific instructions provided')}
"""

@mcp.tool()
async def get_alerts(state: str) -> str:
    """Get weather alerts for a US state.

    Args:
        state: Two-letter US state code (e.g. CA, NY)
    """
    url = f"{api_base}/alerts/activate/area/{state}"
    data = await make_new_request(url)

    if not data or "features" not in data:
        return "Unable to fetch alerts or no alerts found."
    
    if not data["features"]:
        return "No active alerts for this state"
    
    alerts = [format_alert(feature) for feature in data["features"]]
    return "\n---\n".join(alerts)

@mcp.tool()
async def get_forecast(latitude: float, longitude: float) -> str:
    """Get weather forecast for a location.

    Args:
        latitude: Latitude of the location
        longitude: Longitude of the location
    """
    points_url = f"{api_base}/points/{latitude},{longitude}"
    points_data = await make_new_request(points_url)

    if not points_data:
        return "Unable to fetch forecast data for this location"
    
    forecast_url = points_data["properties"]["forecast"]
    forecast_data = await make_new_request(forecast_url)

    if not forecast_data:
        return "Unable to fetch detailed forecast"
    
    periods = forecast_data["properties"]["periods"]
    forecasts = []
    for period in periods[:5]:
        forecast = f"""
{period["name"]}:
Temperature: {period['temperature']}°{period['temperatureUnit']}
Wind: {period['windSpeed']} {period['windDirection']}
Forecast: {period['detailedForecast']}
"""
        forecasts.append(forecast)
    return "\n---\n".join(forecasts)

if __name__ == "__main__":
    mcp.run(transport='stdio')
