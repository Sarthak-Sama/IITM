from flask import Blueprint, render_template, redirect, url_for, request, flash, session, send_from_directory
from models import db, Admin, Customer, ServiceProfessional, Service, ServiceRequest
from collections import Counter
from datetime import datetime

# Define blueprints for different roles
auth_bp = Blueprint('auth', __name__)
admin_bp = Blueprint('admin', __name__)
customer_bp = Blueprint('customer', __name__)
professional_bp = Blueprint('professional', __name__)


# ---------------- Auth Routes ----------------------- #
# Login route
@auth_bp.route('/', methods=['GET', 'POST'])
def login():
    # Check if the user is already logged in (session has user_id)
    if 'user_id' in session:
        # Check the role and redirect to the respective dashboard
        if session['role'] == 'admin':
            return redirect(url_for('admin.admin_dashboard'))
        elif session['role'] == 'customer':
            return redirect(url_for('customer.customer_homepage'))
        elif session['role'] == 'professional':
            return redirect(url_for('professional.provider_dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Check if the user is an Admin
        admin = Admin.query.filter_by(email=email).first()
        if admin and admin.password == password:
            session['user_id'] = admin.id
            session['role'] = 'admin'
            flash('Login successful!', 'success')
            return redirect(url_for('admin.admin_dashboard'))
        
        # Check if the user is a Customer
        customer = Customer.query.filter_by(email=email).first()
        if customer and customer.password == password:
            session['user_id'] = customer.id
            session['role'] = 'customer'
            flash('Login successful!', 'success')
            return redirect(url_for('customer.customer_homepage'))
        
        # Check if the user is a Service Professional
        professional = ServiceProfessional.query.filter_by(email=email).first()
        if professional and professional.password == password:
            if not professional.is_verified:
                flash('You are not yet verified, Please Wait!', 'danger')
                return redirect(url_for('auth.login'))
            else:
                session['user_id'] = professional.id
                session['role'] = 'professional'
                flash('Login successful!', 'success')
                return redirect(url_for('professional.provider_dashboard'))
        
        # If no matching user was found, or password is incorrect
        flash('Invalid email or password. Please try again.', 'danger')
        return redirect(url_for('auth.login'))

    return render_template('index.html')



# Customer Register route
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        fullname = request.form.get('fullname')
        address = request.form.get('address')
        pincode = request.form.get('pincode')
        
        # Check if the email already exists
        if Admin.query.filter_by(email=email).first() or Customer.query.filter_by(email=email).first() or ServiceProfessional.query.filter_by(email=email).first():
            flash('Email already exists. Please use a different email.', 'danger')
            return redirect(url_for('auth.register'))

        # Create a new user (example for Customer)
        new_customer = Customer(email=email, password=password, fullname=fullname, address=address, pincode=pincode)
        db.session.add(new_customer)
        db.session.commit()
        session['user_id'] = new_customer.id
        session['role'] = 'customer'
        return redirect(url_for('customer.customer_homepage'))


    return render_template('customer_signup.html')

# Provider Register route
@auth_bp.route('/register/provider', methods=['GET', 'POST'])
def register_provider():
    services = Service.query.all()
    
    if request.method == 'POST':
        # Fetch the service object by name and use `.first()` to get the first result
        service = Service.query.filter(Service.name == request.form.get('service_name')).first()

        # Check if service exists
        if not service:
            flash('Selected service does not exist.', 'danger')
            return redirect(url_for('auth.register_provider'))

        # Fetch form data
        email = request.form.get('email')
        password = request.form.get('password')
        fullname = request.form.get('fullname')
        service_id = service.id  
        service_type = service.name 
        experience = request.form.get('experience')
        address = request.form.get('address')
        pincode = request.form.get('pincode')
        
        # Check if the email already exists
        if Admin.query.filter_by(email=email).first() or Customer.query.filter_by(email=email).first() or ServiceProfessional.query.filter_by(email=email).first():
            flash('Email already exists. Please use a different email.', 'danger')
            return redirect(url_for('auth.register_provider'))    

        # Create a new provider (ServiceProfessional)
        new_provider = ServiceProfessional(
            email=email,
            password=password,
            fullname=fullname,
            service_id=service_id,
            service_type=service_type,
            experience=experience,
            address=address,
            pincode=pincode
        )
        
        db.session.add(new_provider)
        db.session.commit()

        flash('You have registered. Now wait to get Verified!', 'danger')
        return redirect(url_for('auth.login'))
    
    return render_template('provider_signup.html', services=services)


#Logout Route
@auth_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    session.clear()
    flash('You have been logged out!', 'danger')
    return redirect(url_for('auth.login'))



# -------------- Authentication MiddleWares ----------------------- #

@admin_bp.before_request
def check_login_admin():
    if 'user_id' not in session or session['role'] != 'admin':
        flash('You need to log in first!', 'danger')
        return redirect(url_for('auth.login'))
    

# Professional blueprint
@professional_bp.before_request
def check_login_professional():
    if 'user_id' not in session or session['role'] != 'professional':
        flash('You need to log in first!', 'danger')
        return redirect(url_for('auth.login'))
    
    user = ServiceProfessional.query.get(session['user_id'])
    if user and user.is_blacklisted:
        session.clear()
        flash('Your account has been restricted. Contact support for assistance.', 'danger')
        return redirect(url_for('auth.login'))

# Customer blueprint
@customer_bp.before_request
def check_login_customer():
    if 'user_id' not in session or session['role'] != 'customer':
        flash('You need to log in first!', 'danger')
        return redirect(url_for('auth.login'))
    user = Customer.query.get(session['user_id'])
    if user and user.is_blacklisted:
        session.clear()
        flash('Your account has been restricted. Contact support for assistance.', 'danger')
        return redirect(url_for('auth.login'))

# ---------------- Admin Routes ----------------------- #
# Admin dashboard
@admin_bp.route('/dashboard')
def admin_dashboard():
    services = Service.query.all()
    professionals = ServiceProfessional.query.all()
    service_requests = ServiceRequest.query.all()
    customers = Customer.query.all()

    return render_template('admin_dashboard.html', services=services, professionals=professionals, requests=service_requests, customers=customers)

# Add Service
@admin_bp.route('/add_service', methods=['GET', 'POST'])
def add_service():
    if request.method == 'POST':


        service_name = request.form['name']
        description = request.form['description']
        base_price = request.form['price']
        time_required = request.form['time']

        new_service = Service(
            name=service_name,
            base_price=base_price,
            description=description,
            time_required=time_required
        )
        db.session.add(new_service)
        db.session.commit()

        return redirect(url_for('admin.admin_dashboard'))
    return render_template('new_service_form.html')


from werkzeug.utils import secure_filename

@admin_bp.route('/edit_service/<int:service_id>', methods=['GET', 'POST'])
def edit_service(service_id):
    service = Service.query.get(service_id)
    if not service:
        return "Service not found", 404

    if request.method == 'POST':
        
        # Update service attributes
        service.name = request.form['name']
        service.description = request.form['description']
        service.base_price = request.form['price']
        service.time_required = request.form['time']

        # Commit changes to the database
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Error updating service: {e}")
            return "Error updating service", 500

        return redirect(url_for('admin.admin_dashboard'))

    # Render the form with the current service details
    return render_template('edit_service_form.html', service=service)

# Delete Service
@admin_bp.route('/delete_service/<int:service_id>', methods=['GET', 'POST'])
def delete_service(service_id):
    service_to_delete = Service.query.get(service_id)
    
    service_type = service_to_delete.name
    providers_to_delete = ServiceProfessional.query.filter_by(service_type=service_type).all()

    try:
        db.session.delete(service_to_delete)
        
        for provider in providers_to_delete:
            db.session.delete(provider)
        
        db.session.commit()
    
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting service: {e}")
        flash('Error deleting service', 'error')

    return redirect(url_for('admin.admin_dashboard'))


# Block User
@admin_bp.route('/block_customer/<int:customer_id>', methods=['POST'])
def block_customer(customer_id):
    customer = Customer.query.get(customer_id)
    if customer:
        customer.is_blacklisted = True
        db.session.commit()

    return redirect(url_for('admin.admin_dashboard'))

# Unblock User
@admin_bp.route('/unblock_customer/<int:customer_id>', methods=['POST'])
def unblock_customer(customer_id):
    customer = Customer.query.get(customer_id)
    if customer:
        customer.is_blacklisted = False  # Unblock customer
        db.session.commit()

    return redirect(url_for('admin.admin_dashboard'))

# Block User
@admin_bp.route('/block_professional/<int:professional_id>', methods=['POST'])
def block_professional(professional_id):
    professional = ServiceProfessional.query.get(professional_id)
    if professional:
        professional.is_blacklisted = True
        db.session.commit()

    return redirect(url_for('admin.admin_dashboard'))

# Unblock User
@admin_bp.route('/unblock_professional/<int:professional_id>', methods=['POST'])
def unblock_professional(professional_id):
    professional = ServiceProfessional.query.get(professional_id)
    if professional:
        professional.is_blacklisted = False  # Unblock professional
        db.session.commit()

    return redirect(url_for('admin.admin_dashboard'))

# Verify Provider (Professional)
@admin_bp.route('/verify_provider/<int:professional_id>', methods=['POST'])
def verify_provider(professional_id):
    professional = ServiceProfessional.query.get(professional_id)
    if professional:
        professional.is_verified = True  # Mark professional as verified
        db.session.commit()

    return redirect(url_for('admin.admin_dashboard'))

# Reject Provider (Professional)
@admin_bp.route('/reject_provider/<int:professional_id>', methods=['POST'])
def reject_provider(professional_id):
    professional = ServiceProfessional.query.get(professional_id)
    if professional:
        professional.is_verified = False  # Mark professional as rejected
        db.session.commit()

    return redirect(url_for('admin.admin_dashboard'))


# Admin Seach functionality 
@admin_bp.route('/search', methods=['POST'])
def search():
    search_type = request.form.get('search_type')  # Get the selected search type (id, service_type, or name)
    search_query = request.form.get('search_query')  # Get the search query text

    results = []

    # Search logic based on the type selected
    if search_type == 'id':
        # Assuming the ID is an integer, you may need to handle errors if the input is not valid
        results = ServiceProfessional.query.filter(ServiceProfessional.id == search_query).all()
    elif search_type == 'service_type':
        results = ServiceProfessional.query.filter(ServiceProfessional.service_type.ilike(f'%{search_query}%')).all()
    elif search_type == 'name':
        results = ServiceProfessional.query.filter(ServiceProfessional.fullname.ilike(f'%{search_query}%')).all()

    return render_template('admin_search_page.html', results=results, search_type=search_type)


# Search Page Route
@admin_bp.route('/search', methods=['GET', 'POST'])
def search_page():
    return render_template('admin_search_page.html')

#Summary Page Route
@admin_bp.route('/summary', methods=['GET', 'POST'])
def summary_page():
    # Query the total number of customers, professionals, and requests
    total_customers = Customer.query.count()
    total_professionals = ServiceProfessional.query.count()
    total_requests = ServiceRequest.query.count()

    # Calculate the average rating for service requests, excluding ratings of 0 or None
    average_rating = db.session.query(
        db.func.avg(ServiceRequest.rating)
    ).filter(ServiceRequest.rating > 0).scalar()

    if average_rating is None:
        average_rating = "No ratings available"

    # Query the ratings data from the ServiceRequest table, excluding ratings of 0 or None
    ratings_data = db.session.query(
        db.func.count().label('count'), ServiceRequest.rating
    ).filter(ServiceRequest.rating > 0).group_by(ServiceRequest.rating).all()

    # Prepare the ratings data (assuming ratings are stored as integer values like 1, 2, 3, 4, 5)
    customer_ratings_data = {
        "Excellent": 0,
        "Good": 0,
        "Average": 0,
        "Poor": 0,
        "Very Poor": 0
    }

    # Populate customer_ratings_data based on the actual data
    for rating in ratings_data:
        if rating.rating == 5:
            customer_ratings_data["Excellent"] = rating.count
        elif rating.rating == 4:
            customer_ratings_data["Good"] = rating.count
        elif rating.rating == 3:
            customer_ratings_data["Average"] = rating.count
        elif rating.rating == 2:
            customer_ratings_data["Poor"] = rating.count
        elif rating.rating == 1:
            customer_ratings_data["Very Poor"] = rating.count

    # Query the service request data for the bar chart
    service_requests_data = {
        "Requested": ServiceRequest.query.filter_by(status='requested').count(),
        "Accepted": ServiceRequest.query.filter_by(status='accepted').count(),
        "Closed": ServiceRequest.query.filter_by(status='closed').count()
    }

    return render_template(
        'admin_summary_page.html',
        total_customers=total_customers,
        total_professionals=total_professionals,
        total_requests=total_requests,
        average_rating=average_rating,
        customer_ratings_data=customer_ratings_data,
        service_requests_data=service_requests_data
    )



# -----------------Provider Routes-----------------------
# Provider dashboard
@professional_bp.route('/dashboard')
def provider_dashboard():
    professional_id = session.get('user_id')
    
    # Retrieve service requests for the logged-in professional where the status is 'requested' or 'accepted'
    requests = ServiceRequest.query.filter(
        ServiceRequest.professional_id == professional_id,
        ServiceRequest.status.in_(['requested', 'accepted'])
    ).all()

    # Retrieve closed requests
    closed_requests = ServiceRequest.query.filter(
        ServiceRequest.professional_id == professional_id,
        ServiceRequest.status.in_(['rejected', 'closed'])
    ).all()
    
    return render_template('provider_dashboard.html', requests=requests, closed_requests=closed_requests)


@professional_bp.route('/search', methods=['GET', 'POST'])
def search_page():
    results = []
    search_type = None  # Initialize search_type
    error_message = None  # Initialize error_message

    if request.method == 'POST':
        search_type = request.form.get('search_type')
        search_query = request.form.get('search_query')

        # Ensure search_query is not empty
        if not search_query:
            error_message = "Search query cannot be empty."
            return render_template('provider_search_page.html', results=results, search_type=search_type, error_message=error_message)

        if search_type == 'pincode':
            # Search by pincode
            results = ServiceRequest.query.join(Customer).filter(
                Customer.pincode == search_query,
                ServiceRequest.status == 'requested',
                ServiceRequest.professional_id == session['user_id']
            ).all()

        elif search_type == 'date':
            search_date = datetime.strptime(search_query, '%Y-%m-%d').date()
            print(search_date)
                
            # Filter by only the date part of `date_of_request`
            results = ServiceRequest.query.filter(
                db.func.date(ServiceRequest.date_of_request) == search_date,
                ServiceRequest.status == 'requested'
            ).all()
    return render_template('provider_search_page.html', results=results, search_type=search_type, error_message=error_message)


@professional_bp.route('/accept_request/<int:request_id>', methods=['POST'])
def accept_request(request_id):
    service_request = ServiceRequest.query.get(request_id)
    
    if service_request:
        service_request.status = 'accepted'
        db.session.commit()  # Commit the change to the database
    
    return redirect(url_for('professional.provider_dashboard'))


@professional_bp.route('/reject_request/<int:request_id>', methods=['POST'])
def reject_request(request_id):
    service_request = ServiceRequest.query.get(request_id)
    
    if service_request:
        service_request.status = 'rejected'
        db.session.commit()  # Commit the change to the database
    
    return redirect(url_for('professional.provider_dashboard'))  # Redirect back to the dashboard



@professional_bp.route('summary')
def summary_page():
    professional_id = session.get('user_id')
    
    if not professional_id:
        return redirect(url_for('auth.login'))
    
    # Fetch the logged-in professional's details
    professional = ServiceProfessional.query.get(professional_id)
    if not professional:
        return redirect(url_for('auth.login'))
    
    # Fetch ratings data
    ratings = [r.rating for r in ServiceRequest.query.filter_by(professional_id=professional.id).with_entities(ServiceRequest.rating).all()]
    
    # Use Counter to count occurrences of each rating from 1 to 5
    ratings_count = Counter(ratings)
    ratings_data = {str(rating): ratings_count.get(rating, 0) for rating in range(1, 6)}
    
    # Fetch the count of service requests based on status
    total_accepted = ServiceRequest.query.filter_by(professional_id=professional.id, status='accepted').count()
    total_closed = ServiceRequest.query.filter_by(professional_id=professional.id, status='closed').count()
    total_requested = ServiceRequest.query.filter_by(professional_id=professional.id, status='requested').count()

    # Prepare service request data for bar chart
    service_requests_data = {
        'Accepted': total_accepted,
        'Closed': total_closed,
        'Requested': total_requested
    }

    # Render the template with the fetched data
    return render_template('provider_summary_page.html', 
                           professional=professional, 
                           ratings_data=ratings_data, 
                           service_requests_data=service_requests_data)



# --------------------- Customer Routes ----------------------- #

# Customer dashboard
@customer_bp.route('/home')
def customer_homepage():
    services = Service.query.all()
    services_history = ServiceRequest.query.filter_by(customer_id=session['user_id'])

    return render_template('customer_homepage.html', services=services, records=services_history)

@customer_bp.route('/get_providers', methods=['GET'])
def get_providers():
    # Retrieve 'service_name' from the query parameters
    service_name = request.args.get('service_name')
    print("Service Name:", service_name)
    
    # Query based on the service name
    providers = ServiceProfessional.query.filter(ServiceProfessional.service_type == service_name).all()
    services_history = ServiceRequest.query.filter_by(customer_id=session['user_id'])
    return render_template("customer_see_providers.html", providers=providers, service_name=service_name, records=services_history)

# Service request route
@customer_bp.route('/request_service', methods=['GET', 'POST'])
def request_service():
    if request.method == 'POST':
        service_id = request.form.get('service_id')
        professional_id = request.form.get('professional_id')
        
        new_request = ServiceRequest(service_id=service_id, customer_id=session['user_id'], professional_id=professional_id)
        db.session.add(new_request)
        db.session.commit()
        return redirect(url_for('customer.customer_homepage'))

@customer_bp.route('/delete_service', methods=['GET', 'POST'])
def delete_service():
    if request.method == 'POST':
        service_id = request.form.get('service_id')
        service_request = ServiceRequest.query.get(service_id)

        db.session.delete(service_request)
        db.session.commit()
        
        return redirect(url_for('customer.customer_homepage'))


from datetime import datetime

@customer_bp.route('/close_service/<int:service_id>', methods=['GET', 'POST'])
def close_service(service_id):
    service_request = ServiceRequest.query.get(service_id)
    
    if request.method == 'POST' and service_request:
        # Get the professional handling this service request
        professional = ServiceProfessional.query.get(service_request.professional_id)
        
        # Get the rating and remarks from the form
        rating = request.form.get('rating')
        remarks = request.form.get('remarks')
        
        # Update the service request details
        service_request.status = 'closed'
        service_request.rating = int(rating)  # Convert rating to an integer
        service_request.remarks = remarks
        service_request.date_of_completion = datetime.utcnow()
        
        # Commit the service request changes
        db.session.commit()
        
        # Update the professional's average rating
        if professional:
            # Fetch all ratings for this professional's completed requests
            completed_requests = ServiceRequest.query.filter_by(
                professional_id=professional.id, status='closed'
            ).all()
            
            # Calculate the new average rating
            total_ratings = sum(req.rating for req in completed_requests if req.rating)
            num_ratings = len([req for req in completed_requests if req.rating is not None])
            professional.rating = total_ratings / num_ratings if num_ratings > 0 else 0
            
            # Commit the professional's updated rating
            db.session.commit()
        
        return redirect(url_for('customer.customer_homepage'))

    # Render the form for the user to submit their rating and remarks
    return render_template('close_request_form.html', service_request=service_request)






@customer_bp.route('/search', methods=['GET', 'POST'])
def search_page():
    results = []
    search_type = None

    if request.method == 'POST':
        search_type = request.form.get('search_type')
        search_query = request.form.get('search_query')

        if search_type == 'pincode':
            results = ServiceProfessional.query.filter(ServiceProfessional.pincode == search_query).all()
        elif search_type == 'name':
            results = ServiceProfessional.query.filter(ServiceProfessional.fullname == search_query).all()
        elif search_type == 'service_type':
            results = ServiceProfessional.query.filter(ServiceProfessional.service_type == search_query).all()

    return render_template('customer_search_page.html', results=results, search_type=search_type)




@customer_bp.route('/summary', methods=['GET', 'POST'])
def summary_page():

    user_id = session.get('user_id')

    # Query the number of requests for each status for the current user using SQLAlchemy
    total_requests = ServiceRequest.query.filter_by(customer_id=user_id).count()  # Total number of requests for current user
    requested = ServiceRequest.query.filter_by(customer_id=user_id, status='requested').count()  # 'requested' status for current user
    closed = ServiceRequest.query.filter_by(customer_id=user_id, status='closed').count()  # 'closed' status for current user
    rejected = ServiceRequest.query.filter_by(customer_id=user_id, status='rejected').count()  # 'rejected' status for current user
    accepted = ServiceRequest.query.filter_by(customer_id=user_id, status='accepted').count()  # 'accepted' status for current user

    # Pass the data to the template
    return render_template(
        'customer_summary_page.html', 
        total_requests=total_requests,
        requested=requested,
        closed=closed,
        rejected=rejected,
        accepted=accepted
    )
