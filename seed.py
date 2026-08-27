from datetime import date, timedelta
from decimal import Decimal

from app import create_app
from extensions import db
from models import Donation, Organization, Project, User


SEED_USERS = {
    "admin@mazingirahub.test": {
        "full_name": "Mazingira Admin",
        "phone": "254700000001",
        "role": "admin",
    },
    "donor@mazingirahub.test": {
        "full_name": "Test Donor",
        "phone": "254700000002",
        "role": "donor",
    },
    "org@mazingirahub.test": {
        "full_name": "Green Future Organization",
        "phone": "254700000003",
        "role": "organization",
    },
}
SEED_PASSWORD = "MazingiraTest123!"


def get_or_create_user(email, values):
    user = User.query.filter_by(email=email).first()
    if not user:
        user = User(email=email, **values)
        user.set_password(SEED_PASSWORD)
        db.session.add(user)
        db.session.flush()
    return user


def seed():
    admin = get_or_create_user("admin@mazingirahub.test", SEED_USERS["admin@mazingirahub.test"])
    donor = get_or_create_user("donor@mazingirahub.test", SEED_USERS["donor@mazingirahub.test"])
    organization_user = get_or_create_user(
        "org@mazingirahub.test",
        SEED_USERS["org@mazingirahub.test"],
    )

    organization = Organization.query.filter_by(name="Green Future Kenya").first()
    if not organization:
        organization = Organization(
            name="Green Future Kenya",
            description="Community-led environmental restoration and education.",
            mission="Restore local ecosystems through practical community action.",
            location="Nairobi, Kenya",
            approved_by=admin.id,
            approved=True,
        )
        db.session.add(organization)
        db.session.flush()

    project = Project.query.filter_by(
        organization_id=organization.id,
        title="Urban Tree Restoration",
    ).first()
    if not project:
        project = Project(
            organization_id=organization.id,
            title="Urban Tree Restoration",
            description="Plant and maintain trees in underserved urban neighborhoods.",
            goal_amount=Decimal("100000.00"),
            amount_raised=Decimal("0.00"),
            start_date=date.today(),
            end_date=date.today() + timedelta(days=180),
            completed=False,
        )
        db.session.add(project)
        db.session.flush()

    donation = Donation.query.filter_by(
        donor_id=donor.id,
        project_id=project.id,
    ).first()
    if not donation:
        donation = Donation(
            donor_id=donor.id,
            organization_id=organization.id,
            project_id=project.id,
            amount=Decimal("2500.00"),
            currency="KES",
            donation_type="one-time",
            is_anonymous=False,
            status="pending",
        )
        db.session.add(donation)

    db.session.commit()
    print("Seed complete")
    print(f"Admin: {admin.email}")
    print(f"Donor: {donor.email}")
    print(f"Organization user: {organization_user.email}")
    print(f"Organization ID: {organization.id}")
    print(f"Project ID: {project.id}")
    print(f"Donation ID: {donation.id}")


if __name__ == "__main__":
    application = create_app()
    with application.app_context():
        seed()
