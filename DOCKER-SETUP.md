# Run everything with one Docker command

This project includes a production-ready Docker Compose configuration that builds and runs the backend (Flask + Streamlit) and the Next.js research frontend in one command.

How to run

1. Ensure your environment variables are set (copy `.env.example` to `.env` and edit keys).

2. Run this single command from the repository root:

```powershell
docker-compose up --build
```

Services and default ports

- `trading-app` (Flask backend + Streamlit):
  - Flask API: http://localhost:8000
  - Streamlit UI: http://localhost:8501
- `frontend` (Next.js research UI):
  - Next.js app: http://localhost:3000

Notes

- The Next.js frontend is configured to call the backend at the internal Docker network address `http://trading-app:8000`. If you need the frontend to call an external backend host, set `NEXT_PUBLIC_API_BASE_URL` in your environment or `.env` before running compose.
- To run only the backend services (without the Next frontend):

```powershell
docker-compose up --build trading-app
```

---

This file was added automatically when the Next.js research UI was integrated into the repository. Use it as the single-command entrypoint for local development and quick demos.
