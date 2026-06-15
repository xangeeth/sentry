from database import SessionLocal, engine
import models
from models import HardwareLifecycle
from datetime import date

# THE FIX: This tells SQLAlchemy to build any missing tables in sentry.db safely
models.Base.metadata.create_all(bind=engine)

def seed_hardware_data():
    db = SessionLocal()
    
    # Check if data already exists to prevent accidental duplicates
    if db.query(HardwareLifecycle).first():
        print("[*] Database is already seeded with hardware data.")
        db.close()
        return

    # Our Simulated Enterprise Inventory
    enterprise_switches = [
        {"vendor": "Cisco", "model": "Catalyst 9300", "eos": date(2027, 10, 31), "eol": date(2032, 10, 31)},
        {"vendor": "HP", "model": "Aruba 2930F", "eos": date(2025, 12, 1), "eol": date(2030, 12, 1)},
        {"vendor": "Juniper", "model": "EX4300", "eos": date(2024, 6, 30), "eol": date(2029, 6, 30)}
    ]

    print("[*] Injecting Enterprise Hardware Lifecycle data...")
    
    for switch in enterprise_switches:
        new_hardware = HardwareLifecycle(
            vendor=switch["vendor"],
            model=switch["model"],
            end_of_sale=switch["eos"],
            end_of_life=switch["eol"]
        )
        db.add(new_hardware)
    
    db.commit()
    db.close()
    print("[+] Seeding complete! Database is primed.")

if __name__ == "__main__":
    seed_hardware_data()