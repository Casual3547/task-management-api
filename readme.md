# Task Management API

A REST API built with Flask for managing users and tasks.

I built this project to get practical experience building a backend application from the ground up, including authentication, database relationships, validation, migrations, and automated testing.

## Features

- User registration
- User login
- JWT access and refresh tokens
- Logout and token revocation
- Create tasks
- View tasks
- View individual tasks
- Update tasks
- Delete tasks
- Task ownership and authorization
- Request validation
- PostgreSQL database
- Database migrations
- Automated tests with Pytest

## Tech Stack

- Python
- Flask
- Flask-SQLAlchemy
- SQLAlchemy
- PostgreSQL
- Psycopg
- Flask-Migrate
- Alembic
- Flask-JWT-Extended
- Pytest

## Database

The application uses PostgreSQL as its database.

Database schema changes are managed with Flask-Migrate and Alembic.

```bash
flask db migrate
flask db upgrade
```

## Setup

### Clone the repository

```bash
git clone https://github.com/Casual3547/task-management-api.git
cd Task-Management-Api
```

### Create a virtual environment

```bash
python -m venv .venv
```

### Activate the virtual environment

```bash
source .venv/bin/activate
```

### Install dependencies

```bash
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file in the project root:

```env
DATABASE_URL=postgresql+psycopg://username@localhost:5432/database_name
JWT_SECRET_KEY=your-secret-key
```

Do not commit the `.env` file to GitHub.

### Run the application

Apply the database migrations:

```bash
flask db upgrade
```

Start the application:

```bash
flask run
```

The API will be available at:

```text
http://127.0.0.1:5000
```

## Running Tests

Run the test suite with:

```bash
python -m pytest
```

The test suite covers authentication, token handling, task creation, validation, CRUD operations, and task ownership authorization.

## API Endpoints

### Authentication

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/auth/register` | Register a new user |
| POST | `/api/auth/login` | Log in |
| POST | `/api/auth/logout` | Log out and revoke the access token |

### Tasks

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/tasks` | Get the current user's tasks |
| POST | `/api/tasks` | Create a task |
| GET | `/api/tasks/<task_id>` | Get a specific task |
| PATCH | `/api/tasks/<task_id>` | Update a task |
| DELETE | `/api/tasks/<task_id>` | Delete a task |

Protected endpoints require a valid JWT access token.

## Project Structure

```text
Task-Management-Api/
├── app.py
├── model.py
├── tests/
├── migrations/
├── .gitignore
├── requirements.txt
└── README.md
```

## Current Status

The core API is complete and working with PostgreSQL.

The project currently includes JWT authentication, task ownership authorization, database migrations, request validation, and automated tests.

## Live APi

https://task-management-api-ftc6.onrender.com/