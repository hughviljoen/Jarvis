import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import google.generativeai as genai
import requests
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Enable CORS for mobile browser testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"
WEATHER_API_KEY = "YOUR_OPENWEATHER_API_KEY" # Optional
genai.configure(api_key=GEMINI_API_KEY)

class UserRequest(BaseModel):
    prompt: str
    dob: str  # YYYY-MM-DD
    location: str

def get_age(dob_str):
    birth_date = datetime.strptime(dob_str, "%Y-%m-%d")
    today = datetime.today()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

def get_weather(city):
    # Mocking weather if no key provided, otherwise use OpenWeatherMap
    if not WEATHER_API_KEY or WEATHER_API_KEY == "YOUR_OPENWEATHER_API_KEY":
        return "Rainy" # Forced rain to test "Pivot Logic"
    
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}"
    res = requests.get(url).json()
    return res.get('weather', [{}])[0].get('main', 'Clear')

@app.post("/ask-jarvis")
async def ask_jarvis(data: UserRequest):
    age = get_age(data.dob)
    weather = get_weather(data.location)
    
    # Contextual System Prompt
    system_instruction = f"""
    You are Jarvis. User Age: {age}. Current Weather: {weather}.
    Rules:
    1. If user age < 18, never suggest 18+ venues (bars, clubs).
    2. If weather is 'Rainy' or 'Stormy', do NOT suggest outdoor activities. 
       Always pivot to an indoor alternative and explain why.
    3. Use real-time data search style for recommendations.
    4. Keep responses concise and helpful.
    """

    model = genai.GenerativeModel('gemini-1.5-flash')
    
    try:
        response = model.generate_content([system_instruction, data.prompt])
        return {
            "reply": response.text,
            "context": {"age": age, "weather": weather}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
