from flask import Flask, request, render_template, redirect, url_for, flash, abort, send_from_directory
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user
from forms import SettingsForm, CreatePostForm, RegisterForm, LoginForm, CommentForm
from flask_gravatar import Gravatar
from functools import wraps
import os
import requests
from errors import *
from wallpapers import WALLPAPERS
from dotenv import load_dotenv
from Newsmaker import NewsLetterMaker

load_dotenv()

# ==================================================================================================================== #
HASHING_METHOD = "pbkdf2:sha256"
SALT_TIMES = 8

APP_SECRET_KEY = os.environ.get("APP_SECRET_KEY")
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///blog.db")
NEWS_API_KEY = os.environ.get("NEWS_API_KEY")
ENDPOINT = "http://newsapi.org/v2/top-headlines"
DEFAULT_BG = "https://images.unsplash.com/photo-1464802686167-b939a6910659?crop=entropy&cs=srgb&fm=jpg&ixid" \
             "=MnwyMTQyMTB8MHwxfHNlYXJjaHwxfHxzcGFjZXxlbnwwfDB8fHwxNjE1ODQzNjk2&ixlib=rb-1.2.1&q=85"

wallpapers = [wallpaper["urls"]["regular"] for wallpaper in WALLPAPERS[:50]]
# ==================================================================================================================== #
app = Flask(__name__)
app.config['SECRET_KEY'] = APP_SECRET_KEY
ckeditor = CKEditor(app)
Bootstrap(app)
# ==================================================================================================================== #
# CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
# ==================================================================================================================== #

gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)

# ==================================================================================================================== #


login_manager = LoginManager()
login_manager.init_app(app)


# ==================================================================================================================== #
# Functions
def admin_only(function):
    @wraps(function)
    def wrapper_function(*args, **kwargs):
        if len(User.query.all()) == 1:
            return function(*args, **kwargs)
        else:
            try:
                user_id = int(current_user.get_id())
            except TypeError:
                return abort(403)
            else:
                user = User.query.get(user_id)
                if user.admin_acess:
                    return function(*args, **kwargs)
                else:
                    return abort(403)

    return wrapper_function


def is_writer():
    try:
        user_id = int(current_user.get_id())
    except TypeError:
        return False
    else:
        user = User.query.get(user_id)
        if user.writer_acess:
            return True
        return False


def get_top_news():
    parameters = {
        "country": "us",
        "category": "technology",
        "apiKey": NEWS_API_KEY
    }
    response = requests.get(url=ENDPOINT, params=parameters)
    response.raise_for_status()
    try:
        return response.json()["articles"]
    except KeyError:
        return abort(500)


def get_favourite_wallpaper():
    user_id = current_user.get_id()
    if user_id is not None:
        user = User.query.get(user_id)
        return user.favourite_bg
    else:
        return DEFAULT_BG


# ==================================================================================================================== #
# CONFIGURE TABLES
class User(db.Model, UserMixin):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    # ********** Add Children Relationship ********** #
    posts = relationship("BlogPost", back_populates="author")
    comments = relationship("Comment", back_populates="comment_author")
    # *********************************************** #

    email = db.Column(db.String(250), nullable=False, unique=True)
    password = db.Column(db.String(250), nullable=False)
    name = db.Column(db.String(250), nullable=False)
    admin_acess = db.Column(db.Boolean, nullable=False)
    writer_acess = db.Column(db.Boolean, nullable=False)
    favourite_bg = db.Column(db.String(250), nullable=False)


class BlogPost(db.Model):
    __tablename__ = "blogposts"
    id = db.Column(db.Integer, primary_key=True)

    # ********** Add Parent Relationship ********** #
    # Create Foreign Key, "user_data.id" the users refers to the tablename of User.
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    # Create reference to the User object, the "posts" refers to the posts protperty in the User class.
    author = relationship("User", back_populates="posts")
    # ********************************************* #

    # ********** Add Children Relationship ********** #
    comments = relationship("Comment", back_populates="parent_post")
    # ********************************************* #

    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)


class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)

    # ********** Add Parent Relationship ********** #
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    comment_author = relationship("User", back_populates="comments")

    parent_post = relationship("BlogPost", back_populates="comments")
    post_id = db.Column(db.Integer, db.ForeignKey("blogposts.id"))
    # ********************************************* #

    text = db.Column(db.Text, nullable=False)


# ==================================================================================================================== #


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


db.create_all()


# ==================================================================================================================== #


@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first() is None:
            hashed_password = generate_password_hash(form.password.data, method=HASHING_METHOD, salt_length=SALT_TIMES)
            new_user = User(
                email=form.email.data,
                password=hashed_password,
                name=form.user_name.data,
                admin_acess=False,
                writer_acess=False,
                favourite_bg=DEFAULT_BG
            )
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for("home"))
        else:
            flash(ALREADY_LOGGED_IN_ERROR)
            return redirect(url_for("login"))
    return render_template("register.html", form=form, task="Register", favourite_bg=get_favourite_wallpaper())


@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None:
            user_hashed_pass = user.password
            correct_password = check_password_hash(user_hashed_pass, form.password.data)
            if correct_password:
                login_user(user)
                return redirect(url_for("home"))
            else:
                flash(PASSWORD_ERROR)
                return render_template("login.html", form=form, task="Login", favourite_bg=get_favourite_wallpaper())
        else:
            flash(EMAIL_ERROR)
            return render_template("login.html", form=form, task="Login", favourite_bg=get_favourite_wallpaper())
    return render_template("login.html", form=form, task="Login", favourite_bg=get_favourite_wallpaper())


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route("/delete_user/<user_id>", methods=["POST", "GET"])
def delete_user(user_id):
    requested_user = User.query.get(user_id)
    db.session.delete(requested_user)
    db.session.commit()
    return redirect(url_for("admin_dashboard"))


@app.route("/user-settings/<int:user_id>", methods=["POST", "GET"])
def settings(user_id):
    user = User.query.get(user_id)
    form = SettingsForm(
        name=user.name,
        email=user.email,
    )
    if request.method == "POST":
        if form.validate_on_submit():
            new_email = form.email.data
            new_name = form.name.data
            user.email = new_email
            user.name = new_name
            db.session.commit()
            return redirect(url_for("home"))
    print(current_user.get_id())
    return render_template("settings.html", form=form, user_logged_in=current_user.is_authenticated,
                           task="User Settings", favourite_bg=get_favourite_wallpaper(), all_wallpapers=wallpapers,
                           wallpaper_num=len(wallpapers))


@app.route("/transfer_to_settings")
def go_to_settings():
    return redirect(url_for("settings", user_id=current_user.get_id()))


@app.route("/setwallpaper/<int:wallpaper_number>")
def set_wallapper(wallpaper_number):
    chosen_wallpaper = wallpapers[wallpaper_number]
    user = User.query.get(current_user.get_id())
    user.favourite_bg = chosen_wallpaper
    db.session.commit()
    return redirect(url_for("home"))


@app.route("/magazine", methods=["GET", "POST"])
def magazine():
    if request.method == "POST":
        maker = NewsLetterMaker()
        maker.make_magic()
        return send_from_directory(directory="static/newsletter/pdfs", filename="final_issue.pdf")
    return render_template("get-mag.html", favourite_bg=get_favourite_wallpaper(), task="Magazine Download",
                           user_logged_in=current_user.is_authenticated)


# ==================================================================================================================== #

# Home page
featured_posts = get_top_news()


@app.route("/")
def home():
    posts = BlogPost.query.all()
    posts.reverse()
    if len(posts) != 0:
        return render_template("home/index.html", featured_posts=featured_posts,
                               user_logged_in=current_user.is_authenticated, task="Home",
                               favourite_bg=get_favourite_wallpaper(), show_posts=True, latest_post=posts[0])
    else:
        return render_template("home/index.html", featured_posts=featured_posts,
                               user_logged_in=current_user.is_authenticated, task="Home",
                               favourite_bg=get_favourite_wallpaper(), show_posts=False)


@app.route("/refresh-news")
def refresh():
    global featured_posts
    featured_posts = get_top_news()
    return redirect(url_for("flash_news"))


@app.route("/flash-news")
def flash_news():
    if current_user.is_authenticated:
        user = User.query.get(current_user.get_id())
        return render_template("home/flash_news.html", featured_posts=featured_posts, bg_image=user.favourite_bg,
                               task="Flash News", favourite_bg=get_favourite_wallpaper())
    else:
        return render_template("home/flash_news.html", featured_posts=featured_posts, bg_image=DEFAULT_BG,
                               task="Flash News", favourite_bg=get_favourite_wallpaper())


# ==================================================================================================================== #

@app.route('/blog')
def get_all_posts():
    posts = BlogPost.query.all()
    if not is_writer():
        return render_template("galactic blog/index.html", all_posts=posts,
                               user_logged_in=current_user.is_authenticated, task="Blog",
                               favourite_bg=get_favourite_wallpaper())
    else:
        return render_template("galactic blog/index.html", all_posts=posts, user_logged_in=True, admin_access=True,
                               task="Blog", favourite_bg=get_favourite_wallpaper())


@app.route("/blog/post/<int:post_id>", methods=["GET", "POST"])
def show_post(post_id):
    requested_post = BlogPost.query.get(post_id)
    form = CommentForm()
    if form.validate_on_submit():
        if current_user.is_authenticated:
            new_comment = Comment(
                text=form.body.data,
                comment_author=current_user,
                parent_post=requested_post
            )
            db.session.add(new_comment)
            db.session.commit()
            print(requested_post.comments)
        else:
            flash(COMMENT_LOGIN_ERROR)
            return redirect(url_for("login"))
    return render_template("galactic blog/post.html", post=requested_post, is_writer=is_writer(), post_id=post_id,
                           form=form,
                           user_logged_in=current_user.is_authenticated, task="Blog Post",
                           favourite_bg=get_favourite_wallpaper(), hide_bg=True)


@app.route("/blog/new-post", methods=["POST", "GET"])
@admin_only
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author=current_user,
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("galactic blog/make-post.html", form=form, task="New Blog Post",
                           favourite_bg=get_favourite_wallpaper())


# ==================================================================================================================== #
# ==================================================================================================================== #
# ==================================================================================================================== #
#                                               Admin Panel                                                            #
# ==================================================================================================================== #
# ==================================================================================================================== #
# ==================================================================================================================== #
@app.route("/admin_panel")
@admin_only
def admin_dashboard():
    all_users = User.query.all()
    return render_template("admin panel/index.html", user_data=all_users)


@app.route("/acess/<acess_type>/<action>/<user_id>")
@admin_only
def acess(acess_type, user_id, action):
    requested_user = User.query.get(user_id)
    if action == "give":
        if acess_type == "admin":
            requested_user.admin_acess = True
        elif acess_type == "writer":
            requested_user.writer_acess = True
    else:
        if acess_type == "admin":
            requested_user.admin_acess = False
        elif acess_type == "writer":
            requested_user.writer_acess = False
    db.session.commit()
    return redirect(url_for("admin_dashboard"))


@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
@admin_only
def edit_post(post_id):
    post = BlogPost.query.get(post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.author = post.author
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))

    return render_template("galactic blog/make-post.html", form=edit_form)


@app.route("/delete/<int:post_id>")
@admin_only
def delete_post(post_id):
    post_to_delete = BlogPost.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


# ==================================================================================================================== #
# ==================================================================================================================== #
# ==================================================================================================================== #
# ==================================================================================================================== #
# ==================================================================================================================== #
# ==================================================================================================================== #
# ==================================================================================================================== #

# Not found pages
@app.errorhandler(404)
def page_not_found(e):
    error_data = ERROR_CODES["404"]
    return render_template("galactic blog/error.html", error=error_data)


@app.errorhandler(403)
def page_not_found(e):
    error_data = ERROR_CODES["403"]
    return render_template("galactic blog/error.html", error=error_data)


@app.errorhandler(500)
def page_not_found(e):
    error_data = ERROR_CODES["500"]
    return render_template("galactic blog/error.html", error=error_data)


# ==================================================================================================================== #
if __name__ == "__main__":
    app.run(debug=True)
