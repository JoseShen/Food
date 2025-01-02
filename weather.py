import requests
import os
from dotenv import load_dotenv
load_dotenv()
def get_weather(city):
    """
    Get current weather data for a city using OpenWeather API
    
    Parameters:
    city (str): Name of the city    
    Returns:
    dict: Weather data
    """
    OPEN_WEATHER_API_KEY = os.getenv('OPEN_WEATHER_API_KEY')

    base_url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        'q': city,
        'appid': OPEN_WEATHER_API_KEY,
        'units': 'metric' 
    }
    
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()  # Raise an exception for bad status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching weather data: {e}")
        return None

# Example usage
