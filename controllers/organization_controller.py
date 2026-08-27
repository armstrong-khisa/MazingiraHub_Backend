from flask import request, jsonify
from functools import wraps
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity

from extensions import db

from models.organization import Organization
from models.user import User
from models.organization_application import OrganizationApplication

from schemas.organization_schema import OrganizationSchema
from schemas.organization_application_schema import OrganizationApplicationSchema
from schemas.user_schema import serialize_user, validate_profile_update


# ============================================================
# SCHEMAS
# ============================================================

organization_schema = OrganizationSchema()
organizations_schema = OrganizationSchema(many=True)

application_schema = OrganizationApplicationSchema()
applications_schema = OrganizationApplicationSchema(many=True)


# ============================================================
# ORGANIZATION ROUTES
# ============================================================

def role_required(*allowed_roles):
    def decorator(function):
        @wraps(function)
        @jwt_required()
        def wrapper(*args, **kwargs):
            claims = get_jwt()
            user_role = claims.get("role")

            if user_role not in allowed_roles:
                return jsonify({
                    "success": False,
                    "message": "You do not have permission to perform this action"
                }), 403

            return function(*args, **kwargs)

        return wrapper
    return decorator

def register_organization_routes(app):

    # ========================================================
    # 1. SUBMIT ORGANIZATION APPLICATION
    # ========================================================
    @app.route(
        "/organizations/applications",
        methods=["POST"]
    )
    @jwt_required()
    def submit_organization_application():

        data = request.get_json(silent=True) or {}

        # Check if request contains JSON
        if not data:
            return jsonify({
                "success": False,
                "message": "Request body is required"
            }), 400

        data["user_id"] = int(get_jwt_identity())
        if "name" in data and "org_name" not in data:
            data["org_name"] = data.pop("name")

        try:
            # Convert JSON data into an SQLAlchemy object
            application = application_schema.load(data)

            # Add application to database
            db.session.add(application)

            # Save changes
            db.session.commit()

            return jsonify({
                "success": True,
                "message": "Organization application submitted successfully",
                "data": application_schema.dump(application)
            }), 201

        except Exception as error:

            # Undo database changes if something fails
            db.session.rollback()

            return jsonify({
                "success": False,
                "message": "Failed to submit organization application",
                "error": str(error)
            }), 400


    # ========================================================
    # 2. GET ALL ORGANIZATION APPLICATIONS
    # ========================================================

    @app.route(
        "/organizations/applications",
        methods=["GET"]
    )
    @role_required("admin")
    def get_organization_applications():

        applications = OrganizationApplication.query.all()

        return jsonify({
            "success": True,
            "count": len(applications),
            "data": applications_schema.dump(applications)
        }), 200


    # ========================================================
    # 3. GET ONE ORGANIZATION APPLICATION
    # ========================================================

    @app.route(
        "/organizations/applications/<int:application_id>",
        methods=["GET"]
    )

    @role_required("admin")
    def get_organization_application(application_id):

        application = OrganizationApplication.query.get(
            application_id
        )

        if not application:
            return jsonify({
                "success": False,
                "message": "Organization application not found"
            }), 404

        return jsonify({
            "success": True,
            "data": application_schema.dump(application)
        }), 200


    # ========================================================
    # 4. APPROVE ORGANIZATION APPLICATION
    # ========================================================

    @app.route(
        "/organizations/applications/<int:application_id>/approve",
        methods=["PATCH"]
    )

    @role_required("admin")
    def approve_organization_application(application_id):

        application = OrganizationApplication.query.get(
            application_id
        )

        # Check whether application exists
        if not application:
            return jsonify({
                "success": False,
                "message": "Organization application not found"
            }), 404

        # Prevent approving an already approved application
        if application.status == "approved":
            return jsonify({
                "success": False,
                "message": "This application is already approved"
            }), 400

        # Prevent approving a rejected application
        if application.status == "rejected":
            return jsonify({
                "success": False,
                "message": "A rejected application cannot be approved"
            }), 400

        reviewed_by = get_jwt_identity()

        try:

            # Update application
            application.status = "approved"
            application.reviewed_by = reviewed_by

            # Create organization from approved application
            organization = Organization(
                name=application.org_name,
                description=application.description,
                approved_by=reviewed_by,
                user_id=application.user_id,
                approved=True
            )

            application.applicant.role = "organization"

            db.session.add(organization)

            # Save everything
            db.session.commit()

            return jsonify({
                "success": True,
                "message": "Organization application approved successfully",

                "application": application_schema.dump(
                    application
                ),

                "organization": organization_schema.dump(
                    organization
                )
            }), 200

        except Exception as error:

            db.session.rollback()

            return jsonify({
                "success": False,
                "message": "Failed to approve organization application",
                "error": str(error)
            }), 400


    # ========================================================
    # 5. REJECT ORGANIZATION APPLICATION
    # ========================================================

    @app.route(
        "/organizations/applications/<int:application_id>/reject",
        methods=["PATCH"]
    )
    @role_required("admin")
    def reject_organization_application(application_id):

        application = OrganizationApplication.query.get(
            application_id
        )

        # Check whether application exists
        if not application:
            return jsonify({
                "success": False,
                "message": "Organization application not found"
            }), 404

        # Prevent rejecting an already approved application
        if application.status == "approved":
            return jsonify({
                "success": False,
                "message": "An approved application cannot be rejected"
            }), 400

        # Prevent rejecting twice
        if application.status == "rejected":
            return jsonify({
                "success": False,
                "message": "This application is already rejected"
            }), 400

        reviewed_by = get_jwt_identity()

        try:

            application.status = "rejected"
            application.reviewed_by = reviewed_by

            db.session.commit()

            return jsonify({
                "success": True,
                "message": "Organization application rejected successfully",
                "data": application_schema.dump(application)
            }), 200

        except Exception as error:

            db.session.rollback()

            return jsonify({
                "success": False,
                "message": "Failed to reject organization application",
                "error": str(error)
            }), 400


    # ========================================================
    # ORGANIZATIONS
    # ========================================================

    @app.route("/api/organization/profile", methods=["GET"])
    @role_required("organization")
    def get_current_organization_profile():
        user = db.session.get(User, int(get_jwt_identity()))
        organization = Organization.query.filter_by(user_id=user.id).first()

        if not organization:
            return jsonify({
                "success": False,
                "message": "Organization profile not found"
            }), 404

        profile = organization_schema.dump(organization)
        profile.update(serialize_user(user))
        return jsonify({"profile": profile}), 200

    @app.route("/api/organization/profile", methods=["PUT"])
    @role_required("organization")
    def update_current_organization_profile():
        user = db.session.get(User, int(get_jwt_identity()))
        organization = Organization.query.filter_by(user_id=user.id).first()
        if not organization:
            return jsonify({
                "success": False,
                "message": "Organization profile not found"
            }), 404

        data = request.get_json(silent=True) or {}
        user_data = validate_profile_update({
            field: data[field]
            for field in ("full_name", "phone")
            if field in data
        }) if any(field in data for field in ("full_name", "phone")) else {}
        for field, value in user_data.items():
            setattr(user, field, value)

        for field in ("name", "description", "mission", "location"):
            if field in data:
                setattr(organization, field, data[field])

        db.session.commit()
        profile = organization_schema.dump(organization)
        profile.update(serialize_user(user))
        return jsonify({"profile": profile}), 200

    # ========================================================
    # 6. GET ALL ORGANIZATIONS
    # ========================================================

    @app.route(
        "/organizations",
        methods=["GET"]
    )
    def get_organizations():

        organizations = Organization.query.all()

        return jsonify({
            "success": True,
            "count": len(organizations),
            "data": organizations_schema.dump(organizations)
        }), 200


    # ========================================================
    # 7. GET ONE ORGANIZATION
    # ========================================================

    @app.route(
        "/organizations/<int:organization_id>",
        methods=["GET"]
    )
    def get_organization(organization_id):

        organization = Organization.query.get(
            organization_id
        )

        if not organization:
            return jsonify({
                "success": False,
                "message": "Organization not found"
            }), 404

        return jsonify({
            "success": True,
            "data": organization_schema.dump(organization)
        }), 200


    # ========================================================
    # 8. CREATE ORGANIZATION
    # ========================================================

    @app.route(
        "/organizations",
        methods=["POST"]
    )
    def create_organization():

        data = request.get_json()

        if not data:
            return jsonify({
                "success": False,
                "message": "Request body is required"
            }), 400

        try:

            organization = organization_schema.load(data)

            db.session.add(organization)

            db.session.commit()

            return jsonify({
                "success": True,
                "message": "Organization created successfully",
                "data": organization_schema.dump(
                    organization
                )
            }), 201

        except Exception as error:

            db.session.rollback()

            return jsonify({
                "success": False,
                "message": "Failed to create organization",
                "error": str(error)
            }), 400


    # ========================================================
    # 9. UPDATE ORGANIZATION
    # ========================================================

    @app.route(
        "/organizations/<int:organization_id>",
        methods=["PATCH"]
    )
    def update_organization(organization_id):

        organization = Organization.query.get(
            organization_id
        )

        if not organization:
            return jsonify({
                "success": False,
                "message": "Organization not found"
            }), 404

        data = request.get_json()

        if not data:
            return jsonify({
                "success": False,
                "message": "Request body is required"
            }), 400

        try:

            organization = organization_schema.load(
                data,
                instance=organization,
                partial=True
            )

            db.session.commit()

            return jsonify({
                "success": True,
                "message": "Organization updated successfully",
                "data": organization_schema.dump(
                    organization
                )
            }), 200

        except Exception as error:

            db.session.rollback()

            return jsonify({
                "success": False,
                "message": "Failed to update organization",
                "error": str(error)
            }), 400


    # ========================================================
    # 10. DELETE ORGANIZATION
    # ========================================================

    @app.route(
        "/organizations/<int:organization_id>",
        methods=["DELETE"]
    )
    def delete_organization(organization_id):

        organization = Organization.query.get(
            organization_id
        )

        if not organization:
            return jsonify({
                "success": False,
                "message": "Organization not found"
            }), 404

        try:

            db.session.delete(organization)

            db.session.commit()

            return jsonify({
                "success": True,
                "message": "Organization deleted successfully"
            }), 200

        except Exception as error:

            db.session.rollback()

            return jsonify({
                "success": False,
                "message": "Failed to delete organization",
                "error": str(error)
            }), 400
