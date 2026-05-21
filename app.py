from dotenv import load_dotenv
load_dotenv()

import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    login_required,
    current_user,
)
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
from mysql.connector import Error
from datetime import datetime

app = Flask(__name__)
# Use environment variable for secret key
secret_key = os.getenv("FLASK_SECRET_KEY")
if not secret_key:
    raise ValueError(
        "FLASK_SECRET_KEY environment variable is not set. "
        "Please set it in your .env file before running the application."
    )
app.secret_key = secret_key

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# MySQL Database Configuration using environment variables
db_config = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "andrei"),
    "database": os.getenv("DB_NAME", "halamanan07"),
    "port": int(os.getenv("DB_PORT", "3306")),
}

# ============================================
# USER CLASS FOR FLASK-LOGIN
# ============================================


class User(UserMixin):
    def __init__(self, user_id, username, email, phone, province, city):
        self.id = user_id
        self.username = username
        self.email = email
        self.phone = phone
        self.province = province
        self.city = city


# ============================================
# DATABASE CONNECTION FUNCTION
# ============================================


def get_db_connection():
    try:
        connection = mysql.connector.connect(**db_config)
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None


# ============================================
# FLASK-LOGIN USER LOADER
# ============================================


@login_manager.user_loader
def load_user(user_id):
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
        user_data = cursor.fetchone()
        cursor.close()
        connection.close()

        if user_data:
            return User(
                user_data["user_id"],
                user_data["username"],
                user_data["email"],
                user_data["phone"],
                user_data["province"],
                user_data["city"],
            )
    return None


# ============================================
# ROUTES
# ============================================


# HOME PAGE
@app.route("/")
def home():
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)

        cursor.execute("SELECT COUNT(*) as count FROM users")
        total_farmers = cursor.fetchone()["count"]

        cursor.execute(
            "SELECT COUNT(*) as count FROM resources WHERE status = 'Available'"
        )
        total_resources = cursor.fetchone()["count"]

        cursor.execute(
            "SELECT COUNT(*) as count FROM requests WHERE status = 'Available'"
        )
        total_requests = cursor.fetchone()["count"]

        cursor.execute(
            "SELECT COUNT(*) as count FROM payments WHERE status = 'Completed'"
        )
        total_connections = cursor.fetchone()["count"]

        cursor.close()
        connection.close()

        return render_template(
            "home.html",
            total_farmers=total_farmers,
            total_resources=total_resources,
            total_requests=total_requests,
            total_connections=total_connections,
        )

    return render_template("home.html")


# LOGIN ROUTE
@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        # Try to find user by email or username
        cursor.execute(
            "SELECT * FROM users WHERE email=%s OR username=%s", (email, email)
        )
        user = cursor.fetchone()
        cursor.close()
        connection.close()
        if user:
            # Assuming you have check_password_hash imported
            if check_password_hash(user["password_hash"], password):
                user_obj = User(
                    user["user_id"],
                    user["username"],
                    user["email"],
                    user["phone"],
                    user["province"],
                    user["city"],
                )
                login_user(user_obj)
                flash("Successfully logged in!", "success")
                return redirect(url_for("home"))
            else:
                flash("Incorrect password. Please try again.", "error")
        else:
            flash(
                "No account found with that email or username. Please register first.",
                "error",
            )
        return redirect(url_for("login"))
    return render_template("login.html")


# REGISTER ROUTE
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        province = request.form.get("province")
        city = request.form.get("city")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        if password != confirm_password:
            flash("Passwords do not match", "error")
            return render_template("register.html")

        if len(password) < 6:
            flash("Password must be at least 6 characters", "error")
            return render_template("register.html")

        hashed_password = generate_password_hash(password)

        connection = get_db_connection()
        if connection:
            try:
                cursor = connection.cursor()
                cursor.execute(
                    """
                    INSERT INTO users (username, email, phone, province, city, password_hash, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                    (
                        name,
                        email,
                        phone,
                        province,
                        city,
                        hashed_password,
                        datetime.now(),
                    ),
                )

                connection.commit()
                cursor.close()
                connection.close()

                flash("Registration successful! Please login.", "success")
                return redirect(url_for("login"))
            except Error as e:
                flash(f"Registration failed: {str(e)}", "error")
                connection.close()

    return render_template("register.html")


# LOGOUT ROUTE
@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out", "success")
    return redirect(url_for("home"))


# BROWSE RESOURCES
@app.route("/browse")
@login_required
def browse():
    category = request.args.get("category", "")
    status = request.args.get("status", "")
    search = request.args.get("search", "")

    connection = get_db_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)

        query = """
            SELECT r.*, u.username as farmer_name, u.city as farmer_city, u.province as farmer_province
            FROM resources r
            JOIN users u ON r.user_id = u.user_id
            WHERE 1=1
        """
        params = []
        if category:
            query += " AND r.category = %s"
            params.append(category)
        if status:
            query += " AND r.status = %s"
            params.append(status)
        if search:
            query += " AND (r.name LIKE %s OR r.description LIKE %s)"
            like_val = f"%{search}%"
            params.extend([like_val, like_val])
        query += " ORDER BY r.created_at DESC"
        cursor.execute(query, params)
        resources = cursor.fetchall()

        # For recent requests section, get last 6 available requests
        cursor.execute("""
            SELECT r.*, u.username as farmer_name
            FROM requests r
            JOIN users u ON r.user_id = u.user_id
            WHERE r.status = 'Available'
            ORDER BY r.created_at DESC
            LIMIT 6
        """)
        recent_requests = cursor.fetchall()

        cursor.close()
        connection.close()
        return render_template(
            "browse.html",
            resources=resources,
            recent_requests=recent_requests,
            search_query=search,
            category=category,
            status=status,
        )

    return render_template(
        "browse.html",
        resources=[],
        recent_requests=[],
        search_query="",
        category="",
        status="",
    )


# POST OFFER ROUTE
@app.route("/post-offer", methods=["GET", "POST"])
@login_required
def post_offer():
    if request.method == "POST":
        category = request.form.get("category")
        name = request.form.get("name")
        description = request.form.get("description")
        start_available_date = request.form.get("start_available_date")
        end_available_date = request.form.get("end_available_date")
        arrangement = request.form.get("arrangement")
        resource_type = request.form.get("resource_type")

        connection = get_db_connection()
        if connection:
            try:
                cursor = connection.cursor()
                cursor.execute(
                    """
                    INSERT INTO resources (user_id, category, name, description, 
                                          start_available_date, end_available_date, status, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                    (
                        current_user.id,
                        category,
                        name,
                        description,
                        start_available_date,
                        end_available_date,
                        "Available",
                        datetime.now(),
                    ),
                )

                connection.commit()
                cursor.close()
                connection.close()

                flash("Your offer has been posted!", "success")
                return redirect(url_for("browse"))
            except Error as e:
                flash(f"Error posting offer: {str(e)}", "error")
                connection.close()

    return render_template("post_offer.html")


# POST REQUEST ROUTE
@app.route("/post-request", methods=["GET", "POST"])
@login_required
def post_request():
    if request.method == "POST":
        category = request.form.get("category")
        needed_item = request.form.get("needed_item")
        description = request.form.get("description")
        needed_date = request.form.get("needed_date")
        urgency = request.form.get("urgency")
        arrangement = request.form.get("arrangement")

        connection = get_db_connection()
        if connection:
            try:
                cursor = connection.cursor()
                cursor.execute(
                    """
                    INSERT INTO requests (user_id, category, needed_item, description, status, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """,
                    (
                        current_user.id,
                        category,
                        needed_item,
                        description,
                        "Available",
                        datetime.now(),
                    ),
                )

                connection.commit()
                cursor.close()
                connection.close()

                flash("Your request has been posted!", "success")
                return redirect(url_for("browse"))
            except Error as e:
                flash(f"Error posting request: {str(e)}", "error")
                connection.close()

    return render_template("post_request.html")


# MY CONNECTIONS
@app.route("/my-connections")
@login_required
def my_connections():
    user_id = current_user.id

    connection = get_db_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)

        # Get pending connections
        cursor.execute(
            """
            SELECT * FROM connections 
            WHERE (requester_id = %s OR helper_id = %s) 
            AND status = 'Pending'
            ORDER BY created_at DESC
        """,
            (user_id, user_id),
        )
        pending = cursor.fetchall()

        # Get approved connections
        cursor.execute(
            """
            SELECT * FROM connections 
            WHERE (requester_id = %s OR helper_id = %s) 
            AND status = 'Approved'
            ORDER BY created_at DESC
        """,
            (user_id, user_id),
        )
        approved = cursor.fetchall()

        # Get completed connections
        cursor.execute(
            """
            SELECT * FROM connections 
            WHERE (requester_id = %s OR helper_id = %s) 
            AND status = 'Completed'
            ORDER BY created_at DESC
        """,
            (user_id, user_id),
        )
        completed = cursor.fetchall()

        # Get rejected connections
        cursor.execute(
            """
            SELECT * FROM connections 
            WHERE (requester_id = %s OR helper_id = %s) 
            AND status = 'Rejected'
            ORDER BY created_at DESC
        """,
            (user_id, user_id),
        )
        rejected = cursor.fetchall()

        cursor.close()
        connection.close()

        return render_template(
            "my_connections.html",
            pending_connections=pending,
            approved_connections=approved,
            completed_connections=completed,
            rejected_connections=rejected,
            pending_count=len(pending),
            approved_count=len(approved),
            completed_count=len(completed),
            rejected_count=len(rejected),
        )

    return render_template("my_connections.html")


# PROFILE ROUTE (FIXED - WITH PROPER CONNECTION HISTORY)
@app.route("/profile")
@login_required
def profile():
    user_id = current_user.id
    connection = get_db_connection()

    if connection:
        cursor = connection.cursor(dictionary=True)

        # Get user's offers
        cursor.execute(
            "SELECT * FROM resources WHERE user_id = %s ORDER BY created_at DESC",
            (user_id,),
        )
        my_offers = cursor.fetchall()

        # Get user's requests
        cursor.execute(
            "SELECT * FROM requests WHERE user_id = %s ORDER BY created_at DESC",
            (user_id,),
        )
        my_requests = cursor.fetchall()

        # Get connection history - FIXED QUERY
        cursor.execute(
            """
            SELECT 
                c.*,
                CASE 
                    WHEN c.requester_id = %s THEN u2.username 
                    ELSE u1.username 
                END as other_farmer_name,
                COALESCE(r.name, req.needed_item) as resource_name,
                CASE 
                    WHEN c.resource_id IS NOT NULL THEN 'Offer'
                    WHEN c.request_id IS NOT NULL THEN 'Request'
                    ELSE 'Unknown'
                END as connection_type
            FROM connections c
            LEFT JOIN users u1 ON c.requester_id = u1.user_id
            LEFT JOIN users u2 ON c.helper_id = u2.user_id
            LEFT JOIN resources r ON c.resource_id = r.resource_id
            LEFT JOIN requests req ON c.request_id = req.request_id
            WHERE c.requester_id = %s OR c.helper_id = %s
            ORDER BY c.created_at DESC
        """,
            (user_id, user_id, user_id),
        )
        connection_history = cursor.fetchall()

        # Get payments where user is buyer (PURCHASES)
        cursor.execute(
            """
            SELECT p.*, r.name as resource_name, u.username as seller_name, u.phone as seller_phone
            FROM payments p
            JOIN resources r ON p.resource_id = r.resource_id
            JOIN users u ON p.seller_id = u.user_id
            WHERE p.buyer_id = %s
            ORDER BY p.created_at DESC
        """,
            (user_id,),
        )
        purchases = cursor.fetchall()

        # Get payments where user is seller (SALES)
        cursor.execute(
            """
            SELECT p.*, r.name as resource_name, u.username as buyer_name, u.phone as buyer_phone
            FROM payments p
            JOIN resources r ON p.resource_id = r.resource_id
            JOIN users u ON p.buyer_id = u.user_id
            WHERE p.seller_id = %s
            ORDER BY p.created_at DESC
        """,
            (user_id,),
        )
        sales = cursor.fetchall()

        cursor.close()
        connection.close()

        return render_template(
            "profile.html",
            my_offers=my_offers,
            my_requests=my_requests,
            connection_history=connection_history,
            purchases=purchases,
            sales=sales,
            total_offers=len(my_offers),
            total_requests=len(my_requests),
            total_connections=len(connection_history),
            total_purchases=len(purchases),
            total_sales=len(sales),
        )

    return render_template("profile.html")


# ============================================
# PAYMENT SYSTEM ROUTES (NEW)
# ============================================


# VIEW RESOURCE DETAILS
@app.route("/resource/<int:resource_id>")
@login_required
def view_resource(resource_id):
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)

        # Get resource details
        cursor.execute(
            """
            SELECT r.*, u.username as farmer_name, u.phone, u.city, u.province, u.user_id
            FROM resources r
            JOIN users u ON r.user_id = u.user_id
            WHERE r.resource_id = %s
        """,
            (resource_id,),
        )
        resource = cursor.fetchone()

        # Check if current user already inquired
        if resource:
            cursor.execute(
                """
                SELECT * FROM inquiries 
                WHERE resource_id = %s AND buyer_id = %s
            """,
                (resource_id, current_user.id),
            )
            existing_inquiry = cursor.fetchone()
        else:
            existing_inquiry = None

        cursor.close()
        connection.close()

        if resource:
            return render_template(
                "resource_detail.html",
                resource=resource,
                has_inquired=existing_inquiry is not None,
            )
        else:
            flash("Resource not found", "error")
            return redirect(url_for("browse"))

    flash("Error loading resource", "error")
    return redirect(url_for("browse"))


# INQUIRE - SEND NOTIFICATION TO SELLER
@app.route("/inquire/<int:resource_id>", methods=["POST"])
@login_required
def inquire_resource(resource_id):
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)

            # Get resource info
            cursor.execute(
                "SELECT user_id FROM resources WHERE resource_id = %s", (resource_id,)
            )
            resource = cursor.fetchone()

            if not resource:
                flash("Resource not found", "error")
                cursor.close()
                connection.close()
                return redirect(url_for("browse"))

            seller_id = resource["user_id"]

            if seller_id == current_user.id:
                flash("You cannot inquire about your own resource", "error")
                cursor.close()
                connection.close()
                return redirect(url_for("view_resource", resource_id=resource_id))

            # Check if already inquired
            cursor.execute(
                """
                SELECT inquiry_id FROM inquiries 
                WHERE resource_id = %s AND buyer_id = %s
            """,
                (resource_id, current_user.id),
            )
            existing = cursor.fetchone()

            if existing:
                flash("You have already sent an inquiry for this resource", "info")
            else:
                # Create inquiry
                cursor.execute(
                    """
                    INSERT INTO inquiries (resource_id, buyer_id, seller_id, status, created_at)
                    VALUES (%s, %s, %s, %s, %s)
                """,
                    (resource_id, current_user.id, seller_id, "Sent", datetime.now()),
                )

                connection.commit()
                flash("✅ Inquiry sent! The seller will be notified.", "success")

            cursor.close()
            connection.close()
            return redirect(url_for("view_resource", resource_id=resource_id))

        except Error as e:
            flash(f"Error sending inquiry: {str(e)}", "error")
            connection.close()
            return redirect(url_for("browse"))

    flash("Database connection error", "error")
    return redirect(url_for("browse"))


# PAYMENT HISTORY
@app.route("/payment-history")
@login_required
def payment_history():
    user_id = current_user.id
    connection = get_db_connection()

    if connection:
        cursor = connection.cursor(dictionary=True)

        # Get payments where user is buyer
        cursor.execute(
            """
            SELECT p.*, r.name as resource_name, u.username as seller_name, u.phone as seller_phone
            FROM payments p
            JOIN resources r ON p.resource_id = r.resource_id
            JOIN users u ON p.seller_id = u.user_id
            WHERE p.buyer_id = %s
            ORDER BY p.created_at DESC
        """,
            (user_id,),
        )
        purchases = cursor.fetchall()

        # Get payments where user is seller
        cursor.execute(
            """
            SELECT p.*, r.name as resource_name, u.username as buyer_name, u.phone as buyer_phone
            FROM payments p
            JOIN resources r ON p.resource_id = r.resource_id
            JOIN users u ON p.buyer_id = u.user_id
            WHERE p.seller_id = %s
            ORDER BY p.created_at DESC
        """,
            (user_id,),
        )
        sales = cursor.fetchall()

        cursor.close()
        connection.close()

        return render_template("payment_history.html", purchases=purchases, sales=sales)

    return render_template("payment_history.html")


# INQUIRIES/NOTIFICATIONS
@app.route("/inquiries")
@login_required
def inquiries():
    user_id = current_user.id
    connection = get_db_connection()

    if connection:
        cursor = connection.cursor(dictionary=True)

        # Get inquiries for resources I'm selling
        cursor.execute(
            """
            SELECT i.*, r.name as resource_name, u.username as buyer_name, u.phone as buyer_phone, u.city, u.province
            FROM inquiries i
            JOIN resources r ON i.resource_id = r.resource_id
            JOIN users u ON i.buyer_id = u.user_id
            WHERE i.seller_id = %s
            ORDER BY i.created_at DESC
        """,
            (user_id,),
        )
        received_inquiries = cursor.fetchall()

        cursor.close()
        connection.close()

        return render_template("inquiries.html", received_inquiries=received_inquiries)

    return render_template("inquiries.html")


# ============================================
# SELLER PAYMENT APPROVAL ROUTES (NEW)
# ============================================


# PENDING PAYMENTS FOR SELLER (FIXED - CORRECTED QUERY)
@app.route("/pending-payments")
@login_required
def pending_payments():
    seller_id = current_user.id
    connection = get_db_connection()

    if connection:
        cursor = connection.cursor(dictionary=True)

        try:
            # Get ONLY pending payments (not already approved/rejected)
            cursor.execute(
                """
                SELECT p.*, r.name as resource_name, u.username as buyer_name, u.phone as buyer_phone, u.city, u.province
                FROM payments p
                JOIN resources r ON p.resource_id = r.resource_id
                JOIN users u ON p.buyer_id = u.user_id
                WHERE p.seller_id = %s AND p.status = 'Pending'
                ORDER BY p.created_at DESC
            """,
                (seller_id,),
            )
            pending_payments_list = cursor.fetchall()

            # Also get completed and rejected for reference
            cursor.execute(
                """
                SELECT p.*, r.name as resource_name, u.username as buyer_name
                FROM payments p
                JOIN resources r ON p.resource_id = r.resource_id
                JOIN users u ON p.buyer_id = u.user_id
                WHERE p.seller_id = %s AND (p.status = 'Completed' OR p.status = 'Failed')
                ORDER BY p.created_at DESC
                LIMIT 5
            """,
                (seller_id,),
            )
            recent_actions = cursor.fetchall()

            cursor.close()
            connection.close()

            return render_template(
                "seller_payments.html",
                pending_payments=pending_payments_list,
                recent_actions=recent_actions,
                payment_count=len(pending_payments_list),
            )
        except Error as e:
            print(f"Database error: {str(e)}")
            cursor.close()
            connection.close()
            flash(f"Error loading payments: {str(e)}", "error")
            return render_template("seller_payments.html", payment_count=0)

    return render_template("seller_payments.html", payment_count=0)


# APPROVE PAYMENT
@app.route("/approve-payment/<int:payment_id>", methods=["POST"])
@login_required
def approve_payment(payment_id):
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)

            # Get payment details
            cursor.execute(
                "SELECT * FROM payments WHERE payment_id = %s", (payment_id,)
            )
            payment = cursor.fetchone()

            if not payment:
                flash("Payment not found", "error")
                cursor.close()
                connection.close()
                return redirect(url_for("pending_payments"))

            # Check if current user is the seller
            if payment["seller_id"] != current_user.id:
                flash("You are not authorized to approve this payment", "error")
                cursor.close()
                connection.close()
                return redirect(url_for("pending_payments"))

            # Update payment status to Completed
            cursor.execute(
                """
                UPDATE payments 
                SET status = %s, approved_by = %s, approved_at = %s
                WHERE payment_id = %s
            """,
                ("Completed", current_user.id, datetime.now(), payment_id),
            )

            connection.commit()
            flash("✅ Payment approved successfully!", "success")

            cursor.close()
            connection.close()
            return redirect(url_for("pending_payments"))

        except Error as e:
            flash(f"Error approving payment: {str(e)}", "error")
            connection.close()
            return redirect(url_for("pending_payments"))

    flash("Database connection error", "error")
    return redirect(url_for("pending_payments"))


# REJECT PAYMENT
@app.route("/reject-payment/<int:payment_id>", methods=["POST"])
@login_required
def reject_payment(payment_id):
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)

            # Get payment details
            cursor.execute(
                "SELECT * FROM payments WHERE payment_id = %s", (payment_id,)
            )
            payment = cursor.fetchone()

            if not payment:
                flash("Payment not found", "error")
                cursor.close()
                connection.close()
                return redirect(url_for("pending_payments"))

            # Check if current user is the seller
            if payment["seller_id"] != current_user.id:
                flash("You are not authorized to reject this payment", "error")
                cursor.close()
                connection.close()
                return redirect(url_for("pending_payments"))

            rejection_reason = request.form.get(
                "rejection_reason", "No reason provided"
            )

            # Update payment status to Failed
            cursor.execute(
                """
                UPDATE payments 
                SET status = %s, approved_by = %s, approved_at = %s, rejection_reason = %s
                WHERE payment_id = %s
            """,
                (
                    "Failed",
                    current_user.id,
                    datetime.now(),
                    rejection_reason,
                    payment_id,
                ),
            )

            connection.commit()
            flash("❌ Payment rejected. Buyer has been notified.", "success")

            cursor.close()
            connection.close()
            return redirect(url_for("pending_payments"))

        except Error as e:
            flash(f"Error rejecting payment: {str(e)}", "error")
            connection.close()
            return redirect(url_for("pending_payments"))

    flash("Database connection error", "error")
    return redirect(url_for("pending_payments"))


# UPDATE PAYMENT ROUTE TO SET INITIAL STATUS AS 'Pending'
# REPLACE THE EXISTING /payment ROUTE WITH THIS:


# PAYMENT PAGE (UPDATED WITH TRANSACTION_REF)
@app.route("/payment/<int:resource_id>", methods=["GET", "POST"])
@login_required
def payment(resource_id):
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT r.*, u.username as farmer_name, u.phone, u.city, u.province, u.user_id
            FROM resources r
            JOIN users u ON r.user_id = u.user_id
            WHERE r.resource_id = %s
        """,
            (resource_id,),
        )
        resource = cursor.fetchone()

        if request.method == "POST":
            amount = request.form.get("amount")
            payment_method = request.form.get("payment_method")
            transaction_ref = request.form.get(
                "transaction_ref"
            )  # NEW: Get transaction ref
            notes = request.form.get("notes")

            try:
                # Create payment record with transaction reference
                cursor.execute(
                    """
                    INSERT INTO payments (resource_id, buyer_id, seller_id, amount, payment_method, 
                                        status, transaction_ref, notes, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                    (
                        resource_id,
                        current_user.id,
                        resource["user_id"],
                        amount,
                        payment_method,
                        "Pending",
                        transaction_ref,
                        notes,
                        datetime.now(),
                    ),
                )

                connection.commit()
                flash("✅ Payment submitted! Waiting for seller approval.", "success")
                cursor.close()
                connection.close()
                return redirect(url_for("payment_history"))

            except Error as e:
                flash(f"Error processing payment: {str(e)}", "error")

        cursor.close()
        connection.close()

        if resource:
            return render_template("payment_page.html", resource=resource)
        else:
            flash("Resource not found", "error")
            return redirect(url_for("browse"))

    flash("Database connection error", "error")
    return redirect(url_for("browse"))


# EDIT OFFER ROUTE
@app.route("/edit-offer/<int:resource_id>", methods=["GET", "POST"])
@login_required
def edit_offer(resource_id):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM resources WHERE resource_id=%s AND user_id=%s",
        (resource_id, current_user.id),
    )
    offer = cursor.fetchone()
    if not offer:
        flash("Offer not found or you don't have permission to edit.", "error")
        cursor.close()
        connection.close()
        return redirect(url_for("profile"))

    if request.method == "POST":
        category = request.form.get("category")
        name = request.form.get("name")
        description = request.form.get("description")
        start_available_date = request.form.get("start_available_date")
        end_available_date = request.form.get("end_available_date")
        arrangement = request.form.get("arrangement")
        resource_type = request.form.get("resource_type")
        cursor.execute(
            """
            UPDATE resources SET category=%s, name=%s, description=%s, start_available_date=%s, end_available_date=%s, arrangement=%s, resource_type=%s
            WHERE resource_id=%s AND user_id=%s
        """,
            (
                category,
                name,
                description,
                start_available_date,
                end_available_date,
                arrangement,
                resource_type,
                resource_id,
                current_user.id,
            ),
        )
        connection.commit()
        flash("Offer updated successfully!", "success")
        cursor.close()
        connection.close()
        return redirect(url_for("profile"))
    cursor.close()
    connection.close()
    return render_template("edit_offer.html", offer=offer)


# EDIT REQUEST ROUTE
@app.route("/edit-request/<int:request_id>", methods=["GET", "POST"])
@login_required
def edit_request(request_id):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM requests WHERE request_id=%s AND user_id=%s",
        (request_id, current_user.id),
    )
    req = cursor.fetchone()
    if not req:
        flash("Request not found or you don't have permission to edit.", "error")
        cursor.close()
        connection.close()
        return redirect(url_for("profile"))

    if request.method == "POST":
        category = request.form.get("category")
        needed_item = request.form.get("needed_item")
        description = request.form.get("description")
        needed_date = request.form.get("needed_date")
        urgency = request.form.get("urgency")
        arrangement = request.form.get("arrangement")
        cursor.execute(
            """
            UPDATE requests SET category=%s, needed_item=%s, description=%s, needed_date=%s, urgency=%s, arrangement=%s
            WHERE request_id=%s AND user_id=%s
        """,
            (
                category,
                needed_item,
                description,
                needed_date,
                urgency,
                arrangement,
                request_id,
                current_user.id,
            ),
        )
        connection.commit()
        flash("Request updated successfully!", "success")
        cursor.close()
        connection.close()
        return redirect(url_for("profile"))
    cursor.close()
    connection.close()
    return render_template("edit_request.html", req=req)


# ============================================
# ERROR HANDLERS
# ============================================


@app.errorhandler(404)
def page_not_found(error):
    return redirect(url_for("home")), 404


@app.errorhandler(500)
def internal_error(error):
    return redirect(url_for("home")), 500


# ============================================
# RUN APP
# ============================================

if __name__ == "__main__":
    # Get debug mode from environment variable, default to False for security
    debug_mode = os.getenv("FLASK_DEBUG", "False").lower() in ["true", "1", "yes"]
    port = int(os.getenv("FLASK_PORT", "5000"))
    app.run(debug=debug_mode, port=port)
