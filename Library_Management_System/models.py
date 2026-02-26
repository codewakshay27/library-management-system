from flask_login import UserMixin
from Library_Management_System import db

# ✅ NEW IMPORT (password security ke liye)
from werkzeug.security import generate_password_hash, check_password_hash


# =========================
# USER MODEL
# =========================
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(255))

    email = db.Column(db.String(255), unique=True)

    password = db.Column(db.String(255))

    # Relationship to Copy
    book = db.relationship("Copy", backref="issue", lazy=True)

    admin = db.Column(db.Boolean, default=False)

    # ✅ SAFE PASSWORD HASH FUNCTION (NEW)
    def set_password(self, password):
        self.password = generate_password_hash(password)

    # ✅ SAFE PASSWORD CHECK (BACKWARD COMPATIBLE)
    def check_password(self, password):

        # If password is hashed (new users)
        if self.password and self.password.startswith("pbkdf2:"):
            return check_password_hash(self.password, password)

        # If password is plain text (old users)
        return self.password == password


# =========================
# BOOK MODEL
# =========================
class Book(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(255), unique=True)

    author = db.Column(db.String(255))

    description = db.Column(db.Text)

    # CATEGORY FIELD
    category = db.Column(db.String(50), default="Other")

    # Relationship with Copy
    copies = db.relationship(
        "Copy",
        backref="book_obj",
        cascade="all, delete",
        lazy=True
    )

    total_copy = db.Column(db.Integer)

    issued_copy = db.Column(db.Integer)

    present_copy = db.Column(db.Integer)


# =========================
# COPY MODEL
# =========================
class Copy(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    date_added = db.Column(db.DateTime())

    issued_by = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=True,
        default=None
    )

    date_issued = db.Column(db.DateTime(), default=None)

    date_return = db.Column(db.DateTime(), default=None)

    # BOOK FOREIGN KEY
    book = db.Column(
        db.Integer,
        db.ForeignKey("book.id")
    )

    # HISTORY FIELD
    returned = db.Column(db.Boolean, default=False)


# =========================
# CATEGORY MODEL
# =========================
class Category(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    def __repr__(self):
        return f"<Category {self.name}>"