# Python Standard Library
import json
from datetime import datetime, timedelta

# Flask & Extensions
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from sqlalchemy import or_, func, extract

# Local Application Imports
from .. import db
from ..models import Complaint, IssueType, ComplaintStatus, User, PriorityEnum
from ..forms import ComplaintFilterForm, UpdateComplaintStatusForm
from ..services.email_service import email_sender

# --- Blueprint Definition ---
admin_bp = Blueprint("admin", __name__, template_folder="../templates/admin")


# === Main Admin Dashboard Route ===
@admin_bp.route("/dashboard")
@login_required
def dashboard():
    # 1. Create a base query that is pre-filtered by user role.
    base_query = Complaint.query
    if current_user.role == "Official":
        base_query = Complaint.query.filter(Complaint.assigned_to_id == current_user.id)

    # 2. Calculate all analytics USING THE BASE QUERY.
    # Stat Cards
    total_complaints = base_query.count()
    status_counts_query = (
        base_query.with_entities(Complaint.status, func.count(Complaint.status))
        .group_by(Complaint.status)
        .all()
    )
    status_counts = {status.name: count for status, count in status_counts_query}
    stats = {
        "total": total_complaints,
        "pending": status_counts.get("PENDING", 0),
        "in_progress": status_counts.get("IN_PROGRESS", 0),
        "resolved": status_counts.get("RESOLVED", 0),
    }

    # Doughnut Chart & Breakdown List
    issue_counts_query = (
        base_query.with_entities(Complaint.issue_type, func.count(Complaint.issue_type))
        .group_by(Complaint.issue_type)
        .order_by(func.count(Complaint.issue_type).desc())
        .all()
    )
    issue_labels = [issue.value for issue, count in issue_counts_query]
    issue_data = [count for issue, count in issue_counts_query]
    issue_counts = {issue.value: count for issue, count in issue_counts_query}

    # 3. Apply user's search/filter criteria to the base query.
    form = ComplaintFilterForm(request.args, meta={"csrf": False})
    final_query = base_query

    search_term = form.search.data
    status_filter = form.status.data
    issue_type_filter = form.issue_type.data

    if search_term:
        final_query = final_query.filter(
            or_(
                Complaint.ticket_id.ilike(f"%{search_term}%"),
                Complaint.address_text.ilike(f"%{search_term}%"),
            )
        )
    if status_filter:
        final_query = final_query.filter(
            Complaint.status == ComplaintStatus[status_filter]
        )
    if issue_type_filter:
        final_query = final_query.filter(
            Complaint.issue_type == IssueType[issue_type_filter]
        )

    # 4. Get the final list of complaints for the table.
    complaints = final_query.order_by(Complaint.created_at.desc()).all()

    # 5. Render the template with all the correctly scoped data.
    return render_template(
        "dashboard.html",
        title="Admin Dashboard",
        complaints=complaints,
        form=form,
        stats=stats,
        issue_labels=json.dumps(issue_labels),
        issue_data=json.dumps(issue_data),
        issue_counts=issue_counts,
    )


# === Complaint Detail & Update Route ===
@admin_bp.route("/complaint/<int:complaint_id>", methods=["GET", "POST"])
@login_required
def complaint_detail(complaint_id):
    complaint = Complaint.query.get_or_404(complaint_id)
    form = UpdateComplaintStatusForm()

    if current_user.role == "Admin":
        officials = User.query.filter_by(role="Official").order_by(User.name).all()
        form.assigned_to.choices = [(0, "--- Unassigned ---")] + [
            (o.id, o.name) for o in officials
        ]
    else:
        del form.assigned_to

    if form.validate_on_submit():
        complaint.status = ComplaintStatus[form.status.data]
        complaint.priority = PriorityEnum[form.priority.data]
        complaint.admin_notes = form.admin_notes.data

        if "assigned_to" in form:
            assigned_id = form.assigned_to.data
            complaint.assigned_to_id = assigned_id if assigned_id != 0 else None

        if complaint.status == ComplaintStatus.RESOLVED:
            complaint.resolved_at = datetime.utcnow()

        # Send email notification on every status update
        if complaint.reporter and complaint.reporter.email:
            email_sender.send_email(
                to=complaint.reporter.email,
                subject=f"Update on Your Report: {complaint.ticket_id}",
                template="email/status_update.html",
                name=complaint.reporter.name,
                ticket_id=complaint.ticket_id,
                new_status=complaint.status.value,
                notes=complaint.admin_notes,
            )

        db.session.commit()
        flash(f"Ticket {complaint.ticket_id} has been updated.", "success")
        return redirect(url_for("admin.dashboard"))

    elif request.method == "GET":
        form.status.data = complaint.status.name
        form.priority.data = complaint.priority.name
        form.admin_notes.data = complaint.admin_notes
        if "assigned_to" in form:
            form.assigned_to.data = complaint.assigned_to_id or 0

    return render_template(
        "complaint_detail.html",
        title="Complaint Details",
        complaint=complaint,
        form=form,
    )


# === API Endpoint for Live Filtering (If you implemented it) ===
# This is the separate API endpoint for the AJAX feature.
# It is kept separate from the main dashboard route.
@admin_bp.route("/api/complaints")
@login_required
def api_complaints():
    query = Complaint.query

    if current_user.role == "Official":
        query = query.filter(Complaint.assigned_to_id == current_user.id)

    search_term = request.args.get("search")
    status_filter = request.args.get("status")
    issue_type_filter = request.args.get("issue_type")

    if search_term:
        query = query.filter(
            or_(
                Complaint.ticket_id.ilike(f"%{search_term}%"),
                Complaint.address_text.ilike(f"%{search_term}%"),
            )
        )
    if status_filter:
        query = query.filter(Complaint.status == ComplaintStatus[status_filter])
    if issue_type_filter:
        query = query.filter(Complaint.issue_type == IssueType[issue_type_filter])

    complaints = query.order_by(Complaint.created_at.desc()).all()

    results = []
    for c in complaints:
        results.append(
            {
                "ticket_id": c.ticket_id,
                "issue_type": c.issue_type.value,
                "location": c.address_text,
                "reported_on": c.created_at.strftime("%Y-%m-%d %H:%M"),
                "status": c.status.value,
                "status_name": c.status.name,
                "url": url_for("admin.complaint_detail", complaint_id=c.id),
            }
        )

    return jsonify(results)
