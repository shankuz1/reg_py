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
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

# Create a resource for our service
resource = Resource.create({SERVICE_NAME: "student-reg"})

# Only set a new TracerProvider if one hasn't been set already.
current_provider = trace.get_tracer_provider()
if not isinstance(current_provider, TracerProvider):
    trace.set_tracer_provider(TracerProvider(resource=resource))
# Otherwise, we keep the existing provider.
provider = trace.get_tracer_provider()

tracer = trace.get_tracer(__name__)

# Add a console span processor for debugging
console_processor = BatchSpanProcessor(ConsoleSpanExporter())
provider.add_span_processor(console_processor)

# Configure the OTLP exporter (HTTP) without the 'insecure' parameter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

# Configure the OTLP exporter for HTTP
otlp_exporter = OTLPSpanExporter(
    endpoint="http://otel-collector:4318/v1/traces"
)
otlp_processor = BatchSpanProcessor(otlp_exporter)
provider.add_span_processor(otlp_processor)
# -------------------------------
# Flask App Initialization
# -------------------------------
app = Flask(__name__)
CORS(app)

# ---------------------------------------------------------------------
# Database Configuration
# ---------------------------------------------------------------------
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
# Helper Functions with Manual Spans
# ---------------------------------------------------------------------
def validate_student_data(data):
    with tracer.start_as_current_span("validate_student_data"):
        required_fields = ['firstName', 'lastName', 'email', 'dob']
        for field in required_fields:
            if not data.get(field):
                trace.get_current_span().set_attribute(f"validation.error.{field}", True)
                return False
        return True

def persist_student(student):
    with tracer.start_as_current_span("persist_student"):
        db.session.add(student)
        db.session.commit()

def additional_processing(student):
    with tracer.start_as_current_span("additional_processing"):
        trace.get_current_span().set_attribute("student.processed", True)
        # Simulate additional processing here
        return

# ---------------------------------------------------------------------
# API Routes (Manually Instrumented)
# ---------------------------------------------------------------------
@app.route('/register', methods=['POST'])
def register():
    with tracer.start_as_current_span("POST /register") as parent_span:
        data = request.get_json()
        if not validate_student_data(data):
            return jsonify({"error": "Missing required fields"}), 400
        try:
            dob_date = datetime.strptime(data['dob'], '%Y-%m-%d').date()
            new_student = Student(
                firstName=data['firstName'],
                lastName=data['lastName'],
                email=data['email'],
                dob=dob_date
            )
            persist_student(new_student)
            additional_processing(new_student)
            return jsonify(new_student.to_dict()), 200
        except Exception as e:
            parent_span.record_exception(e)
            print(e)
            return jsonify({"error": "Error creating student"}), 400

@app.route('/students', methods=['GET'])
def get_students():
    with tracer.start_as_current_span("GET /students"):
        try:
            students = Student.query.all()
            return jsonify([student.to_dict() for student in students]), 200
        except Exception as e:
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
            print(e)
            return jsonify({"error": "An error occurred while deleting the user"}), 500

# ---------------------------------------------------------------------
# Run the App
# ---------------------------------------------------------------------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=3002, debug=True)
