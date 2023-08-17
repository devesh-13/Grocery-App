import os
from flask import Flask, request, session, url_for, flash, render_template, redirect
from functools import wraps
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
current_dir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///" + os.path.join(current_dir, "testdb.sqlite3")
db = SQLAlchemy()
db.init_app(app)
app.app_context().push()

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    passhash = db.Column(db.String, nullable=False)
    name = db.Column(db.String)
    isadmin = db.Column(db.String, nullable=False, default=0)

    def check_password(self, password):
        return check_password_hash(self.passhash, password)
    @property
    def password(self):
        raise AttributeError('Password cant be shown')
    @password.setter
    def password(self, password):
        self.passhash= generate_password_hash(password)

class Product(db.Model):
    __tablename__ = 'product'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    man_date = db.Column(db.String, nullable=False)
    items = db.relationship("Category", secondary="link")

class Category(db.Model):
    __tablename__ = 'category'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String)
    items = db.relationship("Product", secondary="link")

    products= db.relationship('Product', backref='category')

class CategoryItems(db.Model):
    __tablename__ = 'link'
    product_id = db.Column(db.Integer,   db.ForeignKey("product.id"), primary_key=True, nullable=False)
    category_id = db.Column(db.Integer,  db.ForeignKey("category.id"), primary_key=True, nullable=False)

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = quantity = db.Column(db.Integer, nullable=False)

def auth(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return func(*args, **kwargs)
    return inner

a={'user_id': 'None'}

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("loginpage.html")
    if request.method=='POST':
        username=request.form.get('username')
        password=request.form.get('password')
        user=User.query.filter_by(username=username).first()
        if not user:
            return redirect(url_for('login'))
        if not user.check_password(password):
            return redirect(url_for('login'))
        a['user_id']=user.id
        return redirect(url_for('index'))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("registerpage.html")
    if request.method == "POST":
        username=request.form.get('username')
        password=request.form.get('password')
        name=request.form.get('name')
        user=User(username=username, password=password, name=name)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))

@app.route("/", methods=["GET", "POST"])
# @auth
def index():
    if request.method == "GET":
        #articles = db.session.query(Article).all()
        categories = Category.query.all()
        user=User.query.get(a['user_id'])
        if user==None:
            return redirect("/login")
        elif user.isadmin==1:
            return redirect("/admin")
        else:
            return render_template("index.html", categories=categories, user=user)

@app.route("/logout", methods=["GET", "POST"])
def logout():
    a['user_id']='None'
    return redirect('/login')


@app.route("/profile", methods=["GET", "POST"])
def profile():
    return render_template("profile.html", user=User.query.get(a['user_id']))

@app.route("/cart", methods=["GET", "POST"])
def cart():
    return render_template("profile.html", user=User.query.get(a['user_id']))

@app.route("/orders", methods=["GET", "POST"])
def order():
    return render_template("profile.html", user=User.query.get(a['user_id']))

@app.route("/admin", methods=["GET", "POST"])
def admin():
    return render_template("admin.html", user=User.query.get(a['user_id']), categories=Category.query.all())

@app.route("/add_category", methods=["GET", "POST"])
def add_category():
    if request.method=='GET':
        return render_template("add_category.html", user=User.query.get(a['user_id']),categories=Category.query.all())
    if request.method=='POST':
        name=request.form.get('name')
        category=Category(name=name)
        db.session.add(category)
        db.session.commit()
        return redirect('/admin')

@app.route("/delete_category", methods=["GET", "POST"])
def delete_category():
    if request.method=='GET':
        return render_template("delete_category.html", user=User.query.get(a['user_id']),categories=Category.query.all())
    if request.method=='POST':
        id=request.form.get('id')
        category=Category(id=id)
        db.session.delete(category)
        db.session.commit()
        return redirect('/admin')

@app.route("/products/<categoryname>", methods=["GET", "POST"])
def articles_by_author(categoryname):
    if request.method == "GET":
        products = Product.query.filter(Product.items.any(name=categoryname))
        return render_template("listofitems.html", products=products, categoryname=categoryname)

if __name__ == '__main__':
  # Run the Flask app
    app.run(
      host='0.0.0.0',
      debug=True,
      port=8080
    )
