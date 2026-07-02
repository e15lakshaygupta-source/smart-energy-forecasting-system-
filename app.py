from flask import Flask, render_template, request, redirect, url_for, session
import joblib
import pandas as pd
from datetime import datetime
import random
import sqlite3 
import csv 

from reportlab.pdfgen import canvas 

from flask import make_response

from reportlab.platypus import SimpleDocTemplate, Paragraph

from reportlab.lib.styles import getSampleStyleSheet 

app = Flask(__name__)
app.secret_key = "energy123"



# =====================================
# Prediction History
# =====================================
history = []

# =====================================
# Load ML Model
# =====================================
model = joblib.load("energy_model.pkl")

# =====================================
# Login
# =====================================
@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect("energy.db")
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        )

        user = cursor.fetchone()

        conn.close()

        if user:

            session['user'] = username

            return redirect(url_for('home'))

        return render_template(
            "login.html",
            error="Invalid Username or Password"
        )

    return render_template("login.html") 


# =====================================
# Register
# =====================================

@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect("energy.db")
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE username=?",
            (username,)
        )

        existing_user = cursor.fetchone()

        if existing_user:

            conn.close()

            return render_template(
                "register.html",
                error="Username Already Exists"
            )

        cursor.execute(
            "INSERT INTO users(username,password) VALUES (?,?)",
            (username, password)
        )

        conn.commit()
        conn.close()

        return redirect(url_for('login'))

    return render_template("register.html") 


# =====================================
# Logout
# =====================================
@app.route('/logout')
def logout():

    session.pop('user', None)

    return render_template("logout.html")


# =====================================
# Home
# =====================================
@app.route('/')
def home():

    if 'user' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect("energy.db")
    cursor = conn.cursor()

    # Total Predictions
    cursor.execute("""
        SELECT COUNT(*)
        FROM predictions
        WHERE username=?
    """, (session['user'],))

    total_predictions = cursor.fetchone()[0]

    # Average Consumption
    cursor.execute("""
        SELECT AVG(consumption)
        FROM predictions
        WHERE username=?
    """, (session['user'],))

    avg = cursor.fetchone()[0]

    if avg is None:
        avg = 0

    avg_consumption = round(avg, 2)

    # Highest Consumption
    cursor.execute("""
        SELECT MAX(consumption)
        FROM predictions
        WHERE username=?
    """, (session['user'],))

    highest = cursor.fetchone()[0]

    if highest is None:
        highest = 0

    highest_consumption = round(highest, 2)

    # Total Cost
    cursor.execute("""
        SELECT SUM(cost)
        FROM predictions
        WHERE username=?
    """, (session['user'],))

    total = cursor.fetchone()[0]

    if total is None:
        total = 0

    total_cost = round(total, 2)

    conn.close()

    return render_template(

        "index.html",

        total_predictions=total_predictions,

        avg_consumption=avg_consumption,

        highest_consumption=highest_consumption,

        total_cost=total_cost

    )


# =====================================
# Energy Prediction
# =====================================
@app.route('/predict', methods=['POST'])
def predict():

    if 'user' not in session:
        return redirect(url_for('login'))

    try:
        hour = int(request.form['hour'])
        days = int(request.form['days'])

        # ML Model Prediction
        input_data = pd.DataFrame({
            'Hour': [hour]
        })

        prediction = model.predict(input_data)

        consumption = round(float(prediction[0]), 2)

        # Usage Status
        if consumption < 4:
            status = "🟢 Low Usage"
        elif consumption <= 7:
            status = "🟡 Medium Usage"
        else:
            status = "🔴 High Usage"

        # Cost Calculation
        cost = round(consumption * 8, 2)

        monthly_bill = round(cost * days, 2)

        # Energy Saving Advice
        if consumption > 7:
            advice = """
• Turn off unused appliances
• Use LED bulbs
• Reduce AC usage during peak hours
• Unplug chargers when not in use
• Use Energy Efficient Appliances
"""
        else:
            advice = """
• Energy usage is normal
• Continue efficient consumption habits
• Monitor monthly consumption
"""

        # Current Date & Time
        prediction_date = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

        # Save Prediction to SQLite
        conn = sqlite3.connect("energy.db")
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO predictions
        (username, hour, consumption, cost, status, prediction_date)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            session['user'],
            hour,
            consumption,
            cost,
            status,
            prediction_date
        ))

        conn.commit()
        conn.close()

        return render_template(
            "result.html",
            consumption=consumption,
            cost=cost,
            monthly_bill=monthly_bill,
            status=status,
            advice=advice
        )

    except Exception as e:
        return f"Error: {e}" 


# =====================================
# Prediction History
# =====================================

@app.route('/history')
def prediction_history():

    if 'user' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect("energy.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT username,
               hour,
               consumption,
               cost,
               status,
               prediction_date
        FROM predictions
        WHERE username=?
        ORDER BY id DESC
    """, (session['user'],))

    history = cursor.fetchall()

    conn.close()

    return render_template(
        "history.html",
        history=history
    )


# =====================================
# Dashboard
# =====================================
@app.route('/dashboard')
def dashboard():

    if 'user' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect("energy.db")
    cursor = conn.cursor()

    username = session['user']

    # Total Predictions
    cursor.execute(
        "SELECT COUNT(*) FROM predictions WHERE username=?",
        (username,)
    )
    total_predictions = cursor.fetchone()[0]

    # Average Consumption
    cursor.execute(
        "SELECT AVG(consumption) FROM predictions WHERE username=?",
        (username,)
    )
    avg = cursor.fetchone()[0]
    avg_consumption = round(avg, 2) if avg else 0

    # Highest Consumption
    cursor.execute(
        "SELECT MAX(consumption) FROM predictions WHERE username=?",
        (username,)
    )
    highest = cursor.fetchone()[0]
    highest_consumption = highest if highest else 0

    # Total Cost
    cursor.execute(
        "SELECT SUM(cost) FROM predictions WHERE username=?",
        (username,)
    )
    total = cursor.fetchone()[0]
    total_cost = round(total, 2) if total else 0

    conn.close()

    return render_template(
        "dashboard.html",
        username=username,
        total_predictions=total_predictions,
        avg_consumption=avg_consumption,
        highest_consumption=highest_consumption,
        total_cost=total_cost
    ) 

# =====================================
# Export History CSV
# =====================================
@app.route('/export_csv')
def export_csv():

    if 'user' not in session:
        return redirect(url_for('login'))

    with open('prediction_history.csv', 'w', newline='') as file:

        writer = csv.writer(file)

        writer.writerow([
            'User',
            'Hour',
            'Consumption',
            'Cost',
            'Status',
            'Date'
        ])

        for item in history:

            writer.writerow([
                item['user'],
                item['hour'],
                item['consumption'],
                item['cost'],
                item['status'],
                item['date']
            ])

    return "CSV File Created Successfully!"


# =====================================
# Electricity Bill Page
# =====================================
@app.route('/bill')
def bill():

    if 'user' not in session:
        return redirect(url_for('login'))

    return render_template("bill.html")


# =====================================
# Generate Bill
# =====================================
@app.route('/generate_bill', methods=['POST'])
def generate_bill():

    if 'user' not in session:
        return redirect(url_for('login'))

    customer = request.form['customer']

    previous = float(request.form['previous'])
    current = float(request.form['current'])
    rate = float(request.form['rate'])

    units = current - previous

    if units < 0:
        return "Current Reading Must Be Greater Than Previous Reading"

    energy_charge = units * rate

    fixed_charge = 100

    duty = energy_charge * 0.05

    total_bill = energy_charge + fixed_charge + duty

    bill_no = random.randint(100000, 999999)

    bill_date = datetime.now().strftime("%d-%m-%Y")

    # =====================================
    # Save Bill Data for PDF Download
    # =====================================
    session['bill_data'] = {
        "bill_no": bill_no,
        "bill_date": bill_date,
        "customer": customer,
        "previous": previous,
        "current": current,
        "units": units,
        "rate": rate,
        "energy_charge": round(energy_charge, 2),
        "fixed_charge": fixed_charge,
        "duty": round(duty, 2),
        "total_bill": round(total_bill, 2)
    }

    return render_template(
        "bill_result.html",
        bill_no=bill_no,
        bill_date=bill_date,
        customer=customer,
        previous=previous,
        current=current,
        units=units,
        rate=rate,
        energy_charge=round(energy_charge, 2),
        fixed_charge=fixed_charge,
        duty=round(duty, 2),
        total_bill=round(total_bill, 2)
    )



# =====================================
# Download PDF Bill
# =====================================
@app.route('/download_bill')
def download_bill():

    if 'user' not in session:
        return redirect(url_for('login'))

    if 'bill_data' not in session:
        return "No bill available. Please generate a bill first."

    bill = session['bill_data']

    pdf = canvas.Canvas("static/Electricity_Bill.pdf")

    pdf.setTitle("Electricity Bill")

    # Company Name

    pdf.setFont("Helvetica-Bold", 22)

    pdf.drawString(
    100,
    800,
    "SMART ENERGY POWER CORPORATION"
)

    # Subtitle

    pdf.setFont("Helvetica", 12)

    pdf.drawString(
    180,
    780,
    "Electricity Consumption Bill"
)

    # Horizontal Line

    pdf.line(40, 765, 550, 765)


    # =====================================
    # Consumer Information
    # =====================================

    pdf.setFont("Helvetica-Bold", 14)

    pdf.drawString(50, 740, "Consumer Information")

    pdf.line(40, 730, 550, 730)

    pdf.setFont("Helvetica", 12)

    pdf.drawString(
    50,
    705,
    f"Consumer Name : {bill['customer']}"
)

    pdf.drawString(
    50,
    680,
    f"Bill Number : {bill['bill_no']}"
)

    pdf.drawString(
    320,
    680,
    f"Bill Date : {bill['bill_date']}"
)

    pdf.line(40, 660, 550, 660)  

    # =====================================
    # Meter Reading Details
    # =====================================

    pdf.setFont("Helvetica-Bold", 14)

    pdf.drawString(
    50,
    635,
    "Meter Reading Details"
)

    pdf.line(40, 625, 550, 625)

    pdf.setFont("Helvetica", 12)

    pdf.drawString(
    50,
    600,
    f"Previous Reading : {bill['previous']}"
)

    pdf.drawString(
    50,
    575,
    f"Current Reading : {bill['current']}"
)

    pdf.drawString(
    50,
    550,
    f"Units Consumed : {bill['units']}"
)

    pdf.line(40, 530, 550, 530)

# =====================================
# Charges Summary
# =====================================

    pdf.setFont("Helvetica-Bold", 14)

    pdf.drawString(
    50,
    505,
    "Charges Summary"
)

    pdf.line(40, 495, 550, 495)

    pdf.setFont("Helvetica", 12)

    pdf.drawString(
    50,
    470,
    f"Rate Per Unit : ₹{bill['rate']}"
)

    pdf.drawString(
    50,
    445,
    f"Energy Charge : ₹{bill['energy_charge']}"
)

    pdf.drawString(
    50,
    420,
    f"Fixed Charge : ₹{bill['fixed_charge']}"
)

    pdf.drawString(
    50,
    395,
    f"Electricity Duty : ₹{bill['duty']}"
)

    pdf.line(40, 380, 550, 380)



# =====================================
# Total Bill
# =====================================

    pdf.setFont("Helvetica-Bold", 18)

    pdf.drawString(
    50,
    345,
    f"TOTAL BILL AMOUNT : ₹{bill['total_bill']}"
)

    pdf.line(40, 330, 550, 330)

# =====================================
# Footer
# =====================================

    pdf.setFont("Helvetica", 11)

    pdf.drawString(
    50,
    300,
    "Thank you for using Smart Energy Forecasting System."
)

    pdf.drawString(
    50,
    280,
    "This is a computer-generated electricity bill."
)

    pdf.drawString(
    50,
    260,
    "Customer Care : 1800-123-4567"
)

    pdf.drawString(
    50,
    240,
    "Email : support@smartenergy.com"
)

    pdf.drawString(
    360,
    180,
    "Authorized Signature"
)

    pdf.line(340, 175, 520, 175)

    pdf.save()

    return redirect("/static/Electricity_Bill.pdf")


# =====================================
# Admin Panel
# =====================================

@app.route('/admin')
def admin():

    if 'user' not in session:
        return redirect(url_for('login'))

    if session['user'] != "admin":
        return "Access Denied"

    conn = sqlite3.connect("energy.db")
    cursor = conn.cursor()

    # Total Users
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    # Fetch All Users
    cursor.execute("SELECT username FROM users")
    users = cursor.fetchall() 

    # Fetch All Predictions

    cursor.execute("""

SELECT username,
       hour,
       consumption,
       cost,
       status,
       prediction_date

FROM predictions

ORDER BY prediction_date DESC

""")

    predictions = cursor.fetchall()


    
    # Total Predictions
    cursor.execute("SELECT COUNT(*) FROM predictions")
    total_predictions = cursor.fetchone()[0]

    # Total Revenue
    cursor.execute("SELECT SUM(cost) FROM predictions")
    revenue = cursor.fetchone()[0]

    if revenue is None:
        revenue = 0     

    total_revenue = round(revenue, 2)

    conn.close()

    return render_template(
    "admin.html",
    total_users=total_users,
    total_predictions=total_predictions,
    total_revenue=total_revenue,
    users=users,
    predictions=predictions
) 


# =====================================
# Run Application
# =====================================

if __name__ == "__main__":
 app.run(debug=True)                      