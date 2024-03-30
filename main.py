from flask import Flask, request, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bookstore.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = "\x82\xdc\x15\xc6\x179m\xbf}SxM7}\xb0o\xa2\x87\xfd\t;3\xf6\xc4"
db = SQLAlchemy(app)
app.app_context().push()
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('author.id'), nullable=False)
    price = db.Column(db.Float, nullable=False)
    short_info = db.Column(db.String(250), nullable=True)

    cart = db.relationship('Cart', backref='book')
    order = db.relationship('Order', backref='book')


class Author(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    books = db.relationship('Book', backref='author')

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    price = db.Column(db.Float, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(100), default="pending")

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


db.create_all()

@app.route('/')
def index():
    books = Book.query.all()
    return render_template('index.html', books=books)

@app.route('/add_to_cart/<int:book_id>')
def add_to_cart(book_id):
    
    cart = Cart(book_id=book_id)
    db.session.add(cart)
    db.session.commit()

    flash('book added to cart')
    return redirect(url_for('index'))

@app.route('/cart')
def view_cart():
    books_in_cart = Cart.query.all()
    return render_template('cart.html', books=books_in_cart)

@app.route('/cart/delete/<int:cart_id>')
def delete_cart(cart_id):
    Cart.query.filter_by(id=cart_id).delete()
    db.session.commit()
    flash('cart deleted')

    return redirect(url_for('view_cart'))

@app.route('/checkout', methods=['POST'])
def checkout():
    name = request.form.get('name')
    phone = request.form.get('phone')
    address = request.form.get('address')

    books_in_cart = Cart.query.all()
    for cart in books_in_cart:
        db.session.add(Order(book_id=cart.book.id, price=cart.book.price, name=name, phone=phone, address=address))

    Cart.query.delete()

    db.session.commit()

    flash('Your order has been successfully registered. Thank you for your purchase')
    return redirect(url_for('index'))


@app.route('/admin')
@login_required
def admin_view():
    books = Book.query.all()
    authors = Author.query.all()
    orders = Order.query.all()

    return render_template('admin.html', books=books, authors=authors, orders=orders)

@app.route('/admin/create/book', methods=['POST'])
def create_book():
    title = request.form.get('title')
    author_id = request.form.get('author_id')
    price = request.form.get('price')
    short_inf = request.form.get('short_info')
    book = Book(title=title, author_id=author_id, price=price, short_info=short_inf)
    db.session.add(book)
    db.session.commit()

    flash('book created')
    return redirect(url_for('admin_view'))

@app.route('/admin/create/author', methods=['POST'])
def create_author():
    name = request.form.get('name')
    author = Author(name=name)
    db.session.add(author)
    db.session.commit()

    flash('author created')
    return redirect(url_for('admin_view'))

@app.route('/admin/order/approve/<int:order_id>')
def approve_order(order_id):
    order = Order.query.get(order_id)
    order.status = "Approved"

    db.session.commit()
    flash('order approved')
    return redirect(url_for('admin_view'))

@app.route('/admin/order/deni/<int:order_id>')
def deni_order(order_id):
    order = Order.query.get(order_id)
    order.status = "Denied"

    db.session.commit()
    flash('order Denied')
    return redirect(url_for('admin_view'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        print(username, password)
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            login_user(user)
            return redirect(url_for('admin_view'))
        else:
            return 'Invalid username or password'
    else:
        return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == '__main__':
    user = User(username="admin", password="admin")
    db.session.add(user)
    db.session.commit()
    app.run(debug=True)
