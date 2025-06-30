from fastapi import FastAPI
from backend.routers import tea

app = FastAPI()

app.include_router(tea.router)

