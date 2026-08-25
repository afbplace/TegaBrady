#!/usr/bin/env python3
"""
Quick search examples - Copy and modify these for your own searches
"""
from contacts_database import ContactsDatabase
from contacts_model import ContactRole, MusicGenre

db = ContactsDatabase("sample_contacts.json")

# ============================================
# EXAMPLE 1: Find all Radio DJs
# ============================================
print("📻 ALL RADIO DJS:")
djs = db.search_by_role(ContactRole.RADIO_DJ)
for dj in djs:
    print(f"  - {dj.name} at {dj.company}")


# ============================================
# EXAMPLE 2: Find all A&R professionals
# ============================================
print("\n👨‍💼 ALL A&R PROFESSIONALS:")
ars = db.search_by_role(ContactRole.A_AND_R)
for ar in ars:
    print(f"  - {ar.name} at {ar.company} | Years: {ar.years_experience}")


# ============================================
# EXAMPLE 3: Find all Hip Hop contacts
# ============================================
print("\n🎤 ALL HIP HOP CONTACTS:")
hiphop = db.search_by_genre(MusicGenre.HIP_HOP)
for contact in hiphop:
    roles = ", ".join([r.value for r in contact.roles])
    print(f"  - {contact.name} ({roles})")


# ============================================
# EXAMPLE 4: Find all contacts in New York
# ============================================
print("\n🗽 CONTACTS IN NEW YORK:")
ny_contacts = db.search_by_location("New York")
for contact in ny_contacts:
    print(f"  - {contact.name} | Email: {contact.email}")


# ============================================
# EXAMPLE 5: Find experienced producers (10+ years)
# ============================================
print("\n🎹 EXPERIENCED PRODUCERS (10+ YEARS):")
producers = db.search_by_role(ContactRole.PRODUCER)
experienced = [p for p in producers if p.years_experience and p.years_experience >= 10]
for prod in experienced:
    print(f"  - {prod.name} | {prod.years_experience} years | Success: {prod.success_rate*100:.0f}%")


# ============================================
# EXAMPLE 6: Advanced search - Pop managers
# ============================================
print("\n📋 POP MANAGERS:")
pop_managers = db.advanced_search(
    roles=[ContactRole.MANAGER],
    genres=[MusicGenre.POP]
)
for mgr in pop_managers:
    print(f"  - {mgr.name} at {mgr.company} | {mgr.location}")


# ============================================
# EXAMPLE 7: Find verified indie contacts with 10+ years
# ============================================
print("\n⭐ VERIFIED INDIE VETERANS (10+ YEARS):")
indie_veterans = db.advanced_search(
    genres=[MusicGenre.INDIE],
    verified_only=True,
    min_experience=10
)
for contact in indie_veterans:
    roles = ", ".join([r.value for r in contact.roles])
    print(f"  - {contact.name} ({roles}) | {contact.years_experience} years")


# ============================================
# EXAMPLE 8: Search by company
# ============================================
print("\n🏢 CONTACTS AT UNIVERSAL MUSIC GROUP:")
umg = db.search_by_company("Universal")
for contact in umg:
    print(f"  - {contact.name} | Email: {contact.email} | Phone: {contact.phone}")


# ============================================
# EXAMPLE 9: Get all verified contacts
# ============================================
print("\n✅ ALL VERIFIED CONTACTS:")
verified = db.filter_verified(True)
print(f"  Total: {len(verified)} verified professionals")
for contact in verified[:3]:  # Show first 3
    print(f"    - {contact.name}")
if len(verified) > 3:
    print(f"    ... and {len(verified)-3} more")


# ============================================
# EXAMPLE 10: Get statistics
# ============================================
print("\n📊 DATABASE STATISTICS:")
print(f"  Total contacts: {db.get_contacts_count()}")
print(f"  Verified: {len(db.filter_verified())}")

role_counts = {}
for contact in db.get_all_contacts():
    for role in contact.roles:
        role_counts[role.value] = role_counts.get(role.value, 0) + 1

print(f"\n  Top roles:")
for role, count in sorted(role_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
    print(f"    - {role}: {count}")
