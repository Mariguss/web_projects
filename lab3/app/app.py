# Разработайте веб-приложение с использованием фреймворка Flask. 
# Приложение должно предоставлять следующий функционал.

# 1) Страница "Счётчик посещений"
# На данной странице пользователю должно отображаться сообщение, 
# содержащее информацию о количестве посещений им данной страницы. 
# Реализуйте этот функционал с помощью глобального объекта session.

# 2) Аутентификация пользователей
# Реализуйте механизм аутентификации пользователей с использованием библиотеки Flask-Login. 
# Добавьте в приложение страницу с формой для ввода логина и пароля. 
# Также на форме должен присутствовать чекбокс "Запомнить меня", 
# реализующий функционал сохранения данных сессии после закрытия браузера. 
# Добавьте в приложение пользователя с логином "user" и паролем "qwerty". 
# После удачной аутентификации пользователь должен быть перенаправлен на главную страницу, 
# где ему должно быть отображено сообщение об успешном входе. 
# В случае некорректного ввода пользователь должен остаться на странице с формой, 
# где ему должно быть отображено сообщение о неверно введённых данных.

# 3) "Секретная страница"
# Добавьте в приложение страницу, к которой имеют доступ только аутентифицированные пользователи. 
# Добавьте в навбар ссылку на данную страницу. 
# Ссылка должна отображаться только для аутентифицированных пользователей. 
# В случае, если неаутентифицированный пользователь попробует получить доступ к данной странице, 
# он должен быть перенаправлен на страницу входа с сообщением о том, что для доступа к запрашиваемой 
# странице необходимо пройти процедуру аутентификации. 
# После прохождения аутентификации пользователь автоматически должен быть перенаправлен на запрашиваемую ранее страницу.

# Добавтьте в навбар ссылки на все страницы приложения.

from flask import Flask, render_template, redirect, request, session, url_for, flash
from flask_session import Session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

app.config["SECRET_KEY"] = "your-secret-key-here-change-in-production"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = 'filesystem'

Session(app)

# Инициализация Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)

login_manager.login_view = 'auth'  # Страница входа
login_manager.login_message = 'Пожалуйста, войдите в систему для доступа к этой странице.'
login_manager.login_message_category = 'warning'

class User(UserMixin):
    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# База данных пользователей (в памяти)
users_db = {
    '1': User('1', 'user', generate_password_hash('qwerty'))
}

@login_manager.user_loader
def load_user(user_id):
    # Возвращаем пользователя по его ID
    return users_db.get(str(user_id))

@app.route('/login', methods=['GET', 'POST'])
def auth():
    # Если пользователь уже вошел, перенаправляем на главную
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        
        # Ищем пользователя по логину
        user = None
        for u in users_db.values():
            if u.username == username:
                user = u
                break
        
        # Проверяем логин и пароль
        if user and user.check_password(password):
            # Вход пользователя
            login_user(user, remember=remember)
            flash(f'Добро пожаловать, {username}! Вы успешно вошли в систему.', 'success')
            
            # Перенаправление на запрашиваемую страницу
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('home'))
        else:
            flash('Неверный логин или пароль. Попробуйте снова.', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы.', 'info')
    return redirect(url_for('home'))

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/count')
def count():
    if 'visits' in session:
        session['visits'] += 1
    else:
        session['visits'] = 1
    return render_template('count.html', count_visits = session['visits'])

@app.route('/secret')
@login_required 
def secret():
    return render_template('secret.html')

if __name__ == '__main__':
    app.run(debug=True)