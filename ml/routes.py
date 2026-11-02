import os
import random
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from models import db, JobScan, Notification
from werkzeug.utils import secure_filename
from PIL import Image
import pytesseract
import io
from pdfminer.high_level import extract_text as extract_pdf_text
from docx import Document

# Define Skillsets for Roles
ROLE_SKILLS = {
    "Data Analyst": ["python", "sql", "excel", "power bi", "tableau", "statistics", "data visualization", "pandas", "numpy", "matplotlib", "seaborn"],
    "Software Engineer": ["python", "java", "javascript", "c++", "c#", "git", "docker", "kubernetes", "sql", "nosql", "aws", "azure", "ci/cd", "rest api", "algorithms", "data structures"],
    "Software Developer": ["python", "java", "javascript", "git", "sql", "agile", "unit testing", "api design", "backend", "frontend"],
    "Full Stack Developer": ["html", "css", "javascript", "react", "node.js", "sql", "nosql", "git", "rest api", "docker", "express", "mongodb"],
    "Data Scientist": ["python", "r", "statistics", "machine learning", "sql", "pandas", "numpy", "scikit-learn", "data visualization", "linear algebra"],
    "Java Developer": ["java", "spring boot", "hibernate", "sql", "maven", "junit", "microservices", "jpa", "rest api"],
    "Python Developer": ["python", "django", "flask", "pytest", "sql", "pandas", "numpy", "celery", "redis", "rest api"],
    "Cloud Computing": ["aws", "azure", "gcp", "docker", "kubernetes", "terraform", "cloud architecture", "linux", "networking", "serverless"],
    "AI Engineer": ["python", "tensorflow", "pytorch", "neural networks", "nlp", "computer vision", "deep learning", "keras", "machine learning"],
    "Web Developer": ["html", "css", "javascript", "react", "angular", "vue", "node.js", "bootstrap", "tailwind", "responsive design", "typescript", "sass"],
    "Digital Marketer": ["seo", "sem", "google analytics", "social media marketing", "content strategy", "email marketing", "copywriting", "ppc", "ads", "advertising"],
    "HR Manager": ["recruitment", "interviews", "onboarding", "employee relations", "performance management", "labor laws", "conflict resolution", "payroll", "training", "development"]
}

def extract_text(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.pdf':
        try:
            return extract_pdf_text(file_path)
        except Exception as e:
            return str(e)
    elif ext == '.docx':
        try:
            doc = Document(file_path)
            return "\n".join([para.text for para in doc.paragraphs])
        except Exception as e:
            return str(e)
    return ""

def calculate_resume_score(text, role):
    text = text.lower()
    required_skills = ROLE_SKILLS.get(role, [])
    if not required_skills:
        return 0, [], [], []

    found_skills = [skill for skill in required_skills if skill in text]
    missing_skills = [skill for skill in required_skills if skill not in text]
    
    score = (len(found_skills) / len(required_skills)) * 100
    
    suggestions = []
    if score < 50:
        suggestions.append("Consider taking online courses to gain missing core skills.")
    if missing_skills:
        suggestions.append(f"Adding experience with {', '.join(missing_skills[:3])} could significantly boost your profile.")
    if score >= 80:
        suggestions.append("Your resume is very strong! Focus on personal projects to stand out.")
    
    return round(score, 1), found_skills, missing_skills, suggestions

ml = Blueprint('ml', __name__)

# Configure Tesseract path
@ml.before_app_request
def setup_tesseract():
    pytesseract.pytesseract.tesseract_cmd = current_app.config['TESSERACT_PATH']

# Mock AI Model logic (In a real scenario, we'd load a pickled model)
# For this scratch project, we'll use a rule-based + probabilistic mock for "AI"
import re

# Enhanced Indicators
HIGH_RISK_KEYWORDS = [
    'whatsapp', 'telegram', 'payment', 'bank details', 'wire transfer', 
    'zelle', 'crypto', 'cashapp', 'venmo', 'ssn', 'social security', 
    'gift card', 'equipment fee', 'upfront', 'application fee', 
    'processing fee', 'registration fee', 'security deposit', 
    'refundable deposit', 'training fee'
]
MEDIUM_RISK_KEYWORDS = [
    'urgent', 'no experience', 'high pay', 'immediate start', 'work from home', 
    'passive income', 'daily pay', 'unlimited earning', 'hiring immediately', 
    'guaranteed income', 'no interview', 'no background check'
]

def analyze_text(text):
    text = text.lower()
    score = 0
    
    # 1. High Risk Keywords (Weighted 2.0)
    for word in HIGH_RISK_KEYWORDS:
        if word in text:
            score += 2.0
            
    # 2. Medium Risk Keywords (Weighted 1.0)
    for word in MEDIUM_RISK_KEYWORDS:
        if word in text:
            score += 1.0
            
    # 3. Pattern Matching
    # a. Too good to be true Salary (e.g., $5000/week)
    salary_patterns = [
        r'\$\d{4,}\s*(per|/)\s*(week|day)',
        r'\$\d{2,}\d00\s*(per|/)\s*hour',
        r'earn\s*\$?\d{3,}',
        r'\$\d{3,}\s*-\s*\$\d{3,}\s*(per|/)\s*(hour|hr)'
    ]
    for pattern in salary_patterns:
        if re.search(pattern, text):
            score += 2.5
            
    # b. Demanding money (e.g., Rs.20000 fee, pay $50)
    fee_patterns = [
        r'fees?\s*of\s*(rs\.?|₹|\$|inr)?\s*\d+',
        r'pay\s*(amount|fee)?\s*(of)?\s*(rs\.?|₹|\$|inr)?\s*\d+',
        r'deposit\s*(of)?\s*(rs\.?|₹|\$|inr)?\s*\d+',
        r'(rs\.?|₹|\$|inr)\s*\d+\s*(fee|deposit|payment)'
    ]
    for pattern in fee_patterns:
        if re.search(pattern, text):
            score += 3.0
            
    # 4. Email/Link Checks
    if re.search(r'\b[A-Za-z0-9._%+-]+@(gmail|yahoo|outlook|hotmail)\.com\b', text):
        score += 1.0 # Unprofessional email for job posting
        
    # Calculate Confidence
    # Base confidence starts at 0.5, increases with score but caps at 0.98
    confidence = 0.5 + (0.1 * score)
    if confidence > 0.98: confidence = 0.98
    if confidence < 0.5: confidence = 0.55
    
    # Decision Logic: If score > 1.0, it's suspicious
    result = "Fake" if score >= 1.5 else "Real"
    
    # If it's a "Real" result but close to threshold, reduce confidence
    if result == "Real" and score > 0:
        confidence = 0.6
        
    return result, confidence

@ml.route('/detect', methods=['POST'])
@login_required
def detect():
    description = request.form.get('description', '')
    image_file = request.files.get('job_image')
    
    content = description
    image_path = None

    if image_file and image_file.filename != '':
        filename = secure_filename(image_file.filename)
        upload_dir = os.path.join('static', 'uploads')
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
        
        rel_path = os.path.join('uploads', filename)
        abs_path = os.path.join('static', rel_path)
        image_file.save(abs_path)
        image_path = rel_path
        
        # OCR Analysis
        try:
            extracted_text = pytesseract.image_to_string(Image.open(abs_path))
            content += " " + extracted_text
        except Exception as e:
            flash(f"OCR Error: {str(e)}. Proceeding with text only.", "warning")

    if not content.strip():
        flash("Please provide either text or an image for analysis.", "danger")
        return redirect(url_for('main.new_scan'))

    # Generate a title from content if not provided
    title = content.strip().split('\n')[0][:50]
    if not title:
        title = "Untitled Scan"

    result, confidence = analyze_text(content)
    
    new_scan = JobScan(
        title=title,
        content=content[:500], # Store first 500 chars
        result=result,
        confidence=confidence,
        user_id=current_user.id,
        image_path=image_path
    )
    db.session.add(new_scan)
    
    if current_user.notifications_enabled:
        notif_msg = f"New analysis complete for '{title}': Result is {result}."
        action_url = "https://www.linkedin.com/jobs" if result == "Real" else None
        notification = Notification(message=notif_msg, user_id=current_user.id, action_url=action_url)
        db.session.add(notification)
        
    db.session.commit()
    
    flash(f"Analysis Complete: Your job offer is likely {result} ({int(confidence*100)}% confidence)", "success")
    return redirect(url_for('main.scan_result', scan_id=new_scan.id))

@ml.route('/delete_scan/<int:scan_id>', methods=['POST'])
@login_required
def delete_scan(scan_id):
    scan = JobScan.query.get_or_404(scan_id)
    if scan.user_id != current_user.id:
        flash("Unauthorized action.", "danger")
        return redirect(url_for('main.dashboard'))
    
    db.session.delete(scan)
    
    db.session.commit()
    flash("Scan record deleted successfully.", "success")
    return redirect(url_for('main.dashboard'))


class AssistantManager:
    def __init__(self):
        self.knowledge_base = {
            "intents": {
                "greeting": {
                    "keywords": ["hello", "hi", "hey", "greetings"],
                    "responses": ["Hello! I am ScanShield AI, your career safety companion. How can I assist you with your job search today?"],
                    "follow_up": "Are you currently reviewing a suspicious job offer?"
                },
                "scam_info": {
                    "keywords": ["scam", "fake", "fraud", "legit", "safe"],
                    "responses": [
                        "Common job scams usually involve requests for money, suspicious communication via WhatsApp/Telegram, or 'too good to be true' salaries.",
                        "If they ask you to pay for equipment or training up-front, it's almost certainly a scam."
                    ],
                    "follow_up": "Would you like me to check some specific 'red flags' with you?"
                },
                "red_flags": {
                    "keywords": ["red flag", "flags", "warning", "signs", "suspicious"],
                    "responses": [
                        "Watch out for: 1. No formal interview 2. Unprofessional email 3. High pay for low effort 4. Pressure to act fast.",
                        "Recruiters from real companies will NEVER ask for your bank details or social security number via text chat."
                    ],
                    "follow_up": "Did your recruiter contact you from a personal email like @gmail.com?"
                },
                "verify_methods": {
                    "keywords": ["verify", "check", "how to", "authenticate"],
                    "responses": ["To verify: Check the official company careers page, look for the recruiter on LinkedIn, and call the company's official HR department if unsure."],
                    "follow_up": "I can also analyze the job description for you if you paste it here!"
                },
                "career_advice": {
                    "keywords": ["advice", "career", "tips", "help", "growth", "interview"],
                    "responses": ["Focus on building a strong LinkedIn presence and only apply through verified platforms. Keep your resume updated and highlight your core skills."],
                    "follow_up": "Are you looking for tips on a specific industry?"
                }
            },
            "dynamic_responses": {
                "payment": "Legitimate employers NEVER ask for payment. If they mentioned any fees, please stop communication immediately.",
                "whatsapp": "Communication through WhatsApp or Telegram is a major red flag for professional recruitment.",
                "remote_equipment": "If they ask you to buying equipment from 'their vendor' and promised a check for reimbursement, it's a classic check-cashing scam."
            }
        }

    def get_response(self, message, context=None):
        message = message.lower()
        
        # 1. Check for specific high-risk mentions first (Dynamic/Urgent)
        if "payment" in message or "pay" in message or "money" in message:
            return self.knowledge_base["dynamic_responses"]["payment"], "payment_risk"
        if "whatsapp" in message or "telegram" in message:
            return self.knowledge_base["dynamic_responses"]["whatsapp"], "comm_risk"
        if "equipment" in message or "check" in message:
            return self.knowledge_base["dynamic_responses"]["remote_equipment"], "scam_type"

        # 2. Intent Matching
        best_intent = None
        max_overlap = 0
        
        for intent, data in self.knowledge_base["intents"].items():
            overlap = sum(1 for kw in data["keywords"] if kw in message)
            if overlap > max_overlap:
                overlap += 1 # Boost direct keyword matches
            if overlap > max_overlap:
                max_overlap = overlap
                best_intent = intent
        
        if best_intent:
            intent_data = self.knowledge_base["intents"][best_intent]
            response = random.choice(intent_data["responses"])
            if "follow_up" in intent_data:
                response += " " + intent_data["follow_up"]
            return response, best_intent

        # 3. Contextual Fallback
        if context == "red_flags":
            return "Aside from those, always check if the company domain matches their email. Does it look professional?", "red_flags"

        # 4. Default
        if "?" in message:
            return "I'm not entirely sure about that specific detail, but I recommend checking if the employer is verified on LinkedIn. Would you like more tips on safety?", "general"
        
        return "I'm here to help you stay safe. Tell me more about the job you're looking at, or ask about 'red flags'.", "idle"

assistant_manager = AssistantManager()

@ml.route('/chatbot', methods=['POST'])
def chatbot():
    data = request.json
    user_msg = data.get('message', '').strip()
    context = data.get('context')
    
    response, new_context = assistant_manager.get_response(user_msg, context)
    
    return jsonify({
        "response": response,
        "context": new_context
    })

@ml.route('/resume_analysis')
@login_required
def resume_analysis():
    return render_template('resume_analysis.html', roles=ROLE_SKILLS.keys())

@ml.route('/analyze_resume', methods=['POST'])
@login_required
def analyze_resume():
    if 'resume' not in request.files:
        flash("No file uploaded.", "danger")
        return redirect(url_for('ml.resume_analysis'))
    
    file = request.files['resume']
    role = request.form.get('role')
    
    if file.filename == '':
        flash("No file selected.", "danger")
        return redirect(url_for('ml.resume_analysis'))
    
    if file and role:
        filename = secure_filename(file.filename)
        upload_dir = os.path.join('static', 'uploads', 'resumes')
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
            
        file_path = os.path.join(upload_dir, filename)
        file.save(file_path)
        
        text = extract_text(file_path)
        score, found_skills, missing_skills, suggestions = calculate_resume_score(text, role)
        
        return render_template('resume_result.html', 
                               score=score, 
                               found_skills=found_skills, 
                               missing_skills=missing_skills, 
                               suggestions=suggestions,
                               role=role)
    
    flash("Invalid request.", "danger")
    return redirect(url_for('ml.resume_analysis'))
