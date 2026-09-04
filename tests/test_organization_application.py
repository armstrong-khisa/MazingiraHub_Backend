from flask_jwt_extended import create_access_token

from extensions import db
from models import Organization, OrganizationApplication, User


def test_donor_creates_pending_organization_account(client, app):
    donor = client.post(
        "/api/auth/register",
        json={
            "full_name": "Test Donor",
            "email": "donor@example.com",
            "password": "Secret123!",
            "role": "donor",
        },
    )
    donor_token = donor.json["access_token"]

    response = client.post(
        "/organizations/applications",
        headers={"Authorization": f"Bearer {donor_token}"},
        json={
            "org_name": "Green Kenya",
            "email": "green@example.com",
            "password": "Organization123!",
            "description": "Restoring native forests",
            "image_url": "https://example.com/logo.jpg",
        },
    )

    assert response.status_code == 201
    with app.app_context():
        organization_user = User.query.filter_by(email="green@example.com").one()
        application = OrganizationApplication.query.one()
        assert organization_user.status == "inactive"
        assert application.user_id == organization_user.id
        assert application.image_url == "https://example.com/logo.jpg"


def test_admin_approval_activates_account_and_copies_image(client, app):
    with app.app_context():
        donor = User(
            full_name="Test Donor",
            email="donor@example.com",
            role="donor",
        )
        donor.set_password("Secret123!")
        organization_user = User(
            full_name="Green Kenya",
            email="green@example.com",
            role="organization",
            status="inactive",
        )
        organization_user.set_password("Organization123!")
        db.session.add_all([donor, organization_user])
        db.session.flush()
        application = OrganizationApplication(
            user_id=organization_user.id,
            org_name="Green Kenya",
            description="Restoring native forests",
            image_url="https://example.com/logo.jpg",
        )
        admin = User(
            full_name="Admin",
            email="admin@example.com",
            role="admin",
        )
        admin.set_password("Admin123!")
        db.session.add_all([application, admin])
        db.session.commit()
        admin_token = create_access_token(
            identity=str(admin.id), additional_claims={"role": "admin"}
        )
        application_id = application.id

    response = client.patch(
        f"/api/admin/applications/{application_id}/approve",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    with app.app_context():
        organization_user = User.query.filter_by(email="green@example.com").one()
        organization = Organization.query.filter_by(name="Green Kenya").one()
        assert organization_user.status == "active"
        assert organization.user_id == organization_user.id
        assert organization.image_url == "https://example.com/logo.jpg"