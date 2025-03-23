import logging
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

# -------------------------------
# OpenTelemetry Setup
# -------------------------------
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.context import attach, detach
from opentelemetry.propagate import get_global_textmap

# Create a resource with the service name "backend-man"
resource = Resource.create({SERVICE_NAME: "backend-man"})

# Set the tracer provider if not already set
current_provider = trace.get_tracer_provider()
if not isinstance(current_provider, TracerProvider):
    trace.set_tracer_provider(TracerProvider(resource=resource))
provider = trace.get_tracer_provider()
tracer = trace.get_tracer(__name__)

# Add span processors (exporting to console and OTLP)
provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
provider.add_span_processor(
    BatchSpanProcessor(
        OTLPSpanExporter(endpoint="http://otel-collector:4318/v1/traces")
    )
)

# -------------------------------
# Logging Setup
# -------------------------------
# Custom formatter that adds trace and span IDs from the current OpenTelemetry span.
class OTELFormatter(logging.Formatter):
    def format(self, record):
        span = trace.get_current_span()
        span_context = span.get_span_context() if span else None
        if span_context and span_context.is_valid:
            record.trace_id = format(span_context.trace_id, '032x')
            record.span_id = format(span_context.span_id, '016x')
        else:
            record.trace_id = "None"
            record.span_id = "None"
        return super().format(record)

# Configure a logger that writes to a file
logger = logging.getLogger("backend_logger")
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler("/app/logs/backend.log")
formatter = OTELFormatter(
    '{"timestamp": "%(asctime)s", "severity": "%(levelname)s", '
    '"message": "%(message)s", "trace_id": "%(trace_id)s", "span_id": "%(span_id)s"}'
)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# -------------------------------
# Flask App Initialization
# -------------------------------
app = Flask(__name__)
CORS(app, expose_headers=["traceparent", "tracestate"])

# -------------------------------
# Database Configuration
# -------------------------------
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://myuser:mypassword@my-postgres:5432/mydatabase'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# -------------------------------
# Student Model
# -------------------------------
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

# -------------------------------
# OpenTelemetry Trace Helper
# -------------------------------
def start_child_span_from_request(span_name):
    headers = dict(request.headers)
    context = get_global_textmap().extract(headers)
    token = attach(context)
    span = tracer.start_as_current_span(span_name)
    return span, token

# -------------------------------
# Helper Functions with Spans
# -------------------------------
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
        # Simulate additional processing

# -------------------------------
# API Routes
# -------------------------------
@app.route('/register', methods=['POST'])
def register():
    span_ctx, token = start_child_span_from_request("POST /register")
    with span_ctx as parent_span:
        data = request.get_json()
        if not validate_student_data(data):
            detach(token)
            logger.error("Missing required fields in /register")
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
            logger.info(f"Student registered: {new_student.to_dict()}")
            return jsonify(new_student.to_dict()), 200
        except Exception as e:
            parent_span.record_exception(e)
            logger.error(f"Error creating student: {str(e)}")
            return jsonify({"error": "Error creating student"}), 400
        finally:
            detach(token)

@app.route('/students', methods=['GET'])
def get_students():
    span_ctx, token = start_child_span_from_request("GET /students")
    with span_ctx:
        try:
            students = Student.query.all()
            logger.info("Fetched all students")
            return jsonify([student.to_dict() for student in students]), 200
        except Exception as e:
            logger.error(f"Error fetching students: {str(e)}")
            return jsonify({"error": "Error fetching students"}), 500
        finally:
            detach(token)

@app.route('/deleteUser', methods=['DELETE'])
def delete_user():
    span_ctx, token = start_child_span_from_request("DELETE /deleteUser")
    with span_ctx:
        try:
            data = request.get_json()
            email = data.get('email')
            first_name = data.get('firstName')
            if not email or not first_name:
                logger.error("Email and firstName are required in /deleteUser")
                return jsonify({"error": "Email and firstName are required"}), 400

            students_to_delete = Student.query.filter_by(email=email, firstName=first_name).all()
            if not students_to_delete:
                logger.error("No user found in /deleteUser")
                return jsonify({"error": "No user found with the provided email and firstName"}), 404

            count_deleted = len(students_to_delete)
            for student in students_to_delete:
                db.session.delete(student)
            db.session.commit()
            logger.info(f"Deleted {count_deleted} user(s)")
            return jsonify({"message": f"{count_deleted} user(s) deleted successfully"}), 200
        except Exception as e:
            logger.error(f"Error deleting user: {str(e)}")
            return jsonify({"error": "An error occurred while deleting the user"}), 500
        finally:
            detach(token)

# -------------------------------
# Start App
# -------------------------------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=3002, debug=True)
