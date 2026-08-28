def test_donations_require_authentication(client):
    response = client.get("/api/donations")

    assert response.status_code == 401
