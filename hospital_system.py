from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
from datetime import datetime, date
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

class HospitalSystem:
    def __init__(self):
        self.conn = None
        self.cursor = None
        
    def connect_db(self):
        """Connect to MySQL database"""
        try:
            self.conn = mysql.connector.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                user=os.getenv('DB_USER', 'root'),
                password=os.getenv('DB_PASSWORD', ''),
                database=os.getenv('DB_NAME', 'hospital_db')
            )
            if self.conn.is_connected():
                self.cursor = self.conn.cursor(dictionary=True)
                print("✓ Connected to MySQL database successfully!")
                return True
        except Error as e:
            print(f"✗ Error connecting to database: {e}")
            return False
    
    def get_db_connection(self):
        """Get database connection for each request"""
        if not self.conn or not self.conn.is_connected():
            if not self.connect_db():
                return None, None
        return self.conn, self.cursor

# Initialize the system
hospital_system = HospitalSystem()

# Helper function to check database connection
def check_db_connection():
    conn, cursor = hospital_system.get_db_connection()
    if conn is None:
        return False, "Database connection failed"
    return True, "Database connected successfully"

# Helper function to create tables if they don't exist
def create_tables_if_not_exist():
    try:
        conn, cursor = hospital_system.get_db_connection()
        if conn is None:
            return False
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS patients (
                id INT AUTO_INCREMENT PRIMARY KEY,
                patient_name VARCHAR(100) NOT NULL,
                age INT NOT NULL,
                gender VARCHAR(10) NOT NULL,
                contact VARCHAR(15) NOT NULL,
                address TEXT,
                disease VARCHAR(100),
                admission_date DATE,
                discharge_date DATE,
                status VARCHAR(20) DEFAULT 'Admitted',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        print("✓ Patients table verified/created successfully!")
        return True
    except Error as e:
        print(f"✗ Error creating table: {e}")
        return False

# Helper function to convert database rows to JSON-serializable format
def convert_row_to_json(row):
    """Convert database row to JSON-serializable format"""
    if not row:
        return row
    
    result = {}
    for key, value in row.items():
        if isinstance(value, (datetime, date)):
            result[key] = value.strftime('%Y-%m-%d')
        else:
            result[key] = value
    return result

# API Routes
@app.route('/')
def index():
    db_status, db_message = check_db_connection()
    return jsonify({
        "message": "Hospital Patient Record System API",
        "status": "active",
        "database_status": db_status,
        "database_message": db_message,
        "endpoints": {
            "GET /api/patients": "Get all patients",
            "GET /api/patients/<id>": "Get patient by ID",
            "POST /api/patients": "Add new patient",
            "PUT /api/patients/<id>": "Update patient",
            "DELETE /api/patients/<id>": "Delete patient",
            "GET /api/patients/search/<query>": "Search patients",
            "GET /api/stats": "Get system statistics",
            "GET /api/patients/status/<status>": "Get patients by status",
            "POST /api/patients/<id>/discharge": "Discharge patient",
            "GET /api/health": "Health check",
            "POST /api/init": "Initialize database tables"
        }
    })

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get system statistics"""
    try:
        conn, cursor = hospital_system.get_db_connection()
        if conn is None:
            return jsonify({"error": "Database connection failed"}), 500
        
        # Get total patients
        cursor.execute("SELECT COUNT(*) as total FROM patients")
        total = cursor.fetchone()['total']
        
        # Get admitted patients
        cursor.execute("SELECT COUNT(*) as admitted FROM patients WHERE status = 'Admitted'")
        admitted = cursor.fetchone()['admitted']
        
        # Get discharged patients
        cursor.execute("SELECT COUNT(*) as discharged FROM patients WHERE status = 'Discharged'")
        discharged = cursor.fetchone()['discharged']
        
        # Get today's admissions
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute("SELECT COUNT(*) as today FROM patients WHERE admission_date = %s", (today,))
        today_result = cursor.fetchone()
        today_admissions = today_result['today'] if today_result else 0
        
        return jsonify({
            "total_patients": total or 0,
            "admitted": admitted or 0,
            "discharged": discharged or 0,
            "today_admissions": today_admissions or 0,
            "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
    except Error as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/patients', methods=['GET'])
def get_all_patients():
    """Get all patients"""
    try:
        conn, cursor = hospital_system.get_db_connection()
        if conn is None:
            return jsonify({"error": "Database connection failed"}), 500
        
        # Get query parameters
        search = request.args.get('search', '')
        limit = int(request.args.get('limit', 100))
        
        if search:
            # Try to convert search to integer for ID search
            try:
                patient_id = int(search)
                cursor.execute("SELECT * FROM patients WHERE id = %s ORDER BY id DESC LIMIT %s", (patient_id, limit))
            except ValueError:
                # Search by name if not a number
                cursor.execute("SELECT * FROM patients WHERE patient_name LIKE %s ORDER BY id DESC LIMIT %s", 
                             (f"%{search}%", limit))
        else:
            cursor.execute("SELECT * FROM patients ORDER BY id DESC LIMIT %s", (limit,))
        
        patients = cursor.fetchall()
        
        # Convert all rows to JSON-serializable format
        serializable_patients = []
        for patient in patients:
            serializable_patients.append(convert_row_to_json(patient))
        
        return jsonify({
            "count": len(serializable_patients),
            "patients": serializable_patients
        })
        
    except Error as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/patients/<int:patient_id>', methods=['GET'])
def get_patient(patient_id):
    """Get patient by ID"""
    try:
        conn, cursor = hospital_system.get_db_connection()
        if conn is None:
            return jsonify({"error": "Database connection failed"}), 500
        
        cursor.execute("SELECT * FROM patients WHERE id = %s", (patient_id,))
        patient = cursor.fetchone()
        
        if not patient:
            return jsonify({"error": "Patient not found"}), 404
        
        # Convert to JSON-serializable format
        serializable_patient = convert_row_to_json(patient)
        
        return jsonify(serializable_patient)
        
    except Error as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/patients', methods=['POST'])
def add_patient():
    """Add new patient"""
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['patient_name', 'age', 'gender', 'contact', 'disease']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        conn, cursor = hospital_system.get_db_connection()
        if conn is None:
            return jsonify({"error": "Database connection failed"}), 500
        
        # Set admission date to today if not provided
        admission_date = data.get('admission_date')
        if not admission_date:
            admission_date = datetime.now().strftime('%Y-%m-%d')
        
        query = """
            INSERT INTO patients (patient_name, age, gender, contact, address, disease, admission_date, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'Admitted')
        """
        values = (
            data['patient_name'].strip(),
            int(data['age']),
            data['gender'].strip(),
            data['contact'].strip(),
            data.get('address', '').strip(),
            data['disease'].strip(),
            admission_date
        )
        
        cursor.execute(query, values)
        conn.commit()
        
        return jsonify({
            "message": "Patient added successfully!",
            "patient_id": cursor.lastrowid
        }), 201
        
    except Error as e:
        return jsonify({"error": str(e)}), 500
    except ValueError as e:
        return jsonify({"error": f"Invalid data format: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/patients/<int:patient_id>', methods=['PUT'])
def update_patient(patient_id):
    """Update patient details"""
    try:
        data = request.json
        
        conn, cursor = hospital_system.get_db_connection()
        if conn is None:
            return jsonify({"error": "Database connection failed"}), 500
        
        # Check if patient exists
        cursor.execute("SELECT * FROM patients WHERE id = %s", (patient_id,))
        patient = cursor.fetchone()
        
        if not patient:
            return jsonify({"error": "Patient not found"}), 404
        
        # Build update query dynamically
        updates = []
        values = []
        
        # Fields that can be updated
        if 'patient_name' in data and data['patient_name'] is not None:
            updates.append("patient_name = %s")
            values.append(data['patient_name'].strip())
        
        if 'age' in data and data['age'] is not None:
            updates.append("age = %s")
            values.append(int(data['age']))
            
        if 'gender' in data and data['gender'] is not None:
            updates.append("gender = %s")
            values.append(data['gender'].strip())
            
        if 'contact' in data and data['contact'] is not None:
            updates.append("contact = %s")
            values.append(data['contact'].strip())
            
        if 'address' in data:
            updates.append("address = %s")
            values.append(data['address'].strip() if data['address'] else None)
            
        if 'disease' in data and data['disease'] is not None:
            updates.append("disease = %s")
            values.append(data['disease'].strip())
            
        if 'status' in data and data['status'] is not None:
            updates.append("status = %s")
            values.append(data['status'].strip())
            
            # Handle discharge date if status is changed to Discharged
            if data['status'].strip().lower() == 'discharged':
                discharge_date = data.get('discharge_date', datetime.now().strftime('%Y-%m-%d'))
                updates.append("discharge_date = %s")
                values.append(discharge_date)
            elif data['status'].strip().lower() == 'admitted':
                updates.append("discharge_date = %s")
                values.append(None)
        
        if not updates:
            return jsonify({"error": "No fields to update"}), 400
        
        # Add patient_id to values
        values.append(patient_id)
        
        query = f"UPDATE patients SET {', '.join(updates)} WHERE id = %s"
        cursor.execute(query, values)
        conn.commit()
        
        return jsonify({
            "message": "Patient updated successfully!",
            "patient_id": patient_id
        })
        
    except Error as e:
        return jsonify({"error": str(e)}), 500
    except ValueError as e:
        return jsonify({"error": f"Invalid data format: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/patients/<int:patient_id>', methods=['DELETE'])
def delete_patient(patient_id):
    """Delete patient record"""
    try:
        conn, cursor = hospital_system.get_db_connection()
        if conn is None:
            return jsonify({"error": "Database connection failed"}), 500
        
        # Check if patient exists
        cursor.execute("SELECT patient_name FROM patients WHERE id = %s", (patient_id,))
        patient = cursor.fetchone()
        
        if not patient:
            return jsonify({"error": "Patient not found"}), 404
        
        cursor.execute("DELETE FROM patients WHERE id = %s", (patient_id,))
        conn.commit()
        
        return jsonify({
            "message": f"Patient {patient['patient_name']} deleted successfully!",
            "patient_id": patient_id
        })
        
    except Error as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/patients/search/<string:query>', methods=['GET'])
def search_patients(query):
    """Search patients by name or ID"""
    try:
        conn, cursor = hospital_system.get_db_connection()
        if conn is None:
            return jsonify({"error": "Database connection failed"}), 500
        
        # Try to search by ID first if query is numeric
        if query.isdigit():
            cursor.execute("SELECT * FROM patients WHERE id = %s", (int(query),))
        else:
            cursor.execute("SELECT * FROM patients WHERE patient_name LIKE %s", (f"%{query}%",))
        
        patients = cursor.fetchall()
        
        # Convert all rows to JSON-serializable format
        serializable_patients = []
        for patient in patients:
            serializable_patients.append(convert_row_to_json(patient))
        
        return jsonify({
            "count": len(serializable_patients),
            "patients": serializable_patients
        })
        
    except Error as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/patients/status/<string:status>', methods=['GET'])
def get_patients_by_status(status):
    """Get patients by status (Admitted/Discharged)"""
    try:
        conn, cursor = hospital_system.get_db_connection()
        if conn is None:
            return jsonify({"error": "Database connection failed"}), 500
        
        if status.lower() not in ['admitted', 'discharged']:
            return jsonify({"error": "Invalid status. Use 'admitted' or 'discharged'"}), 400
        
        cursor.execute("SELECT * FROM patients WHERE status = %s ORDER BY admission_date DESC", (status.capitalize(),))
        patients = cursor.fetchall()
        
        # Convert all rows to JSON-serializable format
        serializable_patients = []
        for patient in patients:
            serializable_patients.append(convert_row_to_json(patient))
        
        return jsonify({
            "count": len(serializable_patients),
            "patients": serializable_patients
        })
        
    except Error as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/patients/<int:patient_id>/discharge', methods=['POST'])
def discharge_patient(patient_id):
    """Discharge a patient"""
    try:
        data = request.json
        
        conn, cursor = hospital_system.get_db_connection()
        if conn is None:
            return jsonify({"error": "Database connection failed"}), 500
        
        # Check if patient exists and is admitted
        cursor.execute("SELECT * FROM patients WHERE id = %s AND status = 'Admitted'", (patient_id,))
        patient = cursor.fetchone()
        
        if not patient:
            return jsonify({"error": "Patient not found or already discharged"}), 404
        
        discharge_date = data.get('discharge_date', datetime.now().strftime('%Y-%m-%d'))
        
        cursor.execute(
            "UPDATE patients SET status = 'Discharged', discharge_date = %s WHERE id = %s",
            (discharge_date, patient_id)
        )
        conn.commit()
        
        return jsonify({
            "message": f"Patient {patient['patient_name']} discharged successfully!",
            "patient_id": patient_id,
            "discharge_date": discharge_date
        })
        
    except Error as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    db_status, db_message = check_db_connection()
    return jsonify({
        "status": "healthy" if db_status else "unhealthy",
        "database": db_message,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/init', methods=['POST'])
def init_database():
    """Initialize database tables"""
    success = create_tables_if_not_exist()
    if success:
        return jsonify({"message": "Database tables created successfully!"})
    else:
        return jsonify({"error": "Failed to create database tables"}), 500

# Serve frontend if needed (optional)
@app.route('/ui')
def serve_frontend_ui():
    """Serve the frontend HTML file"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Hospital System - Frontend Missing</title>
    </head>
    <body>
        <h1>Frontend Setup Required</h1>
        <p>Backend API is running successfully!</p>
        <p>To use the frontend:</p>
        <ol>
            <li>Save the HTML frontend code to a file named <code>hospital_frontend.html</code></li>
            <li>Open that file in your browser</li>
            <li>Make sure this backend is running on <code>http://localhost:5000</code></li>
        </ol>
        <p>API Status: <span style="color: green;">✓ Running</span></p>
        <p>Test endpoints:</p>
        <ul>
            <li><a href="/api/health">/api/health</a> - Health check</li>
            <li><a href="/api/stats">/api/stats</a> - System statistics</li>
            <li><a href="/api/patients">/api/patients</a> - All patients</li>
        </ul>
    </body>
    </html>
    """

if __name__ == '__main__':
    print("=" * 60)
    print("   HOSPITAL PATIENT RECORD SYSTEM API")
    print("=" * 60)
    print("Starting server...")
    print("Server will run on: http://localhost:5000")
    print("\nChecking database connection...")
    
    # Check database connection on startup
    db_status, db_message = check_db_connection()
    print(f"Database: {db_message}")
    
    if db_status:
        print("\n✓ Backend is ready!")
        print("\nTo use the system:")
        print("1. Open 'hospital_frontend.html' in your browser")
        print("2. Make sure this server is running")
        print("3. The frontend will connect to: http://localhost:5000")
    else:
        print("\n⚠  Database connection failed!")
        print("Please check:")
        print("1. MySQL is running")
        print("2. Database 'hospital_db' exists")
        print("3. Check .env file configuration")
        print("\nYou can still run the server, but database operations will fail.")
    
    print("\n" + "=" * 60)
    app.run(debug=True, port=5000)