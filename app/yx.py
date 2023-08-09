from routes import *
from stories import Story
from Story_Forms import CreateStoryForm
import shelve


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