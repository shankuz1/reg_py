from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# -------------------------------
# Manual OpenTelemetry Instrumentation Setup
# -------------------------------
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

# Set up the tracer provider with a resource that names our service
resource = Resource.create({SERVICE_NAME: "backend"})
trace.set_tracer_provider(TracerProvider(resource=resource))
tracer = trace.get_tracer(__name__)

# Add a span processor to export spans to the console for debugging
span_processor = BatchSpanProcessor(ConsoleSpanExporter())
trace.get_tracer_provider().add_span_processor(span_processor)

# -------------------------------
# Flask App Initialization
# -------------------------------
app = Flask(__name__)
CORS(app)

# ---------------------------------------------------------------------
# Database Configuration
# ---------------------------------------------------------------------
# Using the Docker Compose service name "my-postgres" for the database host.
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://myuser:mypassword@my-postgres:5432/mydatabase'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ---------------------------------------------------------------------
# Define the 'Student' Model
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
# API Routes (Manually Instrumented)
# ---------------------------------------------------------------------

@app.route('/register', methods=['POST'])
def register():
    with tracer.start_as_current_span("POST /register"):
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
            tracer.get_current_span().record_exception(e)
            print(e)
            return jsonify({"error": "Error creating student"}), 400


@app.route('/students', methods=['GET'])
def get_students():
    with tracer.start_as_current_span("GET /students"):
        try:
            students = Student.query.all()
            return jsonify([student.to_dict() for student in students]), 200
        except Exception as e:
            tracer.get_current_span().record_exception(e)
            print(e)
            return jsonify({"error": "Error fetching students"}), 500


@app.route('/deleteUser', methods=['DELETE'])
def delete_user():
    with tracer.start_as_current_span("DELETE /deleteUser"):
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
            tracer.get_current_span().record_exception(e)
            print(e)
            return jsonify({"error": "An error occurred while deleting the user"}), 500


# ---------------------------------------------------------------------
# Run the App
# ---------------------------------------------------------------------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=3002, debug=True)
