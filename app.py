#!/usr/bin/env python3
"""
Flask web application for Music Industry Contacts Finder
Run with: python app.py
Then visit: http://localhost:5000
"""
from flask import Flask, render_template, request, jsonify
from contacts_database import ContactsDatabase
from contacts_model import ContactRole, MusicGenre

app = Flask(__name__)
db = ContactsDatabase("sample_contacts.json")


@app.route('/')
def index():
    """Home page"""
    total = db.get_contacts_count()
    verified = len(db.filter_verified())

    return render_template('index.html',
                         total_contacts=total,
                         verified_contacts=verified,
                         roles=[role for role in ContactRole],
                         genres=[genre for genre in MusicGenre])


@app.route('/api/contacts/all')
def get_all_contacts():
    """Get all contacts as JSON"""
    contacts = db.get_all_contacts()
    return jsonify([contact_to_dict(c) for c in contacts])


@app.route('/api/contacts/search', methods=['POST'])
def search_contacts():
    """Search contacts with filters"""
    data = request.json
    query_type = data.get('type', 'name')
    query = data.get('query', '')

    results = []

    if query_type == 'name':
        results = db.search_by_name(query)
    elif query_type == 'company':
        results = db.search_by_company(query)
    elif query_type == 'location':
        results = db.search_by_location(query)
    elif query_type == 'country':
        results = db.search_by_country(query)
    elif query_type == 'role':
        try:
            role = ContactRole[query]
            results = db.search_by_role(role)
        except KeyError:
            pass
    elif query_type == 'genre':
        try:
            genre = MusicGenre[query]
            results = db.search_by_genre(genre)
        except KeyError:
            pass

    return jsonify([contact_to_dict(c) for c in results])


@app.route('/api/contacts/advanced', methods=['POST'])
def advanced_search():
    """Advanced search with multiple filters"""
    data = request.json

    roles = None
    if data.get('roles'):
        try:
            roles = [ContactRole[r] for r in data.get('roles')]
        except KeyError:
            roles = None

    genres = None
    if data.get('genres'):
        try:
            genres = [MusicGenre[g] for g in data.get('genres')]
        except KeyError:
            genres = None

    results = db.advanced_search(
        roles=roles,
        genres=genres,
        location=data.get('location') or None,
        country=data.get('country') or None,
        verified_only=data.get('verified_only', False),
        min_experience=data.get('min_experience') or None
    )

    return jsonify([contact_to_dict(c) for c in results])


@app.route('/api/contacts/<contact_id>')
def get_contact(contact_id):
    """Get single contact details"""
    contact = db.get_contact(contact_id)
    if contact:
        return jsonify(contact_to_dict(contact))
    return jsonify({'error': 'Contact not found'}), 404


@app.route('/api/stats')
def get_stats():
    """Get database statistics"""
    all_contacts = db.get_all_contacts()

    role_counts = {}
    for contact in all_contacts:
        for role in contact.roles:
            role_counts[role.value] = role_counts.get(role.value, 0) + 1

    genre_counts = {}
    for contact in all_contacts:
        for genre in contact.genres:
            genre_counts[genre.value] = genre_counts.get(genre.value, 0) + 1

    location_counts = {}
    for contact in all_contacts:
        if contact.location:
            location_counts[contact.location] = location_counts.get(contact.location, 0) + 1

    return jsonify({
        'total_contacts': db.get_contacts_count(),
        'verified': len(db.filter_verified()),
        'unverified': len(db.filter_verified(False)),
        'roles': role_counts,
        'genres': genre_counts,
        'locations': location_counts
    })


def contact_to_dict(contact):
    """Convert contact object to dictionary"""
    return {
        'id': contact.id,
        'name': contact.name,
        'roles': [role.value for role in contact.roles],
        'genres': [genre.value for genre in contact.genres],
        'company': contact.company,
        'email': contact.email,
        'phone': contact.phone,
        'location': contact.location,
        'country': contact.country,
        'website': contact.website,
        'bio': contact.bio,
        'years_experience': contact.years_experience,
        'success_rate': contact.success_rate,
        'verified': contact.verified
    }


if __name__ == '__main__':
    print("\n🎵 Music Industry Contacts Finder - Web App")
    print("=" * 50)
    print("✅ Starting server on http://localhost:5000")
    print("Press Ctrl+C to stop\n")
    app.run(debug=True, host='localhost', port=5000)
