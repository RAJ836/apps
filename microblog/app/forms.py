from flask import request
from flask_wtf import FlaskForm
from app.models import User
from wtforms import StringField,PasswordField,BooleanField,SubmitField,TextAreaField
from wtforms.validators import DataRequired,ValidationError,EqualTo,Email,Length
from flask_login import current_user
class LoginForm(FlaskForm):
    username = StringField('USERNAME',validators=[DataRequired()])
    password = PasswordField('PASSWORD',validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email',validators=[DataRequired(),Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_pass = PasswordField('Confirm Password',validators=[DataRequired(),EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self,username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already Exists !')
    def validate_email(self,email):
        user = User.query.filter_by(email = email.data).first()
        if user:
            raise ValidationError("Email already exists !")


class EditProfileForm(FlaskForm):
    username = StringField('Username',validators=[DataRequired(())])
    about_me = TextAreaField('About Me',validators=[Length(min=0,max=140)])
    submit = SubmitField('Update')
    def validate_username(self,username):
        if current_user.username ==username.data:
            pass
        else:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('Please use a different username !')

class EmptyForm(FlaskForm):
    submit = SubmitField('Submit')

class PostForm(FlaskForm):
    post = TextAreaField('Post something',validators=[DataRequired(),Length(min=0,max=140)])
    submit = SubmitField('Post')

class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Email',validators=[DataRequired(),Email()])
    submit = SubmitField('Request Password Reset')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password',validators=[DataRequired()])
    password2=PasswordField('Repeat Password',validators=[DataRequired(),EqualTo('password')])
    submit = SubmitField('Request Password Reset')

class SearchForm(FlaskForm):
    q=StringField('Search',validators=[DataRequired()])
    def __init__(self, *args, **kwargs):
        if 'formdata' not in kwargs:
            kwargs['formdata'] = request.args
        if 'csrf_enabled' not in kwargs:
            kwargs['csrf_enabled'] = False
        super(SearchForm, self).__init__(*args, **kwargs)