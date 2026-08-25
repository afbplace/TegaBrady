"""
Sample data for music industry contacts
This file can be run to populate the database with example contacts
"""
from contacts_database import ContactsDatabase
from contacts_model import Contact, ContactRole, MusicGenre, SocialMedia, SocialMediaPlatform


def load_sample_data():
    """Load sample contacts into database"""
    db = ContactsDatabase("sample_contacts.json")

    # Sample label executives
    contacts = [
        Contact(
            id="001",
            name="Sarah Chen",
            roles=[ContactRole.LABEL_EXEC, ContactRole.A_AND_R],
            genres=[MusicGenre.HIP_HOP, MusicGenre.POP, MusicGenre.INDIE],
            company="Universal Music Group",
            email="s.chen@umg.com",
            phone="+1-212-555-0101",
            location="New York",
            country="USA",
            website="https://umg.com",
            social_media=[
                SocialMedia(SocialMediaPlatform.LINKEDIN, "sarahchen-music", "https://linkedin.com/in/sarahchen-music"),
                SocialMedia(SocialMediaPlatform.TWITTER, "@sarahchenmusic", "https://twitter.com/sarahchenmusic"),
            ],
            bio="20+ years in music industry, discovering emerging talent in hip-hop and indie pop",
            years_experience=22,
            success_rate=0.78,
            verified=True,
        ),
        Contact(
            id="002",
            name="Marcus Johnson",
            roles=[ContactRole.LABEL_OWNER, ContactRole.A_AND_R],
            genres=[MusicGenre.R_AND_B, MusicGenre.HIP_HOP, MusicGenre.REGGAE],
            company="Blue Moon Records",
            email="marcus@bluemoonrecords.com",
            phone="+1-404-555-0202",
            location="Atlanta",
            country="USA",
            website="https://bluemoonrecords.com",
            social_media=[
                SocialMedia(SocialMediaPlatform.INSTAGRAM, "@bluemoonrecords", "https://instagram.com/bluemoonrecords"),
                SocialMedia(SocialMediaPlatform.TWITTER, "@bluemoon_rec", "https://twitter.com/bluemoon_rec"),
            ],
            bio="Founded Blue Moon Records in 2015, specializing in R&B and hip-hop artists",
            years_experience=18,
            success_rate=0.82,
            verified=True,
        ),
        # Radio DJs
        Contact(
            id="003",
            name="DJ Sophia Martinez",
            roles=[ContactRole.RADIO_DJ],
            genres=[MusicGenre.EDM, MusicGenre.INDIE, MusicGenre.POP],
            company="KCRW Radio",
            email="sophia@kcrw.org",
            location="Los Angeles",
            country="USA",
            website="https://kcrw.org",
            social_media=[
                SocialMedia(SocialMediaPlatform.INSTAGRAM, "@djsophiam", "https://instagram.com/djsophiam"),
                SocialMedia(SocialMediaPlatform.TIKTOK, "@djsophiam", "https://tiktok.com/@djsophiam"),
            ],
            bio="Morning radio host on KCRW, passionate about emerging indie and electronic music",
            years_experience=12,
            verified=True,
        ),
        Contact(
            id="004",
            name="DJ Alex Thompson",
            roles=[ContactRole.RADIO_DJ, ContactRole.JOURNALIST],
            genres=[MusicGenre.ROCK, MusicGenre.INDIE, MusicGenre.FOLK],
            company="BBC Radio 1",
            email="a.thompson@bbc.co.uk",
            location="London",
            country="UK",
            website="https://bbc.co.uk/radio1",
            social_media=[
                SocialMedia(SocialMediaPlatform.TWITTER, "@alexdjradio", "https://twitter.com/alexdjradio"),
            ],
            bio="Rock and indie specialist at BBC Radio 1, known for discovering new alternative talent",
            years_experience=15,
            verified=True,
        ),
        # Producers
        Contact(
            id="005",
            name="David 'D-Wave' Williams",
            roles=[ContactRole.PRODUCER, ContactRole.ENGINEER],
            genres=[MusicGenre.EDM, MusicGenre.HIP_HOP, MusicGenre.POP],
            company="Independent",
            email="dwaveproduction@gmail.com",
            location="Austin",
            country="USA",
            website="https://dwaveproduction.com",
            social_media=[
                SocialMedia(SocialMediaPlatform.INSTAGRAM, "@dwaveproduction", "https://instagram.com/dwaveproduction"),
                SocialMedia(SocialMediaPlatform.YOUTUBE, "DWaveProduction", "https://youtube.com/dwaveproduction"),
            ],
            bio="Grammy-nominated producer with 10+ years experience in electronic and hip-hop production",
            years_experience=11,
            success_rate=0.85,
            verified=True,
        ),
        # Managers & Agents
        Contact(
            id="006",
            name="Jennifer 'Jen' Park",
            roles=[ContactRole.MANAGER, ContactRole.BOOKING_AGENT],
            genres=[MusicGenre.POP, MusicGenre.INDIE, MusicGenre.R_AND_B],
            company="Park Entertainment Group",
            email="jen@parkent.com",
            phone="+1-310-555-0606",
            location="Los Angeles",
            country="USA",
            website="https://parkent.com",
            social_media=[
                SocialMedia(SocialMediaPlatform.LINKEDIN, "jenpark-entertainment", "https://linkedin.com/in/jenpark-entertainment"),
            ],
            bio="Managing 15+ artists across pop, indie, and R&B genres. Booking shows at major venues nationwide",
            years_experience=16,
            verified=True,
        ),
        # Music Lawyers
        Contact(
            id="007",
            name="Robert 'Rob' Henderson",
            roles=[ContactRole.MUSIC_LAWYER],
            genres=[MusicGenre.HIP_HOP, MusicGenre.POP, MusicGenre.ROCK],
            company="Henderson & Associates Law",
            email="rhenderson@henlaw.com",
            phone="+1-212-555-0707",
            location="New York",
            country="USA",
            website="https://henlaw.com",
            bio="Specializing in music contracts, copyright law, and artist representation for 25+ years",
            years_experience=25,
            verified=True,
        ),
        # Publicists
        Contact(
            id="008",
            name="Nina Vasquez",
            roles=[ContactRole.PUBLICIST],
            genres=[MusicGenre.POP, MusicGenre.INDIE, MusicGenre.LATIN],
            company="Vasquez PR & Media",
            email="nina@vasquezpr.com",
            location="Miami",
            country="USA",
            website="https://vasquezpr.com",
            social_media=[
                SocialMedia(SocialMediaPlatform.INSTAGRAM, "@vasquezpr", "https://instagram.com/vasquezpr"),
                SocialMedia(SocialMediaPlatform.TWITTER, "@vasquezpr", "https://twitter.com/vasquezpr"),
            ],
            bio="Publicity expert managing press campaigns for emerging and established pop and Latin artists",
            years_experience=13,
            verified=True,
        ),
        # Sync Agents
        Contact(
            id="009",
            name="Charles 'Charlie' Mitchell",
            roles=[ContactRole.SYNC_AGENT],
            genres=[MusicGenre.INDIE, MusicGenre.EDM, MusicGenre.FOLK],
            company="Sync Masters Global",
            email="charlie@syncmasters.com",
            location="Nashville",
            country="USA",
            website="https://syncmasters.com",
            bio="Licensing music for TV, film, and advertising. Network of 500+ independent artists",
            years_experience=9,
            verified=True,
        ),
        # Journalists
        Contact(
            id="010",
            name="Elena Rossi",
            roles=[ContactRole.JOURNALIST],
            genres=[MusicGenre.INDIE, MusicGenre.ROCK, MusicGenre.INDIE],
            company="Pitchfork Media",
            email="elenr@pitchfork.com",
            location="Brooklyn",
            country="USA",
            website="https://pitchfork.com",
            social_media=[
                SocialMedia(SocialMediaPlatform.TWITTER, "@elenarossiwrites", "https://twitter.com/elenarossiwrites"),
            ],
            bio="Senior music critic at Pitchfork covering indie and alternative rock",
            years_experience=12,
            verified=True,
        ),
    ]

    for contact in contacts:
        db.add_contact(contact)

    print(f"✓ Loaded {len(contacts)} sample contacts into sample_contacts.json")
    print(f"Total contacts: {db.get_contacts_count()}")


if __name__ == "__main__":
    load_sample_data()
