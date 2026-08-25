from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum
from datetime import datetime


class ContactRole(Enum):
    """Music industry contact roles"""
    LABEL_EXEC = "Label Executive"
    A_AND_R = "A&R (Artists and Repertoire)"
    RADIO_DJ = "Radio DJ"
    PRODUCER = "Producer"
    MANAGER = "Manager"
    BOOKING_AGENT = "Booking Agent"
    PUBLICIST = "Publicist"
    PROMOTER = "Promoter"
    ENGINEER = "Audio Engineer"
    MUSICIAN = "Musician"
    LABEL_OWNER = "Label Owner"
    MUSIC_LAWYER = "Music Lawyer"
    SYNC_AGENT = "Sync Agent"
    JOURNALIST = "Music Journalist"


class MusicGenre(Enum):
    """Music genres"""
    HIP_HOP = "Hip Hop"
    POP = "Pop"
    ROCK = "Rock"
    R_AND_B = "R&B"
    COUNTRY = "Country"
    EDM = "EDM"
    JAZZ = "Jazz"
    CLASSICAL = "Classical"
    REGGAE = "Reggae"
    LATIN = "Latin"
    INDIE = "Indie"
    METAL = "Metal"
    GOSPEL = "Gospel"
    FOLK = "Folk"


class SocialMediaPlatform(Enum):
    """Social media platforms"""
    INSTAGRAM = "Instagram"
    TWITTER = "Twitter"
    LINKEDIN = "LinkedIn"
    FACEBOOK = "Facebook"
    TIKTOK = "TikTok"
    YOUTUBE = "YouTube"


@dataclass
class SocialMedia:
    """Social media profile"""
    platform: SocialMediaPlatform
    handle: str
    url: str


@dataclass
class Contact:
    """Music industry contact"""
    id: str
    name: str
    roles: List[ContactRole]
    genres: List[MusicGenre]
    company: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    country: Optional[str] = None
    website: Optional[str] = None
    social_media: List[SocialMedia] = field(default_factory=list)
    bio: Optional[str] = None
    years_experience: Optional[int] = None
    success_rate: Optional[float] = None
    verified: bool = False
    date_added: datetime = field(default_factory=datetime.now)
    notes: Optional[str] = None

    def __repr__(self) -> str:
        roles_str = ", ".join([role.value for role in self.roles])
        return f"{self.name} ({roles_str}) at {self.company or 'Independent'}"
