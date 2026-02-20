from flask_wtf import FlaskForm
from wtforms import DateTimeLocalField, PasswordField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError

from .models import User


class RegisterForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8, max=128)])
    confirm_password = PasswordField("Confirm Password", validators=[DataRequired(), EqualTo("password")])
    submit = SubmitField("Register")

    def validate_email(self, field):
        if User.query.filter_by(email=field.data.lower().strip()).first():
            raise ValidationError("Email is already registered.")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")


class AccessAttemptForm(FlaskForm):
    pin = PasswordField("PIN", validators=[DataRequired(), Length(min=4, max=20)])
    submit = SubmitField("Attempt Access")


class AccessWindowForm(FlaskForm):
    user_id = SelectField("User", coerce=int, validators=[DataRequired()])
    start_time = DateTimeLocalField("Start", format="%Y-%m-%dT%H:%M", validators=[DataRequired()])
    end_time = DateTimeLocalField("End", format="%Y-%m-%dT%H:%M", validators=[DataRequired()])
    submit = SubmitField("Set Window")


class RoleExpiryForm(FlaskForm):
    role_expires_at = DateTimeLocalField("Temporary admin until", format="%Y-%m-%dT%H:%M", validators=[DataRequired()])
    submit = SubmitField("Set temporary admin")
