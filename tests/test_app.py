import pytest
from datetime import datetime

from app import create_app, db
from app.models import Appointment, Client, User
from app.services import AppointmentConflict, save_appointment


@pytest.fixture
def app():
    application = create_app({
        "TESTING": True,
        "SECRET_KEY": "test-secret",
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False,
    })
    with application.app_context():
        db.drop_all()
        db.create_all()
        user = User(username="teste")
        user.set_password("senha-segura-123")
        db.session.add(user)
        db.session.add(Client(name="Maria Silva", phone="11999990000"))
        db.session.commit()
    yield application
    with application.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def login(client):
    return client.post("/login", data={"username": "teste", "password": "senha-segura-123"}, follow_redirects=True)


def test_password_is_hashed_and_verified(app):
    with app.app_context():
        user = User.query.filter_by(username="teste").first()
        assert user.password_hash != "senha-segura-123"
        assert user.check_password("senha-segura-123")
        assert not user.check_password("incorreta")


def test_dashboard_requires_login_and_loads_after_login(client):
    assert client.get("/").status_code == 302
    response = login(client)
    assert response.status_code == 200
    assert "Clientes cadastrados" in response.get_data(as_text=True)


def test_login_rejects_external_next_redirect(client):
    response = client.post(
        "/login?next=https://example.com",
        data={"username": "teste", "password": "senha-segura-123"},
    )
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")


def test_client_crud_routes(client):
    login(client)
    response = client.post("/clientes", data={"name": "Ana Souza", "phone": "11988887777", "email": "ana@example.com", "submit": "Salvar cliente"}, follow_redirects=True)
    assert response.status_code == 200
    assert "Ana Souza" in response.get_data(as_text=True)


def test_appointment_conflict_and_cancelled_slot(app):
    with app.app_context():
        client = Client.query.filter_by(name="Maria Silva").first()
        starts_at = datetime(2026, 12, 1, 10, 0)
        first = save_appointment(Appointment(), client_id=client.id, starts_at=starts_at)
        with pytest.raises(AppointmentConflict):
            save_appointment(Appointment(), client_id=client.id, starts_at=starts_at)
        first.status = "cancelado"
        db.session.commit()
        save_appointment(Appointment(), client_id=client.id, starts_at=starts_at)


def test_create_appointment_through_web(client):
    login(client)
    response = client.post("/agendamentos/novo", data={"client_id": "1", "starts_at": "2026-12-01T10:00", "status": "agendado", "notes": "Primeira consulta", "submit": "Salvar agendamento"}, follow_redirects=True)
    assert response.status_code == 200
    assert "Maria Silva" in response.get_data(as_text=True)
    assert "01/12/2026 10:00" in response.get_data(as_text=True)
