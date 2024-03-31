from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FileField
from wtforms.validators import DataRequired, Length, EqualTo, equal_to

USERNAME_EMPTY_MSG = "Username cannot be empty!"
PASSWORD_FIELD_EMPTY_MSG = "Password field cannot be empty!"
MIN_MAX_LENGHT_MSG = "Minimum length is 5 max 15!"

"""
Forms for login, registration, create folder and upload file
Some basic validation and message feedback
"""

class UserFormLogin(FlaskForm):
    username = StringField("Username", validators=[DataRequired(message=USERNAME_EMPTY_MSG), Length(min=5, max=15, message=MIN_MAX_LENGHT_MSG)])
    password = PasswordField("Password", validators=[DataRequired(message=PASSWORD_FIELD_EMPTY_MSG)])
    login_btn = SubmitField("Login")

class UserFormRegister(FlaskForm):
    username = StringField("Username", validators=[DataRequired(USERNAME_EMPTY_MSG), Length(min=5, max=15, message=MIN_MAX_LENGHT_MSG)])
    password = PasswordField("Password", validators=[DataRequired(message=PASSWORD_FIELD_EMPTY_MSG)])
    confirm_password = PasswordField("Confirm password", validators=[DataRequired(message=PASSWORD_FIELD_EMPTY_MSG), EqualTo("password", message="Passwords dont match!")])
    register_btn = SubmitField("Register")

class CreateFolderForm(FlaskForm):
    folder_name = StringField("Folder name", render_kw={"placeholder": "New Folder"})
    folder_path = StringField("Folder path", render_kw={"readonly": True, "hidden": True})
    create_btn = SubmitField("Create")
    
class UploadFileForm(FlaskForm):
    upload_file_name = FileField("File name")
    folder_path = StringField("Folder path", render_kw={"readonly": True, "hidden": True})
    upload_btn = SubmitField("Upload")