import os
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from db.database import init_db
from api.routes import auth, dashboard, pipeline, chat

load_dotenv()

app = FastAPI(title="RivalRadar API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Shared BackgroundTasks instance for routes that need it outside request context
background_tasks_store = BackgroundTasks()

app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(pipeline.router)
app.include_router(chat.router)


@app.on_event("startup")
def startup():
    init_db()


@app.get("/health")
def health():
    return {"status": "ok"}
