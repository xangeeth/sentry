from sqlalchemy import Column, Integer, String, DateTime, Date
from datetime import datetime, timezone
from database import Base

# Table 1: The Scanned Inventory (Replacing your Excel sheet)
class Switch(Base):
    __tablename__ = "switches"
    
    id = Column(Integer, primary_key=True, index=True)
    hostname = Column(String, default="Unknown")
    ip_address = Column(String, unique=True, index=True)
    vendor = Column(String)
    model = Column(String)
    firmware_version = Column(String)
    running_config = Column(String)
    threat_count = Column(Integer, default=0)
    last_audited = Column(DateTime, default=lambda: datetime.now(timezone.utc))

# Table 2: The EoL/EoS Reference Database
class HardwareLifecycle(Base):
    __tablename__ = "hardware_lifecycle"
    
    id = Column(Integer, primary_key=True, index=True)
    vendor = Column(String, index=True)  # e.g., Cisco
    model = Column(String, unique=True, index=True)  # e.g., Catalyst 9300
    end_of_sale = Column(Date, nullable=True)
    end_of_life = Column(Date, nullable=True)