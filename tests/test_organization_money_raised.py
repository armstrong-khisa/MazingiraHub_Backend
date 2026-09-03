from decimal import Decimal

from extensions import db
from models import Donation, Organization, User


def test_organization_api_includes_successful_money_raised(client, app):
    with app.app_context():
        donor = User(email="donor-money@example.com", full_name="Money Donor")
        donor.set_password("Secret123!")
        organization = Organization(name="Money Org", approved=True)
        db.session.add_all([donor, organization])
        db.session.flush()
        db.session.add_all([
            Donation(
                donor_id=donor.id,
                organization_id=organization.id,
                amount=Decimal("125.50"),
                status="paid",
            ),
            Donation(
                donor_id=donor.id,
                organization_id=organization.id,
                amount=Decimal("75.00"),
                status="pending",
            ),
        ])
        db.session.commit()
        organization_id = organization.id

    response = client.get(f"/organizations/{organization_id}")

    assert response.status_code == 200
    assert response.json["data"]["moneyRaised"] == 125.5