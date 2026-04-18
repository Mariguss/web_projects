from flask import Flask, render_template, request, make_response
import re

app = Flask(__name__)

@app.route('/')
def home():
    # Устанавливаем cookie при заходе на главную
    response = make_response(render_template('index.html'))
    response.set_cookie('my_cookie', 'hello_from_flask')
    return response

@app.route('/request-data', methods=['GET', 'POST'])
def request_data():
    auth_data = None
    if request.method == 'POST':
        # Получение параметров формы
        auth_data = {
            'username': request.form.get('username'),
            'password': request.form.get('password')
        }
    
    # Браузер сохраняет cookie и отправляет их серверу
    data = {
        'url': request.url,
        'args': request.args.lists(),
        'headers': request.headers,
        'cookies': request.cookies, # Получение всех cookie
        'auth_data': auth_data
    }
    return render_template('request_data.html', data=data)

@app.route('/phone', methods=['GET', 'POST'])
def phone():
    error = None
    formatted_phone = None
    raw_phone = ''

    if request.method == 'POST':
        raw_phone = request.form.get('phone', '')
        
        # Проверка на недопустимые символы
        if not re.match(r'^[\d\s\(\)\-\.\+]*$', raw_phone):
            error = "Недопустимый ввод. В номере телефона встречаются недопустимые символы."
        else:
            # Извлечение только цифр
            digits = re.sub(r'\D', '', raw_phone)
            
            # Проверка длины по условиям
            is_valid_length = False
            if raw_phone.strip().startswith('+7') or raw_phone.strip().startswith('8'):
                if len(digits) == 11:
                    is_valid_length = True
            elif len(digits) == 10:
                is_valid_length = True

            if not is_valid_length:
                error = "Недопустимый ввод. Неверное количество цифр."
            else:
                # Преобразование к формату 8-*-*--
                core_digits = digits[-10:]
                formatted_phone = f"8-{core_digits[0:3]}-{core_digits[3:6]}-{core_digits[6:8]}-{core_digits[8:10]}"

    return render_template('phone.html', raw_phone=raw_phone, error=error, formatted_phone=formatted_phone)

if __name__ == '__main__':
    app.run(debug=True, port=5001)