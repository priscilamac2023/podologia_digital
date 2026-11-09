from datetime import datetime
from urllib.parse import urlsplit

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import select

from app import db
from app.forms import AppointmentForm, ClientForm, LoginForm, RegisterForm
from app.models import Appointment, Client, User
from app.services import AppointmentConflict, save_appointment


auth_bp = Blueprint("auth", __name__)
main_bp = Blueprint("main", __name__)


def _safe_next_url(target):
    """Aceita somente destinos locais para evitar redirecionamento externo no login."""
    if not target:
        return None
    parsed = urlsplit(target)
    if parsed.scheme or parsed.netloc or not target.startswith("/") or target.startswith("//"):
        return None
    return target


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data.strip()).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(_safe_next_url(request.args.get("next")) or url_for("main.index"))
        flash("Usuário ou senha inválidos.", "danger")
    return render_template("login.html", form=form)

@auth_bp.route("/cadastro", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = RegisterForm()

    if form.validate_on_submit():
        invite_code = current_app.config.get("INVITE_CODE", "")

        if not invite_code or form.invite_code.data != invite_code:
            flash("Código de convite inválido.", "danger")
            return render_template("register.html", form=form)

        username = form.username.data.strip()

        if User.query.filter_by(username=username).first():
            flash("Esse nome de usuário já está cadastrado.", "danger")
            return render_template("register.html", form=form)

        if form.password.data != form.confirm_password.data:
            flash("As senhas não coincidem.", "danger")
            return render_template("register.html", form=form)

        user = User(
            full_name=form.full_name.data.strip(),
            username=username,
        )
        user.set_password(form.password.data)

        db.session.add(user)
        db.session.commit()

        flash("Cadastro realizado com sucesso! Entre com seu usuário e senha.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html", form=form)


@auth_bp.post("/logout")
@login_required
def logout():
    logout_user()
    flash("Você saiu do sistema.", "success")
    return redirect(url_for("auth.login"))


@main_bp.get("/")
@login_required
def index():
    now = datetime.now()
    upcoming = db.session.scalars(
        select(Appointment)
        .where(Appointment.starts_at >= now, Appointment.status == "agendado")
        .order_by(Appointment.starts_at)
        .limit(8)
    ).all()
    return render_template(
        "index.html",
        client_count=db.session.scalar(select(db.func.count(Client.id))) or 0,
        appointment_count=db.session.scalar(
            select(db.func.count(Appointment.id)).where(Appointment.status == "agendado")
        ) or 0,
        upcoming=upcoming,
    )


@main_bp.route("/clientes", methods=["GET", "POST"])
@login_required
def clients():
    form = ClientForm()
    if form.validate_on_submit():
        client = Client(name=form.name.data.strip(), phone=form.phone.data.strip(),
                        email=form.email.data or None, notes=form.notes.data or None)
        db.session.add(client)
        db.session.commit()
        flash("Cliente cadastrado com sucesso.", "success")
        return redirect(url_for("main.clients"))
    records = db.session.scalars(select(Client).order_by(Client.name)).all()
    return render_template("clients.html", form=form, clients=records, title="Clientes")


@main_bp.route("/clientes/<int:client_id>/editar", methods=["GET", "POST"])
@login_required
def edit_client(client_id):
    client = db.get_or_404(Client, client_id)
    form = ClientForm(obj=client)
    if form.validate_on_submit():
        form.populate_obj(client)
        client.name, client.phone = client.name.strip(), client.phone.strip()
        db.session.commit()
        flash("Cadastro do cliente atualizado.", "success")
        return redirect(url_for("main.clients"))
    return render_template("client_edit.html", form=form, client=client)


@main_bp.post("/clientes/<int:client_id>/excluir")
@login_required
def delete_client(client_id):
    client = db.get_or_404(Client, client_id)
    if client.appointments:
        flash("Não é possível excluir um cliente com agendamentos registrados.", "warning")
    else:
        db.session.delete(client)
        db.session.commit()
        flash("Cliente excluído.", "success")
    return redirect(url_for("main.clients"))


def _appointment_form(appointment=None):
    form = AppointmentForm(obj=appointment)
    form.client_id.choices = [(c.id, c.name) for c in db.session.scalars(select(Client).order_by(Client.name))]
    return form


@main_bp.route("/agendamentos/novo", methods=["GET", "POST"])
@login_required
def new_appointment():
    form = _appointment_form()
    if not form.client_id.choices:
        flash("Cadastre um cliente antes de criar um agendamento.", "info")
        return redirect(url_for("main.clients"))
    if form.validate_on_submit():
        try:
            appointment = save_appointment(
                Appointment(),
                client_id=form.client_id.data,
                starts_at=form.starts_at.data,
                status=form.status.data,
                notes=form.notes.data or None,
            )
            return redirect(url_for("main.appointment_success", appointment_id=appointment.id))
        except (AppointmentConflict, ValueError) as error:
            db.session.rollback()
            flash(str(error), "danger")
    return render_template("appointment_form.html", form=form, title="Novo agendamento")


@main_bp.route("/agendamentos/<int:appointment_id>/editar", methods=["GET", "POST"])
@login_required
def edit_appointment(appointment_id):
    appointment = db.get_or_404(Appointment, appointment_id)
    form = _appointment_form(appointment)
    if form.validate_on_submit():
        try:
            save_appointment(appointment, client_id=form.client_id.data,
                             starts_at=form.starts_at.data, status=form.status.data,
                             notes=form.notes.data or None)
            flash("Agendamento atualizado.", "success")
            return redirect(url_for("main.appointments"))
        except (AppointmentConflict, ValueError) as error:
            db.session.rollback()
            flash(str(error), "danger")
    return render_template("appointment_form.html", form=form, title="Editar agendamento")


@main_bp.get("/agendamentos")
@login_required
def appointments():
    records = db.session.scalars(
        select(Appointment).join(Client).order_by(Appointment.starts_at.desc())
    ).all()
    return render_template("appointments.html", appointments=records, title="Agendamentos")


@main_bp.post("/agendamentos/<int:appointment_id>/excluir")
@login_required
def delete_appointment(appointment_id):
    appointment = db.get_or_404(Appointment, appointment_id)
    db.session.delete(appointment)
    db.session.commit()
    flash("Agendamento excluído.", "success")
    return redirect(url_for("main.appointments"))


@main_bp.get("/agendamentos/<int:appointment_id>/sucesso")
@login_required
def appointment_success(appointment_id):
    appointment = db.get_or_404(Appointment, appointment_id)
    return render_template("appointment_success.html", appointment=appointment)
