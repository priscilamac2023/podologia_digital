from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()
login_manager = LoginManager()
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

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    from app.routes import auth_bp, main_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    @app.cli.command("create-user")
    def create_user():
        """Cria um usuário administrador inicial sem expor cadastro público."""
        import click
        from werkzeug.security import generate_password_hash

        username = click.prompt("Usuário")
        password = click.prompt("Senha", hide_input=True, confirmation_prompt=True)
        if len(password) < 8:
            raise click.ClickException("A senha deve ter pelo menos 8 caracteres.")
        if User.query.filter_by(username=username).first():
            raise click.ClickException("Esse usuário já existe.")
        db.session.add(User(username=username, password_hash=generate_password_hash(password)))
        db.session.commit()
        click.echo("Usuário criado com sucesso.")

    with app.app_context():
        import os

        os.makedirs(app.instance_path, exist_ok=True)
        db.create_all()

    return app
