
from flask import Flask, request

from flask_sqlalchemy import SQLAlchemy

from flask_marshmallow import Marshmallow

app = Flask(__name__)

# connect to the datbase

app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql+psycopg2://ecommerce_dev:123456@localhost:5432/oct_ecommerce"

db = SQLAlchemy(app)

ma = Marshmallow(app)

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

class ProductSchema(ma.Schema):
    class Meta:
        # fields
        fields = ("id", "name" ,"description", "price", "stock")

# to handle alll products
products_schema = ProductSchema(many=True)
# handle sinfle product
product_schema = ProductSchema(many=False)



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




