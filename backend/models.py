from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime, timezone
from database import Base

class Switch(Base):
    # The actual name of the table inside SQLite
    __tablename__ = "switches"

    # The Columns
    id = Column(Integer, primary_key=True, index=True)
    vendor = Column(String, index=True)
    model = Column(String, index=True)
    firmware_version = Column(String)
    running_config = Column(String)
    
    # Automatically stamps every config with the exact time we audited it
    audit_time = Column(DateTime, default=lambda: datetime.now(timezone.utc))