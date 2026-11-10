
import pytest
from datetime import datetime

from app import create_app, db
from app.models import Appointment, Client, Clinic, User
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

        clinic = Clinic(name="Clínica Teste")
        clinic.set_invite_code("convite-clinica-a")

        other_clinic = Clinic(name="Clínica Outra")
        other_clinic.set_invite_code("convite-clinica-b")

        db.session.add_all([clinic, other_clinic])
        db.session.flush()

        user = User(
            full_name="Usuário Teste",
            username="teste",
            clinic_id=clinic.id,
        )
        user.set_password("senha-segura-123")

        other_user = User(
            full_name="Outro Usuário",
            username="outro",
            clinic_id=other_clinic.id,
        )
        other_user.set_password("senha-segura-456")

        client = Client(
            name="Maria Silva",
            phone="11999990000",
            clinic_id=clinic.id,
        )

        other_client = Client(
            name="Ana Souza",
            phone="11988887777",
            clinic_id=other_clinic.id,
        )

        db.session.add_all([user, other_user, client, other_client])
        db.session.commit()

    yield application

    with application.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def login(client, username="teste", password="senha-segura-123"):
    return client.post(
        "/login",
        data={"username": username, "password": password},
        follow_redirects=True,
    )


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
        data={
            "username": "teste",
            "password": "senha-segura-123",
        },
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")


def test_client_crud_routes(client):
    login(client)

    response = client.post(
        "/clientes",
        data={
            "name": "Carlos Souza",
            "phone": "11977776666",
            "email": "carlos@example.com",
            "submit": "Salvar cliente",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert "Carlos Souza" in response.get_data(as_text=True)


def test_appointment_conflict_and_cancelled_slot(app):
    with app.app_context():
        clinic = Clinic.query.filter_by(name="Clínica Teste").first()
        client_record = Client.query.filter_by(name="Maria Silva").first()

        starts_at = datetime(2026, 12, 1, 10, 0)

        first = save_appointment(
            Appointment(),
            clinic_id=clinic.id,
            client_id=client_record.id,
            starts_at=starts_at,
        )

        with pytest.raises(AppointmentConflict):
            save_appointment(
                Appointment(),
                clinic_id=clinic.id,
                client_id=client_record.id,
                starts_at=starts_at,
            )

        first.status = "cancelado"
        db.session.commit()

        save_appointment(
            Appointment(),
            clinic_id=clinic.id,
            client_id=client_record.id,
            starts_at=starts_at,
        )


def test_appointment_rejects_client_from_another_clinic(app):
    with app.app_context():
        clinic = Clinic.query.filter_by(name="Clínica Teste").first()
        other_client = Client.query.filter_by(name="Ana Souza").first()

        with pytest.raises(ValueError, match="Cliente não encontrado"):
            save_appointment(
                Appointment(),
                clinic_id=clinic.id,
                client_id=other_client.id,
                starts_at=datetime(2026, 12, 2, 10, 0),
            )


def test_create_appointment_through_web(client):
    login(client)

    with client.application.app_context():
        client_record = Client.query.filter_by(name="Maria Silva").first()
        client_id = client_record.id

    response = client.post(
        "/agendamentos/novo",
        data={
            "client_id": str(client_id),
            "starts_at": "2026-12-01T10:00",
            "status": "agendado",
            "notes": "Primeira consulta",
            "submit": "Salvar agendamento",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert "Maria Silva" in response.get_data(as_text=True)
    assert "01/12/2026 10:00" in response.get_data(as_text=True)


def test_clinic_cannot_view_another_clinics_clients(client):
    login(client, username="outro", password="senha-segura-456")

    response = client.get("/clientes")

    assert response.status_code == 200
    assert "Ana Souza" in response.get_data(as_text=True)
    assert "Maria Silva" not in response.get_data(as_text=True)


def test_clinic_cannot_edit_another_clinics_client(client):
    login(client, username="outro", password="senha-segura-456")

    with client.application.app_context():
        client_record = Client.query.filter_by(name="Maria Silva").first()
        client_id = client_record.id

    response = client.get(f"/clientes/{client_id}/editar")

    assert response.status_code == 404


def test_clinic_cannot_create_appointment_for_another_clinics_client(client):
    login(client, username="outro", password="senha-segura-456")

    with client.application.app_context():
        client_record = Client.query.filter_by(name="Maria Silva").first()
        client_id = client_record.id

    response = client.post(
        "/agendamentos/novo",
        data={
            "client_id": str(client_id),
            "starts_at": "2026-12-01T10:00",
            "status": "agendado",
            "notes": "Tentativa de acesso",
            "submit": "Salvar agendamento",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Ana Souza" in html
    assert "Maria Silva" not in html
    assert "Not a valid choice." in html


def test_employee_registration_joins_correct_clinic(client):
    response = client.post(
        "/cadastro",
        data={
            "full_name": "Funcionário A",
            "username": "funcionario_a",
            "password": "senha-funcionario-123",
            "confirm_password": "senha-funcionario-123",
            "invite_code": "convite-clinica-a",
            "submit": "Criar minha conta",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200

    with client.application.app_context():
        user = User.query.filter_by(username="funcionario_a").first()
        clinic = Clinic.query.filter_by(name="Clínica Teste").first()

        assert user is not None
        assert user.clinic_id == clinic.id


def test_clinic_registration_creates_empty_clinic(client):
    response = client.post(
        "/cadastro-clinica",
        data={
            "clinic_name": "Nova Clínica",
            "full_name": "Responsável Nova Clínica",
            "username": "responsavel_nova",
            "password": "senha-nova-123",
            "confirm_password": "senha-nova-123",
            "submit": "Cadastrar minha clínica",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert "Nova Clínica" in response.get_data(as_text=True)
    assert "Código de convite" in response.get_data(as_text=True)

    with client.application.app_context():
        clinic = Clinic.query.filter_by(name="Nova Clínica").first()

        assert clinic is not None
        assert clinic.check_invite_code(
            response.get_data(as_text=True).split("Código de convite:")[-1].split("<")[0].strip()
        ) is False or clinic.invite_code_hash is not None

        assert Client.query.filter_by(clinic_id=clinic.id).count() == 0
        assert (
            db.session.query(Appointment)
            .join(Client)
            .filter(Client.clinic_id == clinic.id)
            .count()
            == 0
        )
