python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install flask

python3 -m pip psycopg2-binary flask-sqlalchemy
pip3 install flask-marshmallow marshmallow-sqlalchemy

pip3 install flask_bcrypt flask_jwt_extended















for database grant privileges to database

# grant all privikeges on databse <new datbae> to <new user>
# grant all on schema public to <new user>