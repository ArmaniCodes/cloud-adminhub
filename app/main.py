from fastapi import FastAPI
from app.routes.users import router

app = FastAPI()
app.include_router(router)

# Health Check
@app.get("/health")
def health_check():
    return {"status":"healthy"}

