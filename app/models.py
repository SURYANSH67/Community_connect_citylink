from . import db, login_manager, bcrypt
from datetime import datetime
from flask_login import UserMixin
import enum


# Required for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    """Admin user model."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(
        db.String(50), nullable=False, default="Citizen"
    )  # Change default to 'Admin' # e.g., 'Admin', 'Official'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.name}>"


class IssueType(enum.Enum):
    POTHOLE = "Pothole"
    STREETLIGHT_OUTAGE = "Streetlight Outage"
    BROKEN_SIDEWALK = "Broken Sidewalk"
    TRASH_OVERFLOW = "Trash Overflow"
    GRAFFITI = "Graffiti"
    OTHER = "Other"


class ComplaintStatus(enum.Enum):
    PENDING = "Pending"
    IN_PROGRESS = "In Progress"
    RESOLVED = "Resolved"
    REJECTED = "Rejected"


class PriorityEnum(enum.Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class Complaint(db.Model):
    """Complaint model."""

    __tablename__ = "complaints"

    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.String(32), unique=True, nullable=False)

    # Using Enum for controlled vocabulary
    issue_type = db.Column(db.Enum(IssueType), nullable=False)
    description = db.Column(db.Text, nullable=False)
    
    priority = db.Column(db.Enum(PriorityEnum), nullable=False, default=PriorityEnum.LOW)

    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    address_text = db.Column(db.String(255), nullable=True)

    image_url = db.Column(db.String(255), nullable=True)

    # reported_by_name = db.Column(db.String(100), nullable=True)
    # reported_by_email = db.Column(db.String(120), nullable=True)
    reporter_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=True
    )  # Can be null for anonymous reports

    # This relationship lets us do 'complaint.reporter' to get the User object.
    reporter = db.relationship(
        "User", foreign_keys=[reporter_id], backref="reported_complaints"
    )

    # The 'assigned_to' relationship remains the same.
    assigned_to_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    assigned_to = db.relationship(
        "User", foreign_keys=[assigned_to_id], backref="assigned_complaints"
    )

    status = db.Column(
        db.Enum(ComplaintStatus), default=ComplaintStatus.PENDING, nullable=False
    )
    admin_notes = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    resolved_at = db.Column(db.DateTime, nullable=True)
    assigned_to_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    # This relationship lets us do 'complaint.assigned_to' to get the User object.
    # The backref lets us do 'user.assigned_complaints' to get a list of complaints.
    assigned_to = db.relationship(
        "User", foreign_keys=[assigned_to_id], backref="assigned_complaints"
    )

    def __repr__(self):
        return f"<Complaint {self.ticket_id}>"
