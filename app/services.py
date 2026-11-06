from sqlalchemy import select

from app import db
from app.models import Appointment, Client


class AppointmentConflict(ValueError):
    """Indica que já existe um atendimento ativo no horário solicitado."""


def is_time_available(starts_at, exclude_id=None):
    query = select(Appointment.id).where(
        Appointment.starts_at == starts_at,
        Appointment.status == "agendado",
    )
    if exclude_id is not None:
        query = query.where(Appointment.id != exclude_id)
    return db.session.execute(query).first() is None


def save_appointment(appointment, *, client_id, starts_at, status="agendado", notes=None):
    if db.session.get(Client, client_id) is None:
        raise ValueError("Cliente não encontrado.")
    if status == "agendado" and not is_time_available(starts_at, appointment.id):
        raise AppointmentConflict("Esse horário já está ocupado. Escolha outro horário.")

    appointment.client_id = client_id
    appointment.starts_at = starts_at
    appointment.status = status
    appointment.notes = notes
    db.session.add(appointment)
    db.session.commit()
    return appointment
