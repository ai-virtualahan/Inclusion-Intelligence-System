from flask import Blueprint, render_template, session, redirect, url_for

super_admin_bp = Blueprint('super_admin', __name__)

@super_admin_bp.route('/super-admin/dashboard')

def super_admin_dash():
    if session.get('role') != 'super_admin':
        return redirect(url_for('login.login'))

    return render_template('super_admin_dash.html')