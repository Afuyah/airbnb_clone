from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models.models import SupportRequest
from app import db
from flask_login import login_required, current_user
from app.forms.forms import SupportRequestForm  # Assuming you create this form

support_bp = Blueprint('support', __name__)

@support_bp.route('/support', methods=['GET', 'POST'])
@login_required
def submit_support_request():
    form = SupportRequestForm()  # Use a form for validation

    if form.validate_on_submit():  # Check if the form is submitted and valid
        support_request = SupportRequest(
            user_id=current_user.id,
            subject=form.subject.data,
            message=form.message.data
        )
        db.session.add(support_request)
        db.session.commit()
        flash('Support request submitted successfully.', 'success')
        return redirect(url_for('support.view_requests'))  # Redirect to a different page

    return render_template('support/submit_request.html', form=form)

@support_bp.route('/my_requests', methods=['GET'])
@login_required
def view_requests():
    requests = SupportRequest.query.filter_by(user_id=current_user.id).all()
    return render_template('support/view_requests.html', requests=requests)
