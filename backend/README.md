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
alembic revision --autogenerate -m "create users table"
```

## 7. Run Migration

```powershell
alembic upgrade head
```

## 8. Start FastAPI

```powershell
python -m uvicorn app.main:app --reload
```

## 9. Test Health Endpoints

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

## 10. Test Auth In Swagger

Start the backend:

```powershell
python -m uvicorn app.main:app --reload
```

Open Swagger:

```text
http://127.0.0.1:8000/docs
```

Auth test flow:

1. Call `POST /api/auth/register` to register a user.

```json
{
  "email": "test@example.com",
  "password": "123456"
}
```

2. Call `POST /api/auth/login` with the same email and password.
3. Copy the returned `access_token`.
4. Click `Authorize` in the top-right corner of Swagger.
5. Paste the token into the Bearer token field.
6. Call `GET /api/auth/me`.
7. Confirm the response returns the current user information.

Swagger uses an HTTP Bearer security scheme, so paste only the token value from `access_token`; do not type `Bearer ` manually.

## 11. Test Dataset Upload In Swagger

Install new dependencies:

```powershell
python -m pip install -r requirements.txt
```

Generate the dataset migration:

```powershell
python -m alembic revision --autogenerate -m "add datasets table"
```

Run the migration:

```powershell
python -m alembic upgrade head
```

Start the backend:

```powershell
python -m uvicorn app.main:app --reload
```

Open Swagger:

```text
http://127.0.0.1:8000/docs
```

Dataset upload test flow:

1. Call `POST /api/auth/register` to register a user.
2. Call `POST /api/auth/login` to log in.
3. Copy the returned `access_token`.
4. Click `Authorize` in Swagger and paste the token value.
5. Call `POST /api/datasets/upload` to upload a CSV or Excel file.
6. Call `GET /api/datasets` to view the current user's dataset list.
7. Call `GET /api/datasets/{dataset_id}` to view dataset details.
8. Call `DELETE /api/datasets/{dataset_id}` to delete the dataset and its local file.
