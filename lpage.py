from flask import Flask, render_template, session, redirect, request, url_for, abort
from cloudipsp import Api, Checkout
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash
from flask_migrate import Migrate

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///lpage.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'my_secret_key'

db = SQLAlchemy(app)
migrate = Migrate(app, db)
def create_admin_user():
    admin_username = 'admin1'
    admin_password = generate_password_hash('1234')
    existing_user = Admin.query.filter_by(username=admin_username).first()
    if existing_user:
        return
    admin_user = Admin(
        username=admin_username,
        password=admin_password,
        is_admin=True
    )
    db.session.add(admin_user)
    db.session.commit()

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    isActive = db.Column(db.Boolean, default=False)
    def __repr__(self):
        return self.title

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(95), nullable=False)
    password = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"{self.username}-{self.password}"

with app.app_context():
    create_admin_user()
    db.create_all()
@app.route('/')
def home():
    item = Item.query.all()
    return render_template('index.html', items=item)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('current_user'):
        return redirect(url_for('home'))

    if request.method == 'POST':
        # Get form data
        username = request.form['username']
        password = request.form.get('password')

        # Check if the user exists
        admin = Admin.query.filter_by(username=username).first()
        if admin and check_password_hash(admin.password, password):
            # If the password is correct, store the user ID in the session
            session['current_user'] = admin.id

            # Check if the user is an admin
            if admin.is_admin:
                session['is_admin'] = True
            else:
                session['is_admin'] = False

            return redirect(url_for('home'))
        else:
            return "Wrong email or password. Please try again."

    return render_template('login.html')


@app.route('/logout')
def logout():
    if not session.get('is_admin'):
        return 'Access denied'
    # Видаляємо сеансову змінну `current_user`
    session.pop('current_user', None)
    # Видаляємо сеансову змінну `is_admin`
    session.pop('is_admin', None)
    return redirect(url_for('home'))


@app.route('/create', methods=['GET', 'POST'])
def create():
    if not session.get('is_admin'):
        abort(404)
    if request.method == 'POST':
        title = request.form['title']
        price = int(request.form['price'])

        item = Item(title=title, price=price)

        # Додаємо товар до бази даних
        try:
            db.session.add(item)
            db.session.commit()
            return redirect(url_for('home'))
        except:
            return 'Помилка'
    # Перенаправляємо користувача на сторінку "/home"
    else:
        return render_template('create.html')


@app.route('/buy/<int:id>')
def item_buy(id):
    item = Item.query.get(id)
    api = Api(merchant_id=1396424,
              secret_key='test')
    checkout = Checkout(api=api)
    data = {
        "currency": "UAH",
        "amount": str(item.price) + '00'
    }
    url = checkout.url(data).get('checkout_url')

    # return render_template('index.html')
    return redirect(url)
if __name__ == '__main__':

    app.run(debug=True)
