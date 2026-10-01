from fastapi import FastAPI
from app.routes import users,auth
from app.security import auth as auth_test

app = FastAPI()
app.include_router(users.router)
app.include_router(auth.router)
app.include_router(auth_test.router)

# Health Check
@app.get("/health")
def health_check():
    return {"status":"healthy"}

