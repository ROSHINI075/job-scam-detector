from flask import Blueprint, render_template, jsonify, request, url_for, abort
from flask_login import login_required, current_user
from models import JobScan, Notification, db

main = Blueprint('main', __name__)

@main.route('/')
@main.route('/index')
def index():
    return render_template('index.html')

@main.route('/dashboard')
@login_required
def dashboard():
    scans = JobScan.query.filter_by(user_id=current_user.id).order_by(JobScan.timestamp.desc()).all()
    
    # Mock Job Database
    MOCK_JOBS = [
        {"title": "Senior Software Engineer", "company": "Tech Solutions Inc.", "location": "Remote", "type": "Software"},
        {"title": "Junior Web Developer", "company": "WebFlow agency", "location": "New York", "type": "Software"},
        {"title": "Data Analyst", "company": "Data Insights", "location": "London", "type": "Data"},
        {"title": "Digital Marketing Specialist", "company": "Brand Boosters", "location": "Remote", "type": "Marketing"},
        {"title": "HR Manager", "company": "People First", "location": "San Francisco", "type": "HR"},
        {"title": "Project Manager", "company": "BuildRight", "location": "Chicago", "type": "Management"},
        {"title": "UI/UX Designer", "company": "Creative Minds", "location": "Remote", "type": "Design"},
        {"title": "Customer Support Lead", "company": "HelpDesk Pro", "location": "Remote", "type": "Customer Service"},
        {"title": "Backend Developer (Python)", "company": "Logic Labs", "location": "Berlin", "type": "Software"},
        {"title": "DevOps Engineer", "company": "Cloud Masters", "location": "Tokyo", "type": "Software"}
    ]
    
    # Simple filtering logic based on profession
    user_profession = current_user.profession.lower() if current_user.profession else "software"
    suggestions = [job for job in MOCK_JOBS if any(word in job['title'].lower() or word in job['type'].lower() for word in user_profession.split())]
    
    # Fallback if no specific match
    if not suggestions:
        suggestions = MOCK_JOBS[:4]
    else:
        suggestions = suggestions[:4] # Limit to 4

    return render_template('dashboard.html', scans=scans, suggestions=suggestions)

@main.route('/new_scan')
@login_required
def new_scan():
    return render_template('new_scan.html')

@main.route('/scan_result/<int:scan_id>')
@login_required
def scan_result(scan_id):
    scan = JobScan.query.get_or_404(scan_id)
    if scan.user_id != current_user.id:
        abort(403)
    return render_template('scan_result.html', scan=scan)

@main.route('/detector')
@main.route('/detector/<int:scan_id>')
@login_required
def detector(scan_id=None):
    scan = None
    if scan_id:
        scan = JobScan.query.get_or_404(scan_id)
        if scan.user_id != current_user.id:
            abort(403)
    return render_template('detector.html', scan=scan)

@main.route('/notifications')
@login_required
def get_notifications():
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.timestamp.desc()).limit(10).all()
    return jsonify([{
        'id': n.id,
        'message': n.message,
        'timestamp': n.timestamp.strftime('%Y-%m-%d %H:%M'),
        'is_read': n.is_read,
        'action_url': n.action_url
    } for n in notifications])

@main.route('/notifications/read/<int:id>', methods=['POST'])
@login_required
def read_notification(id):
    notification = Notification.query.get_or_404(id)
    if notification.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 401
    notification.is_read = True
    db.session.commit()
    return jsonify({'success': True})
