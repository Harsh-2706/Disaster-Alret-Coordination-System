import requests
import json
from datetime import datetime

# API keys (replace with your own)
OPENWEATHERMAP_API_KEY = 'YOUR_OPENWEATHERMAP_API_KEY'
NEWSAPI_KEY = 'YOUR_NEWSAPI_KEY'

# Base URLs for APIs
WEATHER_BASE_URL = 'https://api.openweathermap.org/data/2.5/weather?'
NEWS_BASE_URL = 'https://newsapi.org/v2/everything?'

def get_weather_report(city):
    """Fetch weather report for the given city using OpenWeatherMap API."""
    try:
        # Construct the weather API URL
        weather_url = f"{WEATHER_BASE_URL}q={city}&appid={OPENWEATHERMAP_API_KEY}&units=metric"
        response = requests.get(weather_url)
        
        # Check if the request was successful
        if response.status_code == 200:
            data = response.json()
            main = data['main']
            weather = data['weather'][0]
            
            # Extract weather details
            temperature = main['temp']
            humidity = main['humidity']
            pressure = main['pressure']
            description = weather['description'].capitalize()
            
            return {
                'temperature': temperature,
                'humidity': humidity,
                'pressure': pressure,
                'description': description
            }
        else:
            return None
    except Exception as e:
        print(f"Error fetching weather data: {e}")
        return None

def get_disaster_news(city):
    """Fetch recent disaster-related news for the given city using NewsAPI."""
    try:
        # Keywords for disaster-related news
        disaster_keywords = 'flood OR earthquake OR hurricane OR tornado OR wildfire OR disaster'
        query = f"{disaster_keywords} {city}"
        
        # Construct the news API URL
        news_url = f"{NEWS_BASE_URL}q={query}&apiKey={NEWSAPI_KEY}&language=en&sortBy=publishedAt"
        response = requests.get(news_url)
        
        # Check if the request was successful
        if response.status_code == 200:
            data = response.json()
            articles = data.get('articles', [])
            return articles[:3]  # Return up to 3 recent articles
        else:
            return []
    except Exception as e:
        print(f"Error fetching news data: {e}")
        return []

def main():
    # Get city input from user
    city = input("Enter city name: ").strip()
    
    # Get weather report
    weather = get_weather_report(city)
    if weather:
        print(f"\n{'Weather Report for ' + city:-^50}")
        print(f"Temperature: {weather['temperature']}°C")
        print(f"Humidity: {weather['humidity']}%")
        print(f"Pressure: {weather['pressure']} hPa")
        print(f"Description: {weather['description']}")
    else:
        print(f"\nError: Could not fetch weather data for {city}. Please check the city name or API key.")
    
    # Get disaster news
    print(f"\n{'Recent Disaster News for ' + city:-^50}")
    news_articles = get_disaster_news(city)
    if news_articles:
        for i, article in enumerate(news_articles, 1):
            title = article.get('title', 'No title')
            source = article.get('source', {}).get('name', 'Unknown source')
            url = article.get('url', 'No URL')
            published_at = article.get('publishedAt', 'Unknown date')
            print(f"\n{i}. {title}")
            print(f"   Source: {source}")
            print(f"   Published: {published_at}")
            print(f"   URL: {url}")
    else:
        print(f"No recent disaster-related news found for {city}.")

if _name_ == "_main_":
    main()