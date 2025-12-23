from sqlalchemy.orm import Session
from app.models.movie import Movie
from app.schemas.movie import MovieCreate

def create_movie(db: Session, movie: MovieCreate, file_path: str):
    db_movie = Movie(
        title=movie.title,
        description=movie.description,
        file_path=file_path
    )
    db.add(db_movie)
    db.commit()
    db.refresh(db_movie)
    return db_movie

def get_movie(db: Session, movie_id: int):
    return db.query(Movie).filter(Movie.id == movie_id).first()

def get_all_movies(db):
    return db.query(Movie).all()