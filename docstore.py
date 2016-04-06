import pymongo
import docstorePostDAO
import sessionDAO
import userDAO
import bottle
import cgi
import re
import os
import gridfs
import textract
import tempfile
from bottle import static_file



__author__ = 'rsandstroem'


# General Discussion on structure. This program implements a document store. In this file, which is the controller, we define a bunch of HTTP routes that are handled
# by functions. The basic way that this magic occurs is through the decorator design pattern. Decorators
# allow you to modify a function, adding code to be executed before and after the function. As a side effect
# the bottle.py decorators also put each callback into a route table.

# These are the routes that the docstore must handle. They are decorated using bottle.py

# This route is the main page of the docstore
@bottle.route('/')
def docstore_index():
    cookie = bottle.request.get_cookie("session")

    username = sessions.get_username(cookie)  # see if user is logged in
    if username is None:
        bottle.redirect("/login")

    # even if there is no logged in user, we can show the docstore
    l = posts.get_posts(10)
    return bottle.template('docstore_template', dict(myposts=l, username=username, search=''))

# used to process a comment on a docstore post
@bottle.post('/search')
def search():
    searchstring = bottle.request.forms.get("search")

    cookie = bottle.request.get_cookie("session")
    username = sessions.get_username(cookie)  # see if user is logged in
    if username is None:
        bottle.redirect("/login")

    l = posts.get_posts_by_search(searchstring, 10)
    #if searchstring == "":
    #    errors = "Search my contain a string"
    return bottle.template("docstore_template", dict(myposts=l, username=username, search=searchstring))
    #bottle.redirect("/")


# The main page of the docstore, filtered by tag
@bottle.route('/tag/<tag>')
def posts_by_tag(tag="notfound"):

    tag = cgi.escape(tag)

    cookie = bottle.request.get_cookie("session")
    username = sessions.get_username(cookie)  # see if user is logged in
    if username is None:
        bottle.redirect("/login")

    l = posts.get_posts_by_tag(tag, 10)

    return bottle.template('docstore_template', dict(myposts=l, username=username, search=''))

@bottle.route('/static/<filepath:path>')
def server_static(filepath):
    return static_file(filepath, root='/tmp/static')

# Displays a particular docstore post
@bottle.get("/post/<permalink>")
def show_post(permalink="notfound"):

    cookie = bottle.request.get_cookie("session")
    username = sessions.get_username(cookie)  # see if user is logged in
    if username is None:
        bottle.redirect("/login")
    permalink = cgi.escape(permalink)

    print "about to query on permalink = ", permalink
    post = posts.get_post_by_permalink(permalink)

    if post is None:
        bottle.redirect("/post_not_found")

    # init comment form fields for additional comment
    comment = {'name': "", 'body': ""}

    try:
        myobject = posts.get_object_by_post(post).read()
    except:
        print 'Warning: No binary file associated with posting'
    #try:
    path = '/tmp/static/'
    if not os.path.exists(path):
            os.makedirs(path)
    with open(path+post['filename'], 'wb') as f:
            f.write(myobject)
    objectpath='../static/'+post['filename']
    #except:
    print 'Warning: Path problems to binary file'

    print post
    return bottle.template("entry_template", dict(post=post, objectpath=objectpath, username=username, errors="", comment=comment))


# used to process a comment on a docstore post
@bottle.post('/newcomment')
def post_new_comment():
    body = bottle.request.forms.get("commentBody")
    permalink = bottle.request.forms.get("permalink")

    post = posts.get_post_by_permalink(permalink)
    cookie = bottle.request.get_cookie("session")

    username = sessions.get_username(cookie)

    # if post not found, redirect to post not found error
    if post is None:
        bottle.redirect("/post_not_found")
        return

    # if values not good, redirect to view with errors

    if body == "":
        # user did not fill in enough information

        # init comment for web form
        comment = {'name': username, 'body': body}

        errors = "Post must contain your name and an actual comment."
        return bottle.template("entry_template", dict(post=post, username=username, errors=errors, comment=comment))

    else:

        # it all looks good, insert the comment into the docstore post and redirect back to the post viewer
        posts.add_comment(permalink, username, body)

        bottle.redirect("/post/" + permalink)

@bottle.get("/post_not_found")
def post_not_found():
    return "Sorry, post not found"


# Displays the form allowing a user to add a new post. Only works for logged in users
@bottle.get('/newpost')
def get_newpost():

    cookie = bottle.request.get_cookie("session")
    username = sessions.get_username(cookie)  # see if user is logged in
    if username is None:
        bottle.redirect("/login")

    return bottle.template("newpost_template", dict(subject="", body = "", errors="", tags="", username=username))

#
# Post handler for setting up a new post.
# Only works for logged in user.
@bottle.post('/newpost')
def post_newpost():
    cookie = bottle.request.get_cookie("session")
    username = sessions.get_username(cookie)  # see if user is logged in
    if username is None:
        bottle.redirect("/login")

    title = bottle.request.forms.get("subject")
    tags = bottle.request.forms.get("tags")
    data = bottle.request.files.data

    if data and data.file:
        raw = data.file.read() # This is dangerous for big files

    if title == "" or not data:
        errors = "Post must contain a title and docstore entry"
        return bottle.template("newpost_template", dict(subject=cgi.escape(title, quote=True), username=username,
                                                        data=cgi.escape(data, quote=True), tags=tags, errors=errors))

    # extract tags
    tags = cgi.escape(tags)
    tags_array = extract_tags(tags)

    # extract text
    text = pdftotext_any(raw)
#    text = pdftotext(raw)
#
#    #If no text in this file, it is probably a scanned image. Proceed with OCR (much slower)...
#    if len(text)<2:
#        text = pdftotext_ocr()

    permalink = str(fs.put( data=raw, filename=title, text=text, tags=tags_array, username=username))

    # now bottle.redirect to the docstore permalink
    bottle.redirect("/post/" + permalink)


# displays the initial docstore signup form
@bottle.get('/signup')
def present_signup():
    return bottle.template("signup",
                           dict(username="", password="",
                                password_error="",
                                email="", username_error="", email_error="",
                                verify_error =""))

# displays the initial docstore login form
@bottle.get('/login')
def present_login():
    return bottle.template("login",
                           dict(username="", password="",
                                login_error=""))

# handles a login request
@bottle.post('/login')
def process_login():

    username = bottle.request.forms.get("username")
    password = bottle.request.forms.get("password")

    print "user submitted ", username, "pass ", password

    user_record = users.validate_login(username, password)
    if user_record:
        # username is stored in the user collection in the _id key
        session_id = sessions.start_session(user_record['_id'])

        if session_id is None:
            bottle.redirect("/internal_error")

        cookie = session_id

        # Warning, if you are running into a problem whereby the cookie being set here is
        # not getting set on the redirect, you are probably using the experimental version of bottle (.12).
        # revert to .11 to solve the problem.
        bottle.response.set_cookie("session", cookie)

        bottle.redirect("/welcome")

    else:
        return bottle.template("login",
                               dict(username=cgi.escape(username), password="",
                                    login_error="Invalid Login"))


@bottle.get('/internal_error')
@bottle.view('error_template')
def present_internal_error():
    return {'error':"System has encountered a DB error"}


@bottle.get('/logout')
def process_logout():

    cookie = bottle.request.get_cookie("session")

    sessions.end_session(cookie)

    bottle.response.set_cookie("session", "")


    bottle.redirect("/signup")


@bottle.post('/signup')
def process_signup():

    email = bottle.request.forms.get("email")
    username = bottle.request.forms.get("username")
    password = bottle.request.forms.get("password")
    verify = bottle.request.forms.get("verify")

    # set these up in case we have an error case
    errors = {'username': cgi.escape(username), 'email': cgi.escape(email)}
    if validate_signup(username, password, verify, email, errors):

        if not users.add_user(username, password, email):
            # this was a duplicate
            errors['username_error'] = "Username already in use. Please choose another"
            return bottle.template("signup", errors)

        session_id = sessions.start_session(username)
        print session_id
        bottle.response.set_cookie("session", session_id)
        bottle.redirect("/welcome")
    else:
        print "user did not validate"
        return bottle.template("signup", errors)



@bottle.get("/welcome")
def present_welcome():
    # check for a cookie, if present, then extract value

    cookie = bottle.request.get_cookie("session")
    username = sessions.get_username(cookie)  # see if user is logged in
    if username is None:
        print "welcome: can't identify user...redirecting to signup"
        bottle.redirect("/signup")

    return bottle.template("welcome", {'username': username})


# Helper Functions

#extracts the tag from the tags form element. an experience python programmer could do this in  fewer lines, no doubt
def extract_tags(tags):

    whitespace = re.compile('\s')

    nowhite = whitespace.sub("",tags)
    tags_array = nowhite.split(',')

    # let's clean it up
    cleaned = []
    for tag in tags_array:
        if tag not in cleaned and tag != "":
            cleaned.append(tag)

    return cleaned


# validates that the user information is valid for new signup, return True of False
# and fills in the error string if there is an issue
def validate_signup(username, password, verify, email, errors):
    USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
    PASS_RE = re.compile(r"^.{3,20}$")
    EMAIL_RE = re.compile(r"^[\S]+@[\S]+\.[\S]+$")

    errors['username_error'] = ""
    errors['password_error'] = ""
    errors['verify_error'] = ""
    errors['email_error'] = ""

    if not USER_RE.match(username):
        errors['username_error'] = "invalid username. try just letters and numbers"
        return False

    if not PASS_RE.match(password):
        errors['password_error'] = "invalid password."
        return False
    if password != verify:
        errors['verify_error'] = "password must match"
        return False
    if email != "":
        if not EMAIL_RE.match(email):
            errors['email_error'] = "invalid email address"
            return False
    return True

def pdftotext(myfile):
    # Todo: use tempfile instead
    path = '/tmp/infile.pdf'
    with open(path, 'wb') as f:
            f.write(myfile)
    os.system('pdftotext ' + path + ' temp.txt')
    text = open('temp.txt').read()
    os.remove('temp.txt')
    return text

def pdftotext_ocr():
    # Todo: use tempfile instead
    path = '/tmp/infile.pdf'
    os.system('ocrmypdf ' + path + ' ocr.pdf')
    os.system('pdftotext ocr.pdf temp.txt')
    text = open('temp.txt').read()
    os.remove('temp.txt')
    os.remove('ocr.pdf')
    return text

def pdftotext_any(myfile):
    # Todo: use tempfile instead
    path = '/tmp/infile.pdf'
    with open(path, 'wb') as f:
    #with tempfile.NamedTemporaryFile() as f:
    #    path = f.name
        f.write(myfile)
    text = textract.process(path, method='pdftotext')
    if len(text)<5: # No text found, it is probably an image scan, so we need to do an OCR
        text = textract.process(path, method='tesseract')
    return text


connection_string = "mongodb://localhost"
connection = pymongo.MongoClient(connection_string)
database = connection.test
fs = gridfs.GridFS(database)

posts = docstorePostDAO.DocStorePostDAO(database)
users = userDAO.UserDAO(database)
sessions = sessionDAO.SessionDAO(database)


bottle.debug(True)
bottle.run(host='localhost', port=8082)         # Start the webserver running and wait for requests

