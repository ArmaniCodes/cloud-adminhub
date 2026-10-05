from fastapi import FastAPI
from app.routes import users,auth, audit


app = FastAPI()
app.include_router(users.router)
app.include_router(auth.router)
app.include_router(audit.router)
# Health Check
@app.get("/health")
def health_check():
    return {"status":"healthy"}

