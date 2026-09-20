from fastapi import FastAPI
from .api.routes import health, sessions, chat, document

app = FastAPI(title="Document Intake Assistant API")

app.include_router(health.router, prefix="/api")
app.include_router(sessions.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(document.router, prefix="/api")
