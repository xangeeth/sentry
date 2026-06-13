from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

# Import our custom database files
import models
from database import engine, SessionLocal

# 1. CREATE THE DATABASE FILE
# This line tells SQLAlchemy to look at our models and build the actual SQLite file.
models.Base.metadata.create_all(bind=engine)

# Initialize the application
app = FastAPI(title="Project Sentry API", version="1.0")

# 2. THE DATABASE DEPENDENCY
# This safely opens a connection to the DB for a request, and closes it when done.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 3. THE BLUEPRINT (Pydantic)
class SwitchData(BaseModel):
    vendor: str
    model: str
    firmware_version: str
    running_config: str

# 4. THE ENDPOINTS
@app.get("/")
def read_root():
    return {"status": "Project Sentry Engine is Online", "version": "1.0"}

@app.post("/api/v1/audit")
def audit_switch(switch: SwitchData, db: Session = Depends(get_db)):
    # A. Map the incoming Pydantic data to our SQLAlchemy database model
    new_db_switch = models.Switch(
        vendor=switch.vendor,
        model=switch.model,
        firmware_version=switch.firmware_version,
        running_config=switch.running_config
    )
    
    # B. Add it to the database and lock it in (commit)
    db.add(new_db_switch)
    db.commit()
    db.refresh(new_db_switch) # Refreshes to grab the auto-generated ID
    
    return {
        "message": f"Successfully saved config for {switch.vendor} {switch.model} to Sentry Database.",
        "database_id": new_db_switch.id,
        "status": "Ready for AI Analysis"
    }