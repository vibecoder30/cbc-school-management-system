# CBC Integrated School Management System

Multi-tenant School Management + Learning platform for **20+ schools**, fully aligned to Kenya’s **Competency-Based Curriculum (CBC / 2-6-3-3-3)**.

**Live repo:** https://github.com/vibecoder30/cbc-school-management-system

## Key Features

- **Instant school registration** → school code + admin username & password generated immediately
- **Multi-tenant isolation** – each school’s data is separated by `school_id`
- **CBC structure seeded automatically** on registration (Grades PP1–G12 + subjects by stage)
- **Integrated Learning Hub** – modules with strands, sub-strands, learning outcomes
- **Exams** – formative / summative / national-prep with MCQ auto-marking
- **CBC Achievement Levels** – EE1/EE2, ME1/ME2, AE1/AE2, BE1/BE2
- **School-based continuous assessments**
- Roles: Platform Admin, School Admin, Teacher, Student

## Quick Start

```bash
git clone https://github.com/vibecoder30/cbc-school-management-system.git
cd cbc-school-management-system
pip install -r requirements.txt
python3 app.py
```

Open http://127.0.0.1:5000

### Platform Admin
- Username: `platform_admin`
- Password: `Platform@2026`
- Leave School Code blank

### Register a School
1. Click **Register School**
2. Fill details → you instantly receive School Code + Username + Password
3. Login with those credentials

## Typical Admin Flow
1. Create Classes (linked to CBC grades)
2. Add Teachers & Students (credentials auto-generated)
3. Teachers publish Learning Modules & create Exams
4. Students take exams and see CBC achievement levels
5. Teachers record continuous assessments

## Tech Stack
Python 3 + Flask + SQLAlchemy + Flask-Login + Bootstrap 5

## Production Notes
- Change SECRET_KEY and platform password
- Switch to PostgreSQL for production
- Add HTTPS, rate limiting, email notifications

Built for Kenyan schools on the Competency-Based Curriculum.
