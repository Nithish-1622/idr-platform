# Backend Environment Variables Reference

| Variable Name | Default Value | Description |
|---|---|---|
| `SECRET_KEY` | `django-insecure-...` | Django secret key used for cryptographic signing. |
| `DEBUG` | `False` | Enables Django Debug Mode (Use `True` only in dev). |
| `ALLOWED_HOSTS` | `127.0.0.1,localhost` | Comma-separated list of host/domain names that this Django site can serve. |
| `POSTGRES_DB` | `idr_backend` | PostgreSQL database name. |
| `POSTGRES_USER` | `postgres` | PostgreSQL username. |
| `POSTGRES_PASSWORD` | `postgres` | PostgreSQL password. |
| `POSTGRES_HOST` | `127.0.0.1` | PostgreSQL database host address. |
| `POSTGRES_PORT` | `5432` | PostgreSQL port. |
| `REDIS_URL` | `redis://127.0.0.1:6379/0` | Connection URL for Redis broker & result backend. |
| `USE_SQLITE_TEST` | `False` | Fallback flag for unit testing without PostGIS. |
| `MEDIA_ROOT` | `BASE_DIR/media` | Path to store model artifacts, map packages, and uploaded files. |
