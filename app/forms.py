from flask_wtf import FlaskForm
from wtforms import DateTimeLocalField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, Optional


class LoginForm(FlaskForm):
    username = StringField("Usuário", validators=[DataRequired(), Length(max=80)])
    password = StringField("Senha", validators=[DataRequired()])
    submit = SubmitField("Entrar")


class ClientForm(FlaskForm):
    name = StringField("Nome completo", validators=[DataRequired(), Length(max=120)])
    phone = StringField("Telefone", validators=[DataRequired(), Length(max=30)])
    email = StringField("E-mail", validators=[Optional(), Email(), Length(max=120)])
    notes = TextAreaField("Observações", validators=[Optional(), Length(max=2000)])
    submit = SubmitField("Salvar cliente")


class AppointmentForm(FlaskForm):
    client_id = SelectField("Cliente", coerce=int, validators=[DataRequired(message="Selecione um cliente.")])
    starts_at = DateTimeLocalField(
        "Data e horário", format="%Y-%m-%dT%H:%M", validators=[DataRequired()]
    )
    status = SelectField(
        "Situação",
        choices=[("agendado", "Agendado"), ("concluido", "Concluído"), ("cancelado", "Cancelado")],
        validators=[DataRequired()],
    )
    notes = TextAreaField("Observações", validators=[Optional(), Length(max=2000)])
    submit = SubmitField("Salvar agendamento")
