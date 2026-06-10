from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.v1 import auth

app = FastAPI(title="RezTrader SaaS", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])

@app.get("/")
async def root():
    return {"name": "RezTrader", "status": "online"}

@app.get("/health")
async def health():
    return {"status": "healthy", "version": "1.0.0"}
@app.get("/debug")
async def debug():
    return {"routes": [route.path for route in app.routes]}


@app.get("/debug/routes")
async def debug_routes():
    return {"routes": [{"path": route.path, "methods": list(route.methods)} for route in app.routes if hasattr(route, "methods")]}

