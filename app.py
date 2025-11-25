from flask import Flask, redirect, url_for
from config import Config
from models.database import init_db
from routes.auth import auth_bp, bcrypt
from routes.tasks import tasks_bp

app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
init_db(app)
bcrypt.init_app(app)

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(tasks_bp)

@app.route('/')
def index():
    return redirect(url_for('auth.login'))

if __name__ == '__main__':
    app.run(debug=True)