from functools import wraps
from flask import redirect, url_for, flash
from flask_login import current_user

def check_rights(func):
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        
        # Если юзер аноним — выгоняем
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        
        # ЛОГИКА ПРАВ:
        # Разрешаем, если это Администратор
        is_admin = current_user.role and current_user.role.name == "Администратор"
        
        if is_admin:
            return func(*args, **kwargs) # Пропускаем дальше
        
        # 4. Если не админ и не владелец — ошибка доступа
        flash("У вас недостаточно прав для доступа к данной странице.", "warning")
        return redirect(url_for("index"))
    return wrapper