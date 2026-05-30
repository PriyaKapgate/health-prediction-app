
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import date, datetime
import requests

app = Flask(__name__)
app.config['SECRET_KEY'] = 'healthapp2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Patient(db.Model):
    id            = db.Column(db.Integer, primary_key=True)
    full_name     = db.Column(db.String(150), nullable=False)
    date_of_birth = db.Column(db.String(20),  nullable=False)
    email         = db.Column(db.String(150), nullable=False)
    glucose       = db.Column(db.Float,       nullable=False)
    haemoglobin   = db.Column(db.Float,       nullable=False)
    cholesterol   = db.Column(db.Float,       nullable=False)
    remarks       = db.Column(db.Text,        default='')

def get_health_prediction(name, dob, glucose, haemoglobin, cholesterol):
    api_key = "YOUR_OPENROUTER_API_KEY"
    url = "https://openrouter.ai/api/v1/chat/completions"

    prompt = f"""You are a medical AI assistant. Based on the following blood test results,
provide a brief health prediction (2-3 sentences max) about possible health risks or conditions.

Patient: {name}
Date of Birth: {dob}
Glucose level: {glucose} mg/dL
Haemoglobin: {haemoglobin} g/dL
Cholesterol: {cholesterol} mg/dL

Give a concise, non-alarming health assessment mentioning any possible risk areas."""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "openrouter/auto",
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        data = response.json()
        print("OpenRouter Response:", data)
        if "choices" in data:
            return data["choices"][0]["message"]["content"]
        elif "error" in data:
            return f"API Error: {data['error']['message']}"
        else:
            return f"Unexpected response: {str(data)}"
    except Exception as e:
        return f"Prediction unavailable: {str(e)}"

@app.route('/')
def index():
    patients = Patient.query.all()
    return render_template('index.html', patients=patients)

@app.route('/add', methods=['GET', 'POST'])
def add_patient():
    if request.method == 'POST':
        full_name     = request.form['full_name'].strip()
        date_of_birth = request.form['date_of_birth']
        email         = request.form['email'].strip()
        glucose       = request.form['glucose']
        haemoglobin   = request.form['haemoglobin']
        cholesterol   = request.form['cholesterol']

        errors = []

        if not full_name:
            errors.append("Full name is required.")

        if not date_of_birth:
            errors.append("Date of birth is required.")
        else:
            try:
                dob = datetime.strptime(date_of_birth, '%Y-%m-%d').date()
                if dob >= date.today():
                    errors.append("Date of birth cannot be today or a future date.")
            except ValueError:
                errors.append("Invalid date format.")

        if '@' not in email or '.' not in email.split('@')[-1]:
            errors.append("Please enter a valid email address.")

        try:
            glucose_val = float(glucose)
        except ValueError:
            errors.append("Glucose must be a numeric value.")
            glucose_val = None

        try:
            haemoglobin_val = float(haemoglobin)
        except ValueError:
            errors.append("Haemoglobin must be a numeric value.")
            haemoglobin_val = None

        try:
            cholesterol_val = float(cholesterol)
        except ValueError:
            errors.append("Cholesterol must be a numeric value.")
            cholesterol_val = None

        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('add.html')

        remarks = get_health_prediction(
            full_name, date_of_birth,
            glucose_val, haemoglobin_val, cholesterol_val
        )

        new_patient = Patient(
            full_name     = full_name,
            date_of_birth = date_of_birth,
            email         = email,
            glucose       = glucose_val,
            haemoglobin   = haemoglobin_val,
            cholesterol   = cholesterol_val,
            remarks       = remarks
        )
        db.session.add(new_patient)
        db.session.commit()
        flash('Patient record added successfully!', 'success')
        return redirect(url_for('index'))

    return render_template('add.html')

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_patient(id):
    patient = Patient.query.get_or_404(id)

    if request.method == 'POST':
        full_name     = request.form['full_name'].strip()
        date_of_birth = request.form['date_of_birth']
        email         = request.form['email'].strip()
        glucose       = request.form['glucose']
        haemoglobin   = request.form['haemoglobin']
        cholesterol   = request.form['cholesterol']

        errors = []

        if not full_name:
            errors.append("Full name is required.")

        if not date_of_birth:
            errors.append("Date of birth is required.")
        else:
            try:
                dob = datetime.strptime(date_of_birth, '%Y-%m-%d').date()
                if dob >= date.today():
                    errors.append("Date of birth cannot be today or a future date.")
            except ValueError:
                errors.append("Invalid date format.")

        if '@' not in email or '.' not in email.split('@')[-1]:
            errors.append("Please enter a valid email address.")

        try:
            glucose_val = float(glucose)
        except ValueError:
            errors.append("Glucose must be numeric.")
            glucose_val = None

        try:
            haemoglobin_val = float(haemoglobin)
        except ValueError:
            errors.append("Haemoglobin must be numeric.")
            haemoglobin_val = None

        try:
            cholesterol_val = float(cholesterol)
        except ValueError:
            errors.append("Cholesterol must be numeric.")
            cholesterol_val = None

        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('edit.html', patient=patient)

        remarks = get_health_prediction(
            full_name, date_of_birth,
            glucose_val, haemoglobin_val, cholesterol_val
        )

        patient.full_name     = full_name
        patient.date_of_birth = date_of_birth
        patient.email         = email
        patient.glucose       = glucose_val
        patient.haemoglobin   = haemoglobin_val
        patient.cholesterol   = cholesterol_val
        patient.remarks       = remarks

        db.session.commit()
        flash('Patient record updated successfully!', 'success')
        return redirect(url_for('index'))

    return render_template('edit.html', patient=patient)

@app.route('/delete/<int:id>', methods=['POST'])
def delete_patient(id):
    patient = Patient.query.get_or_404(id)
    db.session.delete(patient)
    db.session.commit()
    flash('Patient record deleted.', 'info')
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)