
import os

import click
from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect


db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()

login_manager.login_view = "auth.login"
login_manager.login_message = "Entre para acessar o sistema."
login_manager.login_message_category = "info"


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object("config.Config")

    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    from app.models import Clinic, User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    from app.routes import auth_bp, main_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    @app.cli.command("create-user")
    def create_user():
        """Cria um usuário vinculado a uma clínica existente."""

        username = click.prompt("Usuário")
        password = click.prompt(
            "Senha",
            hide_input=True,
            confirmation_prompt=True,
        )

        if len(password) < 8:
            raise click.ClickException(
                "A senha deve ter pelo menos 8 caracteres."
            )

        if User.query.filter_by(username=username).first():
            raise click.ClickException("Esse usuário já existe.")

        clinics = Clinic.query.order_by(Clinic.name).all()

        if not clinics:
            raise click.ClickException(
                "Nenhuma clínica cadastrada. Cadastre uma clínica primeiro."
            )

        click.echo("\nClínicas cadastradas:")
        for clinic in clinics:
            click.echo(f"{clinic.id} - {clinic.name}")

        clinic_id = click.prompt("Digite o ID da clínica", type=int)
        clinic = db.session.get(Clinic, clinic_id)

        if clinic is None:
            raise click.ClickException("Clínica não encontrada.")

        user = User(
            username=username,
            clinic_id=clinic.id,
        )
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        click.echo("Usuário criado com sucesso.")

    with app.app_context():
        os.makedirs(app.instance_path, exist_ok=True)
        db.create_all()

    return app
