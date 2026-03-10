import os
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from werkzeug.utils import secure_filename
from ..forms import ComplaintForm, TrackComplaintForm
from ..models import Complaint, IssueType
from ..utils.helpers import generate_ticket_id
from .. import db
from ..services.email_service import email_sender
from flask_login import current_user
from flask import send_from_directory

main_bp = Blueprint(
    'main', __name__,
    template_folder='../templates/main',
    static_folder='../static'
)

@main_bp.route('/')
def index():
    return render_template('index.html', title="Welcome")

@main_bp.route('/submit-complaint', methods=['GET', 'POST'])
def submit_complaint():
    form = ComplaintForm()
    
    # This is the main 'if' block for form processing
    if form.validate_on_submit():
        # --- ALL PROCESSING LOGIC MUST BE INSIDE THIS BLOCK ---
        
        # 1. Handle file upload
        image_filename = None
        if form.photo.data:
            file = form.photo.data
            filename = secure_filename(file.filename)
            upload_path = current_app.config['UPLOAD_FOLDER']
            file.save(os.path.join(upload_path, filename))
            image_filename = os.path.join('uploads', filename)

        # 2. Create the new complaint object
        from app.models import PriorityEnum
        new_complaint = Complaint(
            ticket_id=generate_ticket_id(),
            issue_type=IssueType[form.issue_type.data],
            priority=PriorityEnum[form.priority.data],
            description=form.description.data,
            address_text=form.address_text.data,
            latitude=form.latitude.data or None,
            longitude=form.longitude.data or None,
            image_url=image_filename
        )
        
        # 3. Associate the logged-in user (if applicable)
        if current_user.is_authenticated and current_user.role == 'Citizen':
            new_complaint.reporter = current_user
            
        # 4. Save to database
        db.session.add(new_complaint)
        db.session.commit()
        
        # 5. Send confirmation email
        if new_complaint.reporter and new_complaint.reporter.email:
            email_sender.send_email(
                to=new_complaint.reporter.email,
                subject="Your Report Has Been Submitted",
                template="email/submission_confirmation.html",
                name=new_complaint.reporter.name,
                ticket_id=new_complaint.ticket_id
            )
        
        # 6. Flash message and redirect
        flash('Your complaint has been submitted successfully!', 'success')
        return redirect(url_for('main.submission_success', ticket_id=new_complaint.ticket_id))
        # --- END OF PROCESSING LOGIC ---

    return render_template('submit_complaint.html', title="Submit Complaint", form=form)

@main_bp.route('/success/<ticket_id>')
def submission_success(ticket_id):
    return render_template('submission_success.html', title="Submission Successful", ticket_id=ticket_id)

@main_bp.route('/about')
def about():
    # This now renders the new, professional HTML template.
    return render_template('about.html', title="About Us")

# The one and only track_complaint function
@main_bp.route('/track-complaint', methods=['GET', 'POST'])
def track_complaint():
    form = TrackComplaintForm()
    complaint = None
    if form.validate_on_submit():
        ticket_id = form.ticket_id.data
        # Query the database for the complaint with the given ticket_id
        complaint = Complaint.query.filter_by(ticket_id=ticket_id).first()
    return render_template('track_complaint.html', title="Track Complaint", form=form, complaint=complaint)


@main_bp.route('/support')
def support():
    return render_template('support.html', title="Support")

@main_bp.route('/accessibility')
def accessibility():
    return render_template('accessibility.html', title="Accessibility Policy")

@main_bp.route('/privacy')
def privacy():
    return render_template('privacy.html', title="Privacy & Security")

@main_bp.route('/service-worker.js')
def service_worker():
    return send_from_directory(os.path.join(current_app.root_path, 'static'),
                            'service-worker.js')