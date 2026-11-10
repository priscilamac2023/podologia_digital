
from sqlalchemy import select

from app import db
from app.models import Appointment, Client

class AppointmentConflict(ValueError):
    """Indica que já existe um atendimento ativo no horário solicitado."""

def is_time_available(starts_at, clinic_id, exclude_id=None):
    query = (
        select(Appointment.id)
        .join(Client)
        .where(
            Appointment.starts_at == starts_at,
            Appointment.status == "agendado",
            Client.clinic_id == clinic_id,
        )
    )

    if exclude_id is not None:
        query = query.where(Appointment.id != exclude_id)

    return db.session.execute(query).first() is None

def save_appointment(
    appointment,
    *,
    clinic_id,
    client_id,
    starts_at,
    status="agendado",
    notes=None,
):
    client = db.session.scalar(
        select(Client).where(
            Client.id == client_id,
            Client.clinic_id == clinic_id,
        )
    )

    if client is None:
        raise ValueError("Cliente não encontrado nesta clínica.")

    if status == "agendado" and not is_time_available(
        starts_at,
        clinic_id,
        appointment.id,
    ):
        raise AppointmentConflict(
            "Esse horário já está ocupado. Escolha outro horário."
        )

    appointment.client_id = client_id
    appointment.starts_at = starts_at
    appointment.status = status
    appointment.notes = notes

    db.session.add(appointment)
    db.session.commit()

    return appointment
