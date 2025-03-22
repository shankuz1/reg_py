from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
CORS(app)

# ---------------------------------------------------------------------
# 1) Update this line to match your actual Postgres credentials & DB
#    Format: postgresql://<USER>:<PASSWORD>@<HOST>:<PORT>/<DBNAME>
# ---------------------------------------------------------------------
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://myuser:mypassword@my-postgres:5432/mydatabase'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://myuser:mypassword@localhost:5432/mydatabase'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ---------------------------------------------------------------------
# 2) Define a 'Student' model matching your database table definition
# ---------------------------------------------------------------------
class Student(db.Model):
    __tablename__ = 'student'
    id = db.Column(db.Integer, primary_key=True)
    firstName = db.Column(db.String(50), nullable=False)
    lastName = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    dob = db.Column(db.Date, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "firstName": self.firstName,
            "lastName": self.lastName,
            "email": self.email,
            "dob": self.dob.isoformat(),
        }

# ---------------------------------------------------------------------
# 3) Routes
# ---------------------------------------------------------------------

# POST /register: Registers a new student
@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        first_name = data.get('firstName')
        last_name = data.get('lastName')
        email = data.get('email')
        dob_str = data.get('dob')

        if not (first_name and last_name and email and dob_str):
            return jsonify({"error": "Missing required fields"}), 400

        dob_date = datetime.strptime(dob_str, '%Y-%m-%d').date()

        new_student = Student(
            firstName=first_name,
            lastName=last_name,
            email=email,
            dob=dob_date
        )
        db.session.add(new_student)
        db.session.commit()

        return jsonify(new_student.to_dict()), 200
    except Exception as e:
        print(e)  # For debugging
        return jsonify({"error": "Error creating student"}), 400


# GET /students: Retrieves all student records
@app.route('/students', methods=['GET'])
def get_students():
    try:
        students = Student.query.all()
        return jsonify([student.to_dict() for student in students]), 200
    except Exception as e:
        print(e)
        return jsonify({"error": "Error fetching students"}), 500


# DELETE /deleteUser: Deletes a student by email & firstName
@app.route('/deleteUser', methods=['DELETE'])
def delete_user():
    try:
        data = request.get_json()
        email = data.get('email')
        first_name = data.get('firstName')

        if not email or not first_name:
            return jsonify({"error": "Email and firstName are required"}), 400

        students_to_delete = Student.query.filter_by(email=email, firstName=first_name).all()
        if not students_to_delete:
            return jsonify({"error": "No user found with the provided email and firstName"}), 404

        count_deleted = len(students_to_delete)
        for student in students_to_delete:
            db.session.delete(student)

        db.session.commit()
        return jsonify({"message": f"{count_deleted} user(s) deleted successfully"}), 200

    except Exception as e:
        print(e)
        return jsonify({"error": "An error occurred while deleting the user"}), 500


# ---------------------------------------------------------------------
# 4) Run the app
#    Here, we manually create all tables before starting the server
# ---------------------------------------------------------------------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=3002, debug=True)