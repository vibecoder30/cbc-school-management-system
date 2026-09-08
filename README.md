# CBC Integrated School Management System

Multi-tenant School Management + Learning platform for **20+ schools**, fully aligned to Kenya’s **Competency-Based Curriculum (CBC / 2-6-3-3-3)**.

**Repo:** https://github.com/vibecoder30/cbc-school-management-system

## Important – Get the complete code

The full working `app.py` ( ~40 KB ) and all remaining templates are ready in the project folder.

**Easiest way to get a complete runnable project:**

1. On GitHub, click **Add file → Upload files**
2. Drag the entire contents of the local folder `/home/workdir/artifacts/cbc_sms/` (or download it) into the upload area
3. Commit the changes

Or from your computer (if you have the folder):

```bash
cd /path/to/cbc_sms
git init
git remote add origin https://github.com/vibecoder30/cbc-school-management-system.git
git add .
git commit -m "Complete CBC School Management System"
git branch -M main
git push -u origin main --force
```

## Quick Start (once complete code is in the repo)

```bash
git clone https://github.com/vibecoder30/cbc-school-management-system.git
cd cbc-school-management-system
pip install -r requirements.txt
python app.py
```

Then open **http://127.0.0.1:5000**

### Platform Admin
- Username: `platform_admin`
- Password: `Platform@2026`
- Leave School Code blank

### Register a School
1. Click **Register School**
2. You instantly receive School Code + Username + Password
3. Login with those credentials

## Features
- Instant school registration → admin login
- Multi-tenant (20+ schools)
- Full CBC grades & subjects (PP1–G12)
- Learning modules (strands / sub-strands)
- Exams with CBC achievement levels (EE / ME / AE / BE)
- School-based continuous assessments

Built for Kenyan schools on the Competency-Based Curriculum.
