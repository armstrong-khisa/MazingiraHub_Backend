from flask import Flask

from extensions import db, migrate, jwt


def create_app():
    app = Flask(__name__)

    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///mazingirahub.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JWT_SECRET_KEY"] = "change-this-secret-key"

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    @app.route("/")
    def home():
        return "Welcome to MazingiraHub Backend!"

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True, port=5000)