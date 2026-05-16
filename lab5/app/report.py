from core import db
from models import VisitLogs, User
from auth import check_rights

from flask import Blueprint, render_template, request, flash, send_file
from flask_login import login_required, current_user
from sqlalchemy import func

report_bp = Blueprint('report', __name__, url_prefix='/report', template_folder='templates')


@report_bp.route("/")
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    query = db.select(VisitLogs).order_by(VisitLogs.created_at.desc())
    
    if current_user.role is None or current_user.role.name != "Администратор":
        query = query.where(VisitLogs.user_id == current_user.id)
    
    pagination = db.paginate(query, page=page, per_page=per_page, error_out=False)
    
    return render_template("report/index.html", pagination=pagination)

@report_bp.route("/pages")
@login_required
@check_rights
def pages():
    query = db.session.execute(db.select(
        VisitLogs.path, 
        func.count(VisitLogs.id).label('count')
        ).group_by("path").order_by(func.count(VisitLogs.id).desc())).all()

    return render_template("report/pages.html", query=query)

from models import User

@report_bp.route("/users")
@login_required
@check_rights
def users():

    # concat_ws склеит Фамилию и Имя, даже если Отчество — None
    fio_expr = func.concat_ws(' ', User.last_name, User.first_name, User.middle_name)
    display_name = func.coalesce(fio_expr, 'Неавторизованный пользователь').label('fio')

    # Формируем запрос
    stmt = db.select(
        display_name,
        func.count(VisitLogs.id).label('count')
    ).outerjoin(User, VisitLogs.user_id == User.id)\
     .group_by(User.id, 'fio')\
     .order_by(func.count(VisitLogs.id).desc())

    query = db.session.execute(stmt).all()
    
    return render_template("report/users.html", query=query)

 
import io
import csv

@report_bp.route("/export")
@login_required
@check_rights
def export_pages():
    stats = db.session.execute(
        db.select(VisitLogs.path, func.count(VisitLogs.id))
        .group_by(VisitLogs.path).order_by(func.count(VisitLogs.id).desc())
    ).all()
    
    # Формируем CSV в памяти
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['№', 'Страница', 'Количество посещений'])
    for i, row in enumerate(stats, 1):
        writer.writerow([i, row[0], row[1]])
    
    mem = io.BytesIO()
    mem.write(output.getvalue().encode('utf-8'))
    mem.seek(0)
    return send_file(mem, mimetype='text/csv', as_attachment=True, download_name='pages_report.csv')