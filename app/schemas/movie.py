from pydantic import BaseModel


class MovieCreate(BaseModel):
    title: str
    description: str


class MovieOut(BaseModel):
    id: int
    title: str
    description: str
    file_path: str

    class Config:
        orm_mode = True
