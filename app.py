# app.py
import os
import sqlite3
from flask import Flask, render_template, request, jsonify, g
from sklearn.ensemble import RandomForestClassifier
import numpy as np

app = Flask(__name__, static_folder='.', template_folder='.')

# --- Database Setup ---
DATABASE = 'smart_health_db.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

# --- Machine Learning Pipeline ---
class HealthRiskModel:
    def __init__(self):
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self._train_dummy_model()

    def _train_dummy_model(self):
        X_train = np.array([
            [30, 115, 85, 0, 2], [40, 125, 95, 0, 1], [50, 135, 105, 1, 0], 
            [25, 110, 80, 0, 2], [35, 118, 88, 0, 2], [28, 112, 82, 0, 2], 
            [60, 160, 150, 1, 0], [55, 155, 140, 1, 0], [65, 170, 160, 1, 0] 
        ])
        y_train = np.array([0, 0, 1, 0, 0, 0, 2, 2, 2])
        self.model.fit(X_train, y_train)

    def predict(self, age, systolic_bp, glucose, smoking, activity):
        smoke_val = 1 if smoking == 'Active smoker' else 0
        act_val = 2 if 'Active' in activity else (1 if 'Moderate' in activity else 0)
        
        features = np.array([[age, systolic_bp, glucose, smoke_val, act_val]])
        proba = self.model.predict_proba(features)[0]
        
        risk_score = int((proba[1] * 50) + (proba[2] * 100))
        return risk_score

ml_model = HealthRiskModel()

# --- HTML Route (Only need one now) ---

@app.route('/')
def index():
    """Serves the Single Page Application."""
    return render_template('index.html')

# --- API Routes ---

@app.route('/api/predict', methods=['POST'])
def predict():
    data = request.json
    try:
        age = int(data.get('age', 0))
        systolic_bp = int(data.get('systolic_bp', 0))
        glucose = int(data.get('glucose', 0))
        smoking = data.get('smoking', 'Never smoked')
        activity = data.get('activity', 'Low')

        risk_score = ml_model.predict(age, systolic_bp, glucose, smoking, activity)
        
        if risk_score > 75:
            status = "Action recommended"
            alert_msg = "High risk detected. Please consult a healthcare professional."
        elif risk_score > 40:
            status = "Mild caution"
            alert_msg = "Moderate risk. Monitor your vitals closely."
        else:
            status = "Optimal baseline"
            alert_msg = "Vitals look good. Keep up the healthy habits."

        db = get_db()
        cur = db.cursor()
        
        cur.execute('''
            INSERT INTO health_records (user_id, age, systolic_bp, fasting_glucose, smoking_history, physical_activity, risk_score, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (1, age, systolic_bp, glucose, smoking, activity, risk_score, status))
        
        record_id = cur.lastrowid

        if risk_score > 75:
            cur.execute('''
                INSERT INTO alerts (user_id, record_id, alert_type, message, severity)
                VALUES (?, ?, ?, ?, ?)
            ''', (1, record_id, 'Vital Alert', alert_msg, 'urgent'))
        elif risk_score > 40:
            cur.execute('''
                INSERT INTO alerts (user_id, record_id, alert_type, message, severity)
                VALUES (?, ?, ?, ?, ?)
            ''', (1, record_id, 'Vital Alert', alert_msg, 'watch'))

        db.commit()

        return jsonify({
            "status": "success",
            "risk_score": risk_score,
            "status_label": status,
            "message": alert_msg
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/api/history', methods=['GET'])
def get_history():
    db = get_db()
    cur = db.execute('SELECT * FROM health_records WHERE user_id = 1 ORDER BY record_date DESC LIMIT 10')
    records = [dict(row) for row in cur.fetchall()]
    return jsonify(records)

# --- DEPLOYMENT CONFIGURATION ---
if not os.path.exists(DATABASE):
    init_db()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)