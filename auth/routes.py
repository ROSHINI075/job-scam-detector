from flask import Blueprint, render_template, redirect, url_for, flash, request
from models import db, User, Notification
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
import secrets

auth = Blueprint('auth', __name__)

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        profession = request.form.get('profession')

        user_exists = User.query.filter((User.email == email) | (User.username == username)).first()
        if user_exists:
            flash('Email or Username already exists.', 'danger')
        else:
            hashed_password = generate_password_hash(password)
            token = secrets.token_hex(16)
            new_user = User(username=username, email=email, password=hashed_password, profession=profession, verification_token=token)
            db.session.add(new_user)
            db.session.flush() # Get user id
            
            
            # Add Verification Notification
            notif = Notification(
                message="Welcome! Please verify your email to secure your account.",
                user_id=new_user.id,
                action_url=url_for('auth.verify_email', token=token)
            )
            db.session.add(notif)
            db.session.commit()
            
            flash('Account created! Please verify your email via the notification center.', 'success')
            return redirect(url_for('auth.login'))
    return render_template('auth/register.html')

@auth.route('/verify/<token>')
def verify_email(token):
    user = User.query.filter_by(verification_token=token).first_or_404()
    if user.is_verified:
        flash('Email already verified.', 'info')
    else:
        user.is_verified = True
        user.verification_token = None
        db.session.commit()
        flash('Email verified successfully! Welcome to ScamShield AI.', 'success')
    return redirect(url_for('auth.login'))

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user, remember=True)
            db.session.commit()
            
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.dashboard'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('auth/login.html')

@auth.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        current_user.username = request.form.get('username')
        current_user.profession = request.form.get('profession')
        current_user.notifications_enabled = True if request.form.get('notifications') else False
        
        db.session.commit()
        flash('Your profile has been updated!', 'success')
        return redirect(url_for('main.dashboard'))
        
    return render_template('auth/edit_profile.html')

@auth.route('/toggle_verify')
@login_required
def toggle_verify():
    current_user.is_verified = not current_user.is_verified
    db.session.commit()
    status = "verified" if current_user.is_verified else "unverified"
    flash(f'Your account is now {status}!', 'info')
    return redirect(url_for('main.dashboard'))

@auth.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))

