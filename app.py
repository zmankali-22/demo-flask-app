from datetime import timedelta
from flask import Flask, request

from flask_sqlalchemy import SQLAlchemy

from flask_marshmallow import Marshmallow
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)

# connect to the datbase

app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql+psycopg2://ecommerce_dev:123456@localhost:5432/oct_ecommerce"

app.config["JWT_SECRET_KEY"] = "secret"

db = SQLAlchemy(app)

ma = Marshmallow(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

# Model - table in our database
class Product(db.Model):
    # tablename
    __tablename__ = "products"
    # define the primary key
    id = db.Column(db.Integer, primary_key=True)
    # more attributes
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(100))
    price = db.Column(db.Float)
    stock = db.Column(db.Integer)

class User(db.Model):

    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String, nullable = False, unique =True)
    password = db.Column(db.String(100), nullable = False)
    is_admin = db.Column(db.Boolean, default=False)

class ProductSchema(ma.Schema):
    class Meta:
        # fields
        fields = ("id", "name" ,"description", "price", "stock")

# to handle alll products
products_schema = ProductSchema(many=True)
# handle sinfle product
product_schema = ProductSchema(many=False)

class UserSchema(ma.Schema):
    class Meta:
        fields = ("id", "name", "email", "password", "is_admin")

users_schema = UserSchema(many=True, exclude=["password"])
user_schema = UserSchema(many=False, exclude=["password"])


# cli command
    
@app.cli.command("create")
def create_tables():
    db.create_all()
    print("Tables created")


@app.cli.command("seed")
def seed_db():
    # create a product object
    product1 = Product(
        name = "product1",
        description= "product 1 desc",
        price = 140.45,
        stock = 15
    )

    product2 = Product()
    product2.name = "product2 "
    product2.price = 15.99
    product2.stock = 15

    # add session
    db.session.add(product1)
    db.session.add(product2)

    # users
    users = [
        User(
            name = "User 1",
            email = "user1@email.com",
            password= bcrypt.generate_password_hash("123456").decode('utf8'),
            is_admin = True
        ),
        User(
            name = "User 2",
            email = "user2@email.com",
            password= bcrypt.generate_password_hash("123456").decode('utf8'),
            is_admin = False
        )
    ]
    # add to session
    db.session.add_all(users)

    # commit
    db.session.commit()
    print("Tables seeded")

@app.cli.command("drop")
def drop_tables():
    db.drop_all()
    print("Tables dropped")

#  route to return all products
@app.route('/products')
def get_products():
    stmt = db.select(Product) # select * from products;
    products_list = db.session.scalars(stmt)
    # conver non-serializable to JSON (readable format)
    data = products_schema.dump(products_list)
    return data

# route to return a single product

@app.route('/products/<int:product_id>')
def get_product(product_id):
    stmt = db.select(Product).filter_by(id = product_id) # slect * from products whwre id = prodcut_id
    product = db.session.scalar(stmt)

    if(product):
        data = product_schema.dump(product)
        return data
    else:
        return {"error" : f"Product with id {product_id} not exist"}, 404

@app.route("/products", methods=["POST"])
@jwt_required()
def create_product():
    product_fields = request.get_json()
    print(product_fields)
    new_product = Product(
        name = product_fields.get("name"),
        description = product_fields.get("description"),
        price = product_fields.get("price"),
        stock = product_fields.get("stock")
    )

    db.session.add(new_product)
    db.session.commit()
    data = product_schema.dump(new_product)
    return data, 201

@app.route("/products/<int:product_id>", methods=["PUT", "PATCH"])
def update_product(product_id):
    # find the product from db to update, 
    stmt = db.select(Product).filter_by(id = product_id)
    product = db.session.scalar(stmt)
    #  get the data to be updated - received from the body of the request
    product_fields =request.get_json()
    if product:
    # update the attributes, 
        product.name = product_fields.get("name") or product.name
        product.description = product_fields.get("description") or product.description
        product.price = product_fields.get("price") or product.price
        product.stock = product_fields.get("stock") or product.stock
        
    # commit and the return
        db.session.commit()
        return product_schema.dump(product)

    else:

        # return
        return {"error" : f"Product with id {product_id} doesn't exist"}, 404



@app.route("/products/<int:product_id>", methods = ['DELETE'])
@jwt_required()
def delete_product(product_id):
    is_admin = authoriseAsAdmin()
    if not is_admin:
        return {"error" : "Not authorized to delete a product" }, 403
    stmt = db.select(Product).where(Product.id==product_id)
    product = db.session.scalar(stmt)
    if product:
        db.session.delete(product)
        db.session.commit()
        return {"msg": f"Product {product.name} is deleted"}
    else:
        return {"error": f"Product {product_id} does not exist"}, 404
    

@app.route("/auth/register", methods = ["POST"])
def register_user():
    try:
        user_fields = request.get_json()
        password = user_fields.get("password")
        hashed_password = bcrypt.generate_password_hash(password).decode('utf8')
        user = User(
            name = user_fields.get("name"),
            email = user_fields.get('email'),
            password = hashed_password
        )
        db.session.add(user)
        db.session.commit()
        return user_schema.dump(user), 201
    except IntegrityError:
        return {"error" : f"Email address {user.email} already exists"}, 409

@app.route("/auth/login", methods = ["POST"])
def auth_login():
    # extract fields from body of the request
    user_fields = request.get_json()
    # find the user by email
    stmt = db.select(User).filter_by(email =user_fields.get("email"))
    user = db.session.scalar(stmt)
    # if user exist and password matches
    if user and bcrypt.check_password_hash(user.password, user_fields.get("password")):
        # create jwt
        token = create_access_token(identity=str(user.id), expires_delta=timedelta(days=1))
        # return jwt along with the user info
        return {"email": user.email, "token": token, "is_admin" : user.is_admin}
    
    # else
    else:

        # return error
        return {"error" : "Invalid email or password "}, 401
    
def authoriseAsAdmin():
    user_id = get_jwt_identity()
    stmt = db.select(User).filter_by(id=user_id)
    user = db.session.scalar(stmt)
    return user.is_admin