# Podologia Digital

MVP web responsivo para gestão de clientes e agendamentos de uma clínica de podologia, desenvolvido em Python 3.12 com Flask e SQLite. Projeto acadêmico da disciplina Projeto de Software (Análise e Desenvolvimento de Sistemas — Cruzeiro do Sul).

## Funcionalidades

- Acesso autenticado; as senhas são armazenadas com hash seguro do Werkzeug (PBKDF2 com salt), nunca em texto puro.
- Cadastro, consulta, edição e exclusão de clientes. A exclusão é bloqueada quando existem agendamentos associados.
- CRUD de agendamentos com cliente, data, horário, observações e situação (agendado, concluído ou cancelado).
- Validação de conflito: não permite dois agendamentos ativos no mesmo horário; horários cancelados ficam disponíveis novamente.
- Painel com indicadores e próximos atendimentos, formulários com validação no servidor e proteção CSRF.

## Requisitos

Python 3.12+ e pip.

## Instalação e execução

```bash
python -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Defina uma chave aleatória para produção (ex.: python -c "import secrets; print(secrets.token_hex(32))")
# Linux/macOS
export SECRET_KEY="substitua-por-uma-chave-secreta"
# Windows PowerShell: $env:SECRET_KEY="substitua-por-uma-chave-secreta"

flask --app run.py create-user
python run.py
```

O comando `create-user` solicita usuário e senha (mínimo de 8 caracteres). Não existe cadastro público de usuários. O banco SQLite e o diretório `instance/` são criados automaticamente. Acesse http://127.0.0.1:5000.

Para apontar para outro banco, defina `DATABASE_URL`; 
Testes locais, por exemplo, `sqlite:///teste.db`.

## Testes

```bash
pytest
```

Os testes usam banco SQLite em memória e cobrem autenticação, CRUD básico e a regra de disponibilidade. A proteção CSRF é desabilitada apenas no ambiente de testes.

## Organização

- `app/models.py`: entidades SQLAlchemy (usuário, cliente e agendamento).
- `app/routes.py`: rotas HTTP e fluxo da interface.
- `app/services.py`: regras de negócio e disponibilidade de horários.
- `app/forms.py`: formulários e validações WTForms.
- `app/templates/` e `app/static/`: interface Bootstrap responsiva, CSS e JavaScript.
- `config.py`: configuração por variáveis de ambiente.
- `tests/`: testes unitários e de integração.

## Histórico semântico e revisão

Use commits curtos no formato Conventional Commits (por exemplo, `feat: adiciona validação de horários` ou `fix: bloqueia conflito de agendamento`). Pull requests devem explicar motivação, alterações e testes; manter escopo pequeno; incluir evidências de interface quando aplicável; e passar pela revisão de requisitos, segurança, legibilidade e testes antes do merge.
