from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel

import csv
import io
from fastapi import Response

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

class DiscoveryRequest(BaseModel):
    ip_address: str

class AssistantRequest(BaseModel):
    prompt: str

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



@app.post("/api/v1/discover")
def trigger_discovery(request: DiscoveryRequest):
    # This triggers the Netmiko script we just wrote
    result = discovery.run_discovery(request.ip_address)
    
    if result:
        return {"status": "success", "device": result}
    
    return {"status": "error", "message": f"Failed to connect to {request.ip_address}."}

# --- ENDPOINT 4: THE CSV EXPORT ---
@app.get("/api/v1/export")
def export_csv(db: Session = Depends(get_db)):
    """ Pulls all audited switches from the database and generates a downloadable CSV """
    switches = db.query(models.Switch).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write the Header Row
    writer.writerow(["ID", "Hostname", "IP Address", "Vendor", "Model", "Firmware", "Threat Count", "Last Audited"])
    
    # Write the Data Rows
    for switch in switches:
        writer.writerow([
            switch.id, 
            switch.hostname, 
            switch.ip_address, 
            switch.vendor, 
            switch.model, 
            switch.firmware_version, 
            switch.threat_count, 
            switch.last_audited.strftime("%Y-%m-%d %H:%M:%S")
        ])
        
    # Return as a downloadable file
    return Response(
        content=output.getvalue(), 
        media_type="text/csv", 
        headers={"Content-Disposition": "attachment; filename=sentry_audit_report.csv"}
    )

# --- ENDPOINT 5: THE AI CONFIGURATION ASSISTANT ---
@app.post("/api/v1/assistant")
def chat_with_ai(request: AssistantRequest):
    """ Converts plain-English to vendor CLI syntax """
    response = brain.ask_assistant(request.prompt)
    return {"ai_response": response}

