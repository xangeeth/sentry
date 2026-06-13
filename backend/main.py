from fastapi import FastAPI
from pydantic import BaseModel

# Initialize the application
app = FastAPI(title="Project Sentry API", version="1.0")

# 1. THE BLUEPRINT (Pydantic Model)
# This dictates exactly what a switch configuration MUST look like.
class SwitchData(BaseModel):
    vendor: str
    model: str
    firmware_version: str
    running_config: str

# 2. THE STATUS ENDPOINT (Checking if the engine is alive)
@app.get("/")
def read_root():
    return {"status": "Project Sentry Engine is Online", "version": "1.0"}

# 3. THE AUDIT ENDPOINT (Where the magic will happen)
# This endpoint 'listens' for switch data and validates it against our blueprint.
@app.post("/api/v1/audit")
def audit_switch(switch: SwitchData):
    # Right now, we just echo the data back to prove the connection works.
    # Later, this is where we will send the config to Ollama and the NVD database.
    return {
        "message": f"Successfully received config for {switch.vendor} {switch.model}",
        "status": "Ready for AI Analysis",
        "data_received": switch
    }