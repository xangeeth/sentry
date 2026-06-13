from fastapi import FastAPI

# Initialize the application
app = FastAPI()

# Create our first route
@app.get("/")
def read_root():
    return {"status": "Project Sentry Engine is Online", "version": "1.0"}