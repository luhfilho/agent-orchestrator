
from pydantic import BaseModel, Field

class User(BaseModel):
    """User model"""
    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")
