import os
 
from file_browser import db
from flask_login import UserMixin
from sqlalchemy.event import listens_for
from file_browser.default import create_default_files_and_folders

# User model used to store user name and hashed password
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True, nullable=False, unique=True)
    username = db.Column(db.String, nullable=False, unique=True)
    password = db.Column(db.Text, nullable=False)
    
    def __str__(self):
        return self.username

# An event listener after new user registration to create his folder space + some dummy data for testing  
@listens_for(User, "after_insert")
def create_home_dir_after_insert(map, con, user):
    # Create path for new dir
    root_directory =  f"{user.username}"
    parent_dir = "file_browser/users_space"
    path = os.path.join(parent_dir, root_directory)
    
    # Create user root folder in users_space
    os.mkdir(path)
    
    # Create home dir
    home = "home"
    dir2 = f"file_browser/users_space/{root_directory}"
    path2 = os.path.join(dir2, home)
    os.mkdir(path2)
    
    # Create user folder in home
    user_folder = user.username
    dir3 = f"file_browser/users_space/{root_directory}/{home}"
    path3 = os.path.join(dir3, user_folder)
    os.mkdir(path3)
    
    # Create dummy data and folder structure
    create_default_files_and_folders(path, path3)