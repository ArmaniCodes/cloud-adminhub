from fastapi import FastAPI
from pydantic import BaseModel
from random import randint

app = FastAPI()

class User(BaseModel):
        id: int
        name: str
        email:str
        role: str

class CreateUser(BaseModel):
     name: str
     email: str
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

@app.post("/users",response_model=User)
def post_user(user: CreateUser):
    # Generate random temp id for now
    generate_id = randint(1,1000)
    new_user = {'id':generate_id}
    new_user.update(user.model_dump())
    user_list.append(new_user)
    return new_user