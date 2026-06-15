from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel

import models
import discovery  # Our new module!
from database import engine, SessionLocal
from scanner import check_vulnerabilities
from brain import analyze_config

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Project Sentry API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    threat_count: int = 0 

@app.get("/")
def read_root():
    return {"status": "Project Sentry Engine is Online", "version": "1.0"}

@app.post("/api/v1/scan")
def run_scan(switch: SwitchData):
    scan_results = check_vulnerabilities(
        vendor=switch.vendor, 
        model=switch.model, 
        version=switch.firmware_version
    )
    return {"security_scan": scan_results}

@app.post("/api/v1/analyze")
def run_ai(switch: SwitchData, db: Session = Depends(get_db)):
    ai_summary = analyze_config(
        vendor=switch.vendor,
        model=switch.model,
        running_config=switch.running_config,
        vulnerabilities_found=switch.threat_count 
    )
    
    new_db_switch = models.Switch(
        vendor=switch.vendor,
        model=switch.model,
        firmware_version=switch.firmware_version,
        running_config=switch.running_config
    )
    db.add(new_db_switch)
    db.commit()
    db.refresh(new_db_switch)
    
    return {"ccie_ai_analysis": ai_summary, "database_id": new_db_switch.id}

# --- ENDPOINT 3: DYNAMIC DISCOVERY ---
class DiscoveryRequest(BaseModel):
    ip_address: str
    username: str
    password: str

@app.post("/api/v1/discover")
def discover_switch(request: DiscoveryRequest):
    result = discovery.run_discovery(
        ip=request.ip_address,
        username=request.username,
        password=request.password
    )
    return result