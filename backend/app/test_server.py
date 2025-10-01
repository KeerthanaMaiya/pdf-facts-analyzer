from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Test server is working!"}

@app.get("/health")
def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    print("Starting test server...")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")