#!/usr/bin/env python3
"""
Music Industry Contacts Finder
A comprehensive tool to find and manage music industry contacts
"""
import sys
from typing import Optional, List
from contacts_database import ContactsDatabase
from contacts_model import Contact, ContactRole, MusicGenre, SocialMedia, SocialMediaPlatform
from contact_finder import ContactFinderAggregator, MusicBrainzFinder


class ContactsApp:
    """Main application for managing music industry contacts"""

    def __init__(self, db_file: str = "contacts.json"):
        self.db = ContactsDatabase(db_file)
        self.finder = ContactFinderAggregator()

    def add_contact_interactive(self) -> None:
        """Add a contact interactively"""
        print("\n--- Add New Contact ---")
        name = input("Name: ").strip()
        if not name:
            print("Name is required.")
            return

        email = input("Email (optional): ").strip() or None
        phone = input("Phone (optional): ").strip() or None
        company = input("Company (optional): ").strip() or None
        location = input("Location/City (optional): ").strip() or None
        country = input("Country (optional): ").strip() or None
        website = input("Website (optional): ").strip() or None

        print("\nSelect roles (comma-separated):")
        for i, role in enumerate(ContactRole, 1):
            print(f"  {i}. {role.value}")
        role_input = input("Role numbers (e.g., 1,2,3): ").strip()
        roles = []
        if role_input:
            try:
                role_indices = [int(x.strip()) - 1 for x in role_input.split(',')]
                roles = [list(ContactRole)[i] for i in role_indices if 0 <= i < len(ContactRole)]
            except (ValueError, IndexError):
                print("Invalid role selection.")

        print("\nSelect genres (comma-separated):")
        for i, genre in enumerate(MusicGenre, 1):
            print(f"  {i}. {genre.value}")
        genre_input = input("Genre numbers (e.g., 1,2,3): ").strip()
        genres = []
        if genre_input:
            try:
                genre_indices = [int(x.strip()) - 1 for x in genre_input.split(',')]
                genres = [list(MusicGenre)[i] for i in genre_indices if 0 <= i < len(MusicGenre)]
            except (ValueError, IndexError):
                print("Invalid genre selection.")

        bio = input("Bio/Notes (optional): ").strip() or None
        years_exp = input("Years of experience (optional): ").strip()
        years_experience = int(years_exp) if years_exp.isdigit() else None
        verified = input("Verified? (y/n): ").strip().lower() == 'y'

        contact = Contact(
            id="",
            name=name,
            roles=roles or [ContactRole.MUSICIAN],
            genres=genres or [MusicGenre.POP],
            email=email,
            phone=phone,
            company=company,
            location=location,
            country=country,
            website=website,
            bio=bio,
            years_experience=years_experience,
            verified=verified
        )

        self.db.add_contact(contact)
        print(f"\n✓ Contact added: {contact}")

    def search_menu(self) -> None:
        """Search contacts menu"""
        while True:
            print("\n--- Search Contacts ---")
            print("1. Search by name")
            print("2. Search by role")
            print("3. Search by genre")
            print("4. Search by company")
            print("5. Search by location")
            print("6. Advanced search")
            print("0. Back to main menu")

            choice = input("\nSelect option: ").strip()

            if choice == '1':
                name = input("Enter name: ").strip()
                results = self.db.search_by_name(name)
                self.display_results(results)

            elif choice == '2':
                print("\nAvailable roles:")
                for i, role in enumerate(ContactRole, 1):
                    print(f"  {i}. {role.value}")
                role_num = input("Select role number: ").strip()
                try:
                    role = list(ContactRole)[int(role_num) - 1]
                    results = self.db.search_by_role(role)
                    self.display_results(results)
                except (ValueError, IndexError):
                    print("Invalid selection.")

            elif choice == '3':
                print("\nAvailable genres:")
                for i, genre in enumerate(MusicGenre, 1):
                    print(f"  {i}. {genre.value}")
                genre_num = input("Select genre number: ").strip()
                try:
                    genre = list(MusicGenre)[int(genre_num) - 1]
                    results = self.db.search_by_genre(genre)
                    self.display_results(results)
                except (ValueError, IndexError):
                    print("Invalid selection.")

            elif choice == '4':
                company = input("Enter company name: ").strip()
                results = self.db.search_by_company(company)
                self.display_results(results)

            elif choice == '5':
                location = input("Enter location: ").strip()
                results = self.db.search_by_location(location)
                self.display_results(results)

            elif choice == '6':
                self.advanced_search()

            elif choice == '0':
                break
            else:
                print("Invalid option.")

    def advanced_search(self) -> None:
        """Advanced search with multiple filters"""
        print("\n--- Advanced Search ---")

        roles_input = input("Roles (comma-separated numbers, leave blank for any): ").strip()
        roles = None
        if roles_input:
            try:
                role_indices = [int(x.strip()) - 1 for x in roles_input.split(',')]
                roles = [list(ContactRole)[i] for i in role_indices if 0 <= i < len(ContactRole)]
            except (ValueError, IndexError):
                pass

        genres_input = input("Genres (comma-separated numbers, leave blank for any): ").strip()
        genres = None
        if genres_input:
            try:
                genre_indices = [int(x.strip()) - 1 for x in genres_input.split(',')]
                genres = [list(MusicGenre)[i] for i in genre_indices if 0 <= i < len(MusicGenre)]
            except (ValueError, IndexError):
                pass

        location = input("Location (leave blank for any): ").strip() or None
        country = input("Country (leave blank for any): ").strip() or None
        verified = input("Verified only? (y/n): ").strip().lower() == 'y'
        min_exp = input("Minimum years of experience (leave blank for any): ").strip()
        min_experience = int(min_exp) if min_exp.isdigit() else None

        results = self.db.advanced_search(
            roles=roles,
            genres=genres,
            location=location,
            country=country,
            verified_only=verified,
            min_experience=min_experience
        )

        self.display_results(results)

    def display_results(self, results: List[Contact]) -> None:
        """Display search results"""
        if not results:
            print("\nNo contacts found.")
            return

        print(f"\n--- Found {len(results)} contact(s) ---")
        for i, contact in enumerate(results, 1):
            print(f"\n{i}. {contact.name}")
            if contact.company:
                print(f"   Company: {contact.company}")
            if contact.email:
                print(f"   Email: {contact.email}")
            if contact.phone:
                print(f"   Phone: {contact.phone}")
            if contact.location:
                print(f"   Location: {contact.location}")
            roles = ", ".join([r.value for r in contact.roles])
            print(f"   Roles: {roles}")
            genres = ", ".join([g.value for g in contact.genres])
            print(f"   Genres: {genres}")
            if contact.years_experience:
                print(f"   Experience: {contact.years_experience} years")
            print(f"   Verified: {'Yes' if contact.verified else 'No'}")

    def find_contacts_online(self) -> None:
        """Find new contacts from online sources"""
        print("\n--- Find Contacts Online ---")
        print("1. Search MusicBrainz for labels")
        print("2. Search MusicBrainz for artists")
        print("0. Back")

        choice = input("\nSelect option: ").strip()

        if choice == '1':
            query = input("Enter label name or keyword: ").strip()
            labels = MusicBrainzFinder.search_labels(query)
            if labels:
                print(f"\n--- Found {len(labels)} label(s) ---")
                for label in labels[:10]:
                    print(f"- {label.get('name')} ({label.get('type')})")
            else:
                print("No labels found.")

        elif choice == '2':
            query = input("Enter artist name or keyword: ").strip()
            artists = MusicBrainzFinder.search_artists(query)
            if artists:
                print(f"\n--- Found {len(artists)} artist(s) ---")
                for artist in artists[:10]:
                    print(f"- {artist.get('name')}")
            else:
                print("No artists found.")

    def show_statistics(self) -> None:
        """Display database statistics"""
        total = self.db.get_contacts_count()
        verified = len(self.db.filter_verified())

        print("\n--- Contact Statistics ---")
        print(f"Total contacts: {total}")
        print(f"Verified contacts: {verified}")

        role_counts = {}
        for contact in self.db.get_all_contacts():
            for role in contact.roles:
                role_counts[role.value] = role_counts.get(role.value, 0) + 1

        if role_counts:
            print("\nContacts by role:")
            for role, count in sorted(role_counts.items(), key=lambda x: x[1], reverse=True):
                print(f"  {role}: {count}")

        genre_counts = {}
        for contact in self.db.get_all_contacts():
            for genre in contact.genres:
                genre_counts[genre.value] = genre_counts.get(genre.value, 0) + 1

        if genre_counts:
            print("\nContacts by genre:")
            for genre, count in sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
                print(f"  {genre}: {count}")

    def main_menu(self) -> None:
        """Main menu loop"""
        while True:
            print("\n" + "="*50)
            print("MUSIC INDUSTRY CONTACTS FINDER")
            print("="*50)
            print("1. Add new contact")
            print("2. Search contacts")
            print("3. Find contacts online")
            print("4. View statistics")
            print("5. List all contacts")
            print("0. Exit")

            choice = input("\nSelect option: ").strip()

            if choice == '1':
                self.add_contact_interactive()
            elif choice == '2':
                self.search_menu()
            elif choice == '3':
                self.find_contacts_online()
            elif choice == '4':
                self.show_statistics()
            elif choice == '5':
                results = self.db.get_all_contacts()
                self.display_results(results)
            elif choice == '0':
                print("\nGoodbye!")
                sys.exit(0)
            else:
                print("Invalid option.")


def main():
    """Entry point"""
    app = ContactsApp()
    app.main_menu()


if __name__ == "__main__":
    main()
