from fastapi import FastAPI, HTTPException, Depends
from supabase import create_client, Client
from pydantic import BaseModel

app = FastAPI()

SUPABASE_URL = "https://irtohomqcwviagiekpal.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlydG9ob21xY3d2aWFnaWVrcGFsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTUxNjU4OTQsImV4cCI6MjA3MDc0MTg5NH0.L5kPjrd4SY43csnuTFRuVA7wV0pIIvLXu5wO2mHgo98"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class SignupRequest(BaseModel):
    fullname: str
    email: str
    password: str
    role: str  # 'user' or 'admin'

class LoginRequest(BaseModel):
    email: str
    password: str

#Signup endpoint
@app.post("/signup")
def signup(data: SignupRequest):
    result = supabase.auth.sign_up({
        "email": data.email,
        "password": data.password
    })
    if not result.user:
        raise HTTPException(status_code=400, detail="Signup failed")
    supabase.table("profiles").insert({
        "id": result.user.id,
        "name": data.fullname,
        "email": data.email,
        "role": data.role
    }).execute()
    return {"message": "Signup successful"}

#Login endpoint
@app.post("/login")
def login(data: LoginRequest):
    result=supabase.auth.sign_in_with_password({
        "email": data.email,
        "password": data.password
    })
    if not result.user:
        raise HTTPException(status_code=400, detail="Invalid email or password")
    return {"message": "Login successful",
             "user":{
                 "id": result.user.id,
                 "email": result.user.email,
             },
             "access_token": result.session.access_token
            }

class LandRecordRequest(BaseModel):
    user_id: str
    owner_full_name: str
    contact_number: str
    parcel_id: str
    land_name: str
    size_acres: float
    description: str
    latitude: str
    longitude: str
    legal_issues: str #"yes" or "no"

@app.post("/submit_land_record")
def submit_land_record(data: LandRecordRequest):
    response = supabase.table("land_records").insert({
        "user_id": data.user_id,
        "owner_full_name": data.owner_full_name,
        "contact_number": data.contact_number,
        "parcel_id": data.parcel_id,
        "land_name": data.land_name,
        "size_acres": data.size_acres,
        "description": data.description,
        "latitude": data.latitude,
        "longitude": data.longitude,
        "legal_issues": data.legal_issues,
        "status": "pending"
    }).execute()
    if not response.data:
        raise HTTPException(status_code=400, detail="Submission failed")
    return {"message": "Land record submitted", "record_id": response.data[0]["id"]}

from fastapi import File, UploadFile

@app.post("/upload_document")
def upload_document(record_id: str, doc_type: str, file: UploadFile = File(...)):
    file_bytes = file.file.read()
    file_path = f"{record_id}/{doc_type}_{file.filename}"
    supabase.storage.from_("Documents").upload(file_path, file_bytes)
    file_url = supabase.storage.from_("Documents").get_public_url(file_path)
    response = supabase.table("Documents").insert({
        "record_id": record_id,
        "doc_type": doc_type,
        "file_url": file_url
    }).execute()
    if not response.data:
        raise HTTPException(status_code=400, detail="Document upload failed")
    return {"message": "Document uploaded", "file_url": file_url}