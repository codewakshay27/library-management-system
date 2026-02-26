"""
Routes and views for the flask application.
"""

from datetime import datetime, timedelta
from functools import wraps

from flask import flash, redirect, render_template, request, url_for
from flask.blueprints import Blueprint
from flask.views import MethodView
from flask_login import current_user, login_required, login_user, logout_user

# keep import (existing compatibility)
from werkzeug.security import check_password_hash, generate_password_hash

from . import db, login_manager
from .models import Book, Copy, User, Category

main = Blueprint("main", __name__)

# =========================
# DIRECT ISSUE
# =========================
@main.route("/issue/direct/<int:book_id>", methods=["POST"])
@login_required
def direct_issue(book_id):

    book = Book.query.get(book_id)

    if not book or book.present_copy <= 0:
        flash("Book not available!")
        return redirect(url_for("main.index"))

    existing = Copy.query.filter_by(
        issued_by=current_user.id,
        book=book.id,
        returned=False
    ).first()

    if existing:
        flash("You already issued this book!")
        return redirect(url_for("main.index"))

    copy = Copy.query.filter_by(
        book=book.id,
        issued_by=None,
        returned=False
    ).first()

    if not copy:
        flash("No available copies!")
        return redirect(url_for("main.index"))

    copy.issued_by = current_user.id
    copy.date_issued = datetime.now()
    copy.date_return = datetime.now() + timedelta(days=7)

    book.present_copy -= 1
    book.issued_copy += 1

    db.session.commit()

    flash("Book issued successfully!")
    return redirect(url_for("main.dashboard"))


# =========================
# ADMIN CHECK
# =========================
def requires_admin(f):
    @wraps(f)
    def wrapped(*args, **kwargs):

        if not current_user.is_authenticated:
            flash("Please login first!")
            return redirect(url_for("main.login"))

        if not current_user.admin:
            flash("Admin access required!")
            return redirect(url_for("main.index"))

        return f(*args, **kwargs)

    return wrapped


# =========================
# USER LOADER
# =========================
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# =========================
# HOME
# =========================
from sqlalchemy import or_

@main.route("/")
def index():

    search_query = request.args.get("search")
    category = request.args.get("category")

    books_query = Book.query

    if search_query:
        books_query = books_query.filter(
            or_(
                Book.name.ilike(f"%{search_query}%"),
                Book.author.ilike(f"%{search_query}%")
            )
        )

    if category and category != "All":
        books_query = books_query.filter_by(category=category)

    books = books_query.all()

    return render_template(
        "index.html",
        books=books,
        search_query=search_query,
        selected_category=category
    )


# =========================
# LOGIN (SAFE FIX)
# =========================
class LoginView(MethodView):

    def get(self):
        return render_template("login.html", year=datetime.now().year)

    def post(self):

        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()

        # backward compatible password check
        if user and (
            (hasattr(user, "check_password") and user.check_password(password))
            or check_password_hash(user.password, password)
            or user.password == password
        ):

            login_user(user)

            flash("Login successful!")

            if user.admin:
                return redirect(url_for("main.admin_dashboard"))
            else:
                return redirect(url_for("main.dashboard"))

        flash("Invalid email or password!")
        return redirect(url_for("main.index"))


# =========================
# REGISTER (SAFE)
# =========================
class RegisterView(MethodView):

    def get(self):
        return render_template("register.html", year=datetime.now().year)

    def post(self):

        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")

        existing = User.query.filter_by(email=email).first()

        if existing:
            flash("User already exists!")
            return redirect(url_for("main.index"))

        hashed = generate_password_hash(password)

        user = User(
            name=name,
            email=email,
            password=hashed,
            admin=False
        )

        db.session.add(user)
        db.session.commit()

        login_user(user)

        flash("Registration successful!")

        return redirect(url_for("main.dashboard"))


# =========================
# ADMIN LOGIN (SAFE)
# =========================
class AdminView(MethodView):

    def get(self):
        return render_template("admin.html", year=datetime.now().year)

    def post(self):

        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email, admin=True).first()

        if user and (
            (hasattr(user, "check_password") and user.check_password(password))
            or check_password_hash(user.password, password)
            or user.password == password
        ):

            login_user(user)

            flash("Admin login successful!")
            return redirect(url_for("main.admin_dashboard"))

        flash("Invalid admin credentials!")
        return redirect(url_for("main.index"))


# =========================
# DASHBOARD
# =========================
@main.route("/dashboard")
@login_required
def dashboard():

    books = Copy.query.filter_by(
        issued_by=current_user.id,
        returned=False
    ).all()

    return render_template(
        "dashboard.html",
        books=books,
        now=datetime.now
    )


# =========================
# ADMIN DASHBOARD
# =========================
@main.route("/admin/dashboard")
@login_required
@requires_admin
def admin_dashboard():

    books = Book.query.all()

    overdue_copies = Copy.query.filter(
        Copy.issued_by.isnot(None),
        Copy.date_return < datetime.now()
    ).all()

    return render_template(
        "admin_dashboard.html",
        books=books,
        overdue_copies=overdue_copies,
        fine_per_day=5,
        now=datetime.now
    )
# =========================
# ADD BOOK (SAFE WORKING)
# =========================
class AddBookView(MethodView):

    def get(self):

        categories = Category.query.all()

        return render_template(
            "add_book.html",
            categories=categories
        )

    def post(self):

        name = request.form.get("name")
        author = request.form.get("author")
        description = request.form.get("description")
        number = request.form.get("number")
        category_name = request.form.get("category")

        # validation
        if not name or not author or not number:
            flash("Please fill all required fields!")
            return redirect(url_for("main.add_book"))

        number = int(number)

        category = Category.query.filter_by(name=category_name).first()

        if not category:
            category = Category.query.filter_by(name="Other").first()

            if not category:
                category = Category(name="Other")
                db.session.add(category)
                db.session.commit()

        book = Book(
            name=name,
            author=author,
            description=description,
            category=category.name,
            total_copy=number,
            present_copy=number,
            issued_copy=0
        )

        db.session.add(book)
        db.session.flush()

        # create copies
        for i in range(number):

            copy = Copy(
                book=book.id,
                date_added=datetime.now(),
                returned=False
            )

            db.session.add(copy)

        db.session.commit()

        flash("Book added successfully!")

        return redirect(url_for("main.admin_dashboard"))
# =========================
# REMOVE BOOK (FULL WORKING SAFE)
# =========================
class RemoveBookView(MethodView):

    methods = ["GET", "POST"]

    def get(self):

        # only books with no active issues
        books = Book.query.filter_by(issued_copy=0).all()

        return render_template(
            "remove_book.html",
            books=books
        )


    def post(self):

        book_id = request.form.get("book")

        # safety check
        if not book_id:
            flash("Please select a book to remove!")
            return redirect(url_for("main.remove_book"))

        book = Book.query.get(int(book_id))

        if not book:
            flash("Book not found!")
            return redirect(url_for("main.remove_book"))

        try:
            # delete all copies first (important)
            Copy.query.filter_by(book=book.id).delete()

            # delete book
            db.session.delete(book)

            db.session.commit()

            flash("Book removed successfully!")

        except Exception as e:

            db.session.rollback()

            flash("Error removing book!")

        return redirect(url_for("main.admin_dashboard"))
#issu book method
class IssueBookView(MethodView):

    methods = ["GET", "POST"]

    def get(self):

        books = Book.query.filter(Book.present_copy > 0).all()

        return render_template("issue.html", books=books)

    def post(self):

        book_id = int(request.form.get("book"))

        copy = Copy.query.filter(
            Copy.book == book_id,
            Copy.issued_by.is_(None),
            Copy.returned == False
        ).first()

        if not copy:
            flash("Book not available!")
            return redirect(url_for("main.issue_book"))

        copy.issued_by = current_user.id
        copy.returned = False
        copy.date_issued = datetime.now()
        copy.date_return = datetime.now() + timedelta(days=7)

        book = Book.query.get(book_id)

        book.present_copy -= 1
        book.issued_copy += 1

        db.session.commit()

        flash("Book issued successfully!")

        return redirect(url_for("main.dashboard"))

# =========================
# RETURN BOOK (BUG FIX HERE)
# =========================
class ReturnBookView(MethodView):

    methods = ["GET", "POST"]

    def get(self):

        books = Copy.query.filter_by(
            issued_by=current_user.id,
            returned=False
        ).all()

        return render_template("return.html", books=books)

    def post(self):

        copy_id = request.form.get("book")

        copy = Copy.query.get(int(copy_id))

        if not copy:
            flash("Invalid return!")
            return redirect(url_for("main.return_book"))

        book = copy.book_obj

        book.present_copy += 1
        book.issued_copy -= 1

        # FIX: keep issued_by for history
        copy.returned = True

        db.session.commit()

        flash("Book returned successfully!")
        return redirect(url_for("main.dashboard"))


# =========================
# ISSUE HISTORY (FIXED)
# =========================
@main.route("/history")
@login_required
def issue_history():

    if current_user.admin:
        copies = Copy.query.order_by(Copy.date_issued.desc()).all()
    else:
        copies = Copy.query.filter(
            Copy.issued_by == current_user.id
        ).order_by(
            Copy.date_issued.desc()
        ).all()

    return render_template(
        "history.html",
        copies=copies,
        now=datetime.now
    )


# =========================
# LOGOUT
# =========================
@main.route("/logout")
@login_required
def logout():

    logout_user()

    flash("Logged out successfully!")

    return redirect(url_for("main.index"))


# =========================
# ROUTES (UNCHANGED)
# =========================
main.add_url_rule("/login", view_func=LoginView.as_view("login"))
main.add_url_rule("/register", view_func=RegisterView.as_view("register"))
main.add_url_rule("/admin/login", view_func=AdminView.as_view("admin"))
main.add_url_rule("/return/book",
    view_func=login_required(ReturnBookView.as_view("return_book")),
    methods=["GET", "POST"])
main.add_url_rule(
    "/issue/book",
    view_func=login_required(IssueBookView.as_view("issue_book")),
    methods=["GET", "POST"]
)
# =========================
# ADMIN ISSUE HISTORY
# =========================
@main.route("/admin/issue-history")
@login_required
@requires_admin
def admin_issue_history():

    copies = Copy.query.filter(
        Copy.date_issued.isnot(None)
    ).order_by(
        Copy.date_issued.desc()
    ).all()

    return render_template(
        "admin_issue_history.html",
        copies=copies
    )


# =========================
# ADMIN MANAGE USERS
# =========================
@main.route("/admin/manage-users")
@login_required
@requires_admin
def manage_users():

    users = User.query.filter_by(admin=False).all()

    return render_template(
        "manage_users.html",
        users=users
    )


# =========================
# ADMIN FINE REPORT
# =========================
@main.route("/admin/fine-report")
@login_required
@requires_admin
def fine_report():

    overdue = Copy.query.filter(
        Copy.returned == False,
        Copy.date_return < datetime.now()
    ).all()

    fine_data = []

    for copy in overdue:

        days_late = (datetime.now() - copy.date_return).days
        fine = days_late * 10

        fine_data.append({
            "user": copy.issue.name if copy.issue else "Unknown",
            "book": copy.book_obj.name if copy.book_obj else "Unknown",
            "days": days_late,
            "fine": fine
        })

    return render_template(
        "fine_report.html",
        fine_data=fine_data
    )


# =========================
# ADMIN DELETE USER
# =========================
@main.route("/admin/delete-user/<int:user_id>")
@login_required
@requires_admin
def delete_user(user_id):

    user = User.query.get(user_id)

    if not user or user.admin:

        flash("Invalid action!")
        return redirect(url_for("main.manage_users"))

    db.session.delete(user)
    db.session.commit()

    flash("User deleted successfully!")

    return redirect(url_for("main.manage_users"))


# =========================
# ADMIN ANALYTICS
# =========================
@main.route("/admin/analytics")
@login_required
@requires_admin
def admin_analytics():

    total_users = User.query.filter_by(admin=False).count()
    total_books = Book.query.count()
    total_issued = Copy.query.filter_by(returned=False).count()

    return render_template(
        "admin_analytics.html",
        total_users=total_users,
        total_books=total_books,
        total_issued = Copy.query.filter(
    Copy.issued_by.isnot(None),
    Copy.returned == False
).count()
    )
main.add_url_rule(
    "/add/book",
    view_func=login_required(requires_admin(AddBookView.as_view("add_book"))),
    methods=["GET", "POST"]
)

main.add_url_rule(
    "/remove/book",
    view_func=login_required(requires_admin(RemoveBookView.as_view("remove_book"))),
    methods=["GET", "POST"]
)
@main.route("/about")
def about():
    return render_template("about.html")