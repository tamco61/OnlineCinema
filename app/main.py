from fastapi import FastAPI
from app.api.router import api_router
from app.database import Base, engine

# создаём таблицы
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Online Cinema MVP")

app.include_router(api_router)
