from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from models.models import db, User, Jewel, BorrowRequest
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'jewel_secret')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/jewel_system.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
db.init_app(app)

# Create database tables
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    jewels = Jewel.query.filter(Jewel.count > 0).all()
    return render_template('index.html', jewels=jewels)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        mobile = request.form['mobile']
        address = request.form['address']
        role = request.form.get('role', 'user')

        new_user = User(name=name, email=email, password=password, mobile=mobile, address=address, role=role)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! Please log in.')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['role'] = user.role
            flash('Login successful!')
            return redirect(url_for('index'))
        flash('Invalid credentials.')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.')
    return redirect(url_for('index'))

@app.route('/request/<int:jewel_id>', methods=['GET', 'POST'])
def request_jewel(jewel_id):
    if 'user_id' not in session:
        flash('Please log in to request a jewel.')
        return redirect(url_for('login'))

    jewel = Jewel.query.get_or_404(jewel_id)
    if request.method == 'POST':
        start_time = datetime.fromisoformat(request.form['start_time'])
        end_time = datetime.fromisoformat(request.form['end_time'])
        if start_time >= end_time:
            flash('End time must be after start time.')
            return render_template('request_jewel.html', jewel=jewel)
        if start_time < datetime.now():
            flash('Start time must be in the future.')
            return render_template('request_jewel.html', jewel=jewel)
        notes = request.form.get('notes', '')
        duration_hours = (end_time - start_time).total_seconds() / 3600
        calculated_amount = duration_hours * jewel.price_per_hour
        new_request = BorrowRequest(user_id=session['user_id'], jewel_id=jewel_id, start_time=start_time, end_time=end_time, notes=notes, calculated_amount=calculated_amount)
        db.session.add(new_request)
        db.session.commit()
        flash('Borrow request submitted!')
        return redirect(url_for('dashboard'))
    return render_template('request_jewel.html', jewel=jewel)

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    requests = BorrowRequest.query.filter_by(user_id=session['user_id']).all()
    return render_template('dashboard.html', requests=requests)

@app.route('/add_jewel', methods=['GET', 'POST'])
def add_jewel():
    if session.get('role') != 'admin':
        flash('Access denied.')
        return redirect(url_for('index'))

    if request.method == 'POST':
        name = request.form['name']
        category = request.form['category']
        description = request.form['description']
        price_per_hour = float(request.form['price_per_hour'])
        fine_per_hour = float(request.form['fine_per_hour'])
        count = int(request.form['count'])
        image_filename = None
        if 'image' in request.files:
            file = request.files['image']
            if file.filename != '':
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                image_filename = filename
        new_jewel = Jewel(name=name, category=category, description=description, price_per_hour=price_per_hour, fine_per_hour=fine_per_hour, count=count, image_filename=image_filename)
        db.session.add(new_jewel)
        db.session.commit()
        flash('Jewel added successfully!')
        return redirect(url_for('admin_manage'))

    return render_template('add_jewel.html')

@app.route('/admin/manage')
def admin_manage():
    if session.get('role') != 'admin':
        flash('Access denied.')
        return redirect(url_for('index'))

    jewels = Jewel.query.all()
    return render_template('admin_manage.html', jewels=jewels)

@app.route('/admin/requests')
def admin_requests():
    if session.get('role') != 'admin':
        flash('Access denied.')
        return redirect(url_for('index'))
    requests = BorrowRequest.query.all()
    return render_template('admin_requests.html', requests=requests)

@app.route('/admin/approve/<int:req_id>', methods=['POST'])
def approve_request(req_id):
    if session.get('role') != 'admin':
        flash('Access denied.')
        return redirect(url_for('index'))
    req = BorrowRequest.query.get_or_404(req_id)
    req.status = 'approved'
    jewel = Jewel.query.get(req.jewel_id)
    jewel.count -= 1
    db.session.commit()
    flash('Request approved!')
    return redirect(url_for('admin_requests'))

@app.route('/admin/reject/<int:req_id>', methods=['GET', 'POST'])
def reject_request(req_id):
    if session.get('role') != 'admin':
        flash('Access denied.')
        return redirect(url_for('index'))
    req = BorrowRequest.query.get_or_404(req_id)
    if request.method == 'POST':
        reason = request.form.get('reason', '')
        req.status = 'rejected'
        req.notes = reason  # Assuming notes can store rejection reason
        db.session.commit()
        flash('Request rejected!')
        return redirect(url_for('admin_requests'))
    return render_template('reject_request.html', req=req)

@app.route('/admin/mark_returned/<int:req_id>', methods=['POST'])
def mark_returned(req_id):
    if session.get('role') != 'admin':
        flash('Access denied.')
        return redirect(url_for('index'))
    req = BorrowRequest.query.get_or_404(req_id)
    if req.status == 'approved':
        req.status = 'returned'
        jewel = Jewel.query.get(req.jewel_id)
        jewel.count += 1
        # Calculate fine if overdue
        now = datetime.utcnow()
        if now > req.end_time:
            overdue_hours = (now - req.end_time).total_seconds() / 3600
            req.fine_amount = overdue_hours * jewel.fine_per_hour
        db.session.commit()
        flash('Jewel marked as returned!')
    return redirect(url_for('admin_requests'))

@app.route('/edit_jewel/<int:jewel_id>', methods=['GET', 'POST'])
def edit_jewel(jewel_id):
    if session.get('role') != 'admin':
        flash('Access denied.')
        return redirect(url_for('index'))
    jewel = Jewel.query.get_or_404(jewel_id)
    if request.method == 'POST':
        jewel.name = request.form['name']
        jewel.category = request.form['category']
        jewel.description = request.form['description']
        jewel.price_per_hour = float(request.form['price_per_hour'])
        jewel.fine_per_hour = float(request.form['fine_per_hour'])
        jewel.count = int(request.form['count'])
        if 'image' in request.files:
            file = request.files['image']
            if file.filename != '':
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                jewel.image_filename = filename
        db.session.commit()
        flash('Jewel updated!')
        return redirect(url_for('admin_manage'))
    return render_template('edit_jewel.html', jewel=jewel)

@app.route('/delete_jewel/<int:jewel_id>', methods=['POST'])
def delete_jewel(jewel_id):
    if session.get('role') != 'admin':
        flash('Access denied.')
        return redirect(url_for('index'))
    jewel = Jewel.query.get_or_404(jewel_id)
    db.session.delete(jewel)
    db.session.commit()
    flash('Jewel deleted!')
    return redirect(url_for('admin_manage'))

@app.route('/uploaded_file/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
