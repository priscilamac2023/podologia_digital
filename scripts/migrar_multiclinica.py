import os
from getpass import getpass

from sqlalchemy import create_engine, text
from werkzeug.security import generate_password_hash


NOME_CLINICA = "Clínica Podologia Digital"

url = os.environ.get("DATABASE_URL")
if not url:
    raise SystemExit("ERRO: DATABASE_URL não está configurada.")

engine = create_engine(url)

if engine.dialect.name != "postgresql":
    raise SystemExit("ERRO: este script exige PostgreSQL.")

def contar(conn, tabela):
    return conn.execute(
        text(f'SELECT COUNT(*) FROM "{tabela}"')
    ).scalar_one()


# Conferência inicial: não altera o banco.
with engine.connect() as conn:
    tabelas = conn.execute(
        text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
        """)
    ).scalars().all()

    if "clinics" in tabelas:
        raise SystemExit("ERRO: a tabela clinics já existe. Migração interrompida.")

    for tabela in ("user", "clients"):
        colunas = conn.execute(
            text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = :tabela
            """),
            {"tabela": tabela},
        ).scalars().all()

        if "clinic_id" in colunas:
            raise SystemExit(
                f"ERRO: {tabela} já possui clinic_id. Migração interrompida."
            )

    usuarios = contar(conn, "user")
    pacientes = contar(conn, "clients")
    agendamentos = contar(conn, "appointments")

    sem_cliente = conn.execute(
        text("""
            SELECT COUNT(*)
            FROM appointments a
            LEFT JOIN clients c ON c.id = a.client_id
            WHERE c.id IS NULL
        """)
    ).scalar_one()

    print("\nConferência do banco:")
    print("Usuários:", usuarios)
    print("Pacientes:", pacientes)
    print("Agendamentos:", agendamentos)
    print("Agendamentos sem paciente:", sem_cliente)

    if (usuarios, pacientes, agendamentos) != (2, 4, 2):
        raise SystemExit(
            "ERRO: as quantidades são diferentes das esperadas. Migração cancelada."
        )

    if sem_cliente:
        raise SystemExit(
            "ERRO: existem agendamentos sem paciente. Migração cancelada."
        )


invite_code = getpass(
    "\nDigite o código de convite inicial que você guardou: "
).strip()

if not invite_code:
    raise SystemExit("ERRO: o código não pode ficar vazio.")

confirmacao = input(
    '\nPara autorizar a migração, digite exatamente: MIGRAR Clínica Podologia Digital\n> '
)

if confirmacao != "MIGRAR Clínica Podologia Digital":
    raise SystemExit("Migração cancelada. Nenhuma alteração foi realizada.")


# Todas as alterações abaixo pertencem a uma única transação.
codigo_hash = generate_password_hash(invite_code)

with engine.begin() as conn:
    conn.execute(text("""
        CREATE TABLE clinics (
            id SERIAL PRIMARY KEY,
            name VARCHAR(150) NOT NULL,
            invite_code_hash VARCHAR(256) NOT NULL,
            created_at TIMESTAMP WITHOUT TIME ZONE
                NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """))

    resultado = conn.execute(
        text("""
            INSERT INTO clinics (name, invite_code_hash)
            VALUES (:name, :code_hash)
            RETURNING id
        """),
        {"name": NOME_CLINICA, "code_hash": codigo_hash},
    )
    clinic_id = resultado.scalar_one()

    conn.execute(text(
        'ALTER TABLE "user" ADD COLUMN clinic_id INTEGER'
    ))
    conn.execute(text(
        "ALTER TABLE clients ADD COLUMN clinic_id INTEGER"
    ))

    conn.execute(
        text('UPDATE "user" SET clinic_id = :id'),
        {"id": clinic_id},
    )
    conn.execute(
        text("UPDATE clients SET clinic_id = :id"),
        {"id": clinic_id},
    )

    conn.execute(text("""
        ALTER TABLE "user"
        ALTER COLUMN clinic_id SET NOT NULL
    """))
    conn.execute(text("""
        ALTER TABLE clients
        ALTER COLUMN clinic_id SET NOT NULL
    """))

    conn.execute(text("""
        ALTER TABLE "user"
        ADD CONSTRAINT fk_user_clinic_id_clinics
        FOREIGN KEY (clinic_id) REFERENCES clinics(id)
    """))
    conn.execute(text("""
        ALTER TABLE clients
        ADD CONSTRAINT fk_clients_clinic_id_clinics
        FOREIGN KEY (clinic_id) REFERENCES clinics(id)
    """))

    conn.execute(text("""
        CREATE INDEX ix_user_clinic_id ON "user" (clinic_id)
    """))
    conn.execute(text("""
        CREATE INDEX ix_clients_clinic_id ON clients (clinic_id)
    """))

    usuarios_finais = conn.execute(
        text('SELECT COUNT(*) FROM "user" WHERE clinic_id = :id'),
        {"id": clinic_id},
    ).scalar_one()

    pacientes_finais = conn.execute(
        text("SELECT COUNT(*) FROM clients WHERE clinic_id = :id"),
        {"id": clinic_id},
    ).scalar_one()

    if usuarios_finais != usuarios or pacientes_finais != pacientes:
        raise RuntimeError(
            "A conferência final falhou. A transação será revertida."
        )

print("\nMIGRAÇÃO CONCLUÍDA COM SUCESSO!")
print("Clínica:", NOME_CLINICA)
print("ID da clínica:", clinic_id)
print("Usuários vinculados:", usuarios_finais)
print("Pacientes vinculados:", pacientes_finais)
print("Os agendamentos existentes continuam vinculados aos seus pacientes.")

engine.dispose()
