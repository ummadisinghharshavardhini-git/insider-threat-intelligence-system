from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import employee, health, auth, risk, activity, anomaly, anomaly_routes


app = FastAPI(
    title="ITBIS API",
    description="Insider Threat Behavioral Intelligence System API",
    version="1.0.0"
)


# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://localhost:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include API routers
app.include_router(employee.router)
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(risk.router)
app.include_router(activity.router)
app.include_router(anomaly.router)
app.include_router(anomaly_routes.router)


@app.get("/")
def root():
    return {
        "message": "ITBIS backend is running"
    }
