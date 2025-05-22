### Hunter College 499 Capstone by **Abdul Hosain** and **Zuriel Huerta**

# 🌬️ AirTrak: A Real-Time Air Quality Monitoring System

Welcome to **AirTrak**, a full-stack application built by **Abdul Hosain** and **Zuriel Huerta** that enables real-time tracking, visualization, and management of air quality data using sensor-equipped Raspberry Pi devices.

---

## 📌 Project Overview

Air quality is a key factor in our health and comfort—but consistent tracking outside commercial use can be expensive or inaccessible. **AirTrak** simplifies this by allowing users to place low-cost sensors around key locations and view real-time air quality data (PM2.5, PM10, AQI) through a clean web dashboard.

**Core Goal:**  
To provide accessible, actionable insights into air quality on an individual level.

---

## 🏗️ Architecture Overview

The system is composed of 5 core components:

1. **📡 Raspberry Pi** – Collects data and transmits it using WebSockets.
2. **⚙️ FastAPI Backend** – Formats data and stores it in a hosted SQL database. Also handles authentication with MongoDB.
3. **🖥️ Frontend Dashboard** – Displays live metrics and historical trends via real-time graphs.
4. **📊 Supabase SQL Database** – Stores and serves clean, structured air quality data.
5. **🔐 MongoDB** – Manages login credentials with support for future scalability.

---

## 🧪 Features

- Real-time streaming of air quality data using WebSockets.
- Historical data visualization and CSV import support.
- Login authentication using a MongoDB backend.
- Live charts that update with minimal buffering.
- Public AQI integration via AirVisual API.

---

## 👩‍💻 Tech Stack

**Backend:**
- FastAPI
- Uvicorn
- WebSockets
- Supabase (PostgreSQL)
- MongoDB (authentication)

**Frontend:**
- JavaScript (React)
- Real-time Charts (e.g., Recharts or Chart.js)
- API/WebSocket integrations

**Hardware:**
- Raspberry Pi with PM2.5/PM10 sensor

---

## 🧠 Lessons Learned

- Working in parallel is hard without good task boundaries.
- Database schema design and restructuring was a major challenge.
- Hosting multiple services (frontend, backend, WebSockets) involved numerous configuration hurdles.
- Limited Raspberry Pi and FastAPI documentation led to trial-and-error-based development.

---


