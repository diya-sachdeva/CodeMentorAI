# CodeMentor AI 🧠

An AI-powered DSA interview practice platform. Get real problems tailored to specific companies, write your solution, and receive instant Gemini-powered feedback on correctness, time/space complexity, edge cases, and communication.

## Stack

- **Backend**: FastAPI + SQLAlchemy + SQLite
- **Frontend**: HTML, CSS, Vanilla JS (no build step)
- **AI**: Google Gemini 1.5 Flash
- **Auth**: JWT (stored in httpOnly cookies)

## Setup

### 1. Clone and create a virtual environment

```bash
git clone <your-repo-url>
cd CodeMentorAI

python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set up environment variables

```bash
cp .env.example .env
```

Edit `.env` and fill in:
- `GEMINI_API_KEY` — get one free at [aistudio.google.com](https://aistudio.google.com)
- `SECRET_KEY` — any random long string (used for JWT signing)

### 4. Run the app

```bash
python main.py
```

Visit [http://localhost:8000](http://localhost:8000)

## Features

- 🔐 JWT authentication (signup, login, logout)
- 🎯 Company-tailored DSA problems (Google, Microsoft, Amazon, Atlassian, Adobe)
- 🤖 Gemini evaluates: correctness, time complexity, space complexity, edge cases, communication
- 📊 Dashboard with average score and weak topic tracking
- 📜 Full interview history with detailed feedback

## Project Structure

```
CodeMentorAI/
├── backend/
│   ├── app.py         # FastAPI routes
│   ├── database.py    # SQLAlchemy models + DB setup
│   ├── auth.py        # JWT + password hashing
│   ├── ai.py          # Gemini integration
│   └── models.py      # Pydantic request/response models
├── frontend/
│   ├── index.html     # Landing page
│   ├── login.html
│   ├── signup.html
│   ├── dashboard.html
│   ├── interview.html
│   ├── feedback.html
│   └── history.html
├── static/
│   ├── css/styles.css
│   └── js/main.js
├── main.py            # Entry point
├── requirements.txt
└── .env.example
```

## Planned Improvements (v2)

- In-browser code editor (Monaco) with syntax highlighting
- Code execution sandbox
- Multi-question interview sessions
- Spaced repetition recommendations
- Leaderboard / social features
