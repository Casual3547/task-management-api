import pytest

from app import create_app,db,User,Task


@pytest.fixture
def app():
    test_app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///test.db",
            "JWT_SECRET_KEY": "sswniwiwibiwibiwi"
        }
    )
    return test_app

@pytest.fixture
def client(app):
   with app.test_client() as client:
       yield client

@pytest.fixture
def database(app):
    with app.app_context():
        db.create_all()
    yield app

    with app.app_context():
        db.drop_all()



@pytest.fixture
def auth_headers(client, database):
    response = client.post('/api/auth/register', json={
        "username": "emmanuel",
        "email": "admin@email.com",
        "password": "123456789"
    })
    assert response.status_code == 201
    response = client.post('/api/auth/login', json={
        "username": "emmanuel",
        "email": "admin@email.com",
        "password": "123456789"
    })
    assert response.status_code == 200
    access_token = response.json['access_token']
    return {'Authorization': f'Bearer {access_token}'}

@pytest.fixture
def create_user(client,database):
    def _create_user(username,email,password):
        response = client.post('/api/auth/register', json={
            "username": username,
            "email": email,
            "password": password
        })
        assert response.status_code == 201
        user = db.session.execute(db.select(User).where(User.email == email)).scalar()
        assert user is not None
        return user
    return _create_user


@pytest.fixture
def login_user(client):
    def _login_user(email, password):
        response = client.post('/api/auth/login',json={
            "email": email,
            "password": password
        })
        assert response.status_code == 200
        access_token = response.json['access_token']
        return access_token

    return _login_user


def test_create_user(create_user,login_user):
    user = create_user(
        "emmanuel",
        "admin@email.com",
        "123456789"
    )

    assert user.username == "Emmanuel"
    assert user.email == "admin@email.com"
    authenticated_user = login_user(
         "admin@email.com",
        "123456789"
    )
    assert authenticated_user


def test_home_page(client):
    response = client.get('/')
    assert response.status_code == 200
    assert response.data == b'WELCOME'

def test_register_user(client,database):
    response = client.post('/api/auth/register',json={
        "username": "emmanuel",
        "email": "admin@email.com",
        "password": "123456789"
    })
    assert response.status_code == 201
    with database.app_context():
        user = db.session.execute(db.select(User).where(User.username == "Emmanuel")).scalar()
        assert user is not None

def test_register_duplicate_email(client,database):
    response = client.post('/api/auth/register', json={
        "username": "emmanuel",
        "email": "admin@email.com",
        "password": "123456789"
    })
    assert response.status_code == 201

    response = client.post('/api/auth/register', json={
        "username": "emmanuel",
        "email": "admin@email.com",
        "password": "123456789"
    })
    assert response.status_code == 400


def test_register_invalid_email(client, database):
    response = client.post('/api/auth/register',json={
        "username": "casual",
        "email": "ade",
        "password": "123456789"
    })
    assert response.status_code == 400
    assert response.json == {'error': 'Invalid email address'}
def test_login_success(client, database):
    response = client.post('/api/auth/register', json={
        "username": "emmanuel",
        "email": "admin@email.com",
        "password": "123456789"
    })
    assert response.status_code == 201
    response = client.post('/api/auth/login', json={
        "email": "admin@email.com",
        "password": "123456789"
    })
    assert response.status_code == 200
    assert "access_token" in response.json
    assert "refresh_token" in response.json

def test_login_wrong_password(client, database):
    response = client.post('/api/auth/register', json={
        "username": "emmanuel",
        "email": "admin@email.com",
        "password": "123456789"
    })
    assert response.status_code == 201
    response = client.post('/api/auth/login', json={
        "email": "admin@email.com",
        "password": "mjssnjajsjsh"
    })
    assert response.status_code == 401
    assert response.json == {"error": "Invalid email or password"}

def test_tasks_without_token(client):
    response = client.get('/api/tasks')
    assert response.status_code == 401
    assert response.json == {"error": "Authorization token required"}


def test_tasks_with_token(client,auth_headers):
    response = client.get('/api/tasks',headers=auth_headers)
    assert response.status_code == 200

def test_tasks_invalid_token(client):
    response = client.get('/api/tasks', headers={"Authorization": "Bearer this-is-not-a-real-token"})
    assert response.status_code == 401
    assert response.json == {"error":"Invalid token"}

def test_tasks_revoked_token(client,database):
    response = client.post('/api/auth/register', json={
        "username": "emmanuel",
        "email": "admin@email.com",
        "password": "123456789"
    })
    assert response.status_code == 201
    response = client.post('/api/auth/login', json={
        "email": "admin@email.com",
        "password": "123456789"
    })
    assert response.status_code == 200
    access_token = response.json['access_token']

    response = client.post('/api/auth/logout',headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 200
    assert response.json == {"success":"logged_out successfully"}

    response = client.get('/api/tasks', headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 401
    assert response.json == {"error": "access token has been revoked"}


def test_create_task(client,auth_headers,database):
    user = db.session.execute(db.select(User).where(User.email == "admin@email.com")).scalar()
    assert user is not None
    response = client.post('/api/tasks', headers=auth_headers,
                                       json={
                                           "title": "Project Planning & Task Management API",
                                           "description": "Build a Flask API for creating and managing projects and tasks,"
                                                          " including request validation and data handling.",
                                           "status": "Pending",
                                           "priority": "Low",
                                           "due_date": "2026-09-24",
                                       })
    assert response.status_code == 200
    result = db.session.execute(db.select(Task).where(Task.title == "Project Planning & Task Management API",user.id == Task.user_id )).scalar()
    assert result is not None

def test_create_task_missing_title(client, auth_headers,database):
    response = client.post('/api/tasks', headers=auth_headers,
                           json={
                               "description": "Build a Flask API for creating and managing projects and tasks,"
                                              " including request validation and data handling.",
                               "status": "Pending",
                               "priority": "Low",
                               "due_date": "2026-09-24",
                           })
    assert response.status_code == 400
    assert response.json ==  {"error": "Enter task title"}
def test_create_task_short_title(client,auth_headers, database):

    response = client.post('/api/tasks', headers=auth_headers,
                           json={
                               "title": "Pro",
                               "description": "Build a Flask API for creating and managing projects and tasks,"
                                              " including request validation and data handling.",
                               "status": "Pending",
                               "priority": "Low",
                               "due_date": "2026-09-24",
                           })
    assert response.status_code == 400
    assert response.json =={
    "error": "task must be 4 characters long"
}
def test_create_task_missing_description(client,auth_headers, database):

    response = client.post('/api/tasks', headers=auth_headers,
                           json={
                               "title": "Project Planning & Task Management API",
                               # "description": "Build a Flask API for creating and managing projects and tasks,"
                               #                " including request validation and data handling.",
                               "status": "Pending",
                               "priority": "Low",
                               "due_date": "2026-09-24",
                           })
    assert response.status_code == 400
    assert response.json == {"error": "enter a task description"}


def test_create_task_invalid_status(client,auth_headers,database):

    response = client.post('/api/tasks', headers=auth_headers,
                           json={
                               "title": "Project Planning & Task Management API",
                               "description": "Build a Flask API for creating and managing projects and tasks,"
                                              " including request validation and data handling.",
                               "status": "Unknown",
                               "priority": "Low",
                               "due_date": "2026-09-24",
                           })
    assert response.status_code == 400
    assert response.json == {'error': "status can either be one of these ['Pending', 'In Progress', "
          "'Completed']"}
def test_create_task_invalid_priority(client, auth_headers,database):

    response = client.post('/api/tasks', headers=auth_headers,
                           json={
                               "title": "Project Planning & Task Management API",
                               "description": "Build a Flask API for creating and managing projects and tasks,"
                                              " including request validation and data handling.",
                               "status": "In Progress",
                               "priority": "Unknown",
                               "due_date": "2026-09-24",
                           })
    assert response.status_code == 400
    assert response.json == {
    "error": "priority can either be one of these ['Low', 'Medium', 'High']"
}
def test_create_task_invalid_due_date(client, auth_headers,database):
    response = client.post('/api/tasks', headers=auth_headers,
                           json={
                               "title": "Project Planning & Task Management API",
                               "description": "Build a Flask API for creating and managing projects and tasks,"
                                              " including request validation and data handling.",
                               "status": "In Progress",
                               "priority": "Low",
                               "due_date": "tomorrow",
                           })
    assert response.status_code == 400
    assert response.json == {'error': 'enter a valid date format e.g 2020-08-25'}


def test_get_task(client, auth_headers, database):
    user = db.session.execute(db.select(User).where(User.email == "admin@email.com")).scalar()
    response = client.post('/api/tasks', headers=auth_headers,
                           json={
                               "title": "Project Planning & Task Management API",
                               "description": "Build a Flask API for creating and managing projects and tasks,"
                                              " including request validation and data handling.",
                               "status": "In Progress",
                               "priority": "Low",
                               "due_date": "2026-10-12",
                           })
    assert response.status_code == 200
    assert response.json == {"success":"Task added successfully"}
    task = db.session.execute(db.select(Task).where(user.id == Task.user_id)).scalar()
    response = client.get(f'/api/tasks/{task.id}', headers=auth_headers)
    assert response.status_code == 200
    assert response.json["task"]["title"] == task.title
    assert response.json["task"]["description"] == task.description
    assert response.json["task"]["status"] == task.status
    assert response.json["task"]["priority"] == task.priority
    assert response.json["task"]["id"] == task.id
    assert response.json["task"]["user_id"] == task.user_id

def test_get_nonexistent_task(client, auth_headers):
    response = client.get('/api/tasks/999', headers=auth_headers)
    assert response.status_code == 404
    assert response.json == {'msg': 'task not found'}


def test_user_cannot_access_another_users_task(client,create_user,login_user, database):
    user = create_user("emmanuel","admin@email.com","123456789")
    user_access_token = login_user("admin@email.com","123456789")
    response = client.post('/api/tasks',headers={"Authorization": f"Bearer {user_access_token}"},json={
                               "title": "Project Planning & Task Management API",
                               "description": "Build a Flask API for creating and managing projects and tasks,"
                                              " including request validation and data handling.",
                               "status": "In Progress",
                               "priority": "Low",
                               "due_date": "2026-10-12",
                           })
    assert response.status_code == 200
    task = db.session.execute(db.select(Task).where(user.id == Task.user_id )).scalar()

    create_user("casual", "casual@email.com", "111111111")
    user2_access_token = login_user("casual@email.com", "111111111")
    response = client.get(f'/api/tasks/{task.id}', headers={"Authorization": f'Bearer {user2_access_token}'})
    assert response.status_code == 404
    assert response.json == {"msg":"task not found"}

def test_user_cannot_update_another_users_task(client,create_user,login_user, database):
    user = create_user("emmanuel", "admin@email.com", "123456789")
    user_access_token = login_user("admin@email.com", "123456789")

    response = client.post('/api/tasks', headers={"Authorization": f"Bearer {user_access_token}"}, json={
        "title": "Project Planning & Task Management API",
        "description": "Build a Flask API for creating and managing projects and tasks,"
                       " including request validation and data handling.",
        "status": "In Progress",
        "priority": "Low",
        "due_date": "2026-10-12",
    })
    assert response.status_code == 200
    task = db.session.execute(db.select(Task).where(user.id == Task.user_id)).scalar()
    create_user("casual", "casual@email.com", "111111111")
    user2_access_token = login_user("casual@email.com", "111111111")
    response = client.patch(f'/api/tasks/{task.id}', headers={"Authorization": f'Bearer {user2_access_token}'},json={
        "title": "Pytest Api Testing"
    })
    assert response.status_code == 404
    assert response.json == {"msg": "task not found"}
    task = db.session.execute(db.select(Task).where(user.id == Task.user_id,Task.id == task.id)).scalar()
    assert task.title == "Project Planning & Task Management API"

def test_user_cannot_delete_another_users_task(client,create_user,login_user, database):
    user = create_user("emmanuel", "admin@email.com", "123456789")
    user_access_token = login_user("admin@email.com", "123456789")

    response = client.post('/api/tasks', headers={"Authorization": f"Bearer {user_access_token}"}, json={
        "title": "Project Planning & Task Management API",
        "description": "Build a Flask API for creating and managing projects and tasks,"
                       " including request validation and data handling.",
        "status": "In Progress",
        "priority": "Low",
        "due_date": "2026-10-12",
    })
    task = db.session.execute(db.select(Task).where(user.id == Task.user_id)).scalar()
    assert response.status_code == 200
    create_user("casual", "casual@email.com", "111111111")
    user2_access_token = login_user("casual@email.com", "111111111")
    response = client.delete(f'/api/tasks/{task.id}', headers={"Authorization": f'Bearer {user2_access_token}'})
    assert response.status_code == 404
    assert response.json == {"msg": "task not found"}
    task = db.session.execute(db.select(Task).where(user.id == Task.user_id, Task.id == task.id)).scalar()
    assert task is not None
def test_delete_task(client, auth_headers, database):
    user = db.session.execute(db.select(User).where(User.email == "admin@email.com")).scalar()
    response = client.post('/api/tasks', headers=auth_headers, json={
        "title": "Project Planning & Task Management API",
        "description": "Build a Flask API for creating and managing projects and tasks,"
                       " including request validation and data handling.",
        "status": "In Progress",
        "priority": "Low",
        "due_date": "2026-10-12",
    })
    assert response.status_code == 200
    task = db.session.execute(db.select(Task).where(user.id == Task.user_id)).scalar()
    response = client.delete(f'/api/tasks/{task.id}', headers=auth_headers)
    assert response.status_code == 200
    assert response.json == {"success":"deleted successfully"}
    task = db.session.execute(db.select(Task).where(user.id == Task.user_id,Task.id == task.id)).scalar()
    assert task is None

def test_update_task(client, auth_headers, database):
    user = db.session.execute(db.select(User).where(User.email == "admin@email.com")).scalar()
    response = client.post('/api/tasks', headers=auth_headers, json={
        "title": "Project Planning & Task Management API",
        "description": "Build a Flask API for creating and managing projects and tasks,"
                       " including request validation and data handling.",
        "status": "In Progress",
        "priority": "Low",
        "due_date": "2026-10-12",
    })
    assert response.status_code == 200
    assert response.json == {"success": "Task added successfully"}
    task = db.session.execute(db.select(Task).where(user.id == Task.user_id)).scalar()
    response = client.patch(f'/api/tasks/{task.id}',headers=auth_headers,json={
        "title": "Pytest api management",
        "priority": "High"
    })
    assert response.status_code == 200
    task = db.session.execute(db.select(Task).where(user.id == Task.user_id,Task.id == task.id)).scalar()
    assert task.title == "Pytest api management"
    assert task.priority == "High"