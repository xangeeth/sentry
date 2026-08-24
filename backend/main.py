from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone

import csv
import io
from fastapi import Response

import models
import discovery
from database import engine, SessionLocal
from scanner import check_vulnerabilities
from brain import analyze_config, ask_assistant

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Project Sentry API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"], 
    allow_credentials=False,
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
    running_config: str = "N/A"
    threat_count: int = 0 
    hostname: Optional[str] = "Unknown"
    ip_address: Optional[str] = "127.0.0.1"

class DiscoveryRequest(BaseModel):
    ip_address: str
    username: Optional[str] = None
    password: Optional[str] = None
    secret: Optional[str] = None

class AssistantRequest(BaseModel):
    prompt: str

@app.get("/")
def read_root():
    return {"status": "Project Sentry Engine is Online", "version": "1.0"}

@app.get("/api/v1/switches")
def get_switches(db: Session = Depends(get_db)):
    switches = db.query(models.Switch).all()
    return [
        {
            "id": s.id,
            "hostname": s.hostname or "Unknown",
            "ip_address": s.ip_address or "127.0.0.1",
            "vendor": s.vendor,
            "model": s.model,
            "firmware_version": s.firmware_version,
            "threat_count": s.threat_count if s.threat_count is not None else -1,
            "running_config": s.running_config or "N/A",
            "discovery_protocol": getattr(s, 'discovery_protocol', 'RESTCONF') or 'RESTCONF',
            "last_audited": s.last_audited.isoformat() if s.last_audited else None
        }
        for s in switches
    ]

class DeleteRequest(BaseModel):
    id: Optional[int] = None
    ip_address: Optional[str] = None
    hostname: Optional[str] = None

@app.post("/api/v1/switches/delete")
@app.delete("/api/v1/switches/{identifier}")
def delete_switch(identifier: Optional[str] = None, req: Optional[DeleteRequest] = None, db: Session = Depends(get_db)):
    target_id = req.id if req else None
    target_ip = req.ip_address if req else None
    target_name = req.hostname if req else None
    target_str = identifier or target_ip or target_name or (str(target_id) if target_id else None)

    query = db.query(models.Switch)
    target = None

    if target_id:
        target = query.filter(models.Switch.id == target_id).first()
    if not target and target_str and target_str.isdigit():
        target = query.filter(models.Switch.id == int(target_str)).first()
    if not target and target_str:
        target = query.filter(
            (models.Switch.ip_address == target_str) | (models.Switch.hostname == target_str)
        ).first()
    if not target and target_str and ":" in target_str:
        clean_ip = target_str.split(":")[0]
        target = query.filter(models.Switch.ip_address == clean_ip).first()

    if not target:
        raise HTTPException(status_code=404, detail="Switch record not found in database")

    db.delete(target)
    db.commit()
    return {"status": "success", "message": "Switch deleted successfully"}

class RescanRequest(BaseModel):
    ip_address: Optional[str] = None

@app.post("/api/v1/switches/rescan")
def rescan_switches(req: Optional[RescanRequest] = None, ip_address: Optional[str] = None, db: Session = Depends(get_db)):
    target_ip = (req.ip_address if req else None) or ip_address
    query = db.query(models.Switch)
    if target_ip:
        switches_to_scan = query.filter(
            (models.Switch.ip_address == target_ip) | (models.Switch.ip_address == target_ip.split(":")[0])
        ).all()
    else:
        switches_to_scan = query.all()

    updated_count = 0
    for sw in switches_to_scan:
        res = discovery.run_discovery(sw.ip_address)
        if res and res.get("status") == "success":
            sw.hostname = res.get("hostname", sw.hostname)
            sw.vendor = res.get("vendor", sw.vendor)
            sw.model = res.get("model", sw.model)
            sw.firmware_version = res.get("firmware_version", sw.firmware_version)
            sw.running_config = res.get("running_config", sw.running_config)
            sw.discovery_protocol = res.get("discovery_protocol", sw.discovery_protocol)
            sw.last_audited = datetime.now(timezone.utc)
            updated_count += 1

    db.commit()
    return {"status": "success", "updated_count": updated_count, "message": f"Successfully re-scanned {updated_count} live switch nodes"}

class SwitchData(BaseModel):
    hostname: Optional[str] = None
    ip_address: Optional[str] = None
    vendor: str
    model: str
    firmware_version: str
    running_config: Optional[str] = None

class ScanQuery(BaseModel):
    query: str

@app.get("/api/v1/inventory", response_model=List[dict])
def get_inventory(db: Session = Depends(get_db)):
    switches = db.query(models.Switch).all()
    return [
        {
            "id": s.id,
            "hostname": s.hostname,
            "ip_address": s.ip_address,
            "vendor": s.vendor,
            "model": s.model,
            "firmware_version": s.firmware_version,
            "threat_count": s.threat_count
        }
        for s in switches
    ]

@app.get("/api/v1/lifecycle")
def get_lifecycle(vendor: str = "", model: str = "", db: Session = Depends(get_db)):
    query = db.query(models.HardwareLifecycle)
    if vendor:
        query = query.filter(models.HardwareLifecycle.vendor.ilike(f"%{vendor}%"))
    if model:
        query = query.filter(models.HardwareLifecycle.model.ilike(f"%{model}%"))
    
    records = query.all()
    return [
        {
            "id": r.id,
            "vendor": r.vendor,
            "model": r.model,
            "end_of_sale": r.end_of_sale.isoformat() if r.end_of_sale else None,
            "end_of_life": r.end_of_life.isoformat() if r.end_of_life else None
        }
        for r in records
    ]

@app.post("/api/v1/scan")
def run_scan(scan: ScanQuery):
    scan_results = check_vulnerabilities(scan.query)
    return {"security_scan": scan_results}

def count_config_vulnerabilities(config_text: str) -> int:
    """ Counts explicit security vulnerabilities in running-config """
    if not config_text or config_text == "N/A":
        return 0
    issues = 0
    text_lower = config_text.lower()
    if "enable password" in text_lower:
        issues += 1
    if "transport input telnet" in text_lower or "transport input telnet ssh" in text_lower:
        issues += 1
    if "ip http server" in text_lower and "no ip http server" not in text_lower:
        issues += 1
    if "no service password-encryption" in text_lower:
        issues += 1
    if "snmp-server community public" in text_lower or "snmp-server community private" in text_lower:
        issues += 1
    if "vstack" in text_lower and "no vstack" not in text_lower:
        issues += 1
    return issues

@app.post("/api/v1/analyze")
def run_ai(switch: SwitchData, db: Session = Depends(get_db)):
    # 1. Query NIST NVD API v2.0 for live CVEs matching vendor, model, firmware
    query_str = f"{switch.vendor} {switch.model} {switch.firmware_version}".strip()
    nist_res = check_vulnerabilities(query_str)
    
    # Smart Fallback for NVD Keyword Search
    # NVD often fails on exact "Vendor Model Firmware" strings 
    # If 0 results, try "Vendor Firmware" (e.g., "Cisco 15.2") to find OS-level CVEs without triggering false positives for patched versions.
    if nist_res.get("vulnerabilities_found", 0) == 0:
        fallback_query = f"{switch.vendor} {switch.firmware_version}".strip()
        nist_res = check_vulnerabilities(fallback_query)

    nist_cve_list = nist_res.get("top_critical_threats", [])
    nist_cve_count = nist_res.get("vulnerabilities_found", 0)

    # 2. Audit running-config for explicit security bad practices
    config_issues = count_config_vulnerabilities(switch.running_config or "")

    # 3. Calculate total evaluated threat count
    total_threats = int(nist_cve_count) + config_issues

    # 4. Generate AI security brief
    ai_summary = analyze_config(
        vendor=switch.vendor,
        model=switch.model,
        firmware_version=switch.firmware_version,
        running_config=switch.running_config,
        cve_list=nist_cve_list,
        vulnerabilities_found=total_threats
    )
    
    # Save or update switch in DB with evaluated threat count
    existing_switch = db.query(models.Switch).filter(models.Switch.ip_address == switch.ip_address).first()
    if existing_switch:
        existing_switch.vendor = switch.vendor
        existing_switch.model = switch.model
        existing_switch.firmware_version = switch.firmware_version
        existing_switch.running_config = switch.running_config
        existing_switch.threat_count = total_threats
        db.commit()
        db.refresh(existing_switch)
        db_id = existing_switch.id
    else:
        new_db_switch = models.Switch(
            hostname=switch.hostname or "Discovered-Switch",
            ip_address=switch.ip_address or "127.0.0.1",
            vendor=switch.vendor,
            model=switch.model,
            firmware_version=switch.firmware_version,
            running_config=switch.running_config,
            threat_count=total_threats
        )
        db.add(new_db_switch)
        db.commit()
        db.refresh(new_db_switch)
        db_id = new_db_switch.id
    
    return {
        "ccie_ai_analysis": ai_summary, 
        "database_id": db_id, 
        "threat_count": total_threats,
        "nist_cves": nist_cve_list
    }

@app.post("/api/v1/discover")
def discover_switch(request: DiscoveryRequest, db: Session = Depends(get_db)):
    result = discovery.run_discovery(
        ip=request.ip_address,
        username=request.username,
        password=request.password,
        secret=request.secret
    )
    
    if result and result.get("status") == "success":
        # Save or update discovered device in DB with threat_count = -1 (Pending AI Audit)
        existing = db.query(models.Switch).filter(models.Switch.ip_address == request.ip_address).first()
        protocol_used = result.get("discovery_protocol", "RESTCONF")
        if existing:
            existing.hostname = result.get("hostname", request.ip_address)
            existing.vendor = result.get("vendor", "Cisco")
            existing.model = result.get("model", "Unknown")
            existing.firmware_version = result.get("firmware_version", "Unknown")
            existing.running_config = result.get("running_config", "N/A")
            existing.discovery_protocol = protocol_used
            existing.threat_count = -1 # Pending AI Audit
            db.commit()
        else:
            new_switch = models.Switch(
                hostname=result.get("hostname", request.ip_address),
                ip_address=request.ip_address,
                vendor=result.get("vendor", "Cisco"),
                model=result.get("model", "Unknown"),
                firmware_version=result.get("firmware_version", "Unknown"),
                running_config=result.get("running_config", "N/A"),
                discovery_protocol=protocol_used,
                threat_count=-1 # Pending AI Audit
            )
            db.add(new_switch)
            db.commit()
        return {"status": "success", "device": result}
    
    # Discovery failed -> Return error response
    return {
        "status": "error",
        "message": result.get("message", "Discovery failed") if result else "Failed to connect to device"
    }

@app.get("/api/v1/export")
def export_csv(db: Session = Depends(get_db)):
    """ Pulls all audited switches from the database and generates a downloadable CSV """
    switches = db.query(models.Switch).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow(["ID", "Hostname", "IP Address", "Vendor", "Model", "Firmware", "Threat Count", "Last Audited"])
    
    for switch in switches:
        writer.writerow([
            switch.id, 
            switch.hostname, 
            switch.ip_address, 
            switch.vendor, 
            switch.model, 
            switch.firmware_version, 
            switch.threat_count, 
            switch.last_audited.strftime("%Y-%m-%d %H:%M:%S") if switch.last_audited else "N/A"
        ])
        
    return Response(
        content=output.getvalue(), 
        media_type="text/csv", 
        headers={"Content-Disposition": "attachment; filename=sentry_audit_report.csv"}
    )

@app.post("/api/v1/assistant")
def chat_with_ai(request: AssistantRequest):
    """ Converts plain-English to vendor CLI syntax """
    response = ask_assistant(request.prompt)
    return {"ai_response": response}


