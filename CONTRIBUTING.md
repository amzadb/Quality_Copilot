# Contributing to Quality Copilot

Thanks for contributing. This project is a FastAPI backend plus NiceGUI frontend for AI-assisted QA workflows.

## Prerequisites

- Python 3.10+
- Separate virtualenvs under `backend/.venv` and `frontend/.venv` (recommended)

## Local setup

```powershell
# Backend
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
# Set JWT_SECRET in .env (required when DEBUG=false)
alembic upgrade head
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Frontend (second terminal)
cd frontend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m app.main
```

Open http://127.0.0.1:9000/login

More detail: [README.md](README.md), [docs/DEPLOY_RENDER.md](docs/DEPLOY_RENDER.md).

## Running tests

From `backend/` with the backend venv active:

```powershell
python -m pytest
```

Focused runs:

```powershell
python -m pytest tests/api/test_auth.py -q
python -m pytest tests/api/test_contract.py -q
```

Add or update tests when you change API contracts, auth, or settings behavior.

## Branch naming

Use short, descriptive branch names:

| Prefix | Use |
|--------|-----|
| `feature/` | New capability |
| `fix/` | Bug fix |
| `docs/` | Documentation only |
| `chore/` | Tooling, deps, hygiene |

Examples: `feature/testrail-suites`, `fix/login-error-message`, `docs/render-deploy`.

## Pull requests

1. Fork (or branch from the default branch) and keep changes focused.
2. Run backend tests before opening a PR.
3. Describe **why** the change is needed and how you verified it.
4. Do not commit secrets (`.env`, tokens, real credentials).
5. Match existing code style: typed Python, thin API routes, services for orchestration.

## Code of conduct

Be respectful in issues and reviews. Security-sensitive findings go through [SECURITY.md](SECURITY.md), not public issues.

## License

By contributing, you agree that your contributions are licensed under the [MIT License](LICENSE).
