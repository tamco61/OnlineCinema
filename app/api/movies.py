from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, StreamingResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.services import minio_service, movie_service
from app.schemas.movie import MovieCreate, MovieOut
import requests

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.post("/upload", response_model=MovieOut)
def upload_movie(
    title: str,
    description: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    object_name = file.filename
    minio_service.upload_file(file, object_name)
    db_movie = movie_service.create_movie(
        db, MovieCreate(title=title, description=description), object_name
    )
    return db_movie


@router.get("/{movie_id}/stream")
def stream_proxy(movie_id: int, db: Session = Depends(get_db)):
    movie = movie_service.get_movie(db, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    # Получаем presigned URL из MinIO
    presigned_url = minio_service.get_presigned_url(movie.file_path)

    # Прокси-запрос к MinIO и отдаём поток
    r = requests.get(presigned_url, stream=True)
    return StreamingResponse(r.raw, media_type="video/mp4")

@router.get("/{movie_id}/player", response_class=HTMLResponse)
def player_start(request: Request, movie_id: int, db: Session = Depends(get_db)):
    movie = movie_service.get_movie(db, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    # В player.html будем использовать прокси-эндпоинт
    context = {
        "request": request,
        "movie_title": movie.title,
        "movie_id": movie.id
    }
    return templates.TemplateResponse("player.html", context)


@router.get("/", response_class=HTMLResponse)
def list_movies(request: Request, db: Session = Depends(get_db)):
    movies = movie_service.get_all_movies(db)
    return templates.TemplateResponse("movies_list.html", {
        "request": request,
        "movies": movies
    })