from datetime import datetime

from flask_wtf import FlaskForm
from wtforms import DateTimeLocalField, PasswordField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError


class RegisterForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8, max=128)])
    confirm_password = PasswordField(
        "Confirm Password", validators=[DataRequired(), EqualTo("password", message="Passwords must match")]
    )
    submit = SubmitField("Register")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")


class PinAttemptForm(FlaskForm):
    entered_code = PasswordField("PIN Code", validators=[DataRequired(), Length(min=4, max=12)])
    submit = SubmitField("Attempt Access")


class AccessWindowForm(FlaskForm):
    user_id = SelectField("User", coerce=int, validators=[DataRequired()])
    start_time = DateTimeLocalField("Start", format="%Y-%m-%dT%H:%M", validators=[DataRequired()])
    end_time = DateTimeLocalField("End", format="%Y-%m-%dT%H:%M", validators=[DataRequired()])
    submit = SubmitField("Save Window")

    def validate_end_time(self, field):
        if self.start_time.data and field.data and field.data <= self.start_time.data:
            raise ValidationError("End time must be after start time")


class TempAdminForm(FlaskForm):
    role_expires_at = DateTimeLocalField("Admin role expires at", format="%Y-%m-%dT%H:%M", validators=[DataRequired()])
    submit = SubmitField("Set Temporary Admin")

    def validate_role_expires_at(self, field):
        if field.data <= datetime.utcnow():
            raise ValidationError("Expiry must be in the future")


class LogFilterForm(FlaskForm):
    user_id = StringField("User ID")
    result = SelectField("Result", choices=[("", "All"), ("GRANT", "GRANT"), ("DENY", "DENY")])
    start_time = DateTimeLocalField("From", format="%Y-%m-%dT%H:%M")
    end_time = DateTimeLocalField("To", format="%Y-%m-%dT%H:%M")
    submit = SubmitField("Filter")
