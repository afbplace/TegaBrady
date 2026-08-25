"""
Contact finder for music industry - integrates with various data sources
"""
import requests
from typing import List, Optional, Dict, Any
from contacts_model import Contact, ContactRole, MusicGenre, SocialMedia, SocialMediaPlatform


class MusicBrainzFinder:
    """Find contacts via MusicBrainz API"""
    BASE_URL = "https://musicbrainz.org/ws/2"

    @staticmethod
    def search_artists(query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for artists on MusicBrainz"""
        try:
            response = requests.get(
                f"{MusicBrainzFinder.BASE_URL}/artist",
                params={'query': query, 'limit': limit, 'fmt': 'json'},
                headers={'User-Agent': 'MusicIndustryContactFinder/1.0'}
            )
            if response.status_code == 200:
                return response.json().get('artists', [])
        except Exception as e:
            print(f"Error searching MusicBrainz: {e}")
        return []

    @staticmethod
    def search_labels(query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for labels on MusicBrainz"""
        try:
            response = requests.get(
                f"{MusicBrainzFinder.BASE_URL}/label",
                params={'query': query, 'limit': limit, 'fmt': 'json'},
                headers={'User-Agent': 'MusicIndustryContactFinder/1.0'}
            )
            if response.status_code == 200:
                return response.json().get('labels', [])
        except Exception as e:
            print(f"Error searching MusicBrainz labels: {e}")
        return []


class SpotifyArtistFinder:
    """Find contacts via Spotify API (requires credentials)"""

    def __init__(self, client_id: Optional[str] = None, client_secret: Optional[str] = None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        if client_id and client_secret:
            self._authenticate()

    def _authenticate(self) -> bool:
        """Authenticate with Spotify API"""
        try:
            response = requests.post(
                "https://accounts.spotify.com/api/token",
                auth=(self.client_id, self.client_secret),
                data={'grant_type': 'client_credentials'}
            )
            if response.status_code == 200:
                self.access_token = response.json()['access_token']
                return True
        except Exception as e:
            print(f"Spotify authentication error: {e}")
        return False

    def search_artists(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for artists on Spotify"""
        if not self.access_token:
            return []
        try:
            response = requests.get(
                "https://api.spotify.com/v1/search",
                params={'q': query, 'type': 'artist', 'limit': limit},
                headers={'Authorization': f'Bearer {self.access_token}'}
            )
            if response.status_code == 200:
                return response.json().get('artists', {}).get('items', [])
        except Exception as e:
            print(f"Spotify search error: {e}")
        return []


class LinkedInContactFinder:
    """Find contacts via LinkedIn (requires manual data or API access)"""

    @staticmethod
    def search_music_professionals(company: str, role: str) -> List[Dict[str, str]]:
        """
        Placeholder for LinkedIn search
        In production, this would use LinkedIn API with proper credentials
        """
        # This is a template for LinkedIn integration
        # Requires LinkedIn API credentials
        return []


class TwitterContactFinder:
    """Find music industry professionals on Twitter"""

    def __init__(self, bearer_token: Optional[str] = None):
        self.bearer_token = bearer_token

    def search_by_hashtag(self, hashtag: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for music industry professionals by hashtag"""
        if not self.bearer_token:
            return []
        try:
            headers = {'Authorization': f'Bearer {self.bearer_token}'}
            response = requests.get(
                "https://api.twitter.com/2/tweets/search/recent",
                params={'query': f'#{hashtag}', 'max_results': limit},
                headers=headers
            )
            if response.status_code == 200:
                return response.json().get('data', [])
        except Exception as e:
            print(f"Twitter search error: {e}")
        return []


class AllMusicFinder:
    """Find contacts via AllMusic database"""

    BASE_URL = "https://www.allmusic.com"

    @staticmethod
    def search_record_labels(genre: str) -> List[Dict[str, str]]:
        """Search for record labels by genre"""
        # This would require web scraping or API access to AllMusic
        # Returning template structure
        return []


class ContactFinderAggregator:
    """Aggregate contacts from multiple sources"""

    def __init__(self):
        self.musicbrainz = MusicBrainzFinder()
        self.spotify = SpotifyArtistFinder()
        self.twitter = TwitterContactFinder()
        self.allmusic = AllMusicFinder()

    def find_label_executives(self, query: str) -> List[Dict[str, Any]]:
        """Find label executives by name or company"""
        results = []

        # Search MusicBrainz labels
        mb_labels = self.musicbrainz.search_labels(query)
        for label in mb_labels[:5]:
            results.append({
                'name': label.get('name'),
                'type': 'label',
                'source': 'musicbrainz',
                'data': label
            })

        return results

    def find_artists_and_arrs(self, genre: str) -> List[Dict[str, Any]]:
        """Find artists and A&Rs in a specific genre"""
        results = []

        # Search Spotify for artists
        artists = self.spotify.search_artists(genre)
        for artist in artists[:5]:
            results.append({
                'name': artist.get('name'),
                'type': 'artist',
                'source': 'spotify',
                'genres': artist.get('genres', []),
                'followers': artist.get('followers', {}).get('total'),
                'data': artist
            })

        return results

    def find_radio_stations(self, location: str) -> List[Dict[str, str]]:
        """Find radio stations by location (template)"""
        # This would integrate with radio station databases
        return []

    def find_music_producers(self, genre: str) -> List[Dict[str, Any]]:
        """Find music producers by genre"""
        # Could integrate with producer databases, SoundCloud, BeatStars, etc.
        return []


# Example sources for contacts
MUSIC_INDUSTRY_SOURCES = {
    'indie_labels': [
        'https://www.recordlabelnewsletter.com',
        'https://www.souvenir.org',
        'https://www.allmusic.com/label-directory',
    ],
    'radio_stations': [
        'https://www.radioaccess.com',
        'https://www.radiotoolbox.com',
    ],
    'music_databases': [
        'https://musicbrainz.org',
        'https://www.discogs.com',
        'https://www.allmusic.com',
    ],
    'industry_resources': [
        'https://www.grammy.com',
        'https://www.nmb.org',  # National Association of Music Broadcasters
        'https://www.naras.org',  # Recording Academy
    ]
}
