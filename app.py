from flask import Flask, jsonify, request,session, render_template, url_for, redirect
from flask_sqlalchemy import SQLAlchemy
from random import choice
from flask_marshmallow import Marshmallow
from flask_fontawesome import FontAwesome
from flask_bootstrap import Bootstrap
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///taller_newdb.db'
app.config['SECRET_KEY'] = 'mysecretkey'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
ma = Marshmallow(app)
fa = FontAwesome(app)
Bootstrap(app)
API_SECRET_KEY = os.environ.get('API_SECRET_KEY')

score = 0
character1 = None
character2 = None

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
# db.create_all()

@app.route('/')
@app.route('/home')
@app.route('/index')
def home():
    session.clear()
    global score
    score = 0
    return render_template('home.html')


@app.route('/play', methods=['GET', 'POST'])
def play():
    global character1
    char1 = session.get('char1')
    diff = session.get('diff')
    character1 = choice(db.session.query(Taller).all())
    while True:
        global character2
        character2 = choice(db.session.query(Taller).all())
        if character2.height != character1.height:
            break
    return render_template('play.html',
                               character1=character1,
                               character2=character2,
                               score=score,
                               char1=char1,
                               diff=diff)


@app.route('/check1')
def check1():
    if character1.height > character2.height:
        global score
        score += 1
        session['char1'] = character1.name
        session['diff'] = character1.height - character2.height
        return redirect(url_for('play'))

    else:
        return redirect(url_for('game_over'))


@app.route('/check2')
def check2():
    if character2.height > character1.height:
        global score
        score += 1
        session['char1'] = character2.name
        session['diff'] = character2.height - character1.height
        return redirect(url_for('play'))
    else:
        return redirect(url_for('game_over'))

@app.route('/game-over')
def game_over():
    global score
    final_score = score
    score = 0
    session.clear()
    return render_template('gameover.html', final_score=final_score)


@app.route('/api')
def api():
    return render_template('api.html')


@app.route('/about')
def about():
    return render_template('about.html')

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