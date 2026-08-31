def test_register_returns_access_token(client):
    response = client.post(
        "/api/auth/register",
        json={
            "full_name": "Test Donor",
            "email": "donor@example.com",
            "password": "Secret123!",
            "role": "donor",
        },
    )

    assert response.status_code == 201
    assert response.json["user"]["email"] == "donor@example.com"
    assert response.json["access_token"]
