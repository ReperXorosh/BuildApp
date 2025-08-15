from flask import Blueprint, request, url_for, redirect, render_template, session
from flask_login import login_required, login_user, logout_user

from ..models.users import Users

user = Blueprint('user', __name__)

@user.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login = request.form['login']
        password = request.form['password']

        user = Users.query.filter_by(login=login, password=password).first()

        if user:
            login_user(user)
            return redirect(url_for('main.object_list'))
        else:
            return render_template('main/sign-in.html', error="Неверный логин или пароль")

    return render_template('main/sign-in.html')

@user.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('user.login'))

