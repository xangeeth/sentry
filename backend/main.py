from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

import models
from database import engine, SessionLocal
# Import our new scanner module
from scanner import check_vulnerabilities

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Project Sentry API", version="1.0")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class SwitchData(BaseModel):
    vendor: str
    model: str
    firmware_version: str
    running_config: str

@app.get("/")
def read_root():
    return {"status": "Project Sentry Engine is Online", "version": "1.0"}

@app.post("/api/v1/audit")
def audit_switch(switch: SwitchData, db: Session = Depends(get_db)):
    # 1. Fire the live request to the NIST NVD database
    scan_results = check_vulnerabilities(
        vendor=switch.vendor, 
        model=switch.model, 
        version=switch.firmware_version
    )
    
    # 2. Map incoming data to our local SQLAlchemy database filing cabinet
    new_db_switch = models.Switch(
        vendor=switch.vendor,
        model=switch.model,
        firmware_version=switch.firmware_version,
        running_config=switch.running_config
    )
    
    # 3. Save to local SQLite database
    db.add(new_db_switch)
    db.commit()
    db.refresh(new_db_switch)
    
    # 4. Return the combined intelligence back to the user
    return {
        "message": f"Successfully processed {switch.vendor} {switch.model}",
        "database_id": new_db_switch.id,
        "security_scan": scan_results,
        "status": "Ready for Deep AI Analysis"
    }