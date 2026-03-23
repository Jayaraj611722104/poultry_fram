from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User
from app import db

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/', methods=['GET', 'POST'])
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('farms.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('farms.index'))
        flash('Invalid username or password', 'danger')

    show_register = User.query.count() == 0
    return render_template('auth/login.html', show_register=show_register)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if User.query.count() > 0:
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if getattr(current_user, 'role', 'user') != 'admin':
            flash('Only admins can register new users', 'danger')
            return redirect(url_for('farms.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        role = request.form.get('role', 'user')

        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return render_template('auth/register.html')

        user = User(username=username, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('User created successfully', 'success')
        
        if current_user.is_authenticated and getattr(current_user, 'role', 'user') == 'admin':
            return redirect(url_for('auth.users'))
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')


@auth_bp.route('/users')
@login_required
def users():
    if getattr(current_user, 'role', 'user') != 'admin':
        flash('Only admins can view users', 'danger')
        return redirect(url_for('farms.index'))
    all_users = User.query.all()
    return render_template('auth/users.html', users=all_users)


@auth_bp.route('/users/delete/<int:uid>', methods=['POST'])
@login_required
def delete_user(uid):
    if getattr(current_user, 'role', 'user') != 'admin':
        flash('Only admins can delete users', 'danger')
        return redirect(url_for('farms.index'))
        
    user = User.query.get_or_404(uid)
    if user.id == current_user.id:
        flash('Cannot delete yourself', 'danger')
        return redirect(url_for('auth.users'))
    db.session.delete(user)
    db.session.commit()
    flash('User deleted', 'success')
    return redirect(url_for('auth.users'))


@auth_bp.route('/reset-password', methods=['GET', 'POST'])
@login_required
def reset_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        if current_user.check_password(current_password):
            current_user.set_password(new_password)
            db.session.commit()
            flash('Password updated successfully', 'success')
            return redirect(url_for('farms.index'))
        flash('Current password is incorrect', 'danger')

    return render_template('auth/reset_password.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
