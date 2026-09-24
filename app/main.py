from fastapi import FastAPI

app = FastAPI()

# Health Check
@app.get("/health")
def health_check():
    return {"status":"healthy"}

# In-memory test users for development purposes
user_list = [{'id': 23,'name':"John Smith",'email':'john@doe.com',"role":"Lead Marketing"},
             {'id': 12,'name':"Sarah Smith",'email':'jane@doe.com',"role":"Recruiter"}
             ]

# Users endpoint
@app.get("/users")
def get_users():
    return user_list
