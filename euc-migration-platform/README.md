# EUC VBA to Python Migration Platform

React and FastAPI application for extracting VBA procedures, analysing business rules with Gemini, generating Python, validating the result, and producing report artifacts.

## Run the backend

```powershell
cd app
.\.venv\Scripts\python.exe -m uvicorn fastapi_app:app --host 127.0.0.1 --port 8000
```

## Run the frontend

```powershell
cd app/frontend
npm install
npm run dev
```

The frontend runs at `http://127.0.0.1:5173/` and the API runs at `http://127.0.0.1:8000/`.

## Gemini configuration

Copy `.env.example` to `.env` and provide valid Gemini credentials. Do not commit `.env` or API keys. Steps 3 and 4 use `GEMINI_API_KEY_1`; Step 5 uses `GEMINI_API_KEY_2`.

## Supported workbooks

The upload workflow accepts `.xlsm` and `.xlsb` files. Generated artifacts are stored under `runtime/runs/` and excluded from Git.