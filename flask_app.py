# -*- coding: utf-8 -*-
"""
Created on Thu Feb 27 13:29:32 2020

@author: manoel.alonso
"""

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_bootstrap import Bootstrap


from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_moment import Moment
from datetime import datetime
from flask_login import LoginManager, login_required, login_user, UserMixin, current_user
#from flask_migrate import Migrate
from flask_mail import Mail, Message

import json

with open('/home/manoelutad/configuration.json') as json_file:
    configuration = json.load(json_file)


print("FLASK_APP.PY:",__name__)

#########################################################
# DB - CLASSES - START                                  #
#########################################################
from models import models

#########################################################
# DB - CLASSES - END                                    #
#########################################################


#########################################################
# FLASK - FORMS - START                                 #
#########################################################
from forms import forms
#########################################################
# FLASK - FORMS - END                                   #
#########################################################
app = models.app
db = models.db

Bootstrap(app)

#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///./database/data.db'
#app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False



moment = Moment(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

#migrate = Migrate(app,db)

app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = configuration['gmail_username']
app.config['MAIL_PASSWORD'] = configuration['gmail_password']

app.config['FLASKY_MAIL_SUBJECT_PREFIX'] = '[U-TAD Prog. Web II - Servidor] '
app.config['FLASKY_MAIL_SENDER'] = 'Prof. Manoel Gadi <fraudmodelchallenge@gmail.com>'

mail = Mail(app)

def send_email(to, subject, template, **kwargs):
    msg = Message(app.config['FLASKY_MAIL_SUBJECT_PREFIX'] + subject, sender=app.config['FLASKY_MAIL_SENDER'], recipients=[to])
    msg.body = render_template(template + '.txt', **kwargs)
    msg.html = render_template(template + '.html', **kwargs)
    mail.send(msg)


"""
user1 = User(username='manoel',email='manoel.alonso@u-tad.com',password='12345678')
db.session.add(user1)
db.session.commit()


user2 = User(username='manoel2', email='manoel2.alonso@u-tad.com',password='12345678')
db.session.add(user2)
db.session.commit()

user = User.query.filter_by(id=1).first()
"""

@login_manager.user_loader
def load_user(user_id):
    return models.User.query.get(int(user_id))



@app.route('/')
def index():
    return render_template("index.html", page="index", current_time=datetime.utcnow())

@app.route('/login', methods=['GET','POST'])
def login():
    form = forms.LoginForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            try:
                user = models.User.query.filter_by(username=form.username.data).first()
    #            return "usenname={}; password_bd={}; password_enviada={}".format(user.username,user.password,form.password.data)

                if (user == None):
                    flash('Wrong user or password.')
                elif  user.confirmed == 0:
                    flash('Email address has not been confirmed. Please visit your email to confirm your user before logging in.')
                elif check_password_hash(user.password,form.password.data):
                    login_user(user, remember=form.remember.data)
                    return redirect(url_for('dashboard'))
                else:
                    flash('Access denied - wrong username or password')
            except:
                flash('Access denied - wrong username or password')
    else:
        pass
    return render_template("login.html", page="login", form=form)

import random
@app.route('/signup', methods=['GET','POST'])
def signup():
    form = forms.RegisterForm()
#    form.language.choices = [('pc', 'Pascal'), ('cb', 'Cobol'),('jv', 'Java')]

    if request.method == 'POST':
        if form.validate_on_submit():
            try:
                password_hashed = generate_password_hash(form.password.data,method='sha256')
                new_user = models.User(username=form.username.data,
                                email=form.email.data,
                                password=password_hashed,
                                userhash=str(random.getrandbits(128)),
                                dni=form.dni.data,
                                silo=form.dni.data[3])
                send_email(new_user.email,'Por favor, confirmar correo.','mail/new_user',user=new_user)
                db.session.add(new_user)
                db.session.commit()
                flash("User created successfully")
                return redirect(url_for('login'))
            except:
                db.session.rollback()
                flash("Something went wrong. User has not been created. Please try again.")
    return render_template("signup.html", page="signup", form=form)

@app.route('/confirmuser/<username>/<userhash>', methods=['GET'])
def confirmuser(username,userhash):
    form = forms.LoginForm()
    user = models.User.query.filter_by(username=username).first()
    if user == None:
        flash('Invalid url.')
    elif user.userhash != userhash:
        flash('Invalid url.')
    else:
        user.confirmed = 1
        db.session.commit()
        flash('Email validated, please log in.')

    return render_template("login.html", page="login", form=form)




@app.route('/dashboard')
@login_required
def dashboard():
    return render_template("dashboard.html", page="dashboard",current_user=current_user)

@app.route('/profile')
@login_required
def profile():
    user = models.User.query.filter_by(username=current_user.username).first()
    form = forms.ProfileForm(username=user.username,
                        email=user.email,
                        dni  = user.dni,
                        silo = user.silo)
    return render_template("profile.html", page="profile",current_user=current_user, form=form)


@app.route('/logout')
@login_required
def logout():
    return redirect(url_for('index'))

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html")

@app.errorhandler(500)
def internal_server_error(e):
    return render_template("500.html")

#def internal_server_error(e):
#    return render_template("500.html")

if __name__ == '__main__':
    app.run(debug=True)
    #app.run()

