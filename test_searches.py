#!/usr/bin/env python3
"""
Test script to demonstrate searching and filtering contacts
Run this to see various search examples
"""
from contacts_database import ContactsDatabase
from contacts_model import ContactRole, MusicGenre


def print_contacts(contacts, title):
    """Pretty print contacts"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")
    if not contacts:
        print("❌ No contacts found")
        return
    for i, contact in enumerate(contacts, 1):
        print(f"\n{i}. {contact.name}")
        if contact.company:
            print(f"   🏢 Company: {contact.company}")
        if contact.email:
            print(f"   📧 Email: {contact.email}")
        if contact.phone:
            print(f"   📱 Phone: {contact.phone}")
        if contact.location:
            print(f"   📍 Location: {contact.location}")
        if contact.country:
            print(f"   🌍 Country: {contact.country}")
        roles = ", ".join([r.value for r in contact.roles])
        print(f"   👔 Roles: {roles}")
        genres = ", ".join([g.value for g in contact.genres])
        print(f"   🎵 Genres: {genres}")
        if contact.years_experience:
            print(f"   ⏱️  Experience: {contact.years_experience} years")
        if contact.success_rate:
            print(f"   ⭐ Success Rate: {contact.success_rate*100:.0f}%")
        print(f"   ✅ Verified: {'Yes' if contact.verified else 'No'}")


def main():
    """Run test searches"""
    print("\n🎵 MUSIC INDUSTRY CONTACTS - TEST SEARCHES 🎵")

    # Load database
    db = ContactsDatabase("sample_contacts.json")
    print(f"\n📊 Total contacts in database: {db.get_contacts_count()}")

    # Test 1: Search by name
    print("\n" + "="*70)
    print("TEST 1: SEARCH BY NAME")
    print("="*70)
    results = db.search_by_name("Sarah")
    print_contacts(results, "Search for 'Sarah'")

    results = db.search_by_name("DJ")
    print_contacts(results, "Search for 'DJ'")

    # Test 2: Search by role
    print("\n" + "="*70)
    print("TEST 2: SEARCH BY ROLE")
    print("="*70)
    results = db.search_by_role(ContactRole.LABEL_EXEC)
    print_contacts(results, f"All {ContactRole.LABEL_EXEC.value}s")

    results = db.search_by_role(ContactRole.RADIO_DJ)
    print_contacts(results, f"All {ContactRole.RADIO_DJ.value}s")

    results = db.search_by_role(ContactRole.PRODUCER)
    print_contacts(results, f"All {ContactRole.PRODUCER.value}s")

    # Test 3: Search by genre
    print("\n" + "="*70)
    print("TEST 3: SEARCH BY GENRE")
    print("="*70)
    results = db.search_by_genre(MusicGenre.HIP_HOP)
    print_contacts(results, f"All contacts working with {MusicGenre.HIP_HOP.value}")

    results = db.search_by_genre(MusicGenre.EDM)
    print_contacts(results, f"All contacts working with {MusicGenre.EDM.value}")

    results = db.search_by_genre(MusicGenre.POP)
    print_contacts(results, f"All contacts working with {MusicGenre.POP.value}")

    # Test 4: Search by company
    print("\n" + "="*70)
    print("TEST 4: SEARCH BY COMPANY")
    print("="*70)
    results = db.search_by_company("Universal")
    print_contacts(results, "Search for 'Universal' in company")

    results = db.search_by_company("BBC")
    print_contacts(results, "Search for 'BBC' in company")

    # Test 5: Search by location
    print("\n" + "="*70)
    print("TEST 5: SEARCH BY LOCATION")
    print("="*70)
    results = db.search_by_location("New York")
    print_contacts(results, "Search for 'New York' location")

    results = db.search_by_location("Los Angeles")
    print_contacts(results, "Search for 'Los Angeles' location")

    # Test 6: Filter by experience
    print("\n" + "="*70)
    print("TEST 6: FILTER BY EXPERIENCE")
    print("="*70)
    results = db.filter_by_experience(15)
    print_contacts(results, "Contacts with 15+ years experience")

    results = db.filter_by_experience(10)
    print_contacts(results, "Contacts with 10+ years experience")

    # Test 7: Filter verified
    print("\n" + "="*70)
    print("TEST 7: FILTER VERIFIED CONTACTS")
    print("="*70)
    results = db.filter_verified(True)
    print_contacts(results, "Verified contacts only")

    results = db.filter_verified(False)
    print_contacts(results, "Unverified contacts only")

    # Test 8: Advanced search (multiple filters)
    print("\n" + "="*70)
    print("TEST 8: ADVANCED SEARCH (Multiple Filters)")
    print("="*70)

    # A&Rs and Label Execs working with Hip Hop
    results = db.advanced_search(
        roles=[ContactRole.A_AND_R, ContactRole.LABEL_EXEC],
        genres=[MusicGenre.HIP_HOP]
    )
    print_contacts(results, "A&Rs/Label Execs working with Hip Hop")

    # Producers in Los Angeles
    results = db.advanced_search(
        roles=[ContactRole.PRODUCER],
        location="Los Angeles"
    )
    print_contacts(results, "Producers in Los Angeles")

    # Verified contacts with 10+ years experience
    results = db.advanced_search(
        verified_only=True,
        min_experience=10
    )
    print_contacts(results, "Verified contacts with 10+ years experience")

    # All Radio DJs in the USA
    results = db.advanced_search(
        roles=[ContactRole.RADIO_DJ],
        country="USA"
    )
    print_contacts(results, "Radio DJs in USA")

    # Test 9: Statistics
    print("\n" + "="*70)
    print("TEST 9: STATISTICS")
    print("="*70)

    print(f"\n📊 Contact Statistics:")
    print(f"   Total contacts: {db.get_contacts_count()}")
    print(f"   Verified: {len(db.filter_verified())}")
    print(f"   Unverified: {len(db.filter_verified(False))}")

    print(f"\n👔 Contacts by Role:")
    role_counts = {}
    for contact in db.get_all_contacts():
        for role in contact.roles:
            role_counts[role.value] = role_counts.get(role.value, 0) + 1
    for role, count in sorted(role_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"   {role}: {count}")

    print(f"\n🎵 Contacts by Genre:")
    genre_counts = {}
    for contact in db.get_all_contacts():
        for genre in contact.genres:
            genre_counts[genre.value] = genre_counts.get(genre.value, 0) + 1
    for genre, count in sorted(genre_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"   {genre}: {count}")

    print("\n" + "="*70)
    print("✅ ALL TESTS COMPLETED")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
