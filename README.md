# Chess Analysis Web App

A full-stack application for analyzing your `chess.com` games. Features a **FastAPI** Python backend utilizing a multiprocessing Minimax analysis engine, and a premium **React** frontend for a beautiful visual experience.

## Setup & Running

This application has two components that must be run concurrently.

### 1. Backend (FastAPI Python)
Open a terminal and navigate to the `backend` folder:
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```
*The backend server will run on `http://localhost:8000`*.

### 2. Frontend (React Vite)
Open a **new** terminal window and navigate to the `frontend` folder:
```bash
cd frontend
npm install
npm run dev
```
*The React app will typically run on `http://localhost:5173`. Open this URL in your web browser to access the sleek GUI!*
