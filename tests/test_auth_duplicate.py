def test_register_rejects_duplicate_email(client, registered_client):
    response = client.post(
        "/api/auth/register",
        json={
            "full_name": "Another Donor",
            "email": "donor@example.com",
            "password": "Secret123!",
            "role": "donor",
        },
    )

    assert response.status_code == 409
    assert response.json["error"] == "Email already registered"
