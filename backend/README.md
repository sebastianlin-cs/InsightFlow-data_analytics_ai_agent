# InsightFlow Backend

FastAPI + PostgreSQL + SQLAlchemy + Alembic minimal backend skeleton.

## 1. Enter Backend Directory

```powershell
cd D:\Emory_MSCS\DAgent\InsightFlow\backend
```

## 2. Install Dependencies

Use the Python virtual environment you already created, then install dependencies:

```powershell
python -m pip install -r requirements.txt
```

## 3. Configure Environment Variables

```powershell
copy .env.example .env
```

Edit `.env` if your PostgreSQL username, password, host, port, or database name differs.

## 4. Start PostgreSQL With Docker

```powershell
docker run --name insightflow-postgres `
  -e POSTGRES_USER=postgres `
  -e POSTGRES_PASSWORD=postgres `
  -e POSTGRES_DB=insightflow_db `
  -p 5432:5432 `
  -d postgres:16
```

If a container with the same name already exists, start it with:

```powershell
docker start insightflow-postgres
```

## 5. Initialize Or Use Alembic

Alembic is already configured in this backend. The configuration loads `.env`, imports `app.models`, and uses `Base.metadata` so autogenerate can detect the `User` model.

## 6. Generate Migration

```powershell
python -m alembic revision --autogenerate -m "create users table"
```

## 7. Run Migration

```powershell
python -m alembic upgrade head
```

## 8. Start FastAPI

```powershell
python -m uvicorn app.main:app --reload
```

## 9. Test Endpoints

Open these URLs in a browser or call them from PowerShell:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/health
Invoke-RestMethod http://127.0.0.1:8000/api/health/db
```

Browser URLs:

```text
http://127.0.0.1:8000/api/health
http://127.0.0.1:8000/api/health/db
```
