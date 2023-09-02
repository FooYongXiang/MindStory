import pyrebase
from flask import render_template, request, redirect, session, jsonify, url_for, flash, send_from_directory, abort
from flask import Flask
from datetime import timedelta
from transaction import Transaction
import os
from stories import Story
from Story_Forms import CreateStoryForm



# import firebase_admin
app = Flask(__name__)
app.secret_key = 'wedap'
app.permanent_session_lifetime = timedelta(hours=2)
# from app import app
import os
import shelve
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.utils import secure_filename
import random
import string
from flask_turnstile import Turnstile

turnstile = Turnstile(app=app, site_key='0x4AAAAAAAJkqo2mD4-WN2je', secret_key='0x4AAAAAAAJkqvnY3N8OVHjorcA6A8Aj4Sw',
                      is_enabled=True)
turnstile.init_app(app)
app.config['UPLOAD_DIRECTORY'] = 'app/static/'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
app.config['ALLOWED_EXTENSIONS'] = ['.jpg', '.jpeg', '.png', '.gif']

config = {

    "apiKey": "AIzaSyCGxEFlh18ujGq6tikQCI-3oIcBLMZhOsk",
    "authDomain": "flask-e521c.firebaseapp.com",
    "databaseURL": "https://flask-e521c-default-rtdb.asia-southeast1.firebasedatabase.app",
    "projectId": "flask-e521c",
    "storageBucket": "flask-e521c.appspot.com",
    "messagingSenderId": "750669824566",
    "appId": "1:750669824566:web:04d81f2400bcc35c024e97",
    "measurementId": "G-PHVZZ0SVB6",
    "allowEmailVerification": True
}

firebase = pyrebase.initialize_app(config)
auth = firebase.auth()
fire_db = firebase.database()


@app.route('/', methods=['GET', 'POST'])
def main():
    if 'user' in session:
        return redirect(url_for("home"))
    else:
        return render_template("main.html")


@app.route('/index', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        email = request.form['name']
        password = request.form['password']
        try:
            #critical codes
            user = auth.sign_in_with_email_and_password(email, password)
            user_data = auth.get_account_info(user['idToken'])  # Fetch user data
            is_email_verified = user_data['users'][0]['emailVerified']
            print(user)
            print(user_data)
            print(is_email_verified)
            if is_email_verified:

                session['user']= user
                session['email']= email
                session['password']=password
                
                print(session['user'])
                # return redirect(url_for("home"))
                if turnstile.verify():
                    # SUCCESS
                    return redirect(url_for("home"))

                else:
                    # FAILED
                    return render_template('index.html', umessage="Please verify that you are not a bot", email=email)

            else:
                verification_pending = 'Email verification is pending. Please check your email for the verification link.'
                return render_template('index.html', umessage=verification_pending, email=email)
        except:
            unsuccessful = 'Incorrect Password or Email.'
            return render_template('index.html', umessage=unsuccessful, email=email)
    return render_template('index.html')


@app.route('/create_account', methods=['GET', 'POST'])
def create_account():
    if request.method == 'POST':
        # Emails and Passwords
        email = request.form['name']
        password = request.form['password']
        username = request.form['username']

        option = request.form.get('flexRadioDefault')
        role = ''
        if option:
            print(option)
            # Handle the different options here
            if option == 'option1':
                # Option 1 was chosen
                role = 'StoryTeller'
            elif option == 'option2':
                # Option 2 was chosen
                role = 'Supporter'
        try:
            file = request.files['file']
            profilepic = request.files['profilepic']
            if profilepic:
                profile_img_name = secure_filename(
                    "{}_{}{}".format(email, 'profilepic', os.path.splitext(profilepic.filename)[1].lower()))
                # profile_img_name = os.path.join(app.config['UPLOAD_DIRECTORY'], profile_img_name)
            else:
                profile_img_name = 'defaultpic.jpg'
                # profile_img_name = os.path.join(app.config['UPLOAD_DIRECTORY'],'defaultpic.jpg')
            if file and role == 'StoryTeller':
                # MEDIC
                extension = os.path.splitext(file.filename)[1].lower()
                if extension not in app.config['ALLOWED_EXTENSIONS']:
                    unsuccessful = 'File is not an image'

                    return render_template('create_account.html', umessage=unsuccessful, email=email, option=option,
                                           username=username)


                # Generate a unique filename for the image
                db = shelve.open('storage.db', 'c')
                try:
                    users_dict = db['Users']
                except:
                    print("Error in retrieving Users from storage.db.")
                    users_dict = {}
                global new_file_name
                random_string = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
                new_file_name = secure_filename(
                    "{}_{}{}".format(email, random_string, os.path.splitext(file.filename)[1].lower()))
                # new_file_name_advanced = os.path.join(app.config['UPLOAD_DIRECTORY'], new_file_name)
                money = 0
                users_dict[email] = [new_file_name, profile_img_name, username, role, money, []]
                db['Users'] = users_dict
                db.close()
            else:
                db = shelve.open('storage.db', 'c')
                try:
                    users_dict = db['Users']
                except:
                    print("Error in retrieving Users from storage.db.")
                    users_dict = {}
                money = 0
                users_dict[email] = [None, profile_img_name, username, role, money, []]
                db['Users'] = users_dict
                db.close()


        except RequestEntityTooLarge:
            unsuccessful = 'File is too large (>16MB)'

            return render_template('create_account.html',umessage=unsuccessful,email = email,option=option,username = username)

        try:
            user = auth.sign_in_with_email_and_password(email, password)
            user_data = auth.get_account_info(user['idToken'])
            print(user_data)
            if user_data['users'][0]['emailVerified']:
                flash("Account is already verified", "info")
                return redirect(url_for('index'))
            else:
                # The user's email is registered but not verified (verification link expired)
                # You can choose to send another verification email here if you want

                user = auth.send_email_verification(user['idToken'])
                return redirect(url_for("verification_sent"))
        except:
            # The email is not registered, proceed with creating a new account
            try:
                if len(password) < 6:
                    unsuccessful = 'Password needs to be at least 6 characters'

                    return render_template('create_account.html',umessage=unsuccessful,email = email,option=option,username = username)

                user = auth.create_user_with_email_and_password(email, password)
                user = auth.send_email_verification(user['idToken'])
                #Placed here so that the image will be saved only when created
                if role=='StoryTeller':

                    file.save(os.path.join(
                        app.config['UPLOAD_DIRECTORY'],
                        secure_filename(new_file_name)
                    ))
                if profilepic:
                    profilepic.save(os.path.join(
                        app.config['UPLOAD_DIRECTORY'],
                        secure_filename(profile_img_name)
                    ))
                return redirect(url_for("verification_sent", email=email, password=password))
            except:
                unsuccessful = 'Account creation failed.'
                return render_template('create_account.html', umessage=unsuccessful, email=email, option=option)

    return render_template('create_account.html')


@app.route('/verification_sent')
def verification_sent():
    return render_template('verification_sent.html')


@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if (request.method == 'POST'):
        if turnstile.verify():
            # SUCCESS

            email = request.form['name']
            auth.send_password_reset_email(email)
            return render_template('forgot_password_email.html')
        else:
            # FAILED
            return render_template('forgot_password.html', umessage='Please verify that you are not a robot')

    return render_template('forgot_password.html')



@app.route("/logout")
def logout():
    session.pop("user",None)
    session.pop("email",None)
    session.pop('password',None)

    return redirect(url_for("main"))


# Returns the image in full size
@app.route('/serve-image/<filename>', methods=['GET'])
def serve_image(filename):
    return send_from_directory(app.config['UPLOAD_DIRECTORY'], filename)


@app.route('/faq')
def faq():
    return render_template('faq.html')


@app.route('/contactus', methods=['GET', 'POST'])
def contactus():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']
        fire_db.child('requests').push({'name': name, 'email': email, 'message': message})
        return render_template('contact_sent.html')
    return render_template('contactus.html')


@app.route('/resend_verification', methods=['GET', 'POST'])
def resend_verification():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        try:
            user = auth.sign_in_with_email_and_password(email, password)
            user_data = auth.get_account_info(user['idToken'])
            if user_data['users'][0]['emailVerified']:
                flash("Account is already verified", "info")
                return redirect(url_for('index'))
            else:
                user = auth.send_email_verification(user['idToken'])
                flash("Verification email has been resent. Please check your email for the verification link.", "info")
                return redirect(url_for("resend_verification"))
        except:
            unsuccessful = 'Failed to resend verification email. Please make sure the email is registered and not verified yet.'
            return render_template('resend_verification.html', umessage=unsuccessful)

    return render_template('resend_verification.html')



@app.route('/profile')
def profile():
    if 'user' not in session:
        return redirect(url_for('index'))
    db = shelve.open('storage.db', 'c')
    try:
        users_dict = db['Users']
        user_stories = db['Stories']
    except:
        print("Error in retrieving Users from storage.db.")
        users_dict = {}
    email = session['email']
    data = users_dict[email]
    images = []
    for i in user_stories:
        if user_stories[i].get_storyteller() == email:
            images.append(user_stories[i].get_image() )

    db.close()
    return render_template('profile.html',data=data, images=images)

@app.route('/updateprofile',methods=['GET','POST'])

def updateprofile():
    if 'user' not in session:
        return redirect(url_for('index'))
    if request.method == 'POST':
        # password = request.form['password']
        # password1 = request.form['password1']
        username = request.form['username']
        profilepic = request.files['profilepic']
        email = session['email']
        db = shelve.open('storage.db', 'c')
        try:
            users_dict = db['Users']
        except:
            print("Error in retrieving Users from storage.db.")
            users_dict = {}
            return redirect(url_for('index'))
        if email in users_dict:
            data = users_dict[email]
            if profilepic:
                    #OVER HERE
                profile_img_name = secure_filename("{}_{}{}".format(email, 'profilepic',os.path.splitext(profilepic.filename)[1].lower()))
                current_profile_img_path = os.path.join(app.config['UPLOAD_DIRECTORY'], data[1])
                if os.path.exists(profile_img_name):
                    os.remove(current_profile_img_path)
                profilepic.save(os.path.join(
                        app.config['UPLOAD_DIRECTORY'],
                        secure_filename(profile_img_name)
                    ))
                data[1] = profile_img_name
            # if password:
            #     if password == password1:
            #         if len(password)<6:
            #             return render_template('updateprofile.html',data = data, email = session['email'],umessage='Password needs to be at least 6 characters')
            #         # auth.update_profile(session['user']['idToken'],display_name='',photo_url=None, {'idToken':session['user']['idToken'],'password': password,'returnSecureToken':False})
            #         # auth.setAccountInfo(session['user']['idToken'], {'idToken':session['user']['idToken'],'password': password,'returnSecureToken':False})
            #         auth.verify_password_reset_code(session['user']['idToken'], password)
            #         auth.update_profile
            #         session['password']=password
                    
            #     else:
            #         return render_template('updateprofile.html',data = data, email = session['email'],umessage='Passwords do not match')
            if username:
                data[2] = username
                # auth.update_profile(session['user']['idToken'], {'idToken': session['user']['idToken'],'displayName': username})
            users_dict[email] = data
            
            db['Users'] = users_dict


            db.close()
            return render_template('updateprofile.html',data = data, email = session['email'],smessage='Profile updated')
        return render_template('updateprofile.html',data = data, email = session['email'],umessage='User not found')
    db = shelve.open('storage.db', 'c')
    try:
        users_dict = db['Users']
    except:
        print("Error in retrieving Users from storage.db.")
        users_dict = {}
    email = session['email']
    data = users_dict[email]
    print(session['email'])
    db.close()
    return render_template('updateprofile.html',data = data, email = session['email'])
@app.route("/delete_account/<emails>", methods=['POST'])
def delete_account(emails):
            #     user = auth.sign_in_with_email_and_password(email, password)
            # user_data = auth.get_account_info(user['idToken'])
    if request.method == 'POST':
        if 'user' not in session:
            return redirect(url_for('index'))
        db = shelve.open('storage.db', 'c')
        try:
            users_dict = db['Users']
        except:
            print("Error in retrieving Users from storage.db.")
            users_dict = {}
        email = session['email']
        data = users_dict[email]

        # db.close()
        if emails==session['email']:
            # print('{}/delete'.format(request.form['check']))
            # print('{}/delete'.format(session['email']))
            if '{}'.format(request.form['check']) =='{}/delete'.format(session['email']) and 'user' in session:
                
                user = auth.sign_in_with_email_and_password(session['email'], session['password'])
                # print(user['idToken'])
                user_data = auth.get_account_info(user['idToken'])
                auth.delete_user_account(user['idToken'])
                
                current_profile_img_path = os.path.join(app.config['UPLOAD_DIRECTORY'], data[1])
                if os.path.exists(current_profile_img_path):
                    os.remove(current_profile_img_path)
                del users_dict[session['email']]

                db['Users'] = users_dict
                db.close()
                
                session.pop("user",None)
                session.pop("email",None)
                session.pop('password',None)
                return render_template('delete_account.html')
            else:
                db.close()
                return render_template('updateprofile.html',data = data, email = session['email'],umessage='Fills does not match to delete permamently')
            
        else:
            db.close()
            return redirect(url_for('index'),umessage='You are not authorized to delete this account')


    return render_template('updateprofile.html', data=data)

# YYA Code
def generate_random_code():
    # Generate 6 random characters (uppercase letters and digits)
    characters = string.ascii_uppercase + string.digits
    random_chars = ''.join(random.choice(characters) for _ in range(6))

    # Generate 3 random uppercase letters
    random_letters = ''.join(random.choice(string.ascii_uppercase) for _ in range(3))

    # Generate 6 random digits
    random_digits = ''.join(random.choice(string.digits) for _ in range(6))

    # Combine the parts into the desired format
    return f"Ref no. {random_chars}{random_letters}{random_digits} Confirmed"


@app.route('/view_transaction_codes')
def view_transaction_codes():
    with shelve.open('transaction_code', 'c') as shelf:
        # Retrieve all keys and values from the shelf
        codes_data = list(shelf.items())

        # to clear shelf
        # shelf.clear()

    # Pass the codes_data to the template
    return render_template('view_transaction_codes.html', codes_data=codes_data,user=session['user'])



@app.route('/wallet', methods=['GET', 'POST'])
def wallet():
    if "user" not in session:
        return redirect(url_for('index'))
    if request.method == 'POST' and request.form.get('topup') != None:
        
        with shelve.open('storage.db') as db:
            users = db['Users']
            users[session['user']['email']][4] += int(request.form.get('topup'))
            db['Users'] = users
        
        with shelve.open('transaction_code') as shelf:
            random_code1 = generate_random_code()
            transaction_log1 = Transaction(int(request.form.get('topup')), session['user']['email'], random_code1)
            code_index = len(shelf) + 1
            shelf[f'trans{code_index}'] = transaction_log1
        session['topup_done'] = 'Successfully top up $' + request.form.get('topup') +'.'
    if request.method == 'POST' and request.form.get('withdrawal') != None:
        
        with shelve.open('storage.db') as db:
            users = db['Users']
            if users[session['user']['email']][4] - int(request.form.get('withdrawal')) >= 0:
                users[session['user']['email']][4] -= int(request.form.get('withdrawal'))
                db['Users'] = users
        
                with shelve.open('transaction_code') as shelf:
                    random_code1 = generate_random_code()
                    transaction_log1 = Transaction(-int(request.form.get('withdrawal')), session['user']['email'], random_code1)
                    code_index = len(shelf) + 1
                    shelf[f'trans{code_index}'] = transaction_log1
                    session['withdrawal_done'] = 'You have successfully withdrawed $' + request.form.get('withdrawal')
            else:
                session['withdrawal_failed'] = 'Withdrawal failed, insufficient balance.'

    db = shelve.open('storage.db', 'r')
    users_dict = db['Users']
    user_email = session['user']['email']
    current_user_data = users_dict.get(user_email)
    db.close()
    return render_template('wallet.html', user=session['user']['email'], user_data=current_user_data)
        


ADMIN_PASSWORD = 'fumo'
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    # If it's a POST request, check the provided password
    if request.method == 'POST':
        password = request.form.get('password')

        if password == ADMIN_PASSWORD:
            # Retrieve user data from the Shelf database
            db = shelve.open('storage.db', 'c')
            users_dict = db['Users']
            # give quick money to supporter ($20)
            # for i in users_dict:
            #     print(users_dict[i])
            #     if users_dict[i][3] == 'Supporter':
            #         users_dict[i][4] += 20
            # db['Users'] = users_dict
            db.close()

            # Pass the user data to the 'admin.html' template
            return render_template('admin.html', users=users_dict)
        else:
            # Failed Login
            return render_template('admin_login.html')

    # If it's a GET request, render the password input form as a popup
    return render_template('admin_login.html')
@app.route('/admin_search', methods=['GET'])
def admin_search():
    # Retrieve user data from the Shelf database
    db = shelve.open('storage.db', 'r')
    users_dict = db['Users']
    db.close()

    search_name = request.args.get('search_name', '')
    filtered_users = {}

    for email, user_info in users_dict.items():
        if search_name.lower() in user_info[2].lower() or search_name.lower() in email.lower():
            filtered_users[email] = user_info

    return render_template('admin.html', users=filtered_users)


@app.route('/delete_user', methods=['POST'])
def delete_user():
    if request.method == 'POST':
        data = request.get_json()
        email_to_delete = data.get('email')

        # Retrieve user data from the Shelf database
        db = shelve.open('storage.db', 'w')
        users_dict = db['Users']

        if email_to_delete in users_dict:
            # Remove the user from the dictionary
            del users_dict[email_to_delete]
            db['Users'] = users_dict
            db.close()
            session.pop("user", None)
            session.pop("email", None)
            session.pop('password', None)
            return jsonify({'message': 'User deleted successfully'})

        db.close()
        return jsonify({'error': 'User not found'})

    return jsonify({'error': 'Invalid request'})

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

# from gavin import *
from flask_socketio import SocketIO, send
socketio = SocketIO(app, cors_allowed_origins="*")
@socketio.on('message')
def handle_message(message):
    print("Received message: " + message)
    if message != "User connected!":
        send(message, broadcast=True)

@app.route('/live_chat')
def indexes():
    if 'user' not in session:
        return redirect(url_for('index'))
    db = shelve.open('storage.db', 'c')
    try:
        users_dict = db['Users']
    except:
        print("Error in retrieving Users from storage.db.")
        users_dict = {}
    email = session['email']
    data = users_dict[email]
    return render_template("live_chat.html", data = data,email = session['email'])


# by yx
@app.route('/story_creation', methods=['GET','POST'])
def story_creation():
    # print(session['user'])
    try:
        if "user" not in session:
            return redirect(url_for('index'))
    except KeyError:
        return redirect(url_for('index'))

    # check the roles, if is supporter, cannot access to story creation, return to home page
    db = shelve.open('storage.db', 'c')
    if db.get('story_counter') == None:
        db['story_counter'] = 0
    number_of_stories_stored = db['story_counter']
    print(number_of_stories_stored)
    print(db.get('Stories'))
    users = db['Users']
    db.close()

    if users[session['user']['email']][3]  != 'StoryTeller':
        session['access_denied'] = 'Access denied. Only storytellers can access Story Creation page.'
        return redirect(url_for('home'))

    session.permanent = True
    create_story = CreateStoryForm(request.form)
    if request.method == 'POST' and create_story.validate():
        story_dict = {}
        db = shelve.open('storage.db', 'c')
        try:
            story_dict = db['Stories']
        except:
            print("Error in retrieving Stories from storage.db.")
        story = Story(session['user']['email'], create_story.image.data, create_story.description.data)

        number_of_stories_stored += 1
        story_dict[str(number_of_stories_stored)] = story
        db['Stories'] = story_dict
        db['story_counter'] = number_of_stories_stored
        db.close()
        session['story_created'] = story.get_storyteller() + ' has published ' + story.get_image()
        return redirect(url_for('home'))
    return render_template('story_creation.html', form=create_story)


@app.route('/home', methods=['GET', 'POST'])
def home():
    # print(session['user'])
    try:
        if "user" not in session:
            return redirect(url_for('index'))
    except KeyError:
        return redirect(url_for('index'))

    session.permanent=True
    if request.method == 'POST' and request.form.get('delete') != None:
        db = shelve.open('storage.db', 'c')
        stories = db['Stories']
        index = request.form['counter']
        try:
            stories.pop(index)
        except:
            stories.clear()
        db['Stories'] = stories
        db.close()
    elif request.method == 'POST' and request.form.get('donate_amount') == None and request.form.get('my_comment') == None:
        db = shelve.open('storage.db', 'c')
        stories = db['Stories']
        index = request.form['counter']
        stories[index].set_likes(stories[index].get_likes() + 1)
        db['Stories'] = stories
        db.close()
    elif request.method == 'POST' and request.form.get('my_comment') == None:
        amount = request.form.get('donate_amount')
        db = shelve.open('storage.db', 'r')
        stories = db['Stories']
        db.close()
        index = request.form['counter']
        storyteller_email = stories[index].get_storyteller()

        # Have to check whether balance have enough
        # send the money to the email of the storyteller
        db = shelve.open('storage.db', 'c')
        users = db['Users']
        # quick money transferring
        # users[session['user']['email']][4] = 50
        # users[storyteller_email][4] = 0
        # db['Users'] =users
        balance = str(users[session['user']['email']][4])
        if int(balance) < int(amount):
            session['donation_fail'] = ("Donation failed, insufficient balance.")
            db.close()
        else:
            balance = int(balance) - int(amount)
            users[session['user']['email']][4] = balance
            users[storyteller_email][4] += int(amount)
            db['Users'] = users
            db.close()

            negative_amount = -int(amount)
            random_code1 = generate_random_code()
            transaction_log1 = Transaction(negative_amount, session['user']['email'], random_code1)


            transaction_log2 = Transaction(int(amount), storyteller_email, random_code1)

            # Save the random code to shelf
            with shelve.open('transaction_code') as shelf:
                code_index = len(shelf) + 1
                shelf[f'trans{code_index}'] = transaction_log1
                shelf[f'trans{code_index+1}'] = transaction_log2
            session['donation_done'] = 'You have successfully donated $' + amount + " to " + storyteller_email
            return render_template('transaction_complete.html', random_code=random_code1)

    elif request.method == 'POST':
        db = shelve.open('storage.db', 'c')
        stories = db['Stories']
        index = request.form['counter']
        comments = stories[index].get_comments()
        comments.append(request.form.get('my_comment'))
        stories[index].set_comments(comments)
        db['Stories'] = stories
        db.close()

    db = shelve.open('storage.db', 'c')
    stories = db.get('Stories')
    if stories == None:
        stories = {}
        db['Stories'] = stories
    users = db['Users']
    db.close()
    images = []
    infos = []
    likes = []
    storytellers = []
    comments = []
    count = 0
    comments_length = []
    stories_id = []
    usernames = []
    for i in stories:
        images.insert(0, url_for('static', filename=stories[i].get_image()))
        infos.insert(0, stories[i].get_info())
        likes.insert(0, stories[i].get_likes())
        storytellers.insert(0, stories[i].get_storyteller())
        usernames.insert(0,users[stories[i].get_storyteller()][2])
        comments.insert(0, stories[i].get_comments())
        count += 1
        comments_length.insert(0, len(stories[i].get_comments()))
        stories_id.insert(0, i)
        print(stories_id)
    # print(images)
    return render_template('home.html', user=session['user'], images=images,
                           infos=infos, likes=likes, storytellers=storytellers, comments=comments,
                           count=count, comments_length=comments_length, stories_id = stories_id, usernames=usernames)


@app.route('/search', methods=['GET', 'POST'])
def search():
    # print(session['user'])
    try:
        if "user" not in session:
            return redirect(url_for('index'))
    except KeyError:
        return redirect(url_for('index'))
    session.permanent = True
    found ={}
    count = 0
    if request.method == 'POST' and request.form.get('search_bar') != None:

        field_to_search = request.form.get('search_bar')
        # search in user table
        with shelve.open('storage.db', 'r') as db:
            users = db['Users']
            for i in users:
                if field_to_search.lower() in i.lower() or field_to_search.lower() in users[i][2].lower():
                    found[i] = users[i]
        count = len(found)
    return render_template('search.html', user=session['user'], found=found, count=count)


@app.route('/public_profile/<string:email>', methods=['GET', 'POST'])
def public_profile(email):
    if 'user' not in session:
        return redirect(url_for('index'))
    if request.method == 'POST' and request.form.get('donate') != None:
        
        with shelve.open('storage.db') as db:
            users = db['Users']
            if int(request.form.get('donate')) > users[session['user']['email']][4]: 
                session['donate_fail'] = ("Donation failed, insufficient balance.")
                return redirect(url_for('public_profile', email=email))
            users[session['user']['email']][4] -= int(request.form.get('donate'))
            users[email][4] += int(request.form.get('donate'))
            db['Users'] = users
        
        with shelve.open('transaction_code') as shelf:
            random_code1 = generate_random_code()
            transaction_log1 = Transaction(-int(request.form.get('donate')), session['user']['email'], random_code1)
            code_index = len(shelf) + 1
            shelf[f'trans{code_index}'] = transaction_log1
            transaction_log2 = Transaction(int(request.form.get('donate')), email, random_code1)
            code_index = len(shelf) + 1
            shelf[f'trans{code_index}'] = transaction_log2
        # session['donate_done'] = 'Successfully donated $' + request.form.get('donate')
        return render_template('transaction_complete.html', random_code=random_code1)
    db = shelve.open('storage.db', 'c')
    try:
        users_dict = db['Users']
        user_stories = db['Stories']
    except:
        print("Error in retrieving Users from storage.db.")
        users_dict = {}
    data = users_dict[email]
    images = []
    for i in user_stories:
        if user_stories[i].get_storyteller() == email:
            images.append(user_stories[i].get_image() )

    db.close()
    return render_template('public_profile.html',data=data, images=images)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=80)
