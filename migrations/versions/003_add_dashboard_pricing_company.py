"""Add dashboard, pricing, and company modules

Revision ID: 003_add_dashboard_pricing_company
Revises: 002_add_offline_modules
Create Date: 2024-01-15

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003_add_dashboard_pricing_company'
down_revision = '002_add_offline_modules'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ==========================================================================
    # DASHBOARD MODULE TABLES
    # ==========================================================================
    
    # Social Accounts (linked social logins)
    op.create_table(
        'social_accounts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('provider', sa.String(20), nullable=False),
        sa.Column('provider_user_id', sa.String(200), nullable=False),
        sa.Column('provider_email', sa.String(200), nullable=True),
        sa.Column('access_token', sa.Text(), nullable=True),
        sa.Column('refresh_token', sa.Text(), nullable=True),
        sa.Column('token_expires_at', sa.DateTime(), nullable=True),
        sa.Column('profile_data', postgresql.JSONB(), nullable=True),
        sa.Column('profile_picture_url', sa.String(500), nullable=True),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'provider', name='uq_social_account_user_provider')
    )
    op.create_index('ix_social_accounts_user_id', 'social_accounts', ['user_id'])
    op.create_index('ix_social_accounts_provider', 'social_accounts', ['provider'])
    
    # Amendment Requests
    op.create_table(
        'amendment_requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('request_number', sa.String(50), nullable=False, unique=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('booking_id', sa.Integer(), nullable=False),
        sa.Column('booking_type', sa.String(50), nullable=False),
        sa.Column('booking_reference', sa.String(100), nullable=True),
        sa.Column('amendment_type', sa.String(50), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('requested_changes', postgresql.JSONB(), nullable=True),
        sa.Column('documents', postgresql.JSONB(), nullable=True),
        sa.Column('status', sa.String(30), default='pending'),
        sa.Column('amendment_fee', sa.Numeric(12, 2), default=0),
        sa.Column('supplier_penalty', sa.Numeric(12, 2), default=0),
        sa.Column('refund_amount', sa.Numeric(12, 2), nullable=True),
        sa.Column('admin_remarks', sa.Text(), nullable=True),
        sa.Column('processed_by', sa.Integer(), nullable=True),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['processed_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_amendment_requests_user_id', 'amendment_requests', ['user_id'])
    op.create_index('ix_amendment_requests_status', 'amendment_requests', ['status'])
    
    # User Queries (Support Tickets)
    op.create_table(
        'user_queries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ticket_number', sa.String(50), nullable=False, unique=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('query_type', sa.String(50), nullable=False),
        sa.Column('subject', sa.String(300), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('related_booking_id', sa.Integer(), nullable=True),
        sa.Column('related_enquiry_id', sa.Integer(), nullable=True),
        sa.Column('related_application_id', sa.Integer(), nullable=True),
        sa.Column('attachments', postgresql.JSONB(), nullable=True),
        sa.Column('status', sa.String(30), default='open'),
        sa.Column('priority', sa.String(20), default='normal'),
        sa.Column('resolution', sa.Text(), nullable=True),
        sa.Column('resolved_by', sa.Integer(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['resolved_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_user_queries_user_id', 'user_queries', ['user_id'])
    op.create_index('ix_user_queries_status', 'user_queries', ['status'])
    
    # Query Responses
    op.create_table(
        'query_responses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('query_id', sa.Integer(), nullable=False),
        sa.Column('responder_id', sa.Integer(), nullable=False),
        sa.Column('is_staff_response', sa.Boolean(), default=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('attachments', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.ForeignKeyConstraint(['query_id'], ['user_queries.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['responder_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_query_responses_query_id', 'query_responses', ['query_id'])
    
    # Activity Logs
    op.create_table(
        'activity_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('activity_type', sa.String(50), nullable=False),
        sa.Column('description', sa.String(500), nullable=False),
        sa.Column('entity_type', sa.String(50), nullable=True),
        sa.Column('entity_id', sa.Integer(), nullable=True),
        sa.Column('ip_address', sa.String(50), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_activity_logs_user_id', 'activity_logs', ['user_id'])
    op.create_index('ix_activity_logs_activity_type', 'activity_logs', ['activity_type'])
    op.create_index('ix_activity_logs_created_at', 'activity_logs', ['created_at'])
    
    # ==========================================================================
    # PRICING MODULE TABLES
    # ==========================================================================
    
    # Markup Rules
    op.create_table(
        'markup_rules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('code', sa.String(50), nullable=True),
        sa.Column('service_type', sa.String(30), nullable=False, default='all'),
        sa.Column('supplier_code', sa.String(50), nullable=True),
        sa.Column('supplier_name', sa.String(200), nullable=True),
        sa.Column('airline_code', sa.String(10), nullable=True),
        sa.Column('origin_city', sa.String(10), nullable=True),
        sa.Column('destination_city', sa.String(10), nullable=True),
        sa.Column('origin_country', sa.String(10), nullable=True),
        sa.Column('destination_country', sa.String(10), nullable=True),
        sa.Column('cabin_class', sa.String(20), nullable=True),
        sa.Column('fare_type', sa.String(50), nullable=True),
        sa.Column('hotel_star_rating', sa.Integer(), nullable=True),
        sa.Column('hotel_chain', sa.String(100), nullable=True),
        sa.Column('user_type', sa.String(20), nullable=False, default='all'),
        sa.Column('agent_id', sa.Integer(), nullable=True),
        sa.Column('markup_type', sa.String(20), nullable=False, default='percentage'),
        sa.Column('markup_value', sa.Numeric(12, 4), nullable=False, default=0),
        sa.Column('min_markup', sa.Numeric(12, 2), nullable=True),
        sa.Column('max_markup', sa.Numeric(12, 2), nullable=True),
        sa.Column('min_fare', sa.Numeric(14, 2), nullable=True),
        sa.Column('max_fare', sa.Numeric(14, 2), nullable=True),
        sa.Column('apply_on_net_fare', sa.Boolean(), default=True),
        sa.Column('apply_on_taxes', sa.Boolean(), default=False),
        sa.Column('priority', sa.Integer(), default=0),
        sa.Column('is_stackable', sa.Boolean(), default=False),
        sa.Column('valid_from', sa.Date(), nullable=True),
        sa.Column('valid_to', sa.Date(), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.ForeignKeyConstraint(['agent_id'], ['users.id']),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_markup_rules_tenant_id', 'markup_rules', ['tenant_id'])
    op.create_index('ix_markup_rules_service_type', 'markup_rules', ['service_type'])
    op.create_index('ix_markup_rules_is_active', 'markup_rules', ['is_active'])
    
    # Discount Rules
    op.create_table(
        'discount_rules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('code', sa.String(50), nullable=True, unique=True),
        sa.Column('service_type', sa.String(30), nullable=False, default='all'),
        sa.Column('supplier_code', sa.String(50), nullable=True),
        sa.Column('airline_code', sa.String(10), nullable=True),
        sa.Column('user_type', sa.String(20), nullable=False, default='all'),
        sa.Column('agent_ids', postgresql.JSONB(), nullable=True),
        sa.Column('discount_type', sa.String(20), nullable=False, default='percentage'),
        sa.Column('discount_value', sa.Numeric(12, 4), nullable=False, default=0),
        sa.Column('max_discount', sa.Numeric(12, 2), nullable=True),
        sa.Column('min_booking_amount', sa.Numeric(14, 2), nullable=True),
        sa.Column('usage_limit_total', sa.Integer(), nullable=True),
        sa.Column('usage_limit_per_user', sa.Integer(), nullable=True),
        sa.Column('usage_count', sa.Integer(), default=0),
        sa.Column('apply_on_markup', sa.Boolean(), default=False),
        sa.Column('priority', sa.Integer(), default=0),
        sa.Column('valid_from', sa.Date(), nullable=False),
        sa.Column('valid_to', sa.Date(), nullable=False),
        sa.Column('travel_from', sa.Date(), nullable=True),
        sa.Column('travel_to', sa.Date(), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_discount_rules_tenant_id', 'discount_rules', ['tenant_id'])
    op.create_index('ix_discount_rules_code', 'discount_rules', ['code'])
    op.create_index('ix_discount_rules_is_active', 'discount_rules', ['is_active'])
    
    # Convenience Fee Slabs
    op.create_table(
        'convenience_fee_slabs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('service_type', sa.String(30), nullable=False, default='all'),
        sa.Column('payment_mode', sa.String(50), nullable=False),
        sa.Column('card_type', sa.String(50), nullable=True),
        sa.Column('user_type', sa.String(20), nullable=False, default='all'),
        sa.Column('min_amount', sa.Numeric(14, 2), nullable=False, default=0),
        sa.Column('max_amount', sa.Numeric(14, 2), nullable=True),
        sa.Column('fee_type', sa.String(20), default='percentage'),
        sa.Column('fee_value', sa.Numeric(12, 4), nullable=False, default=0),
        sa.Column('min_fee', sa.Numeric(12, 2), nullable=True),
        sa.Column('max_fee', sa.Numeric(12, 2), nullable=True),
        sa.Column('apply_gst', sa.Boolean(), default=True),
        sa.Column('gst_rate', sa.Numeric(5, 2), default=18.00),
        sa.Column('priority', sa.Integer(), default=0),
        sa.Column('valid_from', sa.Date(), nullable=True),
        sa.Column('valid_to', sa.Date(), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_convenience_fee_slabs_tenant_id', 'convenience_fee_slabs', ['tenant_id'])
    op.create_index('ix_convenience_fee_slabs_payment_mode', 'convenience_fee_slabs', ['payment_mode'])
    
    # Price Audit Logs
    op.create_table(
        'price_audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('booking_id', sa.Integer(), nullable=True),
        sa.Column('booking_type', sa.String(50), nullable=True),
        sa.Column('session_id', sa.String(100), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('user_type', sa.String(20), nullable=True),
        sa.Column('service_type', sa.String(50), nullable=False),
        sa.Column('supplier_code', sa.String(50), nullable=True),
        sa.Column('base_fare', sa.Numeric(14, 2), nullable=False),
        sa.Column('taxes', sa.Numeric(14, 2), default=0),
        sa.Column('markup_rules_applied', postgresql.JSONB(), nullable=True),
        sa.Column('discount_rules_applied', postgresql.JSONB(), nullable=True),
        sa.Column('fee_slabs_applied', postgresql.JSONB(), nullable=True),
        sa.Column('total_markup', sa.Numeric(14, 2), default=0),
        sa.Column('total_discount', sa.Numeric(14, 2), default=0),
        sa.Column('convenience_fee', sa.Numeric(14, 2), default=0),
        sa.Column('final_amount', sa.Numeric(14, 2), nullable=False),
        sa.Column('calculation_metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_price_audit_logs_tenant_id', 'price_audit_logs', ['tenant_id'])
    op.create_index('ix_price_audit_logs_created_at', 'price_audit_logs', ['created_at'])
    
    # ==========================================================================
    # COMPANY MODULE TABLES
    # ==========================================================================
    
    # Company Profiles
    op.create_table(
        'company_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False, unique=True),
        sa.Column('company_name', sa.String(300), nullable=False),
        sa.Column('legal_name', sa.String(300), nullable=True),
        sa.Column('tagline', sa.String(500), nullable=True),
        sa.Column('about_us', sa.Text(), nullable=True),
        sa.Column('logo_url', sa.String(500), nullable=True),
        sa.Column('logo_dark_url', sa.String(500), nullable=True),
        sa.Column('favicon_url', sa.String(500), nullable=True),
        sa.Column('og_image_url', sa.String(500), nullable=True),
        sa.Column('primary_color', sa.String(20), default='#1976D2'),
        sa.Column('secondary_color', sa.String(20), default='#FF9800'),
        sa.Column('accent_color', sa.String(20), nullable=True),
        sa.Column('email', sa.String(200), nullable=True),
        sa.Column('support_email', sa.String(200), nullable=True),
        sa.Column('phone', sa.String(50), nullable=True),
        sa.Column('toll_free', sa.String(50), nullable=True),
        sa.Column('whatsapp', sa.String(50), nullable=True),
        sa.Column('address_line1', sa.String(300), nullable=True),
        sa.Column('address_line2', sa.String(300), nullable=True),
        sa.Column('city', sa.String(100), nullable=True),
        sa.Column('state', sa.String(100), nullable=True),
        sa.Column('country', sa.String(100), nullable=True),
        sa.Column('pincode', sa.String(20), nullable=True),
        sa.Column('website_url', sa.String(300), nullable=True),
        sa.Column('facebook_url', sa.String(300), nullable=True),
        sa.Column('instagram_url', sa.String(300), nullable=True),
        sa.Column('twitter_url', sa.String(300), nullable=True),
        sa.Column('linkedin_url', sa.String(300), nullable=True),
        sa.Column('youtube_url', sa.String(300), nullable=True),
        sa.Column('meta_title', sa.String(200), nullable=True),
        sa.Column('meta_description', sa.Text(), nullable=True),
        sa.Column('meta_keywords', sa.Text(), nullable=True),
        sa.Column('google_analytics_id', sa.String(50), nullable=True),
        sa.Column('facebook_pixel_id', sa.String(50), nullable=True),
        sa.Column('smtp_host', sa.String(200), nullable=True),
        sa.Column('smtp_port', sa.Integer(), nullable=True),
        sa.Column('smtp_username', sa.String(200), nullable=True),
        sa.Column('smtp_password', sa.String(200), nullable=True),
        sa.Column('email_from_name', sa.String(200), nullable=True),
        sa.Column('email_from_address', sa.String(200), nullable=True),
        sa.Column('timezone', sa.String(50), default='Asia/Kolkata'),
        sa.Column('default_currency', sa.String(10), default='INR'),
        sa.Column('date_format', sa.String(20), default='DD/MM/YYYY'),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_company_profiles_tenant_id', 'company_profiles', ['tenant_id'])
    
    # Bank Accounts
    op.create_table(
        'bank_accounts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('bank_name', sa.String(200), nullable=False),
        sa.Column('branch_name', sa.String(200), nullable=True),
        sa.Column('account_name', sa.String(300), nullable=False),
        sa.Column('account_number', sa.String(50), nullable=False),
        sa.Column('account_type', sa.String(20), default='current'),
        sa.Column('ifsc_code', sa.String(20), nullable=True),
        sa.Column('swift_code', sa.String(20), nullable=True),
        sa.Column('iban', sa.String(50), nullable=True),
        sa.Column('routing_number', sa.String(20), nullable=True),
        sa.Column('upi_id', sa.String(100), nullable=True),
        sa.Column('upi_qr_code_url', sa.String(500), nullable=True),
        sa.Column('purpose', sa.String(100), default='wallet_topup'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('display_order', sa.Integer(), default=0),
        sa.Column('is_primary', sa.Boolean(), default=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_bank_accounts_tenant_id', 'bank_accounts', ['tenant_id'])
    
    # Business Registrations
    op.create_table(
        'business_registrations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False, unique=True),
        sa.Column('gst_number', sa.String(50), nullable=True),
        sa.Column('gst_state_code', sa.String(10), nullable=True),
        sa.Column('gst_type', sa.String(20), nullable=True),
        sa.Column('gst_certificate_url', sa.String(500), nullable=True),
        sa.Column('pan_number', sa.String(20), nullable=True),
        sa.Column('pan_name', sa.String(300), nullable=True),
        sa.Column('pan_card_url', sa.String(500), nullable=True),
        sa.Column('cin_number', sa.String(50), nullable=True),
        sa.Column('registration_number', sa.String(100), nullable=True),
        sa.Column('incorporation_date', sa.Date(), nullable=True),
        sa.Column('incorporation_certificate_url', sa.String(500), nullable=True),
        sa.Column('iata_code', sa.String(20), nullable=True),
        sa.Column('iata_certificate_url', sa.String(500), nullable=True),
        sa.Column('travel_license_number', sa.String(100), nullable=True),
        sa.Column('travel_license_expiry', sa.Date(), nullable=True),
        sa.Column('travel_license_url', sa.String(500), nullable=True),
        sa.Column('tan_number', sa.String(20), nullable=True),
        sa.Column('msme_number', sa.String(50), nullable=True),
        sa.Column('msme_certificate_url', sa.String(500), nullable=True),
        sa.Column('insurance_policy_number', sa.String(100), nullable=True),
        sa.Column('insurance_provider', sa.String(200), nullable=True),
        sa.Column('insurance_expiry', sa.Date(), nullable=True),
        sa.Column('insurance_certificate_url', sa.String(500), nullable=True),
        sa.Column('custom_registrations', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_business_registrations_tenant_id', 'business_registrations', ['tenant_id'])
    
    # ==========================================================================
    # ACL TABLES
    # ==========================================================================
    
    # ACL Modules
    op.create_table(
        'acl_modules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False, unique=True),
        sa.Column('display_name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('parent_module_id', sa.Integer(), nullable=True),
        sa.Column('icon', sa.String(50), nullable=True),
        sa.Column('display_order', sa.Integer(), default=0),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.ForeignKeyConstraint(['parent_module_id'], ['acl_modules.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_acl_modules_name', 'acl_modules', ['name'])
    
    # ACL Permissions
    op.create_table(
        'acl_permissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('module_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('display_name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('code', sa.String(150), nullable=False, unique=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.ForeignKeyConstraint(['module_id'], ['acl_modules.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('module_id', 'name', name='uq_acl_permission_module_name')
    )
    op.create_index('ix_acl_permissions_module_id', 'acl_permissions', ['module_id'])
    op.create_index('ix_acl_permissions_code', 'acl_permissions', ['code'])
    
    # ACL Roles
    op.create_table(
        'acl_roles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('display_name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_system_role', sa.Boolean(), default=False),
        sa.Column('is_default', sa.Boolean(), default=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'name', name='uq_acl_role_tenant_name')
    )
    op.create_index('ix_acl_roles_tenant_id', 'acl_roles', ['tenant_id'])
    
    # ACL Role Permissions
    op.create_table(
        'acl_role_permissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.Column('permission_id', sa.Integer(), nullable=False),
        sa.Column('is_granted', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.ForeignKeyConstraint(['role_id'], ['acl_roles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['permission_id'], ['acl_permissions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('role_id', 'permission_id', name='uq_role_permission')
    )
    op.create_index('ix_acl_role_permissions_role_id', 'acl_role_permissions', ['role_id'])
    
    # ACL User Roles
    op.create_table(
        'acl_user_roles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.Column('assigned_by', sa.Integer(), nullable=True),
        sa.Column('assigned_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['role_id'], ['acl_roles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['assigned_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'role_id', name='uq_user_role')
    )
    op.create_index('ix_acl_user_roles_user_id', 'acl_user_roles', ['user_id'])
    op.create_index('ix_acl_user_roles_role_id', 'acl_user_roles', ['role_id'])


def downgrade() -> None:
    # ACL tables
    op.drop_table('acl_user_roles')
    op.drop_table('acl_role_permissions')
    op.drop_table('acl_roles')
    op.drop_table('acl_permissions')
    op.drop_table('acl_modules')
    
    # Company tables
    op.drop_table('business_registrations')
    op.drop_table('bank_accounts')
    op.drop_table('company_profiles')
    
    # Pricing tables
    op.drop_table('price_audit_logs')
    op.drop_table('convenience_fee_slabs')
    op.drop_table('discount_rules')
    op.drop_table('markup_rules')
    
    # Dashboard tables
    op.drop_table('activity_logs')
    op.drop_table('query_responses')
    op.drop_table('user_queries')
    op.drop_table('amendment_requests')
    op.drop_table('social_accounts')
