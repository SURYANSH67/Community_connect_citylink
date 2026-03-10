from flask_wtf import FlaskForm
from wtforms import TextAreaField, SelectField, SubmitField
from flask_wtf.file import FileField, FileAllowed, FileRequired
from .models import IssueType, ComplaintStatus, PriorityEnum
from wtforms import StringField, PasswordField, BooleanField, HiddenField
from wtforms.validators import DataRequired, Length, Optional, Email
from wtforms.validators import  EqualTo, ValidationError
from .models import User

class ComplaintForm(FlaskForm):
    """Form for users to submit a new complaint."""

    # Create choices from the IssueType Enum for the dropdown
    issue_type_choices = [(issue.name, issue.value) for issue in IssueType]

    issue_type = SelectField(
        'Type of Issue',
        choices=issue_type_choices,
        validators=[DataRequired(message="Please select the type of issue.")]
    )
    description = TextAreaField(
        'Description',
        validators=[
            DataRequired(message="Please provide a description."),
            Length(min=20, max=500)
        ]
    )
    
    priority_choices = [(p.name, p.value) for p in PriorityEnum]
    
    priority = SelectField(
        'Priority Level',
        choices=priority_choices,
        default=PriorityEnum.LOW.name,
        validators=[DataRequired(message="Please select a priority level.")]
    )
    address_text = StringField(
        'Location or Address',
        validators=[DataRequired(message="Please provide a location.")]
    )
    latitude = HiddenField('Latitude')
    longitude = HiddenField('Longitude')
    photo = FileField(
        'Upload Photo (Optional)',
        validators=[
            FileAllowed(['jpg', 'jpeg', 'png'], 'Only images are allowed!')
        ]
    )
    reported_by_name = StringField(
        'Your Name (Optional)',
        validators=[Optional(), Length(max=100)]
    )
    # ===================== ADD THIS FIELD =====================
    reported_by_email = StringField(
        'Your Email (For Notifications)',
        validators=[Optional(), Email(message="Please enter a valid email address.")]
    )
    # ==========================================================
    submit = SubmitField('Submit Report')

  # ... (keep the existing imports and ComplaintForm class) ...

class TrackComplaintForm(FlaskForm):
    """Form for tracking an existing complaint."""
    ticket_id = StringField(
        'Enter Your Ticket ID',
        validators=[DataRequired(message="Please enter a ticket ID.")]
    )
    submit = SubmitField('Track Status')
    
    
class LoginForm(FlaskForm):
    """Form for admins to log in."""
    email = StringField(
        'Email',
        validators=[DataRequired(), Email(message="Please enter a valid email.")]
    )
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Login')
    
class UpdateComplaintStatusForm(FlaskForm):
    """Form for admins to update a complaint's status."""
    status_choices = [(status.name, status.value) for status in ComplaintStatus]
    priority_choices = [(p.name, p.value) for p in PriorityEnum]
    
    priority = SelectField(
        'Update Priority',
        choices=priority_choices,
        validators=[DataRequired()]
    )
    
    status = SelectField(
        'New Status',
        choices=status_choices,
        validators=[DataRequired()]
    )
    
    assigned_to = SelectField('Assign To Official', choices=[], coerce=int, validators=[DataRequired()])
    
    admin_notes = TextAreaField(
        'Notes (Optional)',
        validators=[Optional(), Length(max=1000)]
    )
    
    submit = SubmitField('Update Status & Assignment')

class ComplaintFilterForm(FlaskForm):
    """Form for filtering complaints on the admin dashboard."""
    
    # Create choices with a leading "All" option
    status_choices = [('', 'All Statuses')] + [(s.name, s.value) for s in ComplaintStatus]
    issue_type_choices = [('', 'All Issue Types')] + [(i.name, i.value) for i in IssueType]

    search = StringField(
        'Search Term',
        validators=[Optional(), Length(max=100)],
        render_kw={"placeholder": "Ticket ID or Address..."}
    )
    status = SelectField('Status', choices=status_choices, validators=[Optional()])
    issue_type = SelectField('Issue Type', choices=issue_type_choices, validators=[Optional()])
    submit = SubmitField('Filter')


class RegistrationForm(FlaskForm):
    """Form for public users to create an account."""
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is already registered. Please choose a different one or log in.')

class PublicLoginForm(FlaskForm):
    """Form for public users to log in."""
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Login')