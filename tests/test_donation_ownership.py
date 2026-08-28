from datetime import date, timedelta
from decimal import Decimal

from extensions import db
from models import Organization, Project, User


def test_donation_rejects_project_from_another_organization(client, app, donor_headers):
    with app.app_context():
        first_user = User(email="org-one@example.com", full_name="Org One")
        second_user = User(email="org-two@example.com", full_name="Org Two")
        first_user.set_password("Secret123!")
        second_user.set_password("Secret123!")
        db.session.add_all([first_user, second_user])
        db.session.flush()
        first_org = Organization(name="First Org", approved=True, user_id=first_user.id)
        second_org = Organization(name="Second Org", approved=True, user_id=second_user.id)
        db.session.add_all([first_org, second_org])
        db.session.flush()
        project = Project(
            organization_id=second_org.id,
            title="Second Project",
            description="A project owned by another organization.",
            goal_amount=Decimal("1000.00"),
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
        )
        db.session.add(project)
        db.session.commit()
        first_org_id = first_org.id
        project_id = project.id

    response = client.post(
        "/api/donations",
        headers=donor_headers,
        json={
            "organization_id": first_org_id,
            "project_id": project_id,
            "amount": "25.00",
        },
    )

    assert response.status_code == 404
    assert response.json["message"] == "Project not found for this organization."
