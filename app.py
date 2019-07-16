from flask import Flask, redirect, session, render_template, request,session, flash, url_for
from mysqlconnection import connectToMySQL
app = Flask(__name__)    
app.secret_key = "keep it secret, keep it safe"
from flask_bcrypt import Bcrypt        
bcrypt = Bcrypt(app)
import re

@app.route("/")
def landing_page():

    return render_template("index.html")

#registration section & validation
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')
@app.route("/register", methods=['POST'])

# register route

def add_users():
    is_valid = True
    if len(request.form['fname']) < 1:
        is_valid = False
        flash("Please enter a frist name")
        return redirect("/")
    if len(request.form['lname']) < 1:
        is_valid = False
        flash("Please enter a last name")
        return redirect("/")
    if not EMAIL_REGEX.match(request.form['email']):
        flash('invalid email address')
        return redirect('/')
    if len(request.form['password']) < 1:
        is_valid = False
        flash("Please enter a valid password")
        return redirect("/")
    if request.form['conf_password'] != request.form['password']:
        is_valid = False
        flash("password did not match")
        return redirect("/")
    if is_valid:
        pw_hash = bcrypt.generate_password_hash(request.form['password'])
        print(pw_hash)
        mysql = connectToMySQL('team_db')
        query = "INSERT INTO users (first_name, last_name, email, password, created_at, updated_at) VALUES (%(fn)s, %(ln)s, %(em)s, %(pw)s, NOW(), NOW());"
        data = {
            "fn": request.form["fname"],
            "ln": request.form["lname"],
            "em": request.form["email"],
            "pw": pw_hash
        }
        #store in DB redirect to users page
        new_user_id = mysql.query_db(query,data)
        flash("User successfully added!")
        session['greetings'] = request.form["fname"]
        session['user_id'] = new_user_id
    return redirect("/profile" )

# Login route

@app.route("/login", methods=['POST'])
def login():
    mysql = connectToMySQL("team_db")
    query = "SELECT * FROM users WHERE email = %(em)s;"
    data = { "em" : request.form["email"] }
    login_information = mysql.query_db(query, data)
    print(login_information)
    if login_information:
        if bcrypt.check_password_hash(login_information[0]['password'], request.form['password']):
            session['user_id'] = login_information[0]['id']
            session['greetings'] = login_information[0]['first_name']
            return redirect('/user_page')
    flash('You could not be logged in check your username and password')
    return redirect('/')


#ajax validation
@app.route("/username", methods=['POST'])
def username_validation():
    print(request.form)
    found = False
    mysql = connectToMySQL('dojo_tweets')        # connect to the database
    query = "SELECT email FROM users WHERE email = %(data)s;"
    data = { "data": request.form["email"] }
    result = mysql.query_db(query, data)
    if result:
        found = True
    return render_template('partials/user_validation.html', found=found)

#log off
@app.route('/logout')
def logout():
    session.clear()
    return redirect("/")

#set up security when register a new user

@app.route("/profile")
def profile_page():

    return render_template("landing_page.html")

#forgot password route

@app.route("/forgot_pass")
def update_pass():

    return render_template("forgot_pw.html")

# reset password route
# resets password if security answer is in the db

@app.route("/reset_pw", methods=['POST'])
def reset():
    reset_pw = False
    mysql = connectToMySQL('team_db')
    query = "SELECT * FROM users WHERE email = %(em)s"
    data = {"em": request.form['email']}
    user_info = mysql.query_db(query,data)
    if user_info:
        reset_pw = True
        print(reset_pw)
        if reset_pw: #if there is a user returned from prior query get the security question and store it
            mysql = connectToMySQL('team_db')
            query = "SELECT security_question FROM users WHERE email = %(em)s"
            data = {"em": request.form['email']}
            question = mysql.query_db(query,data)
            print(question[0]['security_question'])
            if question[0]['security_question'] != request.form['question-one'] or request.form['question-two'] or request.form['question-three']:
                reset_pw = False
                flash('Security question did not match')
                return redirect('/forgot_pass')
            elif question[0]['security_question'] == request.form['question-one'] or request.form['question-two'] or request.form['question-three']:
                reset_pw = True
                if reset_pw:
                    mysql = connectToMySQL('team_db')
                    pw_hash = bcrypt.generate_password_hash(request.form['password'])
                    query = "UPDATE users SET password = %(new_pw)s WHERE email = %(em)s "
                    data = {
                        "new_pw": pw_hash,
                        "em": request.form['email']
                    }
                    mysql.query_db(query,data)
                    flash('Password Successfully reset!')
                    return redirect('/')


    return redirect('/forgot_pass')


# user sets sec question and is updated in the db
@app.route("/security_questions", methods=['POST'])
def security():
    valid_form = False
    if len(request.form['question-one']) > 1:
        valid_form = True
        form_input = request.form['question-one']
    if len(request.form['question-two']) > 1:
        valid_form = True
        form_input = request.form['question-two']
    if len(request.form['question-three']) > 1:
        valid_form = True
        form_input = request.form['question-three']
    if valid_form:
        print(form_input)
        print(session['user_id'])
        mysql = connectToMySQL('team_db')
        query = "UPDATE users SET security_question = %(question)s WHERE id = %(u_id)s"
        data = {
            "question": form_input,
            "u_id": session['user_id']
        }
        mysql.query_db(query,data)

        # when done setting up profile go to users_page
        return redirect('/user_page') 


# renders the landing page for user
@app.route("/user_page")
def user_page():
    mysql = connectToMySQL('team_db')
    query = "SELECT * FROM posts JOIN users ON users.id = posts.user_id"
    posts = mysql.query_db(query)
    # for post in posts:
    mysql = connectToMySQL('team_db')
    query = "SELECT * FROM comments JOIN users ON user_id = users.id"
    comments = mysql.query_db(query)
 
    return render_template('user_page.html', posts = posts, all_comments = comments)

@app.route("/make_post", methods=['POST'])
def post_message():
    mysql=connectToMySQL('team_db')
    query = "INSERT INTO posts (post, created_at, updated_at, user_id) VALUES ( %(post)s, NOW(), NOW(), %(u_id)s) "
    data = {
        "post": request.form['post'],
        "u_id": session['user_id']
    }
    mysql.query_db(query, data)
    return redirect('/user_page')

@app.route("/comment", methods=['POST'])
def make_a_comment():
    mysql = connectToMySQL('team_db')
    query = "INSERT INTO comments ( comment, user_id, post_id ) VALUES ( %(comment)s, %(uid)s, %(pid)s )"
    data = {
        "comment": request.form['comment_text'],
        "uid": session['user_id'],
        "pid": request.form['post_id']
    }
    mysql.query_db(query, data)
    return redirect('/user_page')

@app.route("/delete", methods=['POST'])
def delete_post():
    mysql = connectToMySQL('team_db')
    query = "DELETE FROM comments WHERE post_id = %(pid)s"
    data = {
        "pid": request.form['post_id']
    }
    mysql.query_db(query, data)
    mysql = connectToMySQL('team_db')
    query = "DELETE FROM posts WHERE id = %(pid)s "
    data = {
        "pid": request.form['post_id']
    }
    mysql.query_db(query, data)
    return redirect('/user_page')

@app.route("/update/<id>")
def update_post(id):
    mysql = connectToMySQL('team_db')
    query = "SELECT * FROM posts WHERE id = %(pid)s "
    data = {
        "pid": id
    }
    post = mysql.query_db(query, data)
    return render_template('update_post.html', posts = post)

@app.route("/update_post", methods=['POST'])
def update():
    mysql = connectToMySQL('team_db')
    query = "UPDATE posts SET post = %(update)s WHERE id = %(pid)s "
    data = {
        "update": request.form['updated_text'],
        "pid": request.form['post_id']
    }
    mysql.query_db(query, data)
    return redirect('/user_page')
if __name__=="__main__":   
    app.run(debug=True) 