import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

from routes import router

app = FastAPI(
    title="ComicCraft - AI Comic Story Creator",
    description="Full-stack AI comic creator powered by FastAPI, Gemini 1.5, and Stable Diffusion.",
    version="1.0.0"
)

# Ensure static subdirectories exist
base_dir = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(base_dir, "static")
panels_dir = os.path.join(static_dir, "panels")
exports_dir = os.path.join(static_dir, "exports")

os.makedirs(panels_dir, exist_ok=True)
os.makedirs(exports_dir, exist_ok=True)

# Mount static files directory
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Include routes
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
