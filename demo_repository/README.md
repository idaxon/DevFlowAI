# Flask Demo API (Target Service)

A lightweight microservice providing user data APIs.

## Endpoints:
- `GET /`: Health status
- `GET /health`: Detailed status check
- `GET /users`: List active users (Requires valid database connection configuration)

## Known Issue:
When `DATABASE_URL` is omitted from the application configuration, `/users` will fail with an HTTP 500 error.
