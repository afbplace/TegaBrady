import json
import os
from typing import List, Optional, Dict, Any
from datetime import datetime
from contacts_model import Contact, ContactRole, MusicGenre, SocialMedia, SocialMediaPlatform
import uuid


class ContactsDatabase:
    """Database for managing music industry contacts"""

    def __init__(self, db_file: str = "contacts.json"):
        self.db_file = db_file
        self.contacts: Dict[str, Contact] = {}
        self.load()

    def load(self) -> None:
        """Load contacts from JSON file"""
        if os.path.exists(self.db_file):
            try:
                with open(self.db_file, 'r') as f:
                    data = json.load(f)
                    for contact_dict in data:
                        contact = self._dict_to_contact(contact_dict)
                        self.contacts[contact.id] = contact
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Error loading database: {e}")

    def save(self) -> None:
        """Save contacts to JSON file"""
        data = [self._contact_to_dict(contact) for contact in self.contacts.values()]
        with open(self.db_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)

    def add_contact(self, contact: Contact) -> Contact:
        """Add a new contact or update existing"""
        if not contact.id:
            contact.id = str(uuid.uuid4())
        self.contacts[contact.id] = contact
        self.save()
        return contact

    def get_contact(self, contact_id: str) -> Optional[Contact]:
        """Get a contact by ID"""
        return self.contacts.get(contact_id)

    def delete_contact(self, contact_id: str) -> bool:
        """Delete a contact"""
        if contact_id in self.contacts:
            del self.contacts[contact_id]
            self.save()
            return True
        return False

    def search_by_name(self, name: str) -> List[Contact]:
        """Search contacts by name (case-insensitive)"""
        name_lower = name.lower()
        return [c for c in self.contacts.values() if name_lower in c.name.lower()]

    def search_by_role(self, role: ContactRole) -> List[Contact]:
        """Find all contacts with a specific role"""
        return [c for c in self.contacts.values() if role in c.roles]

    def search_by_genre(self, genre: MusicGenre) -> List[Contact]:
        """Find all contacts who work with a specific genre"""
        return [c for c in self.contacts.values() if genre in c.genres]

    def search_by_company(self, company: str) -> List[Contact]:
        """Search contacts by company (case-insensitive)"""
        company_lower = company.lower()
        return [c for c in self.contacts.values()
                if c.company and company_lower in c.company.lower()]

    def search_by_location(self, location: str) -> List[Contact]:
        """Search contacts by location (case-insensitive)"""
        location_lower = location.lower()
        return [c for c in self.contacts.values()
                if c.location and location_lower in c.location.lower()]

    def search_by_country(self, country: str) -> List[Contact]:
        """Search contacts by country"""
        country_lower = country.lower()
        return [c for c in self.contacts.values()
                if c.country and country_lower in c.country.lower()]

    def filter_verified(self, verified: bool = True) -> List[Contact]:
        """Get verified or unverified contacts"""
        return [c for c in self.contacts.values() if c.verified == verified]

    def filter_by_experience(self, min_years: int) -> List[Contact]:
        """Find contacts with minimum years of experience"""
        return [c for c in self.contacts.values()
                if c.years_experience and c.years_experience >= min_years]

    def advanced_search(self,
                       roles: Optional[List[ContactRole]] = None,
                       genres: Optional[List[MusicGenre]] = None,
                       location: Optional[str] = None,
                       country: Optional[str] = None,
                       verified_only: bool = False,
                       min_experience: Optional[int] = None) -> List[Contact]:
        """Advanced search with multiple filters"""
        results = list(self.contacts.values())

        if roles:
            results = [c for c in results if any(role in c.roles for role in roles)]

        if genres:
            results = [c for c in results if any(genre in c.genres for genre in genres)]

        if location:
            location_lower = location.lower()
            results = [c for c in results
                      if c.location and location_lower in c.location.lower()]

        if country:
            country_lower = country.lower()
            results = [c for c in results
                      if c.country and country_lower in c.country.lower()]

        if verified_only:
            results = [c for c in results if c.verified]

        if min_experience:
            results = [c for c in results
                      if c.years_experience and c.years_experience >= min_experience]

        return results

    def get_all_contacts(self) -> List[Contact]:
        """Get all contacts"""
        return list(self.contacts.values())

    def get_contacts_count(self) -> int:
        """Get total number of contacts"""
        return len(self.contacts)

    @staticmethod
    def _contact_to_dict(contact: Contact) -> Dict[str, Any]:
        """Convert Contact object to dictionary"""
        return {
            'id': contact.id,
            'name': contact.name,
            'roles': [role.name for role in contact.roles],
            'genres': [genre.name for genre in contact.genres],
            'company': contact.company,
            'email': contact.email,
            'phone': contact.phone,
            'location': contact.location,
            'country': contact.country,
            'website': contact.website,
            'social_media': [
                {'platform': sm.platform.name, 'handle': sm.handle, 'url': sm.url}
                for sm in contact.social_media
            ],
            'bio': contact.bio,
            'years_experience': contact.years_experience,
            'success_rate': contact.success_rate,
            'verified': contact.verified,
            'date_added': contact.date_added.isoformat(),
            'notes': contact.notes
        }

    @staticmethod
    def _dict_to_contact(data: Dict[str, Any]) -> Contact:
        """Convert dictionary to Contact object"""
        social_media = [
            SocialMedia(
                platform=SocialMediaPlatform[sm['platform']],
                handle=sm['handle'],
                url=sm['url']
            )
            for sm in data.get('social_media', [])
        ]

        return Contact(
            id=data.get('id', str(uuid.uuid4())),
            name=data['name'],
            roles=[ContactRole[role] for role in data.get('roles', [])],
            genres=[MusicGenre[genre] for genre in data.get('genres', [])],
            company=data.get('company'),
            email=data.get('email'),
            phone=data.get('phone'),
            location=data.get('location'),
            country=data.get('country'),
            website=data.get('website'),
            social_media=social_media,
            bio=data.get('bio'),
            years_experience=data.get('years_experience'),
            success_rate=data.get('success_rate'),
            verified=data.get('verified', False),
            date_added=datetime.fromisoformat(data.get('date_added', datetime.now().isoformat())),
            notes=data.get('notes')
        )
