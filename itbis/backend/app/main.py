from fastapi import FastAPI

app = FastAPI(title="ITBIS API")


@app.get("/")
def health_check():
    return {"status": "ITBIS backend is running"}
