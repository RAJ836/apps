from app import app,forms,db
from app.email import send_password_reset_email
from flask import g, render_template, flash, redirect, url_for, request, current_app
from app.models import User,Post
from flask_login import login_user,current_user,logout_user,login_required
from werkzeug.urls import url_parse
from datetime import datetime
from wtforms.validators import ValidationError

# posts = [
#     {
#         'author':{'username':'Raj'},
#         'body':'Beautiful day in India'
#     },
#     {
#         'author':{'username':'john'},
#         'body':'programming daily'
#     },
#     {
#         'author':{'username':'Dave'},
#         'body':'third blog post'
#     }
# ]

@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen=datetime.now()
        db.session.commit()
        g.search_form = forms.SearchForm()




@app.route('/',methods=['POST','GET'])
@app.route('/index',methods=['POST','GET'])
@login_required
def index():
    form = forms.PostForm()
    if form.validate_on_submit():
        post = Post(body=form.post.data,author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post is now Live !')
        return redirect(url_for('index'))
    page= request.args.get('page',1,type=int)
    posts=current_user.followed_posts().paginate(page,app.config['POSTS_PER_PAGE'],False)
    next_url = url_for('index',page=posts.next_num) if posts.has_next else None
    prev_url = url_for('index',page=posts.prev_num) if posts.has_prev else None
    return render_template('index.html',title='Home Page',posts=posts.items,form=form,next_url=next_url,prev_url=prev_url)

@app.route('/explore')
@login_required
def explore():
    page=request.args.get('page',1,type=int)
    posts=Post.query.order_by(Post.timestamp.desc()).paginate(page,app.config['POSTS_PER_PAGE'],False)
    next_url = url_for('index',page=posts.next_num) if posts.has_next else None
    prev_url = url_for('index',page=posts.prev_num) if posts.has_prev else None
    return render_template('index.html',title='Explore',posts=posts.items,prev_url=prev_url,next_url=next_url)


@app.route('/register',methods=['POST','GET'])
def register():

    form = forms.RegistrationForm()
    if form.validate_on_submit():
        app.logger.info('Start of Registering the user')
        app.logger.warning(form.username.errors)
        app.logger.warning(form.email.errors)
        username= form.username.data
        email=form.email.data
        password = form.password.data
        user = User(username=username,email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash(f'{username} had registered successfully ! ')
        app.logger.info(f'{username} has registered successfully!')
        return redirect(url_for('login'))
    return render_template('register.html',form=form,title='Register')

@app.route('/login',methods=['POST','GET'])
def login():
    if current_user.is_authenticated:
        flash("Already logged in")
        return redirect(url_for('index'))
    form = forms.LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and  user.check_password(form.password.data):
            app.logger.info(f"{user.username} has  logged in !")
            flash(f'{user.username} has logged in !')
            login_user(user=user,remember=form.remember_me.data)
            next_page = request.args.get('next')
            print(f'next page : {next_page}')

            if not next_page:
                next_page = url_for('index')
            return redirect(next_page)
        else:
            flash(f'Invalid Username or Password')

    return render_template('login.html',form=form,title='Sign In')

@app.route('/logout')
def logout():
    username = current_user.username
    logout_user()
    flash('Logged out')
    app.logger.info(f"{username } has logged out")
    return redirect(url_for('index'))

@app.route('/user/<username>')
@login_required
def user(username):

    form = forms.EmptyForm()
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page',1,type=int)
    posts=user.posts.order_by(Post.timestamp.desc()).paginate(page,app.config['POSTS_PER_PAGE'],False)
    next_url = url_for('index', page=posts.next_num) if posts.has_next else None
    prev_url = url_for('index', page=posts.prev_num) if posts.has_prev else None
    return render_template('user.html',user=user,posts=posts.items,next_url=next_url,prev_url=prev_url,form=form)

@app.route('/edit_profile',methods=['POST','GET'])
@login_required  # to protect against unauthorised users
def edit_profile():
    form = forms.EditProfileForm()
    if form.validate_on_submit():
        current_user.username=form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Updated the Profile!')

    elif request.method == 'GET':
        form.username.data=current_user.username
        form.about_me.data = current_user.about_me

    return render_template('edit_profile.html',form=form,title='Edit Profile')

@app.route('/follow/<username>',methods=['POST'])
@login_required
def follow(username):
    form = forms.EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash('User {} not found.'.format(username))
            return redirect(url_for('index'))
        if user == current_user:
            flash('You cannot follow yourself !')
            return redirect(url_for('user',username=username))
        current_user.follow(user)
        db.session.commit()
        flash(f'Your are now following {username}')
        return redirect(url_for('user', username=username))
    else:
        return redirect(url_for('index'))
@app.route('/unfollow/<username>',methods=['POST'])
@login_required
def unfollow(username):
    form  = forms.EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first_or_404()
        if user is None:
            flash('User {} not found.'.format(username))
            return redirect(url_for('index'))
        if user == current_user:
            flash('You cannot unfollow yourself !')
            return redirect(url_for('user',username=username))
        current_user.unfollow(user)
        db.session.commit()
        flash(f'Your have unfollowed  {username}')
        return redirect(url_for('user', username=username))
    else:
        return redirect(url_for('index'))

@app.route('/reset_password_request',methods=['POST','GET'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = forms.ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Please check your mail for the instructions to reset your password ')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html',
                           title= 'Reset Password',form=form)

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('index'))
    form = forms.ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)


@app.route('/search')
@login_required
def search():
    if not g.search_form.validate():
        return redirect(url_for('explore'))
    page = request.args.get('page', 1, type=int)
    posts, total = Post.search(g.search_form.q.data, page,
                               current_app.config['POSTS_PER_PAGE'])
    next_url = url_for('search', q=g.search_form.q.data, page=page + 1) \
        if total > page * current_app.config['POSTS_PER_PAGE'] else None
    prev_url = url_for('search', q=g.search_form.q.data, page=page - 1) \
        if page > 1 else None
    return render_template('search.html', title='Search', posts=posts,
                           next_url=next_url, prev_url=prev_url)