from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import re
from models import Base, User, Role

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_12345'
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project.db"

db = SQLAlchemy(model_class=Base)
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

with app.app_context():
    db.create_all()
    
    # Создаем роль администратора, если её нет
    admin_role = db.session.execute(db.select(Role).where(Role.name == "Администратор")).scalar()
    if not admin_role:
        admin_role = Role(name="Администратор", description="Суперпользователь")
        db.session.add(admin_role)
        db.session.commit() # Сохраняем, чтобы получить id роли

    # Создаем первого пользователя, если таблица юзеров пуста
    if not db.session.execute(db.select(User)).first():
        admin_user = User(
            login="admin",
            password_hash=generate_password_hash("Admin123!"), # Пароль проходит вашу сложную валидацию
            first_name="Система",
            last_name="Администратор",
            role_id=admin_role.id
        )
        db.session.add(admin_user)
        db.session.commit()
        print("База инициализирована. Логин: admin | Пароль: Admin123!")

# --- ВАЛИДАЦИЯ ---
def validate_password(pwd):
    if len(pwd) < 8 or len(pwd) > 128: return "Длина от 8 до 128 символов."
    if ' ' in pwd: return "Без пробелов."
    if not re.search(r'[A-ZА-ЯЁ]', pwd): return "Минимум одна заглавная буква."
    if not re.search(r'[a-zа-яё]', pwd): return "Минимум одна строчная буква."
    if not re.search(r'\d', pwd): return "Минимум одна цифра."
    allowed = set("~!_?@#$%^&*()-+[]{}></\\|\"',.:;")
    for c in pwd:
        if not c.isalnum() and c not in allowed: return f"Недопустимый символ: {c}"
    return None

def validate_user_data(data, is_update=False):
    errors = {}
    if not data.get("first_name"): errors["first_name"] = "Поле не может быть пустым."
    if not data.get("last_name"): errors["last_name"] = "Поле не может быть пустым."
    
    if not is_update:
        login = data.get("login", "")
        if len(login) < 5 or not re.match(r'^[A-Za-z0-9]+$', login):
            errors["login"] = "Только латинские буквы и цифры, мин. 5 символов."
        
        pwd_err = validate_password(data.get("password", ""))
        if pwd_err: errors["password"] = pwd_err
    return errors

# --- МАРШРУТЫ ---
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        login_val = request.form.get("login")
        password_val = request.form.get("password")
        print(f"Попытка входа: {login_val}") # Увидишь в терминале
        
        user = db.session.execute(db.select(User).where(User.login == login_val)).scalar()
        
        if user:
            print(f"Пользователь найден. Хэш в базе: {user.password_hash}")
            if check_password_hash(user.password_hash, password_val):
                login_user(user)
                return redirect(url_for("index"))
            else:
                print("Пароль не подошел")
        else:
            print("Пользователь не найден")
            
        flash("Неверный логин или пароль", "danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    logout_user() 
    flash("Вы вышли", "info")
    return redirect(url_for("index"))

@app.route("/")
def index():
    users = db.session.execute(db.select(User).order_by(User.id)).scalars().all()
    return render_template("index.html", users=users)

@app.route("/user/<int:id>")
def user_detail(id):
    user = db.get_or_404(User, id)
    return render_template("user/detail.html", user=user)

@app.route("/user/create", methods=["GET", "POST"])
@login_required
def user_create():
    roles = db.session.execute(db.select(Role)).scalars().all()
    errors = {}
    if request.method == "POST":
        errors = validate_user_data(request.form, is_update=False)
        if not errors:
            existing = db.session.execute(db.select(User).where(User.login == request.form["login"])).scalar()
            if existing:
                errors["login"] = "Пользователь с таким логином уже существует"
            else:
                user = User(
                    login=request.form["login"],
                    password_hash=generate_password_hash(request.form["password"]),
                    first_name=request.form["first_name"],
                    last_name=request.form["last_name"],
                    middle_name=request.form.get("middle_name"),
                    role_id=request.form.get("role_id", type=int) or None
                )
                db.session.add(user)
                try:
                    db.session.commit()
                    flash("Пользователь успешно создан", "success")
                    return redirect(url_for("index"))
                except Exception as e:
                    db.session.rollback()
                    flash(f"Ошибка БД: {str(e)}", "danger")
        if errors:
            flash("Исправьте ошибки в форме", "danger")
            
    return render_template("user/create.html", roles=roles, errors=errors, form_data=request.form)

@app.route("/user/<int:id>/update", methods=["GET", "POST"])
@login_required
def user_update(id):
    user = db.get_or_404(User, id)
    roles = db.session.execute(db.select(Role)).scalars().all()
    errors = {}
    
    if request.method == "POST":
        errors = validate_user_data(request.form, is_update=True)
        if not errors:
            user.first_name = request.form["first_name"]
            user.last_name = request.form["last_name"]
            user.middle_name = request.form.get("middle_name")
            user.role_id = request.form.get("role_id", type=int) or None
            try:
                db.session.commit()
                flash("Данные успешно обновлены", "success")
                return redirect(url_for("index"))
            except Exception as e:
                db.session.rollback()
                flash(f"Ошибка БД: {str(e)}", "danger")
        if errors:
             flash("Исправьте ошибки в форме", "danger")
             
    form_data = {
        "first_name": user.first_name, "last_name": user.last_name, 
        "middle_name": user.middle_name, "role_id": user.role_id
    } if request.method == "GET" else request.form
    
    return render_template("user/update.html", user=user, roles=roles, errors=errors, form_data=form_data)

@app.route("/user/<int:id>/delete", methods=["POST"])
@login_required
def user_delete(id):
    user = db.get_or_404(User, id)
    try:
        db.session.delete(user)
        db.session.commit()
        flash("Пользователь удален", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Ошибка удаления: {str(e)}", "danger")
    return redirect(url_for("index"))

@app.route("/password", methods=["GET", "POST"])
@login_required
def change_password():
    errors = {}
    if request.method == "POST":
        old_pwd = request.form.get("old_password")
        new_pwd = request.form.get("new_password")
        confirm_pwd = request.form.get("confirm_password")
        
        if not check_password_hash(current_user.password_hash, old_pwd):
            errors["old_password"] = "Неверный текущий пароль"
        
        pwd_err = validate_password(new_pwd)
        if pwd_err: errors["new_password"] = pwd_err
        
        if new_pwd != confirm_pwd:
            errors["confirm_password"] = "Пароли не совпадают"
            
        if not errors:
            current_user.password_hash = generate_password_hash(new_pwd)
            db.session.commit()
            flash("Пароль успешно изменен", "success")
            return redirect(url_for("index"))
            
    return render_template("password.html", errors=errors)

if __name__ == "__main__":
    app.run(debug=True)