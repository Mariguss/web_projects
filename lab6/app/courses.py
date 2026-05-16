from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required
from sqlalchemy.exc import IntegrityError
from sqlalchemy import desc, asc
from models import db, Course, Category, User, Review
from tools import CoursesFilter, ImageSaver

bp = Blueprint('courses', __name__, url_prefix='/courses')

COURSE_PARAMS = [
    'author_id', 'name', 'category_id', 'short_desc', 'full_desc'
]

def params():
    return { p: request.form.get(p) or None for p in COURSE_PARAMS }

def search_params():
    return {
        'name': request.args.get('name'),
        'category_ids': [x for x in request.args.getlist('category_ids') if x],
    }

@bp.route('/')
def index():
    courses = CoursesFilter(**search_params()).perform()
    pagination = db.paginate(courses)
    courses = pagination.items
    categories = db.session.execute(db.select(Category)).scalars()
    return render_template('courses/index.html',
                           courses=courses,
                           categories=categories,
                           pagination=pagination,
                           search_params=search_params())

@bp.route('/new')
@login_required
def new():
    course = Course()
    categories = db.session.execute(db.select(Category)).scalars()
    users = db.session.execute(db.select(User)).scalars()
    return render_template('courses/new.html',
                           categories=categories,
                           users=users,
                           course=course)

@bp.route('/create', methods=['POST'])
@login_required
def create():
    f = request.files.get('background_img')
    img = None
    course = Course()
    try:
        if f and f.filename:
            img = ImageSaver(f).save()

        image_id = img.id if img else None
        course = Course(**params(), background_image_id=image_id)
        db.session.add(course)
        db.session.commit()
    except IntegrityError as err:
        flash(f'Возникла ошибка при записи данных в БД. Проверьте корректность введённых данных. ({err})', 'danger')
        db.session.rollback()
        categories = db.session.execute(db.select(Category)).scalars()
        users = db.session.execute(db.select(User)).scalars()
        return render_template('courses/new.html',
                            categories=categories,
                            users=users,
                            course=course)

    flash(f'Курс {course.name} был успешно добавлен!', 'success')

    return redirect(url_for('courses.index'))

from flask_login import current_user

@bp.route('/<int:course_id>', methods=['GET', 'POST'])
def show(course_id):
    course = db.get_or_404(Course, course_id)
    if request.method == 'POST':
        rating = request.form.get('rating')  # берём значение из select
        text = request.form.get('text')      # берём текст
        
        # Создаём отзыв
        review = Review(
            rating=int(rating),
            text=text,
            course_id=course_id,
            user_id=current_user.id
        )
        
        # Обновляем рейтинг
        course.rating_sum += int(rating)
        course.rating_num += 1
        
        db.session.add(review)
        db.session.commit()
        
        return redirect(url_for('courses.show', course_id=course_id))
    comments = db.session.execute(
        db.select(Review, User)
        .where(Review.course_id == course_id)
        .join(User, Review.user_id == User.id)
        .order_by(Review.created_at.desc())
        .limit(5)
    ).all()  # .all() вернет список кортежей (Review, User)
    
    return render_template('courses/show.html', course=course, comments=comments)

from flask_login import current_user

@bp.route('/<int:course_id>/reviews', methods=['GET', 'POST'])
def reviews(course_id):
    course = db.get_or_404(Course, course_id)
    
    # Обработка POST запроса
    if request.method == 'POST':
        if current_user.is_authenticated:
            rating = request.form.get('rating')
            text = request.form.get('text')
            
            # Проверяем, нет ли уже отзыва
            existing = db.session.execute(
                db.select(Review).where(
                    Review.course_id == course_id,
                    Review.user_id == current_user.id
                )
            ).first()
            
            if not existing:
                review = Review(
                    rating=int(rating),
                    text=text,
                    course_id=course_id,
                    user_id=current_user.id
                )
                
                # Обновляем рейтинг курса
                course.rating_sum += int(rating)
                course.rating_num += 1
                
                db.session.add(review)
                db.session.commit()
                
                flash('Отзыв добавлен!', 'success')
        
        return redirect(url_for('courses.reviews', course_id=course_id))
    
    # GET запрос - показываем страницу
    page = request.args.get('page', 1, type=int)
    per_page = 10
    sort = request.args.get('sort', 'newest')
    
    query = db.select(Review, User).join(User, Review.user_id == User.id).where(Review.course_id == course_id)
    
    if sort == 'newest':
        query = query.order_by(Review.created_at.desc())
    elif sort == 'positive':
        query = query.order_by(Review.rating.desc(), Review.created_at.desc())
    else:
        query = query.order_by(Review.created_at.desc())
    
    paginated_reviews = db.paginate(query, page=page, per_page=per_page, error_out=False)
    
    # Проверяем, оставлял ли пользователь отзыв
    user_review = None
    if current_user.is_authenticated:
        user_review = db.session.execute(
            db.select(Review).where(
                Review.course_id == course_id,
                Review.user_id == current_user.id
            )
        ).scalar_one_or_none()
    
    return render_template('courses/reviews.html', 
        course=course,
        paginated_reviews=paginated_reviews,
        sort=sort,
        user_review=user_review,
    )