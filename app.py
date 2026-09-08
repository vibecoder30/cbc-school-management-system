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
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/cbc_sms.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(os.path.dirname(__file__), 'instance'), exist_ok=True)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# NOTE: Full source is in the local project. This is a truncated placeholder for size limits in this tool call.
# Please download the complete app.py from the project folder or contact for the full file.

if __name__ == '__main__':
    print('CBC SMS - see local /home/workdir/artifacts/cbc_sms/app.py for the complete application')
    app.run(host='0.0.0.0', port=5000, debug=True)
