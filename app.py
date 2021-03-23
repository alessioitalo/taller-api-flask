from flask import Flask, jsonify, request,session, render_template, url_for, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from random import choice
from flask_marshmallow import Marshmallow
from flask_fontawesome import FontAwesome
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField, TextAreaField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired
from flask_mail import Mail, Message
import os

app = Flask(__name__)
db = SQLAlchemy(app)
ma = Marshmallow(app)
fa = FontAwesome(app)
Bootstrap(app)


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///taller_newdb.db'
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
mail = Mail(app)

RECEIVER = os.environ.get('RECEIVER_MAIL')
API_SECRET_KEY = os.environ.get('API_SECRET_KEY')

# DATABASE
class Taller(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True)
    bio = db.Column(db.String(500), nullable=False)
    height = db.Column(db.Integer, nullable=False)
    photo = db.Column(db.String(500), nullable=False)
    credit = db.Column(db.String(100), nullable=False)


class TallerSchema(ma.Schema):
    class Meta:
        fields = ('id','name','bio','height', 'photo', 'credit')

taller_schema = TallerSchema()


#CONTACT FORM
class ContactForm(FlaskForm):
    name = StringField('Name*', validators=[DataRequired()])
    email = EmailField('Email*', validators=[DataRequired()])
    subject = StringField('Subject')
    message = TextAreaField('Message*', render_kw={'class': 'form-control', 'rows': 6}, validators=[DataRequired()])
    submit = SubmitField('Send')


@app.route('/')
@app.route('/home')
@app.route('/index')
def home():
    session['score'] = 0
    return render_template('home.html')

@app.route('/play', methods=['GET', 'POST'])
def play():
    id_one = session.get('id_one')
    id_two = session.get('id_two')
    character1 = choice(db.session.query(Taller).all())
    while True:
        character2 = choice(db.session.query(Taller).all())
        if character2.height != character1.height:
            break
    if request.method == 'POST':
        if request.args['choice'] == '1':
            if Taller.query.filter_by(id=id_one).first().height > Taller.query.filter_by(id=id_two).first().height:
                session['score'] += 1
                return redirect(url_for('play',
                                        char=Taller.query.filter_by(id=id_one).first().name,
                                        diff=Taller.query.filter_by(id=id_one).first().height - Taller.query.filter_by(id=id_two).first().height)
                                )
            else:
                return redirect(url_for('game_over'))
        if request.args['choice'] == '2':
            if Taller.query.filter_by(id=id_two).first().height > Taller.query.filter_by(id=id_one).first().height:
                session['score'] += 1
                return redirect(url_for('play',
                                        char=Taller.query.filter_by(id=id_two).first().name,
                                        diff=Taller.query.filter_by(id=id_two).first().height - Taller.query.filter_by(id=id_one).first().height)
                                )
            else:
                return redirect(url_for('game_over'))
    else:
        char = request.args.get('char')
        diff = request.args.get('diff')
        score = session['score']
        session['id_one'] = character1.id
        session['id_two'] = character2.id
        return render_template('play.html',
                                   character1=character1,
                                   character2=character2,
                                   id_one=session['id_one'],
                                   id_two=session['id_two'],
                                   char=char,
                                   diff=diff,
                                   score=score
                               )


@app.route('/game-over')
def game_over():
    final_score = session['score']
    session['score'] = 0
    return render_template('gameover.html', final_score=final_score)


@app.route('/api')
def api():
    response = choice(db.session.query(Taller).all())
    return render_template('api.html', response=response)


@app.route('/about', methods=['GET','POST'])
def about():
    form = ContactForm()
    if form.validate_on_submit():
        name = request.form['name']
        email = request.form['email']
        subject = request.form['subject']
        body = request.form['message']
        msg = Message(subject="Who's taller Contact Form", recipients=[RECEIVER])
        msg.html = "<h1>Who's taller Contact Form</h1>" \
                   f"<p>Message from{name}</p>"\
                   f"<p>Email address: {email}</p>" \
                   f"<p>Subject: {subject}</p>" \
                   f"<p>Message: {body}</p>"
        mail.send(msg)
        flash('Message sent! We will get in touch soon...')
        return render_template('about.html', form=form)
    else:
        return render_template('about.html', form=form)

# ERROR HANDLERS

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(e):
    return render_template('500.html'), 505


## REST API
@app.route('/get')
def get_info():
    random_character = choice(db.session.query(Taller).all())
    return jsonify(taller_schema.dump(random_character))


@app.route('/add', methods=['POST'])
def add_info():
    name = request.form['name']
    bio = request.form['bio']
    height = request.form['height']
    photo = request.form['photo']
    credit = request.form['credit']
    secret_key = request.form['secret_key']
    if secret_key == API_SECRET_KEY:
        new_character = Taller(
            name=name,
            bio=bio,
            height=height,
            photo=photo,
            credit=credit)
        db.session.add(new_character)
        db.session.commit()
        return jsonify(response={'Success':'Added to database'})
    else:
        return jsonify(response={'403':'Sorry, you are not authorized to add data.'}), 403

if __name__ == '__main__':
    app.run()
