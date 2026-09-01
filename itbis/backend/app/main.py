from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine
from .routes.health import router as health_router
from .auth import router as auth_router
from .activity_log import log_activity
from .routes.employee import router as employee_router
app = FastAPI(title="ITBIS API")
app.include_router(employee_router)
app.include_router(health_router)
app.include_router(auth_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)


@app.get("/")
def health_check():
    return {"status": "ITBIS backend is running"}


@app.post("/activity")
def create_activity(employee_id: str, activity: str, risk_score: int = 0):
    log_activity(employee_id, activity, risk_score)
    return {"message": "Activity logged successfully"}
