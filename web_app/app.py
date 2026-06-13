import os
import sys
import json
import subprocess
from datetime import datetime
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_session import Session
from database import init_db, user_exists, create_user, get_user, get_user_by_id, add_history, get_user_history, delete_history_record, get_prediction_count, get_connection

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.secret_key = 'your-secret-key-change-in-production'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

Session(app)

ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}
IMG_SIZE = (224, 224)

# Disease descriptions
DISEASE_INFO = {
    'Acne and Rosacea Photos': {
        'description': 'Skin condition causing pimples and redness.',
        'symptoms': 'Red bumps, whiteheads, blackheads, itching',
        'causes': 'Bacteria, hormones, excess oil',
        'treatment': 'Topical retinoids, antibiotics, isotretinoin',
        'prevention': 'Keep skin clean, avoid irritants, moisturize',
        'consult': 'If severe or affecting quality of life'
    },
    'Atopic Dermatitis Photos': {
        'description': 'Chronic inflammatory skin condition causing itching and irritation.',
        'symptoms': 'Intense itching, dry skin, rashes, cracking',
        'causes': 'Genetics, immune system dysfunction',
        'treatment': 'Moisturizers, topical steroids, antihistamines',
        'prevention': 'Use fragrance-free products, avoid triggers',
        'consult': 'If symptoms worsen or cover large areas'
    },
    'Chickenpox': {
        'description': 'Highly contagious viral infection causing fluid-filled blisters.',
        'symptoms': 'Blisters, fever, fatigue, itching',
        'causes': 'Varicella-zoster virus',
        'treatment': 'Antivirals, pain relievers, calamine lotion',
        'prevention': 'Vaccination (varicella vaccine)',
        'consult': 'Immediately, especially if immunocompromised'
    },
    'Measles': {
        'description': 'Highly contagious viral infection with characteristic rash.',
        'symptoms': 'Rash, fever, cough, runny nose, Koplik spots',
        'causes': 'Measles virus',
        'treatment': 'Supportive care, vitamin A, fever management',
        'prevention': 'MMR vaccination',
        'consult': 'Immediately'
    },
    'Melanoma Skin Cancer Nevi and Moles': {
        'description': 'Potentially serious form of skin cancer.',
        'symptoms': 'Irregular moles, color variation, asymmetry, bleeding',
        'causes': 'Sun exposure, genetics, UV radiation',
        'treatment': 'Surgical removal, chemotherapy, immunotherapy',
        'prevention': 'Sunscreen, limit sun exposure, protective clothing',
        'consult': 'Immediately if suspected'
    },
    'Psoriasis pictures Lichen Planus and related diseases': {
        'description': 'Chronic autoimmune skin condition with scaling.',
        'symptoms': 'Red patches, silvery scales, itching, burning',
        'causes': 'Immune system dysfunction, genetics',
        'treatment': 'Topical steroids, phototherapy, systemic therapy',
        'prevention': 'Stress management, skin protection',
        'consult': 'If affecting large body areas'
    },
    'Tinea Ringworm Candidiasis and other Fungal Infections': {
        'description': 'Fungal infections causing itching and rashes.',
        'symptoms': 'Ring-shaped rash, itching, redness, scaling',
        'causes': 'Fungal pathogens',
        'treatment': 'Antifungal creams, oral antifungals',
        'prevention': 'Keep skin dry, avoid shared facilities',
        'consult': 'If spreading or not improving'
    },
    'Warts Molluscum and other Viral Infections': {
        'description': 'Viral skin growths that are usually benign.',
        'symptoms': 'Small growths, bumps, sometimes itching',
        'causes': 'HPV virus and other viral infections',
        'treatment': 'Topical treatments, removal, cryotherapy',
        'prevention': 'Avoid direct contact, maintain hygiene',
        'consult': 'For removal or if concerned'
    },
    'Urticaria Hives': {
        'description': 'Sudden outbreak of itchy welts on the skin.',
        'symptoms': 'Welts, itching, burning sensation',
        'causes': 'Allergic reaction, stress, temperature',
        'treatment': 'Antihistamines, corticosteroids, identify triggers',
        'prevention': 'Avoid triggers, stress management',
        'consult': 'If severe or affecting breathing'
    }
}

# Skin care information
SKIN_TYPES = {
    'Normal Skin': {
        'description': 'Balanced skin with minimal imperfections.',
        'daily_care': 'Maintain natural balance with gentle products',
        'morning': 'Cleanse, tone, moisturize with SPF',
        'night': 'Cleanse, tone, apply night cream',
        'dos': 'Use gentle products, stay hydrated, protect from sun',
        'donts': 'Avoid over-washing, harsh scrubs, extreme temperatures'
    },
    'Oily Skin': {
        'description': 'Skin with excess sebum production.',
        'daily_care': 'Control oil while maintaining hydration',
        'morning': 'Use oil-control cleanser, light moisturizer, SPF',
        'night': 'Gentle cleanser, oil-free night treatment',
        'dos': 'Use water-based products, cleanse twice daily, exfoliate',
        'donts': 'Avoid heavy oils, skip moisturizer, over-cleanse'
    },
    'Dry Skin': {
        'description': 'Skin lacking moisture and natural oils.',
        'daily_care': 'Nourish and hydrate constantly',
        'morning': 'Hydrating cleanser, rich moisturizer, SPF',
        'night': 'Gentle cleanser, intensive moisturizer, face oil',
        'dos': 'Use rich creams, apply moisturizer on damp skin, humidify',
        'donts': 'Avoid harsh cleansers, hot water, alcohol-based products'
    },
    'Combination Skin': {
        'description': 'Mix of oily and dry areas on the face.',
        'daily_care': 'Balance hydration across different zones',
        'morning': 'Balanced cleanser, light moisturizer, SPF',
        'night': 'Gentle cleanser, zone-appropriate moisturizers',
        'dos': 'Use different products for T-zone and cheeks, hydrate',
        'donts': 'Avoid one-product-fits-all approach, over-treat'
    },
    'Sensitive Skin': {
        'description': 'Easily irritated skin prone to reactions.',
        'daily_care': 'Use hypoallergenic and fragrance-free products',
        'morning': 'Gentle cleanser, soothing moisturizer, SPF 30+',
        'night': 'Non-irritating cleanser, calming night cream',
        'dos': 'Patch test products, use minimal ingredients, soothe regularly',
        'donts': 'Avoid fragrance, chemicals, hot water, frequent changes'
    }
}

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

PREDECT_SCRIPT = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'predect.py')

# Admin credentials
ADMIN_CREDENTIALS = {
    'username': 'admin',
    'password': 'admin@2024'  # Change this in production!
}

# Admin registration code (change this in production)
ADMIN_REGISTRATION_CODE = 'admin2024'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.before_request
def before_request():
    session.permanent = True

@app.route('/')
def index():
    if 'admin_id' in session:
        return redirect(url_for('admin_dashboard'))
    if 'user_id' in session:
        return redirect(url_for('home'))
    return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        data = request.get_json()
        
        email = data.get('email', '').strip()
        age = data.get('age', '')
        gender = data.get('gender', '').strip()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        confirm_password = data.get('confirm_password', '').strip()
        signup_type = data.get('signup_type', 'user').strip()
        admin_code = data.get('admin_code', '').strip() if signup_type == 'admin' else None
        
        if not all([email, age, gender, username, password, confirm_password]):
            return jsonify({'success': False, 'message': 'All fields required'}), 400
        
        if password != confirm_password:
            return jsonify({'success': False, 'message': 'Passwords do not match'}), 400
        
        if len(password) < 6:
            return jsonify({'success': False, 'message': 'Password must be at least 6 characters'}), 400
        
        if user_exists(username=username):
            return jsonify({'success': False, 'message': 'Username already taken'}), 400
        
        if user_exists(email=email):
            return jsonify({'success': False, 'message': 'Email already used'}), 400
        
        # Admin signup validation
        if signup_type == 'admin':
            if not admin_code or admin_code != ADMIN_REGISTRATION_CODE:
                return jsonify({'success': False, 'message': 'Invalid admin registration code'}), 400
        
        try:
            age = int(age)
            if age < 1 or age > 150:
                return jsonify({'success': False, 'message': 'Invalid age'}), 400
        except:
            return jsonify({'success': False, 'message': 'Invalid age'}), 400
        
        is_admin = (signup_type == 'admin')
        if create_user(email, age, gender, username, password, is_admin=is_admin):
            account_type = 'Admin account' if is_admin else 'Account'
            return jsonify({'success': True, 'message': f'{account_type} created successfully'}), 201
        else:
            return jsonify({'success': False, 'message': 'Error creating account'}), 500
    
    return render_template('signup.html')

@app.route('/admin/signup', methods=['GET', 'POST'])
def admin_signup():
    """Dedicated admin signup page"""
    if request.method == 'POST':
        data = request.get_json()
        
        email = data.get('email', '').strip()
        age = data.get('age', '')
        gender = data.get('gender', '').strip()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        confirm_password = data.get('confirm_password', '').strip()
        admin_code = data.get('admin_code', '').strip()
        
        if not all([email, age, gender, username, password, confirm_password, admin_code]):
            return jsonify({'success': False, 'message': 'All fields are required'}), 400
        
        if password != confirm_password:
            return jsonify({'success': False, 'message': 'Passwords do not match'}), 400
        
        if len(password) < 8:
            return jsonify({'success': False, 'message': 'Password must be at least 8 characters'}), 400
        
        if user_exists(username=username):
            return jsonify({'success': False, 'message': 'Username already taken'}), 400
        
        if user_exists(email=email):
            return jsonify({'success': False, 'message': 'Email already registered'}), 400
        
        # Validate admin registration code
        if admin_code != ADMIN_REGISTRATION_CODE:
            return jsonify({'success': False, 'message': 'Invalid admin registration code'}), 400
        
        # Age validation
        try:
            age = int(age)
            if age < 18 or age > 150:
                return jsonify({'success': False, 'message': 'Admin must be at least 18 years old'}), 400
        except:
            return jsonify({'success': False, 'message': 'Invalid age'}), 400
        
        # Create admin account
        if create_user(email, age, gender, username, password, is_admin=True):
            return jsonify({'success': True, 'message': 'Admin account created successfully. Please login.'}), 201
        else:
            return jsonify({'success': False, 'message': 'Error creating admin account'}), 500
    
    return render_template('admin_signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        login_type = data.get('login_type', 'user').strip()
        
        if not username or not password:
            return jsonify({'success': False, 'message': 'Username and password required'}), 400
        
        user = get_user(username)
        
        # Admin Login
        if login_type == 'admin':
            if user and user['is_admin'] and check_password_hash(user['password'], password):
                session['admin_id'] = user['id']
                session['admin_username'] = username
                session['is_admin'] = True
                return jsonify({'success': True, 'message': 'Admin login successful'}), 200
            else:
                return jsonify({'success': False, 'message': 'Invalid admin credentials'}), 401
        
        # User Login
        else:
            if user and not user['is_admin'] and check_password_hash(user['password'], password):
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['is_admin'] = False
                return jsonify({'success': True, 'message': 'Login successful'}), 200
            elif user and user['is_admin']:
                return jsonify({'success': False, 'message': 'Please use admin login'}), 401
            else:
                return jsonify({'success': False, 'message': 'Invalid username or password'}), 401
    
    return render_template('login.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Dedicated admin login page"""
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        if not username or not password:
            return jsonify({'success': False, 'message': 'Username and password required'}), 400
        
        user = get_user(username)
        
        if user and user['is_admin'] and check_password_hash(user['password'], password):
            session['admin_id'] = user['id']
            session['admin_username'] = username
            session['is_admin'] = True
            return jsonify({'success': True, 'message': 'Welcome to Admin Dashboard'}), 200
        else:
            return jsonify({'success': False, 'message': 'Invalid admin credentials'}), 401
    
    return render_template('admin_login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/home')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('home.html', username=session.get('username'), skin_types=SKIN_TYPES)

@app.route('/predict', methods=['GET', 'POST'])
def predict():
    if 'user_id' not in session:
        if request.method == 'POST':
            return jsonify({'success': False, 'message': 'Not logged in'}), 401
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'message': 'Invalid file type. Use JPG, JPEG, or PNG'}), 400
        
        filepath = None
        try:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Call predect.py script
            if not os.path.exists(PREDECT_SCRIPT):
                return jsonify({'success': False, 'message': 'Prediction script not found'}), 500
            
            result = subprocess.run(
                [sys.executable, PREDECT_SCRIPT, filepath],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                error_msg = result.stderr or result.stdout
                return jsonify({'success': False, 'message': f'Error: {error_msg}'}), 500
            
            try:
                prediction_data = json.loads(result.stdout)
            except json.JSONDecodeError:
                return jsonify({'success': False, 'message': 'Invalid response from prediction model'}), 500
            
            if 'error' in prediction_data:
                return jsonify({'success': False, 'message': prediction_data['error']}), 500
            
            predicted_disease = prediction_data.get('predicted_disease', 'Unknown')
            confidence = prediction_data.get('confidence', 0) * 100
            
            disease_info = DISEASE_INFO.get(predicted_disease, {})
            
            add_history(session['user_id'], filename, predicted_disease, confidence)
            
            return jsonify({
                'success': True,
                'disease': predicted_disease,
                'confidence': f'{confidence:.2f}',
                'description': disease_info.get('description', 'No description available'),
                'treatment': disease_info.get('treatment', 'Consult a dermatologist'),
                'prevention': disease_info.get('prevention', 'Follow dermatologist recommendations')
            }), 200
        
        except subprocess.TimeoutExpired:
            return jsonify({'success': False, 'message': 'Prediction took too long. Please try again.'}), 500
        except Exception as e:
            return jsonify({'success': False, 'message': f'Error processing image: {str(e)}'}), 500
        finally:
            if filepath and os.path.exists(filepath):
                os.remove(filepath)
    
    return render_template('predict.html')

@app.route('/about')
def about():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('about.html', diseases=DISEASE_INFO)

@app.route('/history')
def history():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_history = get_user_history(session['user_id'])
    history_list = [
        {
            'id': h['id'],
            'image_name': h['image_name'],
            'disease': h['disease'],
            'confidence': f"{h['confidence']:.2f}",
            'date': h['date']
        }
        for h in user_history
    ]
    
    return render_template('history.html', history=history_list)

@app.route('/delete-history/<int:record_id>', methods=['POST'])
def delete_history(record_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    if delete_history_record(record_id, session['user_id']):
        return jsonify({'success': True, 'message': 'Record deleted'}), 200
    else:
        return jsonify({'success': False, 'message': 'Error deleting record'}), 500

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = get_user_by_id(session['user_id'])
    prediction_count = get_prediction_count(session['user_id'])
    
    return render_template('profile.html', 
                         username=user['username'],
                         email=user['email'],
                         age=user['age'],
                         gender=user['gender'],
                         prediction_count=prediction_count)

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'admin_id' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))
    
    # Get statistics
    conn = get_connection()
    cursor = conn.cursor()
    
    # Total users
    cursor.execute('SELECT COUNT(*) as count FROM users')
    total_users = cursor.fetchone()['count']
    
    # Total predictions
    cursor.execute('SELECT COUNT(*) as count FROM history')
    total_predictions = cursor.fetchone()['count']
    
    # Most common disease
    cursor.execute('''
        SELECT disease, COUNT(*) as count FROM history 
        GROUP BY disease ORDER BY count DESC LIMIT 5
    ''')
    top_diseases = cursor.fetchall()
    
    # Recent predictions
    cursor.execute('''
        SELECT h.id, h.image_name, h.disease, h.confidence, h.date, u.username
        FROM history h
        JOIN users u ON h.user_id = u.id
        ORDER BY h.date DESC LIMIT 10
    ''')
    recent_predictions = cursor.fetchall()
    
    conn.close()
    
    return render_template('admin_dashboard.html', 
                         admin_username=session.get('admin_username'),
                         total_users=total_users,
                         total_predictions=total_predictions,
                         top_diseases=top_diseases,
                         recent_predictions=recent_predictions)

@app.route('/admin/users')
def admin_users():
    if 'admin_id' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, email, age, gender, created_at FROM users ORDER BY created_at DESC')
    users = cursor.fetchall()
    conn.close()
    
    return render_template('admin_users.html', 
                         admin_username=session.get('admin_username'),
                         users=users)
    

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
