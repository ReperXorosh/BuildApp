from flask import Blueprint, render_template, session, redirect, url_for, request
from flask_login import login_required

main = Blueprint('main', __name__)

@main.route('/sign-in')
@main.route('/')
def sign_in():
    return render_template('main/sign-in.html')

from ..models.objects import Objects
from ..models.columns import Columns
from ..models.trenches import Trenches
from ..models.reports import Reports


@main.route('/object-list')
@login_required
def object_list():
    objects = Objects.query.all()
    selected_id = request.args.get('objectid', type=int)
    panel = request.args.get('panel', default='menu', type=str) # menu | columns | trenches | reports
    # if not selected_id and objects:
    #     selected_id = objects[0].objectid

    columns = []
    trenches = []
    reports = []


    if selected_id and panel == 'columns':
        columns = Columns.query.filter_by(objectid=selected_id).all()
        trenches = Trenches.query.filter_by(objectid=selected_id).all()
    elif selected_id and panel == 'trenches':
        trenches = Trenches.query.filter_by(objectid=selected_id).all()
    elif selected_id and panel == 'reports':
        reports = Reports.query.filter_by(objectid=selected_id).all()

    return render_template('main/object-list.html',
                           objects=objects, selected_id=selected_id,
                           columns=columns, panel=panel,
                           trenches=trenches, reports=reports)

@main.route('/calendar')
@login_required
def calendar():
    return render_template('main/calendar.html')

@main.route('/others')
@login_required
def others():
    return render_template('main/others.html')

@main.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    # if request.method == 'POST':
    #
    #     current_user.firstname = request.form.get('firstname') or current_user.firstname
    #     current_user.secondname = request.form.get('secondname') or current_user.secondname
    #     current_user.thirdname = request.form.get('thirdname') or current_user.thirdname
    #     current_user.phonenumber = request.form.get('phonenumber') or current_user.phonenumber
    #     current_user.role = request.form.get('role') or current_user.role
    #
    #
    #     file = request.files.get('avatar')
    #     if file and file.filename and allowed_file(file.filename):
    #         upload_dir = current_app.config['UPLOAD_FOLDER']
    #         os.makedirs(upload_dir, exist_ok=True)
    #
    #         ext = '.' + file.filename.rsplit('.', 1)[1].lower()
    #         filename = secure_filename(f"{current_user.userid}_{uuid4().hex}{ext}")
    #         fullpath = os.path.join(upload_dir, filename)
    #         file.save(fullpath)
    #
    #
    #         if current_user.avatar:
    #             old = os.path.join(upload_dir, current_user.avatar)
    #             try:
    #                 if os.path.exists(old):
    #                     os.remove(old)
    #             except Exception:
    #                 pass
    #
    #         current_user.avatar = filename
    #
    #     db.session.commit()
    #     flash('Профиль обновлён', 'success')
    #     return redirect(url_for('main.profile'))
    return render_template('main/profile.html')

# @main.route('/layout')
# def layout():
#     return render_template('main/layout.html')