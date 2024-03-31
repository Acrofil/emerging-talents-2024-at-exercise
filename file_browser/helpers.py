import os
from pathlib import Path

from file_browser import app, basedir
from file_browser import ALLOWED_EXTENSIONS
from flask import session, flash, url_for, redirect
import datetime
import re
import hashlib

def get_user_location_path(parent_path, requested_path):
    """
    This function constructs URL path based on parent and requested paths
    """
    if parent_path == '..':
        return url_for('index') 
    else:
        return url_for('index', requested_path=requested_path)

def get_user_upload_folder():
    """
    Gets the current user working directory.
    Returns None if there is no such user / not loged in.
    user.username is stored in
    :session['user']
    """
    if session["user"]:
        user = session['user']
        
        upload_folder = app.config['UPLOAD_FOLDER']
        default_upload_folder = f"{basedir}/{upload_folder}"
        #path_to_home = f"{default_upload_folder}/{user}/home/"
        #user_folder = os.path.join(path_to_home, user)
        
        path_to_user_root = f"{default_upload_folder}"
        user_folder2 = os.path.join(path_to_user_root, user)
        
        return user_folder2
    
    return None

def get_icon_class(file_name):
    """
    This will set bootstrap icon for file_name type if its in
    :file_types
    """
    file_extension = Path(file_name).suffix
    file_extension = file_extension[1:] if file_extension.startswith(".") else file_extension
    
    file_types = ["aac", "ai", "bmp", "cs", "css", "csv", "doc", "docx", "exe", "gif", "heic", "html", "java", "jpg", "js", "json", "jsx", "key", "m4p", "md", "mdx", "mov", "mp3",
                 "mp4", "otf", "pdf", "php", "png", "pptx", "psd", "py", "raw", "rb", "sass", "scss", "sh", "sql", "svg", "tiff", "tsx", "ttf", "txt", "wav", "woff", "xlsx", "xml", "yml"]
    
    file_class_name = f"bi bi-filetype-{file_extension}" if file_extension in file_types else "bi bi-file-earmark"
    
    return file_class_name

def get_readable_byte_size(num, suffix="B"):
    """
    Convert file bytes to human readable data
    """
    for unit in ("", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"):
        if abs(num) < 1024.0:
            return f"{num:3.1f}{unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f}Yi{suffix}"

def get_time_stamp(time_seconds):
    time_object = datetime.datetime.fromtimestamp(time_seconds)
    time_string = datetime.datetime.strftime(time_object, '%d-%m-%Y %H:%M:%S')
    return time_string
    
def convert_file_info(file, user_path):
    """
    Get each file needed stat using
    :os.stat()
    Then convert it to human readable information using
    :get_readable_byte_size()
    :get_time_stamp()
    And set file or folder icon and type using
    :get_icon_class()
    """
    file_stat = os.stat(file)
    file_bytes = get_readable_byte_size(file_stat.st_size)
    file_time = get_time_stamp(file_stat.st_mtime)
    file_created_time = get_time_stamp(file_stat.st_ctime)
    
    file_icon = "bi bi-folder-fill" if os.path.isdir(file.path) else get_icon_class(file.name)
    file_type = "folder" if os.path.isdir(file.path) else "file"

    return {'name': file.name,
            'size': file_bytes,
            'created_time':file_created_time,
            'modified_time': file_time,
            'file_icon': file_icon,
            'file_link': os.path.relpath(file.path, user_path),
            'file_type': file_type,
            }

def sanitize_folder_name(folder_name):
    """
    Sanitize folder name by removing occurences like
    .. / . <> {} [] | : 
    """
    # Remove invalid characters and add spaces
    folder_name = re.sub(r'[\\/:"*?\[\]\.\.{}<>|]', ' ', folder_name)
    
    # Replace spaces with underscores
    folder_name = folder_name.replace(' ', '_')
    
    # If max length is exceeded cut the name from start to max
    max_length = 100
    if len(folder_name) > max_length:
        folder_name = folder_name[:max_length]
    
    return folder_name

def redirect_url_to_page_and_path(to_path="", to_page='index'):
    """
    Function to redirect to index url with or without current path position
    For example if user is in /home/username/my_folder it will return the user to their folder eg my_folder
    """
    return redirect(url_for(to_page, requested_path=to_path))

def calculate_file_hash(file_path):
    """
    Helper function to calculate file hash using
    :hashlib
    """
    hash = hashlib.md5()
    
    with open(file_path, 'rb') as f:
        while block := f.read(4096):
            hash.update(block)
    return hash.hexdigest()

def allowed_file(filename):
    """
    Allowed extensions
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS