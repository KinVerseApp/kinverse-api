from __future__ import annotations

from sqlalchemy import Enum

# The Postgres enum types below already exist in the database - they're
# created by kinverse-project/databasefiles/postgresql/001_kinverse_schema.sql.
# create_type=False is required so SQLAlchemy never tries to CREATE TYPE
# itself (and never tries to DROP TYPE on a metadata.drop_all()); the SQL
# schema script and any future Alembic migrations own that lifecycle, the
# ORM only describes columns that reference it by name.
#
# Without an explicit Enum mapped this way, a plain String() column sends
# its value to asyncpg typed as character varying, and Postgres rejects it:
# "column \"edge_type\" is of type edge_type_enum but expression is of type
# character varying" - this is not hypothetical, it's what happens on the
# very first real INSERT (see relationships/models.py before this fix).


def pg_enum(name: str, *values: str) -> Enum:
    return Enum(*values, name=name, create_type=False)


AuthProviderEnum = pg_enum("auth_provider_enum", "google", "apple", "microsoft", "email")
AccountStatusEnum = pg_enum("account_status_enum", "active", "suspended", "deleted")
GenderEnum = pg_enum("gender_enum", "female", "male", "non_binary", "unspecified")
DobPrecisionEnum = pg_enum("dob_precision_enum", "exact", "year_only", "unknown")
VisibilityEnum = pg_enum("visibility_enum", "public", "family_network", "direct_relatives", "private")

EdgeTypeEnum = pg_enum("edge_type_enum", "parent_child", "partner")
PartnerTypeEnum = pg_enum("partner_type_enum", "spouse", "partner", "ex_spouse", "ex_partner")
EdgeStatusEnum = pg_enum("edge_status_enum", "pending", "confirmed", "rejected")
EdgeSourceEnum = pg_enum("edge_source_enum", "manual", "invite_accept", "search_match", "ai_suggested")

InvitationScopeEnum = pg_enum("invitation_scope_enum", "person", "tree")
InvitationMethodEnum = pg_enum("invitation_method_enum", "sms", "email", "link", "qr", "whatsapp")
InvitationStatusEnum = pg_enum(
    "invitation_status_enum", "pending", "sent", "opened", "accepted", "declined", "expired"
)

NotificationTypeEnum = pg_enum(
    "notification_type_enum",
    "invite_accepted", "relationship_confirmed", "relationship_request",
    "birthday", "new_family_member",
)

PrivacyFieldEnum = pg_enum(
    "privacy_field_enum", "email", "phone", "date_of_birth", "address", "heritage_info", "biography"
)
