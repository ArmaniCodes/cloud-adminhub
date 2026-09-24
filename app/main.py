from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class User(BaseModel):
        id: int
        name: str
        email:str
        role: str


# Health Check
@app.get("/health")
def health_check():
    return {"status":"healthy"}

# In-memory test users for development purposes
user_list = [{'id': 23,'name':"John Smith",'email':'john@doe.com',"role":"Lead Marketing"},
             {'id': 12,'name':"Sarah Smith",'email':'jane@doe.com',"role":"Recruiter"}
             ]

# Users endpoint
@app.get("/users",response_model=list[User])
def get_users():
    return user_list
