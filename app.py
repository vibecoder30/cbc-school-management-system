#!/usr/bin/env python3
"""
CBC Integrated School Management System
Multi-tenant SaaS for up to 20+ schools.
Instant registration → school admin credentials.
Aligned to Kenya CBC (2-6-3-3-3) with competency-based learning & assessments.
"""

import os
import secrets
from datetime import datetime, date
from functools import wraps

from flask import (
    Flask, render_template, request, redirect, url_for, flash,
    session, jsonify, abort
)
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin, login_user, logout_user,
    login_required, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(32)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cbc_sms.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(os.path.dirname(__file__), 'instance'), exist_ok=True)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class PlatformAdmin(UserMixin, db.Model):
    __tablename__ = 'platform_admins'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def get_id(self):
        return f"pa_{self.id}"


class School(db.Model):
    __tablename__ = 'schools'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    registration_number = db.Column(db.String(50))
    county = db.Column(db.String(80))
    sub_county = db.Column(db.String(80))
    address = db.Column(db.Text)
    phone = db.Column(db.String(30))
    email = db.Column(db.String(120))
    logo_url = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    max_students = db.Column(db.Integer, default=2000)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    users = db.relationship('User', backref='school', lazy='dynamic')
    grades = db.relationship('GradeLevel', backref='school', lazy='dynamic')
    subjects = db.relationship('Subject', backref='school', lazy='dynamic')
    classes = db.relationship('SchoolClass', backref='school', lazy='dynamic')
    students = db.relationship('Student', backref='school', lazy='dynamic')
    teachers = db.relationship('Teacher', backref='school', lazy='dynamic')
    learning_modules = db.relationship('LearningModule', backref='school', lazy='dynamic')
    exams = db.relationship('Exam', backref='school', lazy='dynamic')


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=True)
    username = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(30), nullable=False)
    first_name = db.Column(db.String(80))
    last_name = db.Column(db.String(80))
    phone = db.Column(db.String(30))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    __table_args__ = (db.UniqueConstraint('school_id', 'username', name='uq_school_username'),)

    def get_id(self):
        return f"u_{self.id}"

    @property
    def full_name(self):
        return f"{self.first_name or ''} {self.last_name or ''}".strip() or self.username


class GradeLevel(db.Model):
    __tablename__ = 'grade_levels'
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    name = db.Column(db.String(20), nullable=False)
    code = db.Column(db.String(10), nullable=False)
    stage = db.Column(db.String(40))
    order_index = db.Column(db.Integer, default=0)
    classes = db.relationship('SchoolClass', backref='grade_level', lazy='dynamic')


class Subject(db.Model):
    __tablename__ = 'subjects'
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    code = db.Column(db.String(20))
    stage = db.Column(db.String(40))
    description = db.Column(db.Text)
    is_core = db.Column(db.Boolean, default=True)


class SchoolClass(db.Model):
    __tablename__ = 'school_classes'
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    grade_level_id = db.Column(db.Integer, db.ForeignKey('grade_levels.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    academic_year = db.Column(db.String(20), default='2026')
    class_teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'))
    students = db.relationship('Student', backref='school_class', lazy='dynamic')


class Teacher(db.Model):
    __tablename__ = 'teachers'
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    tsc_number = db.Column(db.String(30))
    specialization = db.Column(db.String(100))
    user = db.relationship('User', backref=db.backref('teacher_profile', uselist=False))


class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    admission_number = db.Column(db.String(40), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('school_classes.id'))
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(10))
    parent_name = db.Column(db.String(120))
    parent_phone = db.Column(db.String(30))
    user = db.relationship('User', backref=db.backref('student_profile', uselist=False))
    __table_args__ = (db.UniqueConstraint('school_id', 'admission_number', name='uq_school_adm'),)


class LearningModule(db.Model):
    __tablename__ = 'learning_modules'
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    grade_level_id = db.Column(db.Integer, db.ForeignKey('grade_levels.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    strand = db.Column(db.String(120))
    sub_strand = db.Column(db.String(120))
    content = db.Column(db.Text)
    learning_outcomes = db.Column(db.Text)
    resources = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_published = db.Column(db.Boolean, default=True)
    subject = db.relationship('Subject')
    grade_level = db.relationship('GradeLevel')


class Exam(db.Model):
    __tablename__ = 'exams'
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    grade_level_id = db.Column(db.Integer, db.ForeignKey('grade_levels.id'), nullable=False)
    exam_type = db.Column(db.String(40), default='formative')
    total_marks = db.Column(db.Integer, default=100)
    duration_minutes = db.Column(db.Integer, default=60)
    instructions = db.Column(db.Text)
    is_published = db.Column(db.Boolean, default=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    due_date = db.Column(db.DateTime)
    subject = db.relationship('Subject')
    grade_level = db.relationship('GradeLevel')
    questions = db.relationship('ExamQuestion', backref='exam', cascade='all, delete-orphan', lazy='dynamic')
    attempts = db.relationship('ExamAttempt', backref='exam', lazy='dynamic')


class ExamQuestion(db.Model):
    __tablename__ = 'exam_questions'
    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey('exams.id'), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.String(30), default='mcq')
    options = db.Column(db.Text)
    correct_answer = db.Column(db.Text)
    marks = db.Column(db.Integer, default=1)
    competency_focus = db.Column(db.String(120))
    order_index = db.Column(db.Integer, default=0)


class ExamAttempt(db.Model):
    __tablename__ = 'exam_attempts'
    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey('exams.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    submitted_at = db.Column(db.DateTime)
    score = db.Column(db.Float)
    max_score = db.Column(db.Float)
    achievement_level = db.Column(db.String(10))
    feedback = db.Column(db.Text)
    answers = db.Column(db.Text)
    student = db.relationship('Student')


class AssessmentRecord(db.Model):
    __tablename__ = 'assessment_records'
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    grade_level_id = db.Column(db.Integer, db.ForeignKey('grade_levels.id'), nullable=False)
    term = db.Column(db.String(20))
    academic_year = db.Column(db.String(20), default='2026')
    achievement_level = db.Column(db.String(10))
    score = db.Column(db.Float)
    comments = db.Column(db.Text)
    recorded_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)
    student = db.relationship('Student')
    subject = db.relationship('Subject')


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

@login_manager.user_loader
def load_user(user_id):
    if user_id.startswith('pa_'):
        return PlatformAdmin.query.get(int(user_id[3:]))
    if user_id.startswith('u_'):
        return User.query.get(int(user_id[2:]))
    return None


def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('login'))
            if isinstance(current_user, PlatformAdmin):
                if 'platform_admin' in roles:
                    return f(*args, **kwargs)
                abort(403)
            if current_user.role not in roles:
                abort(403)
            return f(*args, **kwargs)
        return wrapped
    return decorator


def school_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated or isinstance(current_user, PlatformAdmin):
            abort(403)
        if not current_user.school_id:
            abort(403)
        return f(*args, **kwargs)
    return wrapped


# ---------------------------------------------------------------------------
# CBC seed data helpers
# ---------------------------------------------------------------------------

CBC_GRADES = [
    ("PP1", "PP1", "Pre-Primary", 1),
    ("PP2", "PP2", "Pre-Primary", 2),
    ("Grade 1", "G1", "Lower Primary", 3),
    ("Grade 2", "G2", "Lower Primary", 4),
    ("Grade 3", "G3", "Lower Primary", 5),
    ("Grade 4", "G4", "Upper Primary", 6),
    ("Grade 5", "G5", "Upper Primary", 7),
    ("Grade 6", "G6", "Upper Primary", 8),
    ("Grade 7", "G7", "Junior Secondary", 9),
    ("Grade 8", "G8", "Junior Secondary", 10),
    ("Grade 9", "G9", "Junior Secondary", 11),
    ("Grade 10", "G10", "Senior Secondary", 12),
    ("Grade 11", "G11", "Senior Secondary", 13),
    ("Grade 12", "G12", "Senior Secondary", 14),
]

CBC_SUBJECTS = {
    "Lower Primary": [
        ("Literacy Activities", "LIT", True),
        ("Kiswahili Language Activities", "KIS", True),
        ("English Language Activities", "ENG", True),
        ("Mathematical Activities", "MAT", True),
        ("Environmental Activities", "ENV", True),
        ("Hygiene and Nutrition", "HYG", True),
        ("Religious Education", "RE", True),
        ("Creative Activities", "CRE", True),
    ],
    "Upper Primary": [
        ("English", "ENG", True),
        ("Kiswahili", "KIS", True),
        ("Mathematics", "MAT", True),
        ("Science and Technology", "SCI", True),
        ("Social Studies", "SST", True),
        ("Religious Education", "RE", True),
        ("Creative Arts", "CA", True),
        ("Physical and Health Education", "PHE", True),
        ("Agriculture", "AGR", False),
        ("Home Science", "HS", False),
    ],
    "Junior Secondary": [
        ("English", "ENG", True),
        ("Kiswahili", "KIS", True),
        ("Mathematics", "MAT", True),
        ("Integrated Science", "ISC", True),
        ("Pre-Technical Studies", "PTS", True),
        ("Social Studies", "SST", True),
        ("Business Studies", "BUS", False),
        ("Agriculture", "AGR", False),
        ("Religious Education", "RE", True),
        ("Life Skills Education", "LSE", True),
        ("Creative Arts and Sports", "CAS", False),
        ("Health Education", "HE", True),
    ],
    "Senior Secondary": [
        ("English", "ENG", True),
        ("Kiswahili", "KIS", True),
        ("Mathematics", "MAT", True),
        ("Community Service Learning", "CSL", True),
        ("Biology", "BIO", False),
        ("Chemistry", "CHEM", False),
        ("Physics", "PHY", False),
        ("Computer Science", "CS", False),
        ("History", "HIS", False),
        ("Geography", "GEO", False),
        ("Business Studies", "BUS", False),
        ("Agriculture", "AGR", False),
    ],
    "Pre-Primary": [
        ("Language Activities", "LAN", True),
        ("Mathematical Activities", "MAT", True),
        ("Environmental Activities", "ENV", True),
        ("Psychomotor and Creative Activities", "PCA", True),
        ("Religious Education Activities", "RE", True),
    ],
}

ACHIEVEMENT_LEVELS = {
    "EE1": (90, 100, "Exceeding Expectations – Exceptional"),
    "EE2": (75, 89, "Exceeding Expectations – Very Good"),
    "ME1": (58, 74, "Meeting Expectations – Good"),
    "ME2": (41, 57, "Meeting Expectations – Fair"),
    "AE1": (31, 40, "Approaching Expectations – Needs Improvement"),
    "AE2": (21, 30, "Approaching Expectations – Below Average"),
    "BE1": (11, 20, "Below Expectations"),
    "BE2": (0, 10, "Below Expectations – Critical"),
}


def get_achievement_level(percentage):
    if percentage is None:
        return None
    for code, (lo, hi, _) in ACHIEVEMENT_LEVELS.items():
        if lo <= percentage <= hi:
            return code
    return "BE2"


def seed_school_cbc(school):
    for name, code, stage, order in CBC_GRADES:
        g = GradeLevel(school_id=school.id, name=name, code=code, stage=stage, order_index=order)
        db.session.add(g)
    db.session.flush()
    for stage, subjects in CBC_SUBJECTS.items():
        for name, code, is_core in subjects:
            s = Subject(school_id=school.id, name=name, code=code, stage=stage, is_core=is_core)
            db.session.add(s)
    db.session.commit()


def generate_school_code():
    last = School.query.order_by(School.id.desc()).first()
    n = (last.id + 1) if last else 1
    return f"SCH{n:03d}"


def generate_password(length=10):
    alphabet = "abcdefghijkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(secrets.choice(alphabet) for _ in range(length))


# ---------------------------------------------------------------------------
# Routes – Public & Auth
# ---------------------------------------------------------------------------

@app.route('/')
def index():
    if current_user.is_authenticated:
        if isinstance(current_user, PlatformAdmin):
            return redirect(url_for('platform_dashboard'))
        if current_user.role == 'school_admin':
            return redirect(url_for('school_dashboard'))
        if current_user.role == 'teacher':
            return redirect(url_for('teacher_dashboard'))
        if current_user.role == 'student':
            return redirect(url_for('student_dashboard'))
    return render_template('index.html')


@app.route('/register-school', methods=['GET', 'POST'])
def register_school():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        county = request.form.get('county', '').strip()
        sub_county = request.form.get('sub_county', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        admin_first = request.form.get('admin_first_name', '').strip()
        admin_last = request.form.get('admin_last_name', '').strip()
        admin_email = request.form.get('admin_email', '').strip()
        admin_phone = request.form.get('admin_phone', '').strip()

        if not all([name, admin_first, admin_email]):
            flash('School name, admin first name and email are required.', 'danger')
            return render_template('register_school.html')

        code = generate_school_code()
        school = School(
            name=name, code=code, county=county, sub_county=sub_county,
            phone=phone, email=email or admin_email
        )
        db.session.add(school)
        db.session.flush()

        username = f"admin_{code.lower()}"
        password = generate_password(12)
        user = User(
            school_id=school.id,
            username=username,
            email=admin_email,
            password_hash=generate_password_hash(password),
            role='school_admin',
            first_name=admin_first,
            last_name=admin_last,
            phone=admin_phone
        )
        db.session.add(user)
        db.session.commit()

        seed_school_cbc(school)

        return render_template(
            'registration_success.html',
            school=school,
            username=username,
            password=password,
            admin_email=admin_email
        )

    return render_template('register_school.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        school_code = request.form.get('school_code', '').strip().upper()

        if username == 'platform_admin' or not school_code:
            pa = PlatformAdmin.query.filter_by(username=username).first()
            if pa and check_password_hash(pa.password_hash, password):
                login_user(pa)
                return redirect(url_for('platform_dashboard'))

        school = School.query.filter_by(code=school_code, is_active=True).first()
        if not school:
            flash('Invalid school code or school inactive.', 'danger')
            return render_template('login.html')

        user = User.query.filter_by(school_id=school.id, username=username, is_active=True).first()
        if user and check_password_hash(user.password_hash, password):
            user.last_login = datetime.utcnow()
            db.session.commit()
            login_user(user)
            return redirect(url_for('index'))

        flash('Invalid credentials.', 'danger')
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))


# ---------------------------------------------------------------------------
# Platform Admin
# ---------------------------------------------------------------------------

@app.route('/platform')
@login_required
@role_required('platform_admin')
def platform_dashboard():
    schools = School.query.order_by(School.created_at.desc()).all()
    total_students = Student.query.count()
    total_teachers = Teacher.query.count()
    return render_template(
        'platform_dashboard.html',
        schools=schools,
        total_students=total_students,
        total_teachers=total_teachers
    )


@app.route('/platform/school/<int:school_id>/toggle')
@login_required
@role_required('platform_admin')
def toggle_school(school_id):
    school = School.query.get_or_404(school_id)
    school.is_active = not school.is_active
    db.session.commit()
    flash(f'School {school.name} is now {"active" if school.is_active else "inactive"}.', 'success')
    return redirect(url_for('platform_dashboard'))


# ---------------------------------------------------------------------------
# School Admin
# ---------------------------------------------------------------------------

@app.route('/school')
@login_required
@role_required('school_admin')
@school_required
def school_dashboard():
    school = current_user.school
    stats = {
        'students': school.students.count(),
        'teachers': school.teachers.count(),
        'classes': school.classes.count(),
        'modules': school.learning_modules.count(),
        'exams': school.exams.count(),
    }
    recent_students = school.students.order_by(Student.id.desc()).limit(5).all()
    return render_template('school_dashboard.html', school=school, stats=stats, recent_students=recent_students)


@app.route('/school/teachers', methods=['GET', 'POST'])
@login_required
@role_required('school_admin')
@school_required
def manage_teachers():
    school = current_user.school
    if request.method == 'POST':
        first = request.form.get('first_name', '').strip()
        last = request.form.get('last_name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        tsc = request.form.get('tsc_number', '').strip()
        spec = request.form.get('specialization', '').strip()
        if not first or not email:
            flash('First name and email required.', 'danger')
        else:
            username = f"t_{first.lower()[:3]}{secrets.token_hex(2)}"
            password = generate_password(10)
            user = User(
                school_id=school.id, username=username, email=email,
                password_hash=generate_password_hash(password),
                role='teacher', first_name=first, last_name=last, phone=phone
            )
            db.session.add(user)
            db.session.flush()
            teacher = Teacher(school_id=school.id, user_id=user.id, tsc_number=tsc, specialization=spec)
            db.session.add(teacher)
            db.session.commit()
            flash(f'Teacher created. Username: {username}  Password: {password}', 'success')
        return redirect(url_for('manage_teachers'))

    teachers = school.teachers.all()
    return render_template('manage_teachers.html', school=school, teachers=teachers)


@app.route('/school/students', methods=['GET', 'POST'])
@login_required
@role_required('school_admin')
@school_required
def manage_students():
    school = current_user.school
    classes = school.classes.all()
    if request.method == 'POST':
        first = request.form.get('first_name', '').strip()
        last = request.form.get('last_name', '').strip()
        adm = request.form.get('admission_number', '').strip()
        class_id = request.form.get('class_id')
        gender = request.form.get('gender')
        parent = request.form.get('parent_name', '').strip()
        parent_phone = request.form.get('parent_phone', '').strip()
        if not first or not adm:
            flash('First name and admission number required.', 'danger')
        else:
            username = f"s_{adm.lower()}"
            password = generate_password(8)
            email = f"{username}@{school.code.lower()}.cbc.local"
            user = User(
                school_id=school.id, username=username, email=email,
                password_hash=generate_password_hash(password),
                role='student', first_name=first, last_name=last
            )
            db.session.add(user)
            db.session.flush()
            student = Student(
                school_id=school.id, user_id=user.id, admission_number=adm,
                class_id=int(class_id) if class_id else None,
                gender=gender, parent_name=parent, parent_phone=parent_phone
            )
            db.session.add(student)
            db.session.commit()
            flash(f'Student created. Username: {username}  Password: {password}', 'success')
        return redirect(url_for('manage_students'))

    students = school.students.order_by(Student.id.desc()).all()
    return render_template('manage_students.html', school=school, students=students, classes=classes)


@app.route('/school/classes', methods=['GET', 'POST'])
@login_required
@role_required('school_admin')
@school_required
def manage_classes():
    school = current_user.school
    grades = school.grades.order_by(GradeLevel.order_index).all()
    teachers = school.teachers.all()
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        grade_id = request.form.get('grade_level_id')
        year = request.form.get('academic_year', '2026')
        teacher_id = request.form.get('class_teacher_id') or None
        if name and grade_id:
            cls = SchoolClass(
                school_id=school.id, grade_level_id=int(grade_id),
                name=name, academic_year=year,
                class_teacher_id=int(teacher_id) if teacher_id else None
            )
            db.session.add(cls)
            db.session.commit()
            flash('Class created.', 'success')
        return redirect(url_for('manage_classes'))

    classes = school.classes.all()
    return render_template('manage_classes.html', school=school, classes=classes, grades=grades, teachers=teachers)


@app.route('/school/subjects')
@login_required
@role_required('school_admin', 'teacher')
@school_required
def view_subjects():
    school = current_user.school
    subjects = school.subjects.order_by(Subject.stage, Subject.name).all()
    return render_template('view_subjects.html', school=school, subjects=subjects)


# ---------------------------------------------------------------------------
# Learning Modules
# ---------------------------------------------------------------------------

@app.route('/learning')
@login_required
@school_required
def learning_hub():
    school = current_user.school
    modules = school.learning_modules.filter_by(is_published=True).order_by(LearningModule.created_at.desc()).all()
    grades = school.grades.order_by(GradeLevel.order_index).all()
    subjects = school.subjects.all()
    return render_template('learning_hub.html', school=school, modules=modules, grades=grades, subjects=subjects)


@app.route('/learning/module/<int:module_id>')
@login_required
@school_required
def view_module(module_id):
    module = LearningModule.query.get_or_404(module_id)
    if module.school_id != current_user.school_id:
        abort(403)
    return render_template('view_module.html', module=module)


@app.route('/learning/create', methods=['GET', 'POST'])
@login_required
@role_required('school_admin', 'teacher')
@school_required
def create_module():
    school = current_user.school
    grades = school.grades.order_by(GradeLevel.order_index).all()
    subjects = school.subjects.all()
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        subject_id = request.form.get('subject_id')
        grade_id = request.form.get('grade_level_id')
        strand = request.form.get('strand', '').strip()
        sub_strand = request.form.get('sub_strand', '').strip()
        content = request.form.get('content', '')
        outcomes = request.form.get('learning_outcomes', '')
        if title and subject_id and grade_id:
            m = LearningModule(
                school_id=school.id, subject_id=int(subject_id),
                grade_level_id=int(grade_id), title=title,
                strand=strand, sub_strand=sub_strand, content=content,
                learning_outcomes=outcomes, created_by=current_user.id
            )
            db.session.add(m)
            db.session.commit()
            flash('Learning module published.', 'success')
            return redirect(url_for('learning_hub'))
        flash('Title, subject and grade are required.', 'danger')
    return render_template('create_module.html', grades=grades, subjects=subjects)


# ---------------------------------------------------------------------------
# Exams & Assessments
# ---------------------------------------------------------------------------

@app.route('/exams')
@login_required
@school_required
def exams_list():
    school = current_user.school
    if current_user.role == 'student':
        student = current_user.student_profile
        grade_id = student.school_class.grade_level_id if student and student.school_class else None
        exams = school.exams.filter_by(is_published=True)
        if grade_id:
            exams = exams.filter_by(grade_level_id=grade_id)
        exams = exams.order_by(Exam.created_at.desc()).all()
    else:
        exams = school.exams.order_by(Exam.created_at.desc()).all()
    return render_template('exams_list.html', school=school, exams=exams)


@app.route('/exams/create', methods=['GET', 'POST'])
@login_required
@role_required('school_admin', 'teacher')
@school_required
def create_exam():
    school = current_user.school
    grades = school.grades.order_by(GradeLevel.order_index).all()
    subjects = school.subjects.all()
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        subject_id = request.form.get('subject_id')
        grade_id = request.form.get('grade_level_id')
        exam_type = request.form.get('exam_type', 'formative')
        total = int(request.form.get('total_marks', 100))
        duration = int(request.form.get('duration_minutes', 60))
        instructions = request.form.get('instructions', '')
        if title and subject_id and grade_id:
            exam = Exam(
                school_id=school.id, title=title, subject_id=int(subject_id),
                grade_level_id=int(grade_id), exam_type=exam_type,
                total_marks=total, duration_minutes=duration,
                instructions=instructions, created_by=current_user.id
            )
            db.session.add(exam)
            db.session.commit()
            flash('Exam created. Now add questions.', 'success')
            return redirect(url_for('edit_exam', exam_id=exam.id))
        flash('Required fields missing.', 'danger')
    return render_template('create_exam.html', grades=grades, subjects=subjects)


@app.route('/exams/<int:exam_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('school_admin', 'teacher')
@school_required
def edit_exam(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    if exam.school_id != current_user.school_id:
        abort(403)
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add_question':
            qtext = request.form.get('question_text', '').strip()
            qtype = request.form.get('question_type', 'mcq')
            marks = int(request.form.get('marks', 1))
            options = request.form.get('options', '')
            correct = request.form.get('correct_answer', '')
            competency = request.form.get('competency_focus', '')
            if qtext:
                q = ExamQuestion(
                    exam_id=exam.id, question_text=qtext, question_type=qtype,
                    options=options, correct_answer=correct, marks=marks,
                    competency_focus=competency,
                    order_index=exam.questions.count()
                )
                db.session.add(q)
                db.session.commit()
                flash('Question added.', 'success')
        elif action == 'publish':
            exam.is_published = True
            db.session.commit()
            flash('Exam published to students.', 'success')
        return redirect(url_for('edit_exam', exam_id=exam.id))

    questions = exam.questions.order_by(ExamQuestion.order_index).all()
    return render_template('edit_exam.html', exam=exam, questions=questions)


@app.route('/exams/<int:exam_id>/take', methods=['GET', 'POST'])
@login_required
@role_required('student')
@school_required
def take_exam(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    if exam.school_id != current_user.school_id or not exam.is_published:
        abort(403)
    student = current_user.student_profile
    existing = ExamAttempt.query.filter_by(exam_id=exam.id, student_id=student.id).first()
    if existing and existing.submitted_at:
        flash('You have already submitted this exam.', 'info')
        return redirect(url_for('exam_result', attempt_id=existing.id))

    questions = exam.questions.order_by(ExamQuestion.order_index).all()

    if request.method == 'POST':
        answers = {}
        score = 0.0
        max_score = 0.0
        for q in questions:
            max_score += q.marks
            ans = request.form.get(f'q_{q.id}', '').strip()
            answers[str(q.id)] = ans
            if q.question_type == 'mcq' and ans.lower() == (q.correct_answer or '').lower():
                score += q.marks

        percentage = (score / max_score * 100) if max_score else 0
        level = get_achievement_level(percentage)

        if existing:
            attempt = existing
        else:
            attempt = ExamAttempt(exam_id=exam.id, student_id=student.id)
            db.session.add(attempt)
        attempt.submitted_at = datetime.utcnow()
        attempt.score = score
        attempt.max_score = max_score
        attempt.achievement_level = level
        attempt.answers = str(answers)
        db.session.commit()
        flash(f'Exam submitted! Score: {score}/{max_score} ({percentage:.0f}%) – {level}', 'success')
        return redirect(url_for('exam_result', attempt_id=attempt.id))

    return render_template('take_exam.html', exam=exam, questions=questions)


@app.route('/exams/result/<int:attempt_id>')
@login_required
@school_required
def exam_result(attempt_id):
    attempt = ExamAttempt.query.get_or_404(attempt_id)
    if attempt.student.school_id != current_user.school_id:
        abort(403)
    if current_user.role == 'student' and attempt.student.user_id != current_user.id:
        abort(403)
    return render_template('exam_result.html', attempt=attempt)


@app.route('/assessments', methods=['GET', 'POST'])
@login_required
@role_required('school_admin', 'teacher')
@school_required
def assessments():
    school = current_user.school
    students = school.students.all()
    subjects = school.subjects.all()
    grades = school.grades.all()
    if request.method == 'POST':
        student_id = request.form.get('student_id')
        subject_id = request.form.get('subject_id')
        grade_id = request.form.get('grade_level_id')
        term = request.form.get('term', 'Term 1')
        level = request.form.get('achievement_level')
        score = request.form.get('score')
        comments = request.form.get('comments', '')
        if student_id and subject_id and level:
            rec = AssessmentRecord(
                school_id=school.id, student_id=int(student_id),
                subject_id=int(subject_id), grade_level_id=int(grade_id) if grade_id else None,
                term=term, achievement_level=level,
                score=float(score) if score else None,
                comments=comments, recorded_by=current_user.id
            )
            db.session.add(rec)
            db.session.commit()
            flash('Assessment recorded.', 'success')
        return redirect(url_for('assessments'))

    records = AssessmentRecord.query.filter_by(school_id=school.id).order_by(AssessmentRecord.recorded_at.desc()).limit(50).all()
    return render_template('assessments.html', school=school, students=students,
                           subjects=subjects, grades=grades, records=records,
                           levels=ACHIEVEMENT_LEVELS)


# ---------------------------------------------------------------------------
# Teacher & Student dashboards
# ---------------------------------------------------------------------------

@app.route('/teacher')
@login_required
@role_required('teacher')
@school_required
def teacher_dashboard():
    school = current_user.school
    modules = school.learning_modules.filter_by(created_by=current_user.id).count()
    exams = school.exams.filter_by(created_by=current_user.id).count()
    return render_template('teacher_dashboard.html', school=school, modules=modules, exams=exams)


@app.route('/student')
@login_required
@role_required('student')
@school_required
def student_dashboard():
    school = current_user.school
    student = current_user.student_profile
    modules = school.learning_modules.filter_by(is_published=True).limit(6).all()
    attempts = ExamAttempt.query.filter_by(student_id=student.id).order_by(ExamAttempt.submitted_at.desc()).limit(5).all()
    return render_template('student_dashboard.html', school=school, student=student, modules=modules, attempts=attempts)


# ---------------------------------------------------------------------------
# Init DB & Platform Admin
# ---------------------------------------------------------------------------

def init_db():
    with app.app_context():
        db.create_all()
        if not PlatformAdmin.query.filter_by(username='platform_admin').first():
            pa = PlatformAdmin(
                username='platform_admin',
                email='admin@cbcplatform.ke',
                password_hash=generate_password_hash('Platform@2026')
            )
            db.session.add(pa)
            db.session.commit()
            print("Platform admin created: platform_admin / Platform@2026")


if __name__ == '__main__':
    init_db()
    print("\n" + "="*60)
    print("  CBC Integrated School Management System")
    print("  Multi-tenant • Instant school registration")
    print("  CBC-aligned learning & competency assessments")
    print("="*60)
    print("  Platform Admin:  platform_admin  /  Platform@2026")
    print("  Register a school at /register-school to get instant login")
    print("="*60 + "\n")
    app.run(host='0.0.0.0', port=5000, debug=True)
