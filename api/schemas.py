from pydantic import BaseModel, HttpUrl
from typing import Optional, List

class Comment(BaseModel):
    id: str
    body: str
    author: str

class MediaPayload(BaseModel):
    video_url: HttpUrl
    duration_seconds: Optional[int] = None
    
class AnalyzeRequest(BaseModel):
    post_id: Optional[str] = None
    title: Optional[str] = "Untitled Post"
    comments: List[Comment]
    media: Optional[MediaPayload] = None
