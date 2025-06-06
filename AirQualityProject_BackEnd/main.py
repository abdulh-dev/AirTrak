from fastapi import FastAPI, Query, UploadFile, File, HTTPException, Form
from supabase import create_client, Client
from datetime import datetime
from typing import List
import pandas as pd
import requests
from io import StringIO
import os
from fastapi import WebSocket, WebSocketDisconnect
import json
from pymongo import MongoClient


# MongoDB setup
mongo_client = MongoClient(os.environ.get("MONGODB_URI"))
mongo_db = mongo_client[os.environ.get("MONGO_DB_NAME")]
users_collection = mongo_db["users"]



# === SUPABASE CONFIGURATION ===
database_url = os.environ.get('DATABASE_URL')  # should be your Supabase URL
database_key = os.environ.get('DATABASE_KEY')  # should be your Supabase anon or service key
supabase: Client = create_client(database_url, database_key)



# === PUBLIC AQI API KEY ===
API_KEY = os.environ.get('PUBLIC_AQI_API_KEY')
permissions_string = ""
app = FastAPI()


@app.post("/login")
def login(username: str = Form(...), password: str = Form(...)):
    user = users_collection.find_one({"username": username})

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    if user.get("password") != password:
        permissions_string = user.get("permissions")
        raise HTTPException(status_code=401, detail="Incorrect password")
    
    return {"message": f"Login successful for user: {username}"}


# === PRIVATE DATASET FUNCTIONS ===
def fetch_latest_entry():
    response = (
        supabase.table('airqualitydata')
        .select("*")
        .order('timestamp', desc=True)
        .limit(1)
        .execute()
    )
    return response.data[0] if response.data else {"message": "No data found."}


def insert_realtime_data(pm2_5: float, pm10: float, aqi: int, timestamp: str):
    return supabase.table('airqualitydata').insert({
        "pm2_5": pm2_5,
        "pm10": pm10,
        "aqi": aqi,
        "timestamp": timestamp
    }).execute()


def delete_oldest_entry():
    response = (
        supabase.table('airqualitydata')
        .select("id")
        .order("id", asc=True)
        .limit(1)
        .execute()
    )

    if not response.data:
        return {"message": "No entry to delete."}

    oldest_id = response.data[0]["id"]
    return supabase.table('airqualitydata').delete().eq("id", oldest_id).execute()


# === PUBLIC DATASET FUNCTIONS ===
def update_public_aqi(place_name, current_aqi, last_updated):
    return supabase.table("locationaqi").upsert({
        "place_name": place_name,
        "current_aqi": current_aqi,
        "last_updated": last_updated
    }).execute()


def collect_public_data(cities: list[str], country: str, state: str):
    data = []

    for city in cities:
        url = (
            f"http://api.airvisual.com/v2/city?"
            f"city={city}&state={state}&country={country}&key={API_KEY}"
        )
        response = requests.get(url)

        if response.status_code == 200:
            try:
                aqius = response.json()['data']['current']['pollution']['aqius']
                data.append({'City': city, 'AQI_US': aqius})
            except KeyError:
                print(f"No AQI data found for {city}.")
        else:
            print(f"Failed to get data for {city}: {response.status_code}")

    df = pd.DataFrame(data)
    now = datetime.utcnow().isoformat()

    for _, row in df.iterrows():
        update_public_aqi(row['City'], row['AQI_US'], now)

    return df.to_dict(orient="records")


# === FASTAPI ROUTES ===

@app.get("/private/latest")
def get_latest():
    return fetch_latest_entry()


@app.post("/private/insert")
def insert_data(pm2_5: float, pm10: float, aqi: int, timestamp: str):
    return insert_realtime_data(pm2_5, pm10, aqi, timestamp)


@app.delete("/private/delete-oldest")
def delete_oldest():
    return delete_oldest_entry()


@app.post("/public/collect")
def collect(cities: list[str] = Query(...), country: str = "USA", state: str = "California"):
    return collect_public_data(cities, country, state)



""" Csv file should be formatted like this
pm2_5,pm10,aqi,timestamp
12.5,30.2,85,2025-04-20T12:34:56
15.0,28.1,79,2025-04-20T12:39:56
Not the final form of function due to need for optimization
""" 

@app.post("/upload-csv")
async def upload_csv(file: UploadFile = File(...)):
    if not file.filename.endswith(".csv"):
        return {"error": "Only CSV files are accepted."}

    content = await file.read()
    csv_data = content.decode("utf-8")
    df = pd.read_csv(StringIO(csv_data))

    required_columns = {"pm2_5", "pm10", "aqi", "timestamp"}
    if not required_columns.issubset(df.columns):
        return {
            "error": f"CSV must contain the following columns: {required_columns}"
        }

    inserted_rows = 0
    for _, row in df.iterrows():
        try:
            insert_realtime_data(
                pm2_5=row["pm2_5"],
                pm10=row["pm10"],
                aqi=int(row["aqi"]),
                timestamp=row["timestamp"],
            )
            inserted_rows += 1
        except Exception as e:
            print(f"Failed to insert row: {e}")

    return {"message": f"Inserted {inserted_rows} rows into the database."}


@app.get("/private-data")
def get_private_data():
    response = (
        supabase.table('airqualitydata')
        .select("*")
        .order('timestamp', desc=True)
        .limit(20)
        .execute()
    )
    return response.data


@app.get("/public-data")
def get_public_data():
    response = (
        supabase.table('locationaqi')
        .select("*")
        .order('last_updated', desc=True)
        .limit(20)
        .execute()
    )
    return response.data

@app.websocket("/ws/ingest")
async def websocket_ingest(websocket: WebSocket):
    await websocket.accept()
    print("WebSocket connection accepted")

    try:
        while True:
            message = await websocket.receive_text()  # Expecting CSV string like: "pm2_5,pm10,aqi,timestamp"
            try:
                pm2_5, pm10, aqi, timestamp = message.strip().split(",")
                insert_realtime_data(
                    pm2_5=float(pm2_5),
                    pm10=float(pm10),
                    aqi=int(aqi),
                    timestamp=timestamp
                )
                await websocket.send_text("Data received and stored.")
            except Exception as e:
                await websocket.send_text(f"Error parsing data: {e}")

    except WebSocketDisconnect:
        print("WebSocket disconnected")
