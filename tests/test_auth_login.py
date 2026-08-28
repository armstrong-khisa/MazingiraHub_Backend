def test_login_returns_token_for_valid_credentials(client, registered_client):
    response = client.post(
        "/api/auth/login",
        json={"email": "donor@example.com", "password": "Secret123!"},
    )

    assert response.status_code == 200
    assert response.json["user"]["role"] == "donor"
    assert response.json["access_token"]
