# Music Industry Contacts Finder - Web App Guide

## 🚀 Quick Start

### Option 1: Using the startup script
```bash
bash run_web.sh
```

### Option 2: Direct Python
```bash
python app.py
```

Then open your browser to: **http://localhost:5000**

---

## 📖 Features

### 1. **Simple Search**
Find contacts by:
- **Name**: Search by contact name (e.g., "Sarah Chen")
- **Company**: Search by label, station, or agency (e.g., "Universal")
- **Location**: Search by city (e.g., "New York")
- **Country**: Search by country (e.g., "USA")
- **Role**: Find all A&Rs, DJs, producers, etc.
- **Genre**: Find contacts who work with specific genres

### 2. **Advanced Search**
Combine multiple filters:
- Location & Country
- Minimum years of experience
- Specific roles (multiple selection)
- Music genres (multiple selection)
- Verified contacts only

### 3. **Dashboard**
View statistics:
- Total number of contacts
- Verified contacts count
- Contact distribution by role
- Contact distribution by genre
- Geographic distribution

---

## 🎯 Example Searches

### Find Radio DJs
1. Click "Simple Search"
2. Select "Search by Role"
3. Type "RADIO_DJ" (or select from dropdown)
4. Click Search

**Result**: DJ Sophia Martinez, DJ Alex Thompson

### Find Hip Hop Professionals
1. Click "Simple Search"
2. Select "Search by Genre"
3. Type "HIP_HOP"
4. Click Search

**Result**: 4 contacts working with Hip Hop

### Find Experienced A&Rs in New York
1. Click "Advanced Search"
2. Check "A&R" role
3. Enter "New York" for location
4. Set minimum experience to "10"
5. Click Search

**Result**: Sarah Chen (22 years experience)

### Find Verified Indie Contacts
1. Click "Advanced Search"
2. Check "Indie" genre
3. Check "Verified Only"
4. Click Search

**Result**: 6 verified indie professionals

---

## 🔍 Search Tips

### Role Names (for simple search)
```
LABEL_EXEC           - Label Executive
A_AND_R             - A&R Professional
RADIO_DJ            - Radio DJ
PRODUCER            - Producer
MANAGER             - Manager
BOOKING_AGENT       - Booking Agent
PUBLICIST           - Publicist
PROMOTER            - Promoter
ENGINEER            - Audio Engineer
MUSICIAN            - Musician
LABEL_OWNER         - Label Owner
MUSIC_LAWYER        - Music Lawyer
SYNC_AGENT          - Sync Agent
JOURNALIST          - Music Journalist
```

### Genre Names (for simple search)
```
HIP_HOP             - Hip Hop
POP                 - Pop
ROCK                - Rock
R_AND_B             - R&B
COUNTRY             - Country
EDM                 - EDM
JAZZ                - Jazz
CLASSICAL           - Classical
REGGAE              - Reggae
LATIN               - Latin
INDIE               - Indie
METAL               - Metal
GOSPEL              - Gospel
FOLK                - Folk
```

---

## 🛠️ API Endpoints

If you want to integrate with other tools:

### Get All Contacts
```
GET /api/contacts/all
```

### Simple Search
```
POST /api/contacts/search
Content-Type: application/json

{
  "type": "name|company|location|country|role|genre",
  "query": "search term"
}
```

### Advanced Search
```
POST /api/contacts/advanced
Content-Type: application/json

{
  "roles": ["ROLE1", "ROLE2"],
  "genres": ["GENRE1", "GENRE2"],
  "location": "New York",
  "country": "USA",
  "min_experience": 10,
  "verified_only": true
}
```

### Get Statistics
```
GET /api/stats
```

### Get Single Contact
```
GET /api/contacts/{contact_id}
```

---

## 📱 Responsive Design

The web app is fully responsive:
- ✅ Desktop browsers (Chrome, Firefox, Safari, Edge)
- ✅ Tablet devices
- ✅ Mobile phones

---

## 🎨 Customization

### Change Port
Edit `app.py`:
```python
app.run(debug=True, host='localhost', port=8000)  # Change 5000 to 8000
```

### Modify Colors
Edit `templates/index.html` - look for hex colors like `#667eea` (purple), `#764ba2` (darker purple)

### Add More Contacts
```bash
python -c "
from contacts_database import ContactsDatabase
from contacts_model import Contact, ContactRole, MusicGenre

db = ContactsDatabase('sample_contacts.json')

new_contact = Contact(
    id='',
    name='Your Name',
    roles=[ContactRole.A_AND_R],
    genres=[MusicGenre.POP],
    company='Your Label',
    email='your@email.com',
    years_experience=5,
    verified=True
)
db.add_contact(new_contact)
print('✓ Contact added!')
"
```

---

## ⚙️ Requirements

- Python 3.7+
- Flask 2.3.0+
- requests 2.28.0+

Install with:
```bash
pip install -r requirements.txt
```

---

## 🐛 Troubleshooting

### Port already in use?
```bash
# Try a different port by editing app.py
# Or kill the existing process:
lsof -i :5000
kill -9 <PID>
```

### Page not loading?
- Check that Flask is running (look for "Running on http://localhost:5000")
- Try hard refresh (Ctrl+Shift+R or Cmd+Shift+R)
- Check browser console for errors (F12)

### Searches returning nothing?
- Make sure you use exact role/genre names from the lists above
- Try partial name searches instead
- Check that sample_contacts.json exists

---

## 📈 Performance

- Loads instantly (all data in memory)
- Searches complete in milliseconds
- Suitable for 10,000+ contacts

---

## 🚀 Deployment

To deploy online:
1. Use Gunicorn: `gunicorn app:app`
2. Use Docker: See Dockerfile (create one if needed)
3. Deploy to Heroku, PythonAnywhere, or similar

---

## 📞 Contact

For issues or feature requests, refer to the main README.md

Enjoy! 🎵
