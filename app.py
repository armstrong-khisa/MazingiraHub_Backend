from flask import Flask, jsonify

from extensions import db, migrate, jwt


def create_app():
    app = Flask(__name__)

    # ── Config ─────────────────────────────────────────────────────────────────
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///mazingirahub.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JWT_SECRET_KEY"] = "change-this-secret-key"

    # ── Extensions ─────────────────────────────────────────────────────────────
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    # ── Import models so Flask-Migrate can detect them ─────────────────────────
    from models import User, Organization, Project, Donation, Beneficiary, InventoryItem  # noqa: F401

    # ── Blueprints ─────────────────────────────────────────────────────────────
    from controllers.project_controller import project_bp
    from controllers.beneficiary_controller import beneficiary_bp
    from controllers.inventory_controller import inventory_bp

    app.register_blueprint(project_bp)
    app.register_blueprint(beneficiary_bp)
    app.register_blueprint(inventory_bp)

    # ── Global error handlers ──────────────────────────────────────────────────
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"error": "Bad Request", "message": str(e.description)}), 400

    @app.errorhandler(401)
    def unauthorized(e):
        return jsonify({"error": "Unauthorized", "message": str(e.description)}), 401

    @app.errorhandler(403)
    def forbidden(e):
        return jsonify({"error": "Forbidden", "message": str(e.description)}), 403

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Not Found", "message": str(e.description)}), 404

    @app.errorhandler(422)
    def unprocessable(e):
        return jsonify({"error": "Unprocessable Entity", "message": str(e.description)}), 422

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"error": "Internal Server Error", "message": "Something went wrong."}), 500

    # ── Health check ───────────────────────────────────────────────────────────
    @app.route("/")
    def home():
        return jsonify({"message": "Welcome to MazingiraHub Backend!", "status": "ok"})

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True, port=5000)
