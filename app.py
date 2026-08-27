
import logging
import os

from dotenv import load_dotenv
from flask import Flask, jsonify
from controllers.auth_controller import auth_bp
from extensions import db, ma, migrate, jwt

# Load .env before anything else
load_dotenv()

# Basic logging so callback payloads show in terminal
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


def create_app():
    app = Flask(__name__)

    # ── Config ─────────────────────────────────────────────────────────────────
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///mazingirahub.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JWT_SECRET_KEY"] = os.getenv(
        "JWT_SECRET_KEY",
        "development-secret-key-change-me-32-bytes-long"
    )


    # ── Extensions ─────────────────────────────────────────────────────────────
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    ma.init_app(app)

    # ── Import models so Flask-Migrate can detect them ─────────────────────────
    from models import (  # noqa: F401
        User, Organization, OrganizationApplication, Project, Donation, Payment,
        RecurringDonation, Beneficiary, InventoryItem,
        Story, StoryMedia
    )

    # ── Blueprints ─────────────────────────────────────────────────────────────
    app.register_blueprint(auth_bp)

    from controllers.admin_controller import admin_bp
    from controllers.donation_controller import donation_bp
    from controllers.project_controller import project_bp
    from controllers.beneficiary_controller import beneficiary_bp
    from controllers.inventory_controller import inventory_bp
    from controllers.recurring_donation_controller import recurring_bp
    from controllers.story_controller import story_bp
    from controllers.payment_controller import payment_bp
    from controllers.user_controller import user_bp

    app.register_blueprint(admin_bp)
    app.register_blueprint(donation_bp)
    app.register_blueprint(project_bp)
    app.register_blueprint(beneficiary_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(recurring_bp)
    app.register_blueprint(story_bp)
    app.register_blueprint(payment_bp)
    app.register_blueprint(user_bp)

    from controllers.organization_controller import register_organization_routes
    register_organization_routes(app)
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

    @app.errorhandler(409)
    def conflict(e):
        return jsonify({"error": "Conflict", "message": str(e.description)}), 409

    @app.errorhandler(422)
    def unprocessable(e):
        return jsonify({"error": "Unprocessable Entity", "message": str(e.description)}), 422

    @app.errorhandler(502)
    def bad_gateway(e):
        return jsonify({"error": "Bad Gateway", "message": str(e.description)}), 502

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
