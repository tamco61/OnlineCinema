from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.services import minio_service, movie_service
from app.schemas.movie import MovieCreate, MovieOut

router = APIRouter()


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
def stream_movie(movie_id: int, db: Session = Depends(get_db)):
    movie = movie_service.get_movie(db, movie_id)
    if not movie:
        raise HTTPException(404, "Movie not found")
    url = minio_service.get_presigned_url(movie.file_path)
    return {"stream_url": url}
