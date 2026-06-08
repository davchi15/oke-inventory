from flask import Flask
from db import create_table
from routes import bp

app = Flask(__name__)
create_table()
app.register_blueprint(bp)

if __name__ == "__main__":
    app.run(debug=True)