from flask import Blueprint, render_template, session, redirect, url_for
from db import get_db_connection

vhan_bp = Blueprint('vhan', __name__)

@vhan_bp.route('/vhan/dashboard')
def vhan_dashboard():
    if session.get('role') != 'vhan_admin':
        return redirect(url_for('login.login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    
    cursor.execute("""
        SELECT
        id,
        company_name,
        industry,
        company_size,
        company_number,    
        contact_person,
        position_title,
        contact_number,
        work_email,
        status,
        created_at
    FROM access_requests
    WHERE status = 'pending'
    ORDER BY created_at DESC
""")

    requests = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('vhan_dashboard.html', requests=requests)



@vhan_bp.route('/vhan/approve/<int:req_id>')
def approve_request(req_id):
    if session.get('role') != 'vhan_admin':
        return redirect(url_for('login.login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # get request data
    cursor.execute("SELECT * FROM access_requests WHERE id = %s", (req_id,))
    req = cursor.fetchone()

    # insert to organizations
    cursor.execute("""
        INSERT INTO organizations (company_name, industry, company_size, company_number)
        VALUES (%s, %s, %s, %s)
    """, (
        req['company_name'],
        req['industry'],
        req['company_size'],
        req['company_number']
    ))

    org_id = cursor.lastrowid

    # insert to users
    cursor.execute("""
        INSERT INTO users (
            organization_id,
            contact_person,
            work_email,
            password_hash,
            role,
            status,
            contact_number,
            position_title
        )
        VALUES (%s, %s, %s, %s, 'org_admin', 'approved', %s, %s)
    """, (
        org_id,
        req['contact_person'],
        req['work_email'],
        req['password_hash'],
        req['contact_number'],
        req['position_title']
    ))

    # update request
    cursor.execute("""
        UPDATE access_requests
        SET status = 'approved'
        WHERE id = %s
    """, (req_id,))

    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for('vhan.vhan_dashboard'))

@vhan_bp.route('/vhan/pending-approvals')
def pending_approvals():
    if session.get('role') != 'vhan_admin':
        return redirect(url_for('login.login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            id,
            company_name,
            industry,
            company_size,
            company_number,
            contact_person,
            position_title,
            contact_number,
            work_email,
            status,
            created_at
        FROM access_requests
        WHERE status = 'pending'
        ORDER BY created_at DESC
    """)

    requests = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('pending_approvals.html', requests=requests)