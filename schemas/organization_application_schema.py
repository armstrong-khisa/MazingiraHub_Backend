from extensions import ma
from models.organization_application import OrganizationApplication


class OrganizationApplicationSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = OrganizationApplication
        load_instance = True
        include_fk = True
