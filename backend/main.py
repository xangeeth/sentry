from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

# Import our custom modules
import models
from database import engine, SessionLocal
from scanner import check_vulnerabilities
from brain import analyze_config

# Create Database tables
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
    
    # 2. Extract the number of threats found (defaults to 0 if something fails)
    threat_count = scan_results.get("vulnerabilities_found", 0)
    
    # 3. Fire the config AND the threat intelligence to your CCIE AI
    ai_summary = analyze_config(
        vendor=switch.vendor,
        model=switch.model,
        running_config=switch.running_config,
        vulnerabilities_found=threat_count
    )
    
    # 4. Save to local SQLite database
    new_db_switch = models.Switch(
        vendor=switch.vendor,
        model=switch.model,
        firmware_version=switch.firmware_version,
        running_config=switch.running_config
    )
    db.add(new_db_switch)
    db.commit()
    db.refresh(new_db_switch)
    
    # 5. Return the Ultimate Unified Response
    return {
        "message": f"Successfully processed {switch.vendor} {switch.model}",
        "database_id": new_db_switch.id,
        "security_scan": scan_results,
        "ccie_ai_analysis": ai_summary 
    }