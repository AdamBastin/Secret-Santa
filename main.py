import os

from app import create_app

app = create_app()
app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", os.urandom(24))

if __name__ == "__main__":
    app.run(debug=True)
