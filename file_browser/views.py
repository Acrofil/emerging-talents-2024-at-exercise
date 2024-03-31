import os
from pathlib import Path
from file_browser import db, app, basedir, csrf

from flask import request, redirect, render_template, flash, url_for, session, abort, send_file, jsonify
from flask_login import login_required, login_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash, safe_join
from werkzeug.utils import secure_filename

from file_browser.models import User
from file_browser.forms import UserFormLogin, UserFormRegister, CreateFolderForm, UploadFileForm
from file_browser.helpers import get_user_upload_folder, convert_file_info, get_user_location_path, sanitize_folder_name
from file_browser.helpers import redirect_url_to_page_and_path
from file_browser.helpers import allowed_file
from file_browser.helpers import calculate_file_hash

@app.route("/", defaults={"requested_path": ""}, methods=["GET", "POST"])
@app.route("/<path:requested_path>")
@login_required
def index(requested_path):
    
    user = session['user']
    create_folder_form = CreateFolderForm()
    upload_file_form = UploadFileForm()
    
    user_folder = get_user_upload_folder() 
    abs_path = safe_join(user_folder, requested_path)
    
    if user not in abs_path:
        flash("Not allowed!")
        return redirect_url_to_page_and_path()
    
    if os.path.isfile(abs_path):
        try:
            return send_file(abs_path)
        
        except Exception as e:
            print(e)

    all_files = [convert_file_info(file, user_folder) for file in os.scandir(abs_path)]
    
    parent_path = os.path.relpath(Path(abs_path).parents[0], user_folder)
    path_indicator = get_user_location_path(parent_path, requested_path)
    
    return render_template("home/index.html", 
                           user_folder=user_folder, 
                           files=all_files, 
                           parent_path=parent_path, 
                           path_indicator=path_indicator,
                           create_folder_form=create_folder_form, 
                           upload_file_form=upload_file_form,
                           os=os)

# Register user
@app.route("/register", methods=["GET", "POST"])
def register():
    
    """
    This view registers new user and handles validation.
    
    If form is validated and submited.
    First it checks if there is user with this name in db and if passwords match.
    
    Then for security the password is handled by
    :werkzeug.security.generate_password_hash()
    
    Then new user is created with the credentials specified
    We add it to the database.
    """
    
    form = UserFormRegister()
    
    if request.method == "POST":
        # Register user if form is submited and is valid
        if form.validate() and form.is_submitted:
            register_user = form.username.data
            user_password = form.password.data
            confirm_password = form.confirm_password.data
            
            # Check if user exists
            user = User.query.filter_by(username=register_user).first()
            if user:
                flash(f"User with name '{register_user}' already exists!", category='error')
                return redirect("register")
                
            # Validate that passwords match
            if user_password != confirm_password:
                flash("Passwords dont match!")
                return redirect("register")
            
            # Hash
            hash_password = generate_password_hash(user_password, method="scrypt", salt_length=16)
            
            # Init new User
            new_user = User(
                username=register_user,
                password =hash_password
            )
            
            # Add to db
            db.session.add(new_user)
            db.session.commit()
            
            flash("Registration succes! Proceed with loging in!")
            return redirect(url_for("login"))
        
        redirect(url_for("register"))
    
    return render_template("auth/register.html", form=form)

# Login user
@app.route("/login", methods=["GET", "POST"])
def login():
    form = UserFormLogin()
    if request.method == "POST":
        if  form.validate() and form.is_submitted:
            
            login_username = form.username.data
            login_password = form.password.data
            
            user = User.query.filter_by(username=login_username).first()
            wrong_credentials_error = "Incorect username or password!"
            
            if not user:
                flash(wrong_credentials_error)
                return redirect(url_for("login"))
            
            if not check_password_hash(user.password, login_password):
                flash(wrong_credentials_error)
                return redirect(url_for("login"))
                
            login_user(user)
            session["user"] = user.username
            
            flash("Login success!")
            return redirect(url_for('index')) 
          
    return render_template("auth/login.html", form=form)

# Logout user
@app.route("/logout", methods=["GET", "POST"])
@login_required
def logout():
    logout_user()
    session.clear()
    flash("Logged out!")
    return redirect("login")

@app.route("/return_to_root>", methods=["GET", "POST"])
@login_required
def return_to_root():
    """
    Route to return to root when clicking on folder icon next to the path indicator
    """
    return redirect_url_to_page_and_path()

# Route for create new folder
@app.route("/create_folder", methods=["GET", "POST"])
@login_required
def create_folder():
    """
    Route for creating new folder
    New folder name is sanitazed with custom function using re
    :sanitize_folder_name
    """  
    if request.method == "POST":
        new_folder_name = request.form.get("folder_name")
        current_path = request.form.get("folder_path")
        
        # Catch if any error occur
        try:
            sanitized_folder_name = sanitize_folder_name(new_folder_name)
        except Exception:
            flash("Name not supported! Try again!")
            return redirect_url_to_page_and_path(current_path)
        
        # Get user folder and current path level structure
        user_folder = get_user_upload_folder()
        folder_level = current_path[1:].split("/")

        # Construct the abs path
        abs_path_to_folder = safe_join(user_folder, *folder_level, sanitized_folder_name)
        
        # Check if new folder exists
        if os.path.exists(abs_path_to_folder):
            flash(f"Folder with name '{sanitized_folder_name}' already exists")
            return redirect_url_to_page_and_path(current_path)
        
        # Create new folder or catch exception
        try:
            os.mkdir(abs_path_to_folder)
            flash(f"Folder {sanitized_folder_name} created!")
            return redirect_url_to_page_and_path(current_path)
        
        # Return error and redirect
        except Exception as error:
            flash("An error occured while creating folder! Please try again!")
            return redirect_url_to_page_and_path()
    
    return redirect(url_for('index'))
     
# Route to download file
@app.route("/download/<path:requested_file>")
@login_required
def download(requested_file):
    
    user = session['user']
    user_folder = get_user_upload_folder()
    abs_path = safe_join(user_folder, requested_file)
    
    if user not in user_folder:
        return abort(404)
    
    # If the path doesnt exists abort
    if not os.path.exists(abs_path):
        flash("File doesnt exists! Redirecting to root!")
        return redirect_url_to_page_and_path()
 
    if os.path.isfile(abs_path):
        try:
            # Send the file to the client
            response = send_file(abs_path, as_attachment=True)

            # Calculate hash of the downloaded file
            file_hash = calculate_file_hash(abs_path)

            # Add file hash to response headers
            response.headers['X-File-Hash'] = file_hash

            return response
        
        except Exception as e:
            print(e)

# Verify file integrity after each request
@app.after_request
def verify_file(response):
    if request.endpoint == "download":
        # Get user path and file name
        user_folder = get_user_upload_folder()
        file_name = request.view_args["requested_file"]
        
        # Build path
        file_path = os.path.join(user_folder, file_name)
        
        # Calculate the original file hash and get the stored hash in the headers
        original_file_hash = calculate_file_hash(file_path)
        downloaded_file_hash = response.headers['X-File-Hash']
        
        # Compare original file hash with downloaded
        if original_file_hash != downloaded_file_hash:
            flash(f"Integrity error! Please try downloading the file: {file_name} again!")
        
        else:
            flash(f"File {file_name} downloaded!")
        
        return response
    
    return response

# Route for upload file
@app.route("/upload_file", methods=["GET", "POST"])
@login_required
def upload_file():
    """
    This route handles file upload
    file name is secured with 
    :werkzeug.utils secure_filename()
    
    Allowed file extensions for now are 'txt, pdf, jpg, png, jpeg and gif'
    Max size is 15mb
    """
    if request.method == 'POST':
        user_folder = get_user_upload_folder()
        current_path = request.form.get("folder_path")
        
        folder_level = current_path[1:].split("/")

        # check if the post request has the file part
        if 'upload_file_name' not in request.files:
            flash('No file')
            return redirect('index')
        
        file = request.files['upload_file_name']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            secured_filename = secure_filename(file.filename)
            # Construct the abs path
            abs_path_for_upload = safe_join(user_folder, *folder_level)
            file.save(os.path.join(abs_path_for_upload, secured_filename))
            return redirect_url_to_page_and_path(current_path)
        
        else:
            flash("File format not supported!")
    
    return redirect_url_to_page_and_path()

# Rename file or folder
@app.route("/rename_file", methods=["POST"])
@login_required
def rename():
    if request.method == "POST":
        old_file_name = request.json.get('old_file_name')
        file_name_suffix = request.json.get('file_suffix')
        new_file_name = request.json.get('new_file_name')
        path_to_file = request.json.get('path_to_file')
        
        # Construct the path
        user_folder = get_user_upload_folder()
        folder_level = path_to_file[1:].split("/")
        full_path_to_file = os.path.join(user_folder, *folder_level, old_file_name)
        
        # Secure file name and add the original extension
        secured_new_file_name = sanitize_folder_name(new_file_name)
        
        # Add suffix if file
        if os.path.isfile(full_path_to_file):    
            secured_new_file_name += f".{file_name_suffix}"
        
        # Construct the full path to the new file
        new_file_abs_path = safe_join(user_folder, *folder_level, secured_new_file_name)
        
        # Check if new file exists
        if os.path.exists(new_file_abs_path):
            flash(f"File with name '{secured_new_file_name}' already exists or name not allowed!")
            return jsonify({'error': 'Method not allowed'}), 400
        
        # Path to file to be renamed and the new path
        new_path_to_file = os.path.join(user_folder, *folder_level, new_file_abs_path)
        
        # Catch any error
        try:
            os.rename(full_path_to_file, new_path_to_file)
        except Exception as e:
            flash("Error while renaming!")
        
        # Return response
        return jsonify({'success': True, 'renamed_file': new_file_name}), 200
    else:
        return jsonify({'error': 'Method not allowed'}), 400
    
# Route for deleting file
@app.route("/delete_file", methods=["POST"])
@login_required
def delete_file():
    
    if request.method == "POST":
        user = session['user']
        file_to_delete = request.json.get('delete_file')
        path_to_file = request.json.get('path_to_delete_file')
        
        # Construct the path
        user_folder = get_user_upload_folder()
        folder_level = path_to_file[1:].split("/")
        full_path_to_file = os.path.join(user_folder, *folder_level, file_to_delete)
        
        if not user in full_path_to_file:
            flash("Not allowed!")
            return abort(404)
        
        if not os.path.exists(full_path_to_file):
            flash("Error deleting! No such file")
            return jsonify({'error': 'No such file!'}), 400
        
        try:
            if os.path.isfile(full_path_to_file):
                os.remove(full_path_to_file)
                
            elif os.path.isdir(full_path_to_file):
                
                dir_len = os.listdir(full_path_to_file)
                
                if len(dir_len) == 0:
                    
                    os.rmdir(full_path_to_file)
                else:
                    flash("Directory is not empty! Aborting!")
                    return jsonify({'error': 'Folder is not empty!'}), 400
                
        except Exception:
            flash("File cannot be deleted! Sorry")
            return jsonify({'error': 'Error!'}), 400  
        
        return jsonify({'success': True}), 200
    
    return jsonify({'error': 'Method not allowed'}), 400