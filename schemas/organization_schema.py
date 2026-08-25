from extensions import ma
from models.organization import Organization


class OrganizationSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Organization
        load_instance = True
        include_fk = True
