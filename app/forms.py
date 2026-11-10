from flask_wtf import FlaskForm
from wtforms import (
    DateTimeLocalField,
    PasswordField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Email, Length, Optional


class LoginForm(FlaskForm):
    username = StringField("Usuário", validators=[DataRequired(), Length(max=80)])
    password = PasswordField("Senha", validators=[DataRequired()])
    submit = SubmitField("Entrar")


class ClientForm(FlaskForm):
    name = StringField("Nome completo", validators=[DataRequired(), Length(max=120)])
    phone = StringField("Telefone", validators=[DataRequired(), Length(max=30)])
    email = StringField("E-mail", validators=[Optional(), Email(), Length(max=120)])
    notes = TextAreaField("Observações", validators=[Optional(), Length(max=2000)])
    submit = SubmitField("Salvar cliente")


class AppointmentForm(FlaskForm):
    client_id = SelectField(
        "Cliente",
        coerce=int,
        validators=[DataRequired(message="Selecione um cliente.")],
    )
    starts_at = DateTimeLocalField(
        "Data e horário",
        format="%Y-%m-%dT%H:%M",
        validators=[DataRequired()],
    )
    status = SelectField(
        "Situação",
        choices=[
            ("agendado", "Agendado"),
            ("concluido", "Concluído"),
            ("cancelado", "Cancelado"),
        ],
        validators=[DataRequired()],
    )
    notes = TextAreaField("Observações", validators=[Optional(), Length(max=2000)])
    submit = SubmitField("Salvar agendamento")


class RegisterForm(FlaskForm):
    full_name = StringField(
        "Nome completo",
        validators=[DataRequired(), Length(max=120)],
    )
    username = StringField(
        "Usuário ou e-mail",
        validators=[DataRequired(), Length(max=80)],
    )
    password = PasswordField(
        "Senha",
        validators=[
            DataRequired(),
            Length(min=8, message="A senha deve ter pelo menos 8 caracteres."),
        ],
    )
    confirm_password = PasswordField(
        "Confirmar senha",
        validators=[DataRequired()],
    )
    invite_code = StringField(
        "Código de convite",
        validators=[DataRequired(), Length(max=100)],
    )
    submit = SubmitField("Criar minha conta")


class ClinicRegisterForm(FlaskForm):
    clinic_name = StringField(
        "Nome da clínica",
        validators=[DataRequired(), Length(max=150)],
    )
    full_name = StringField(
        "Nome do responsável",
        validators=[DataRequired(), Length(max=120)],
    )
    username = StringField(
        "Usuário ou e-mail",
        validators=[DataRequired(), Length(max=80)],
    )
    password = PasswordField(
        "Senha",
        validators=[
            DataRequired(),
            Length(min=8, message="A senha deve ter pelo menos 8 caracteres."),
        ],
    )
    confirm_password = PasswordField(
        "Confirmar senha",
        validators=[DataRequired()],
    )
    submit = SubmitField("Cadastrar minha clínica")
