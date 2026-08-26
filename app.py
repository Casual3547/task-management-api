from  datetime import datetime
from flask import Flask,jsonify,request,Blueprint
from sqlalchemy.exc import IntegrityError
from model import db,User,Task,RevokedToken
from flask_jwt_extended import JWTManager,create_access_token,create_refresh_token,jwt_required,get_jwt_identity,get_jwt
from datetime import timedelta
from email_validator import validate_email,EmailNotValidError
from flask_migrate import Migrate
from dotenv import load_dotenv
import os



load_dotenv()
jwt = JWTManager()
api = Blueprint('api',__name__)
migrate = Migrate()



def create_app(config=None):
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
    app.config["JWT_SECRET_KEY"] = os.getenv('JWT_SECRET_KEY',"development-secret-change-this")
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(minutes=15)
    app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=2)
    if config:
        app.config.from_mapping(config)
    jwt.init_app(app)
    db.init_app(app)
    migrate.init_app(app,db)
    app.register_blueprint(api)

    return app


@api.route('/')
def home():
    return 'WELCOME'

@api.route('/api/auth/register',methods=['POST'])
def register():
    try:
        username = request.json.get('username',None)
        if not username:
            return jsonify({"error": "username required"}), 400
        username = username.title()
        if len(username) < 5:
            return jsonify({"error":"username must be 5 characters long"}),400
        email_info = request.json.get('email')
        if not email_info:
            return jsonify({"error": "email required"}),400
        email = validate_email(email_info,check_deliverability=False).normalized
        password = request.json.get('password',None)
        if not password:
            return jsonify({"error": "password required"}), 400
        if len(password) < 8:
            return jsonify({"error":"password must be between 8 characters long"}),400
        user = User(
            username=username,
            email=email
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))
        return jsonify({"success": "User successfully created",
                        "access_token": access_token,
                        "refresh_token": refresh_token}), 201
    except IntegrityError:
        return jsonify({"error": "sorry a user with this email exist in our database"}), 400
    except EmailNotValidError:
        return jsonify({"error": "Invalid email address"}), 400

@api.route('/api/auth/login',methods=['POST'])
def login():
    email = request.json.get('email',None)
    if not email:
        return jsonify({"error":"email required"})
    existing_user = db.session.execute(db.select(User).where(User.email == email)).scalar()
    if existing_user:
        password = request.json.get('password', None)
        if password:
            if existing_user.check_password(password):
                access_token = create_access_token(identity=str(existing_user.id))
                refresh_token = create_refresh_token(identity=str(existing_user.id))
                return jsonify({"success":f"welcome {existing_user.username}",
                                "access_token":access_token,
                                "refresh_token":refresh_token})
            return jsonify({"error": "Invalid email or password"}), 401
        return jsonify({"error": "password required"}),400
    return jsonify({"error": "Invalid email or password"}),401

@api.route('/api/tasks',methods=['POST'])
@jwt_required()
def create_tasks():
    current_user = get_jwt_identity()
    title = request.json.get('title',None)
    if not title:
        return jsonify({"error":"Enter task title"}),400
    if len(title) < 4:
        return jsonify({"error": "task must be 4 characters long"}),400
    description = request.json.get('description',None)
    if not description:
        return jsonify({"error": "enter a task description"}),400
    list_status = ["Pending", "In Progress", "Completed"]
    status = request.json.get('status',None)
    if not status:
        return jsonify({"error": "enter task status"}),400
    if status not in list_status:
        return jsonify({"error": f"status can either be one of these {list_status}"}),400
    list_priority = ["Low", "Medium", "High"]
    priority = request.json.get('priority',None)
    if not priority:
        return jsonify({"error": "enter task priority"}),400
    if priority not in list_priority:
        return jsonify({"error": f"priority can either be one of these {list_priority}"}),400
    if 'due_date' not in request.json:
        due_date = None
    else:
        due_date = request.json.get('due_date', None)
        if due_date is not None:
            try:
                datetime_obj = datetime.strptime(due_date, "%Y-%m-%d")
                due_date = datetime_obj.date()
            except ValueError:
                return jsonify({"error": "enter a valid date format e.g 2020-08-25"}), 400
    task = Task(
    title = title,
    description = description,
    status = status,
    priority = priority,
    due_date = due_date,
    user_id = current_user
    )
    db.session.add(task)
    db.session.commit()
    return jsonify(success="Task added successfully")

@api.route('/api/tasks',methods=['GET'])
@jwt_required()
def user_tasks():
    current_user = get_jwt_identity()
    results = db.session.execute(db.select(Task).order_by(Task.id).where(int(current_user) == Task.user_id)).scalars().all()
    if results:
        return jsonify(tasks=[task.to_dict() for task in results])
    return jsonify({"msg":"no task available for this user"})

@api.route('/api/tasks/<int:task_id>',methods=['GET'])
@jwt_required()
def user_task(task_id):
    current_user = get_jwt_identity()
    results = db.session.execute(db.select(Task).order_by(Task.id).where(int(current_user)== Task.user_id,Task.id == task_id)).scalar()
    if results:
        return jsonify(task=results.to_dict())
    return jsonify({"msg":"task not found"}),404

@api.route('/api/tasks/<int:task_id>',methods=['PATCH'])
@jwt_required()
def update_task(task_id):
    current_user = get_jwt_identity()
    result = db.session.execute(db.select(Task).order_by(Task.id).where(int(current_user) == Task.user_id,Task.id == task_id)).scalar()
    if result:
        result.title = request.json.get('title',result.title)
        result.description = request.json.get('description',result.description)
        result.status = request.json.get('status',result.status)
        result.priority = request.json.get('priority',result.priority)
        if "due_date" in request.json:
            due_date = request.json.get('due_date')
            if due_date is None:
                result.due_date = None
            else:
                try:
                    due_date = datetime.strptime(due_date,"%Y-%m-%d")
                except ValueError:
                    return jsonify({"error": "accepted date format is e.g 2020-09-23"}), 400
                result.due_date = due_date
        db.session.commit()
        return jsonify({"task": "task updated successfully"})
    return jsonify({"msg": "task not found"}), 404


@api.route('/api/tasks/<int:task_id>',methods=['DELETE'])
@jwt_required()
def delete(task_id):
    current_user = get_jwt_identity()
    result = db.session.execute(db.select(Task).order_by(Task.id).where(int(current_user) == Task.user_id, Task.id == task_id)).scalar()
    if result:
        db.session.delete(result)
        db.session.commit()
        return jsonify({"success":"deleted successfully"}),200
    return jsonify({"msg": "task not found"}),404

@api.route('/api/auth/refresh',methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    current_user = get_jwt_identity()
    access_token = create_access_token(identity=current_user)
    return jsonify({"access_token":access_token})

@api.route('/api/auth/logout',methods=['POST'])
@jwt_required()
def logout():
    claims = get_jwt()
    revoked_token = RevokedToken(
        jti = claims['jti'],
        token_type = claims['type']
    )
    db.session.add(revoked_token)
    db.session.commit()
    return jsonify({"success":"logged_out successfully"})

@jwt.token_in_blocklist_loader
def check_if_token_is_revoked(jwt_header,jwt_payload):
    jti = jwt_payload['jti']
    revoked_token = db.session.execute(db.select(RevokedToken).where(jti == RevokedToken.jti)).scalar()
    return revoked_token is not None

@api.errorhandler(404)
def handle_404(e):
    return {
        "error": "resource not found"
    },404

@api.errorhandler(405)
def handle_405(e):
    return {
        "error": "method not allowed"
    },405

@jwt.unauthorized_loader
def token_missing(e):
    return jsonify({"error":"Authorization token required"}),401

@jwt.invalid_token_loader
def invalid_token(e):
    return jsonify({"error":"Invalid token"}),401


@jwt.expired_token_loader
def expired_token(jwt_header,jwt_payload):
    return jsonify({"error":f"{jwt_payload['type']} token expired"}),401

@jwt.revoked_token_loader
def token_revoked(jwt_header, jwt_payload):
        return jsonify({"error":f"{jwt_payload['type']} token has been revoked"}),401

if __name__ == "__main__":
   app = create_app()
   app.run(debug=True)