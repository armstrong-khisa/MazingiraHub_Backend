from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from app import create_app
from extensions import db
from models import (
    Beneficiary,
    Donation,
    InventoryItem,
    Organization,
    OrganizationApplication,
    Payment,
    Project,
    RecurringDonation,
    Story,
    StoryMedia,
    User,
)


SEED_USERS = {
    "admin@mazingirahub.test": {
        "full_name": "Mazingira Admin",
        "phone": "254700000001",
        "role": "admin",
    },
    "admin2@mazingirahub.test": {
        "full_name": "Mazingira Admin 2",
        "phone": "254700000004",
        "role": "admin",
    },
    "donor1@mazingirahub.test": {
        "full_name": "Amina Wanjiku",
        "phone": "254700000002",
        "role": "donor",
    },
    "donor2@mazingirahub.test": {
        "full_name": "Brian Otieno",
        "phone": "254700000005",
        "role": "donor",
    },
    "donor3@mazingirahub.test": {
        "full_name": "Cynthia Akinyi",
        "phone": "254700000006",
        "role": "donor",
    },
    "donor4@mazingirahub.test": {
        "full_name": "David Mwangi",
        "phone": "254700000007",
        "role": "donor",
    },
    "greenfuture@mazingirahub.test": {
        "full_name": "Green Future Kenya",
        "phone": "254700000003",
        "role": "organization",
    },
    "cleanwater@mazingirahub.test": {
        "full_name": "Clean Water Initiative",
        "phone": "254700000008",
        "role": "organization",
    },
    "youth4earth@mazingirahub.test": {
        "full_name": "Youth for Earth",
        "phone": "254700000009",
        "role": "organization",
    },
}
SEED_PASSWORD = "MazingiraTest123!"

ORGANIZATIONS = [
    ("Green Future Kenya", "Community-led environmental restoration and education.", "Restore local ecosystems through practical community action.", "Nairobi, Kenya"),
    ("Clean Water Initiative", "Improving reliable access to safe water in underserved communities.", "Make clean water accessible to every household.", "Turkana, Kenya"),
    ("Youth for Earth", "Equipping young people to lead practical climate action.", "Build a generation of confident environmental leaders.", "Nairobi, Kenya"),
    ("Mombasa Coastal Conservation", "Protecting coastal ecosystems with local communities.", "Restore mangroves and keep the Kenyan coast healthy.", "Mombasa, Kenya"),
    ("Kenya Community Food Network", "Supporting resilient, locally grown food systems.", "Help communities grow nutritious food sustainably.", "Kisumu, Kenya"),
]

PROJECTS = [
    ("Green Future Kenya", "Urban Tree Restoration", "Plant and maintain trees in underserved urban neighborhoods.", "100000.00"),
    ("Green Future Kenya", "Nairobi River Cleanup", "Remove waste and restore public access along the Nairobi River.", "75000.00"),
    ("Green Future Kenya", "School Tree Planting", "Create shade and outdoor learning spaces at local schools.", "60000.00"),
    ("Clean Water Initiative", "Clean Water for Turkana", "Install water points and storage tanks for Turkana communities.", "250000.00"),
    ("Mombasa Coastal Conservation", "Coastal Mangrove Restoration", "Restore mangrove habitats with coastal conservation groups.", "180000.00"),
    ("Kenya Community Food Network", "Community Food Gardens", "Establish productive community gardens and farmer training plots.", "90000.00"),
    ("Mombasa Coastal Conservation", "Plastic-Free Mombasa", "Organize shoreline cleanups and reduce single-use plastic waste.", "85000.00"),
    ("Youth for Earth", "Solar Schools Initiative", "Provide solar lighting and power for rural schools.", "220000.00"),
    ("Youth for Earth", "Wildlife Habitat Restoration", "Restore native habitat corridors through youth-led conservation work.", "150000.00"),
]

DONATIONS = [
    ("donor1@mazingirahub.test", "Urban Tree Restoration", "2500.00"),
    ("donor2@mazingirahub.test", "Nairobi River Cleanup", "10000.00"),
    ("donor3@mazingirahub.test", "School Tree Planting", "5000.00"),
    ("donor4@mazingirahub.test", "Clean Water for Turkana", "1000.00"),
    ("donor1@mazingirahub.test", "Coastal Mangrove Restoration", "25000.00"),
    ("donor2@mazingirahub.test", "Community Food Gardens", "7500.00"),
    ("donor3@mazingirahub.test", "Plastic-Free Mombasa", "3000.00"),
    ("donor4@mazingirahub.test", "Solar Schools Initiative", "15000.00"),
    ("donor1@mazingirahub.test", "Wildlife Habitat Restoration", "12000.00"),
    ("donor2@mazingirahub.test", "Clean Water for Turkana", "50000.00"),
]

BENEFICIARIES = [
    ("Green Future Kenya", "Nairobi public schools", "Schools receiving trees, shade, and environmental education."),
    ("Green Future Kenya", "Nairobi families", "Families benefiting from cleaner, greener neighborhoods."),
    ("Clean Water Initiative", "Turkana families", "Families gaining dependable access to safe water."),
    ("Youth for Earth", "Youth conservation groups", "Young people leading climate and habitat projects."),
    ("Mombasa Coastal Conservation", "Coastal conservation groups", "Local groups restoring mangroves and coastlines."),
    ("Kenya Community Food Network", "Community farming groups", "Groups growing food and sharing farming skills."),
]

INVENTORY = [
    ("Green Future Kenya", "Tree seedlings", "Native seedlings ready for planting.", 2500, "pieces"),
    ("Green Future Kenya", "Watering cans", "Reusable cans for newly planted trees.", 80, "pieces"),
    ("Green Future Kenya", "Gloves", "Protective gardening gloves.", 160, "pairs"),
    ("Mombasa Coastal Conservation", "Waste bags", "Heavy-duty bags for shoreline cleanups.", 1200, "pieces"),
    ("Clean Water Initiative", "Water tanks", "Storage tanks for community water points.", 24, "pieces"),
    ("Kenya Community Food Network", "Farming tools", "Hand tools for community food gardens.", 140, "pieces"),
]

STORIES = [
    ("Green Future Kenya", "1,000 Trees Planted in Nairobi", "Volunteers and school communities planted 1,000 native trees across Nairobi neighborhoods.", True),
    ("Clean Water Initiative", "Clean Water Reaches Turkana", "A new water point is bringing safe, dependable water closer to families in Turkana.", True),
    ("Mombasa Coastal Conservation", "Mangroves Return to the Coast", "Community conservation groups have restored a growing stretch of coastal mangrove habitat.", False),
    ("Youth for Earth", "Youth Leading the Plastic Cleanup", "Young environmental leaders brought together local volunteers for a citywide plastic cleanup.", False),
    ("Kenya Community Food Network", "Community Gardens Begin to Grow", "New food gardens are giving families practical tools for nutritious and resilient food production.", False),
]

STORY_MEDIA = [
    ("1,000 Trees Planted in Nairobi", "https://images.example.test/stories/nairobi-trees.jpg"),
    ("Clean Water Reaches Turkana", "https://images.example.test/stories/turkana-water.jpg"),
    ("Mangroves Return to the Coast", "https://images.example.test/stories/mangroves.jpg"),
]

PAYMENTS = [
    ("donor1@mazingirahub.test", "Urban Tree Restoration", "2500.00", "success", "MPESA-SEED-0001"),
    ("donor2@mazingirahub.test", "Nairobi River Cleanup", "10000.00", "pending", "CHECKOUT-SEED-0002"),
]

RECURRING_DONATIONS = [
    ("donor3@mazingirahub.test", "School Tree Planting", "monthly"),
    ("donor4@mazingirahub.test", "Clean Water for Turkana", "quarterly"),
]

ORGANIZATION_APPLICATIONS = [
    ("greenfuture@mazingirahub.test", "Green Future Kenya", "Community-led tree planting and urban restoration.", "approved", "admin@mazingirahub.test"),
    ("cleanwater@mazingirahub.test", "Clean Water Initiative", "A community organization improving access to safe water.", "approved", "admin@mazingirahub.test"),
    ("youth4earth@mazingirahub.test", "Youth for Earth", "A youth-led network for practical climate action.", "pending", None),
]


def get_or_create_user(email, values):
    user = User.query.filter_by(email=email).first()
    if not user:
        user = User(email=email, **values)
        user.set_password(SEED_PASSWORD)
        db.session.add(user)
        db.session.flush()
    return user


def get_or_create_organization(name, description, mission, location, admin_id):
    organization = Organization.query.filter_by(name=name).first()
    if not organization:
        organization = Organization(
            name=name,
            description=description,
            mission=mission,
            location=location,
            approved_by=admin_id,
            approved=True,
        )
        db.session.add(organization)
        db.session.flush()
    return organization


def seed():
    users = {
        email: get_or_create_user(email, values)
        for email, values in SEED_USERS.items()
    }
    organizations = {
        name: get_or_create_organization(
            name, description, mission, location, users["admin@mazingirahub.test"].id
        )
        for name, description, mission, location in ORGANIZATIONS
    }

    projects = {}
    for organization_name, title, description, goal_amount in PROJECTS:
        project = Project.query.filter_by(
            organization_id=organizations[organization_name].id,
            title=title,
        ).first()
        if not project:
            project = Project(
                organization_id=organizations[organization_name].id,
                title=title,
                description=description,
                goal_amount=Decimal(goal_amount),
                amount_raised=Decimal("0.00"),
                start_date=date.today(),
                end_date=date.today() + timedelta(days=180),
                completed=False,
            )
            db.session.add(project)
            db.session.flush()
        projects[title] = project

    for donor_email, project_title, amount in DONATIONS:
        donor = users[donor_email]
        project = projects[project_title]
        donation = Donation.query.filter_by(
            donor_id=donor.id,
            project_id=project.id,
            amount=Decimal(amount),
        ).first()
        if not donation:
            db.session.add(Donation(
                donor_id=donor.id,
                organization_id=project.organization_id,
                project_id=project.id,
                amount=Decimal(amount),
                currency="KES",
                donation_type="one-time",
                is_anonymous=False,
                status="success",
                payment_method="seed",
            ))

    for organization_name, name, description in BENEFICIARIES:
        if not Beneficiary.query.filter_by(
            organization_id=organizations[organization_name].id, name=name
        ).first():
            db.session.add(Beneficiary(
                organization_id=organizations[organization_name].id,
                name=name,
                description=description,
            ))

    for organization_name, name, description, quantity, unit in INVENTORY:
        if not InventoryItem.query.filter_by(
            organization_id=organizations[organization_name].id, name=name
        ).first():
            db.session.add(InventoryItem(
                organization_id=organizations[organization_name].id,
                name=name,
                description=description,
                quantity=quantity,
                unit=unit,
            ))

    for organization_name, title, content, featured in STORIES:
        if not Story.query.filter_by(
            organization_id=organizations[organization_name].id, title=title
        ).first():
            db.session.add(Story(
                organization_id=organizations[organization_name].id,
                title=title,
                content=content,
                featured=featured,
                published=True,
            ))

    stories = {
        story.title: story
        for story in Story.query.filter(Story.title.in_([item[1] for item in STORIES])).all()
    }
    for title, media_url in STORY_MEDIA:
        if not StoryMedia.query.filter_by(
            story_id=stories[title].id, media_url=media_url
        ).first():
            db.session.add(StoryMedia(
                story_id=stories[title].id,
                media_url=media_url,
            ))

    for donor_email, project_title, amount, status, provider_payment_id in PAYMENTS:
        donation = Donation.query.filter_by(
            donor_id=users[donor_email].id,
            project_id=projects[project_title].id,
            amount=Decimal(amount),
        ).first()
        if donation and not Payment.query.filter_by(donation_id=donation.id).first():
            db.session.add(Payment(
                donation_id=donation.id,
                provider_payment_id=provider_payment_id,
                payment_method="mpesa",
                amount=Decimal(amount),
                currency="KES",
                status=status,
                raw_callback='{"seed": true}',
                paid_at=None if status == "pending" else datetime.now(timezone.utc),
            ))

    for donor_email, project_title, frequency in RECURRING_DONATIONS:
        donation = Donation.query.filter_by(
            donor_id=users[donor_email].id,
            project_id=projects[project_title].id,
        ).first()
        if donation and not RecurringDonation.query.filter_by(donation_id=donation.id).first():
            db.session.add(RecurringDonation(
                donation_id=donation.id,
                frequency=frequency,
                next_donation_date=date.today() + timedelta(days=30),
                status="active",
            ))

    for applicant_email, org_name, description, status, reviewer_email in ORGANIZATION_APPLICATIONS:
        if not OrganizationApplication.query.filter_by(
            user_id=users[applicant_email].id, org_name=org_name
        ).first():
            db.session.add(OrganizationApplication(
                user_id=users[applicant_email].id,
                org_name=org_name,
                description=description,
                registration_docs_url=f"https://docs.example.test/applications/{org_name.lower().replace(' ', '-')}.pdf",
                reviewed_by=users[reviewer_email].id if reviewer_email else None,
                status=status,
            ))

    db.session.commit()
    print("Seed complete")
    print(f"Users: {len(users)}")
    print(f"Organizations: {len(organizations)}")
    print(f"Projects: {len(projects)}")
    print(f"Donations: {len(DONATIONS)}")
    print(f"Beneficiaries: {len(BENEFICIARIES)}")
    print(f"Inventory items: {len(INVENTORY)}")
    print(f"Stories: {len(STORIES)}")
    print(f"Story media: {len(STORY_MEDIA)}")
    print(f"Payments: {len(PAYMENTS)}")
    print(f"Recurring donations: {len(RECURRING_DONATIONS)}")
    print(f"Organization applications: {len(ORGANIZATION_APPLICATIONS)}")


if __name__ == "__main__":
    application = create_app()
    with application.app_context():
        seed()
