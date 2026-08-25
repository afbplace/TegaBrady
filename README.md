# Music Industry Contacts Finder

A comprehensive Python application for finding, organizing, and managing music industry contacts including label executives, A&R managers, radio DJs, producers, managers, publicists, and more.

## Features

- **Contact Management**: Add, search, and manage music industry professionals
- **Advanced Search**: Filter by role, genre, location, experience level, and more
- **Multiple Contact Types**: Support for 14+ different roles in the music industry
- **Genre Support**: Handle 15+ music genres
- **Social Media Integration**: Track contacts across Instagram, Twitter, LinkedIn, TikTok, YouTube, and Facebook
- **Online Discovery**: Integrated search with MusicBrainz and other music databases
- **JSON Database**: Simple file-based storage (easily integrable with databases)
- **Statistics & Reporting**: View contact analytics by role and genre

## Installation

1. Clone or download the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Load sample data (optional):
```bash
python sample_data.py
```

## Usage

### Start the Application

```bash
python main.py
```

### Menu Options

#### 1. Add New Contact
Create a new contact record with:
- Name, email, phone
- Company and location
- Multiple roles (Label Exec, A&R, Radio DJ, etc.)
- Music genres worked with
- Years of experience
- Verification status

#### 2. Search Contacts
- **By Name**: Full or partial name search
- **By Role**: Find all producers, managers, DJs, etc.
- **By Genre**: Find contacts working with specific genres
- **By Company**: Search by label, station, or agency
- **By Location**: Search by city or region
- **Advanced Search**: Combine multiple filters

#### 3. Find Contacts Online
- Search MusicBrainz for labels and artists
- Discover new contacts from music databases

#### 4. View Statistics
- Total contact count
- Verified vs unverified contacts
- Distribution by role and genre
- Contact density analysis

#### 5. List All Contacts
View complete database of all contacts with detailed information

## Data Structure

### Contact Roles
```
- Label Executive
- A&R (Artists and Repertoire)
- Radio DJ
- Producer
- Manager
- Booking Agent
- Publicist
- Promoter
- Audio Engineer
- Musician
- Label Owner
- Music Lawyer
- Sync Agent
- Music Journalist
```

### Music Genres
```
- Hip Hop
- Pop
- Rock
- R&B
- Country
- EDM
- Jazz
- Classical
- Reggae
- Latin
- Indie
- Metal
- Gospel
- Folk
```

## Sample Data

The `sample_data.py` script loads 10 example contacts including:
- Label executives at major labels (Universal Music Group)
- Independent label owners (Blue Moon Records)
- Radio DJs (KCRW, BBC Radio 1)
- Producers and engineers
- Managers and booking agents
- Music lawyers
- Publicists
- Sync agents
- Music journalists

### Load Sample Data
```bash
python sample_data.py
# Then run: python main.py
# Select option 5 to view all contacts
```

## API Usage (Programmatic)

### Using the Database

```python
from contacts_database import ContactsDatabase
from contacts_model import Contact, ContactRole, MusicGenre

# Initialize database
db = ContactsDatabase("contacts.json")

# Create a contact
contact = Contact(
    id="",
    name="John Producer",
    roles=[ContactRole.PRODUCER, ContactRole.ENGINEER],
    genres=[MusicGenre.EDM, MusicGenre.HIP_HOP],
    email="john@example.com",
    company="Sonic Studios",
    years_experience=8,
    verified=True
)

# Add to database
db.add_contact(contact)

# Search
producers = db.search_by_role(ContactRole.PRODUCER)
edm_contacts = db.search_by_genre(MusicGenre.EDM)

# Advanced search
results = db.advanced_search(
    roles=[ContactRole.A_AND_R, ContactRole.LABEL_EXEC],
    genres=[MusicGenre.HIP_HOP],
    location="New York",
    verified_only=True,
    min_experience=5
)

# Display results
for contact in results:
    print(contact)
```

### Using the Contact Finder

```python
from contact_finder import ContactFinderAggregator

finder = ContactFinderAggregator()

# Search MusicBrainz
labels = finder.find_label_executives("Epic Records")
artists = finder.find_artists_and_arrs("hip hop")

# Results include MusicBrainz data for further enrichment
```

## Database Format

Contacts are stored in JSON format:

```json
{
  "id": "unique-id",
  "name": "Sarah Chen",
  "roles": ["LABEL_EXEC", "A_AND_R"],
  "genres": ["HIP_HOP", "POP", "INDIE"],
  "company": "Universal Music Group",
  "email": "s.chen@umg.com",
  "phone": "+1-212-555-0101",
  "location": "New York",
  "country": "USA",
  "website": "https://umg.com",
  "social_media": [
    {
      "platform": "LINKEDIN",
      "handle": "sarahchen-music",
      "url": "https://linkedin.com/in/sarahchen-music"
    }
  ],
  "bio": "20+ years in music industry...",
  "years_experience": 22,
  "success_rate": 0.78,
  "verified": true,
  "date_added": "2026-08-25T10:30:00",
  "notes": "Great for indie pop acts"
}
```

## Music Industry Data Sources

The application is designed to integrate with:

### Free Sources
- **MusicBrainz**: Artist and label data (https://musicbrainz.org)
- **Discogs**: Music database (https://www.discogs.com)
- **AllMusic**: Comprehensive music database (https://www.allmusic.com)
- **Grammy Awards**: Industry recognition (https://www.grammy.com)

### API Integrations (Requires Authentication)
- **Spotify API**: Artist data and verification
- **Twitter API**: Find music professionals by hashtag
- **LinkedIn API**: Label executives and music industry professionals

### Industry Directories
- Record Label Newsletter Directory
- Radio Station Databases
- NARAS (Recording Academy)
- National Association of Music Broadcasters

## Advanced Features

### Verification System
Mark contacts as verified to distinguish between:
- Personally vetted contacts
- Database entries requiring verification
- Contacts with proven track records

### Success Rates
Track success metrics for:
- A&R sign-off rates
- Artist career advancement
- Industry recognition

### Experience Tracking
- Years in current role
- Career progression
- Specialization areas

## Extending the Application

### Add New Data Sources
Edit `contact_finder.py` to add new finder classes:

```python
class MyMusicDBFinder:
    def search_contacts(self, query):
        # Implementation here
        pass
```

### Custom Search Filters
Add new search methods to `ContactsDatabase`:

```python
def search_by_custom_field(self, value):
    return [c for c in self.contacts.values() if match(c, value)]
```

### Database Backends
Replace JSON storage with:
- SQLite
- PostgreSQL
- MongoDB
- DynamoDB

## Performance

- JSON database suitable for 1000-10000 contacts
- Search operations: O(n) complexity
- Upgrade to SQL database for large-scale deployment

## Contributing

To add features:
1. Update data models in `contacts_model.py`
2. Add database methods in `contacts_database.py`
3. Implement UI in `main.py`
4. Add integration in `contact_finder.py`

## Future Enhancements

- [ ] Web interface (Flask/Django)
- [ ] REST API
- [ ] Advanced reporting (charts, export to CSV/Excel)
- [ ] Email campaign integration
- [ ] CRM features
- [ ] Machine learning for contact matching
- [ ] Integration with Spotify, Apple Music APIs
- [ ] Real-time label executive directory updates

## License

MIT License - Feel free to use for personal or commercial projects

## Support

For questions or issues, refer to the contact management documentation or the application's built-in help menu.
