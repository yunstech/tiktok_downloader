from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class VideoInfo(BaseModel):
    video_id: str
    description: str
    create_time: int
    video_url: str
    thumbnail_url: Optional[str] = None
    duration: Optional[int] = None
    view_count: int = 0
    like_count: int = 0
    comment_count: int = 0
    share_count: int = 0


class UserProfile(BaseModel):
    username: str
    user_id: str
    nickname: str
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    follower_count: int = 0
    following_count: int = 0
    video_count: int = 0


class ScrapeRequest(BaseModel):
    username: str = Field(..., description="TikTok username to scrape")
    max_videos: Optional[int] = Field(None, description="Maximum number of videos to scrape")


class ScrapeResponse(BaseModel):
    job_id: str
    username: str
    status: str
    message: str


class JobStatus(BaseModel):
    job_id: str
    username: str
    status: str
    total_videos: int = 0
    downloaded_videos: int = 0
    failed_videos: int = 0
    created_at: str
    updated_at: str
    videos: List[VideoInfo] = []


class DownloadStatus(BaseModel):
    video_id: str
    status: str
    progress: int = 0
    file_path: Optional[str] = None
    error: Optional[str] = None
