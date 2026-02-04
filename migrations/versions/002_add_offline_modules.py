"""
Add Holiday, Visa, Activity, Transfer, CMS and Settings Tables

Revision ID: 002_add_offline_modules
Revises: 001_add_api_keys_and_salesperson_tracking
Create Date: 2024-01-15

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision = '002_add_offline_modules'
down_revision = '001_add_api_keys_and_salesperson_tracking'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # =========================================================================
    # HOLIDAY MODULE TABLES
    # =========================================================================
    
    # Package Themes
    op.create_table(
        'package_themes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('slug', sa.String(120), nullable=False, unique=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('icon_url', sa.String(500), nullable=True),
        sa.Column('image_url', sa.String(500), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('display_order', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_theme_slug', 'package_themes', ['slug'])
    
    # Package Destinations
    op.create_table(
        'package_destinations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('slug', sa.String(220), nullable=False, unique=True),
        sa.Column('country', sa.String(100), nullable=True),
        sa.Column('state', sa.String(100), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('image_url', sa.String(500), nullable=True),
        sa.Column('is_international', sa.Boolean(), default=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('display_order', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_dest_slug', 'package_destinations', ['slug'])
    op.create_index('idx_dest_country', 'package_destinations', ['country'])
    
    # Holiday Packages
    op.create_table(
        'holiday_packages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(300), nullable=False),
        sa.Column('slug', sa.String(320), nullable=False, unique=True),
        sa.Column('code', sa.String(50), nullable=True, unique=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('highlights', JSONB, nullable=True),
        sa.Column('package_type', sa.String(20), nullable=False),
        sa.Column('theme_id', sa.Integer(), sa.ForeignKey('package_themes.id'), nullable=True),
        sa.Column('destination_id', sa.Integer(), sa.ForeignKey('package_destinations.id'), nullable=True),
        sa.Column('duration_days', sa.Integer(), nullable=False),
        sa.Column('duration_nights', sa.Integer(), nullable=False),
        sa.Column('base_price', sa.Float(), nullable=False),
        sa.Column('selling_price', sa.Float(), nullable=False),
        sa.Column('child_price', sa.Float(), nullable=True),
        sa.Column('infant_price', sa.Float(), nullable=True),
        sa.Column('single_supplement', sa.Float(), nullable=True),
        sa.Column('max_pax', sa.Integer(), nullable=True),
        sa.Column('min_pax', sa.Integer(), default=1),
        sa.Column('departure_cities', JSONB, nullable=True),
        sa.Column('fixed_departure_dates', JSONB, nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_featured', sa.Boolean(), default=False),
        sa.Column('featured_order', sa.Integer(), nullable=True),
        sa.Column('meta_title', sa.String(200), nullable=True),
        sa.Column('meta_description', sa.String(500), nullable=True),
        sa.Column('created_by_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_pkg_slug', 'holiday_packages', ['slug'])
    op.create_index('idx_pkg_theme', 'holiday_packages', ['theme_id'])
    op.create_index('idx_pkg_destination', 'holiday_packages', ['destination_id'])
    op.create_index('idx_pkg_featured', 'holiday_packages', ['is_featured', 'featured_order'])
    
    # Package Itineraries
    op.create_table(
        'package_itineraries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('package_id', sa.Integer(), sa.ForeignKey('holiday_packages.id', ondelete='CASCADE'), nullable=False),
        sa.Column('day_number', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(300), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('meals_included', JSONB, nullable=True),
        sa.Column('accommodation', sa.String(200), nullable=True),
        sa.Column('activities', JSONB, nullable=True),
        sa.Column('image_url', sa.String(500), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_itin_package', 'package_itineraries', ['package_id', 'day_number'])
    
    # Package Inclusions/Exclusions
    op.create_table(
        'package_inclusions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('package_id', sa.Integer(), sa.ForeignKey('holiday_packages.id', ondelete='CASCADE'), nullable=False),
        sa.Column('item', sa.String(500), nullable=False),
        sa.Column('is_inclusion', sa.Boolean(), default=True),
        sa.Column('display_order', sa.Integer(), default=0),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Package Images
    op.create_table(
        'package_images',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('package_id', sa.Integer(), sa.ForeignKey('holiday_packages.id', ondelete='CASCADE'), nullable=False),
        sa.Column('image_url', sa.String(500), nullable=False),
        sa.Column('caption', sa.String(200), nullable=True),
        sa.Column('is_primary', sa.Boolean(), default=False),
        sa.Column('display_order', sa.Integer(), default=0),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Package Enquiries
    op.create_table(
        'package_enquiries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('enquiry_number', sa.String(50), nullable=False, unique=True),
        sa.Column('package_id', sa.Integer(), sa.ForeignKey('holiday_packages.id'), nullable=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('phone', sa.String(20), nullable=False),
        sa.Column('travel_date', sa.Date(), nullable=True),
        sa.Column('adults', sa.Integer(), default=1),
        sa.Column('children', sa.Integer(), default=0),
        sa.Column('infants', sa.Integer(), default=0),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('assigned_to_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('quoted_price', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_enq_status', 'package_enquiries', ['status'])
    op.create_index('idx_enq_user', 'package_enquiries', ['user_id'])
    
    # Package Bookings
    op.create_table(
        'package_bookings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('booking_number', sa.String(50), nullable=False, unique=True),
        sa.Column('package_id', sa.Integer(), sa.ForeignKey('holiday_packages.id'), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('enquiry_id', sa.Integer(), sa.ForeignKey('package_enquiries.id'), nullable=True),
        sa.Column('travel_date', sa.Date(), nullable=False),
        sa.Column('adults', sa.Integer(), default=1),
        sa.Column('children', sa.Integer(), default=0),
        sa.Column('infants', sa.Integer(), default=0),
        sa.Column('traveller_details', JSONB, nullable=True),
        sa.Column('base_amount', sa.Float(), nullable=False),
        sa.Column('tax_amount', sa.Float(), default=0),
        sa.Column('discount_amount', sa.Float(), default=0),
        sa.Column('total_amount', sa.Float(), nullable=False),
        sa.Column('paid_amount', sa.Float(), default=0),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('payment_status', sa.String(20), default='pending'),
        sa.Column('special_requests', sa.Text(), nullable=True),
        sa.Column('contact_name', sa.String(200), nullable=True),
        sa.Column('contact_email', sa.String(255), nullable=True),
        sa.Column('contact_phone', sa.String(20), nullable=True),
        sa.Column('created_by_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_pkg_bkg_status', 'package_bookings', ['status'])
    op.create_index('idx_pkg_bkg_user', 'package_bookings', ['user_id'])
    op.create_index('idx_pkg_bkg_date', 'package_bookings', ['travel_date'])
    
    # =========================================================================
    # VISA MODULE TABLES
    # =========================================================================
    
    # Visa Countries
    op.create_table(
        'visa_countries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('code', sa.String(3), nullable=False, unique=True),
        sa.Column('flag_url', sa.String(500), nullable=True),
        sa.Column('image_url', sa.String(500), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('embassy_address', sa.Text(), nullable=True),
        sa.Column('embassy_phone', sa.String(50), nullable=True),
        sa.Column('embassy_email', sa.String(255), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_popular', sa.Boolean(), default=False),
        sa.Column('display_order', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_visa_country_code', 'visa_countries', ['code'])
    
    # Visa Types
    op.create_table(
        'visa_types',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('country_id', sa.Integer(), sa.ForeignKey('visa_countries.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('validity_days', sa.Integer(), nullable=True),
        sa.Column('max_stay_days', sa.Integer(), nullable=True),
        sa.Column('entry_type', sa.String(20), default='single'),
        sa.Column('processing_days', sa.Integer(), nullable=False),
        sa.Column('express_processing_days', sa.Integer(), nullable=True),
        sa.Column('base_price', sa.Float(), nullable=False),
        sa.Column('express_price', sa.Float(), nullable=True),
        sa.Column('service_fee', sa.Float(), default=0),
        sa.Column('gst_percentage', sa.Float(), default=18.0),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_visa_type_country', 'visa_types', ['country_id'])
    
    # Visa Requirements
    op.create_table(
        'visa_requirements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('visa_type_id', sa.Integer(), sa.ForeignKey('visa_types.id', ondelete='CASCADE'), nullable=False),
        sa.Column('document_name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_mandatory', sa.Boolean(), default=True),
        sa.Column('document_format', sa.String(100), nullable=True),
        sa.Column('sample_url', sa.String(500), nullable=True),
        sa.Column('display_order', sa.Integer(), default=0),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Visa Applications
    op.create_table(
        'visa_applications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('application_number', sa.String(50), nullable=False, unique=True),
        sa.Column('visa_type_id', sa.Integer(), sa.ForeignKey('visa_types.id'), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('applicant_name', sa.String(200), nullable=False),
        sa.Column('applicant_email', sa.String(255), nullable=False),
        sa.Column('applicant_phone', sa.String(20), nullable=False),
        sa.Column('passport_number', sa.String(50), nullable=True),
        sa.Column('passport_expiry', sa.Date(), nullable=True),
        sa.Column('travel_date', sa.Date(), nullable=True),
        sa.Column('return_date', sa.Date(), nullable=True),
        sa.Column('purpose_of_visit', sa.String(200), nullable=True),
        sa.Column('documents', JSONB, nullable=True),
        sa.Column('is_express', sa.Boolean(), default=False),
        sa.Column('base_amount', sa.Float(), nullable=False),
        sa.Column('service_fee', sa.Float(), default=0),
        sa.Column('express_fee', sa.Float(), default=0),
        sa.Column('gst_amount', sa.Float(), default=0),
        sa.Column('total_amount', sa.Float(), nullable=False),
        sa.Column('paid_amount', sa.Float(), default=0),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('payment_status', sa.String(20), default='pending'),
        sa.Column('visa_number', sa.String(100), nullable=True),
        sa.Column('visa_issued_date', sa.Date(), nullable=True),
        sa.Column('visa_expiry_date', sa.Date(), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('admin_notes', sa.Text(), nullable=True),
        sa.Column('assigned_to_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_visa_app_status', 'visa_applications', ['status'])
    op.create_index('idx_visa_app_user', 'visa_applications', ['user_id'])
    
    # =========================================================================
    # ACTIVITY MODULE TABLES
    # =========================================================================
    
    # Activity Categories
    op.create_table(
        'activity_categories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('slug', sa.String(120), nullable=False, unique=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('icon_url', sa.String(500), nullable=True),
        sa.Column('image_url', sa.String(500), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('display_order', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_act_cat_slug', 'activity_categories', ['slug'])
    
    # Activity Locations
    op.create_table(
        'activity_locations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('slug', sa.String(220), nullable=False, unique=True),
        sa.Column('city', sa.String(100), nullable=True),
        sa.Column('state', sa.String(100), nullable=True),
        sa.Column('country', sa.String(100), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('image_url', sa.String(500), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('display_order', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_act_loc_slug', 'activity_locations', ['slug'])
    op.create_index('idx_act_loc_country', 'activity_locations', ['country'])
    
    # Activities
    op.create_table(
        'activities',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(300), nullable=False),
        sa.Column('slug', sa.String(320), nullable=False, unique=True),
        sa.Column('code', sa.String(50), nullable=True, unique=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('short_description', sa.String(500), nullable=True),
        sa.Column('highlights', JSONB, nullable=True),
        sa.Column('category_id', sa.Integer(), sa.ForeignKey('activity_categories.id'), nullable=True),
        sa.Column('location_id', sa.Integer(), sa.ForeignKey('activity_locations.id'), nullable=True),
        sa.Column('duration_hours', sa.Float(), nullable=True),
        sa.Column('duration_text', sa.String(100), nullable=True),
        sa.Column('meeting_point', sa.String(500), nullable=True),
        sa.Column('meeting_point_coords', JSONB, nullable=True),
        sa.Column('adult_price', sa.Float(), nullable=False),
        sa.Column('child_price', sa.Float(), nullable=True),
        sa.Column('infant_price', sa.Float(), nullable=True),
        sa.Column('group_discount_percentage', sa.Float(), nullable=True),
        sa.Column('group_min_size', sa.Integer(), nullable=True),
        sa.Column('max_participants', sa.Integer(), nullable=True),
        sa.Column('min_participants', sa.Integer(), default=1),
        sa.Column('cancellation_policy', sa.Text(), nullable=True),
        sa.Column('inclusions', JSONB, nullable=True),
        sa.Column('exclusions', JSONB, nullable=True),
        sa.Column('what_to_bring', JSONB, nullable=True),
        sa.Column('important_info', JSONB, nullable=True),
        sa.Column('gallery', JSONB, nullable=True),
        sa.Column('video_url', sa.String(500), nullable=True),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('is_featured', sa.Boolean(), default=False),
        sa.Column('is_instant_confirmation', sa.Boolean(), default=True),
        sa.Column('meta_title', sa.String(200), nullable=True),
        sa.Column('meta_description', sa.String(500), nullable=True),
        sa.Column('created_by_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_activity_slug', 'activities', ['slug'])
    op.create_index('idx_activity_category', 'activities', ['category_id'])
    op.create_index('idx_activity_location', 'activities', ['location_id'])
    op.create_index('idx_activity_status', 'activities', ['status'])
    
    # Activity Slots
    op.create_table(
        'activity_slots',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('activity_id', sa.Integer(), sa.ForeignKey('activities.id', ondelete='CASCADE'), nullable=False),
        sa.Column('start_time', sa.Time(), nullable=False),
        sa.Column('end_time', sa.Time(), nullable=True),
        sa.Column('capacity', sa.Integer(), nullable=True),
        sa.Column('price_modifier', sa.Float(), default=0),
        sa.Column('is_recurring', sa.Boolean(), default=True),
        sa.Column('recurring_days', JSONB, nullable=True),
        sa.Column('specific_date', sa.Date(), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_slot_activity', 'activity_slots', ['activity_id'])
    
    # Activity Bookings
    op.create_table(
        'activity_bookings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('booking_number', sa.String(50), nullable=False, unique=True),
        sa.Column('activity_id', sa.Integer(), sa.ForeignKey('activities.id'), nullable=False),
        sa.Column('slot_id', sa.Integer(), sa.ForeignKey('activity_slots.id'), nullable=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('activity_date', sa.Date(), nullable=False),
        sa.Column('adults', sa.Integer(), default=1),
        sa.Column('children', sa.Integer(), default=0),
        sa.Column('infants', sa.Integer(), default=0),
        sa.Column('participants', JSONB, nullable=True),
        sa.Column('base_amount', sa.Float(), nullable=False),
        sa.Column('discount_amount', sa.Float(), default=0),
        sa.Column('tax_amount', sa.Float(), default=0),
        sa.Column('total_amount', sa.Float(), nullable=False),
        sa.Column('paid_amount', sa.Float(), default=0),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('payment_status', sa.String(20), default='pending'),
        sa.Column('special_requirements', sa.Text(), nullable=True),
        sa.Column('contact_name', sa.String(200), nullable=True),
        sa.Column('contact_email', sa.String(255), nullable=True),
        sa.Column('contact_phone', sa.String(20), nullable=True),
        sa.Column('voucher_code', sa.String(100), nullable=True),
        sa.Column('voucher_url', sa.String(500), nullable=True),
        sa.Column('cancellation_reason', sa.Text(), nullable=True),
        sa.Column('refund_amount', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_act_bkg_status', 'activity_bookings', ['status'])
    op.create_index('idx_act_bkg_date', 'activity_bookings', ['activity_date'])
    op.create_index('idx_act_bkg_user', 'activity_bookings', ['user_id'])
    
    # =========================================================================
    # TRANSFER MODULE TABLES
    # =========================================================================
    
    # Car Types
    op.create_table(
        'car_types',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('slug', sa.String(120), nullable=False, unique=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(50), default='sedan'),
        sa.Column('max_passengers', sa.Integer(), nullable=False),
        sa.Column('max_luggage', sa.Integer(), default=2),
        sa.Column('features', JSONB, nullable=True),
        sa.Column('image_url', sa.String(500), nullable=True),
        sa.Column('base_price', sa.Float(), nullable=False),
        sa.Column('price_per_km', sa.Float(), nullable=False),
        sa.Column('price_per_hour', sa.Float(), nullable=True),
        sa.Column('minimum_km', sa.Integer(), default=0),
        sa.Column('minimum_hours', sa.Integer(), nullable=True),
        sa.Column('night_charge_percentage', sa.Float(), default=0),
        sa.Column('night_start_hour', sa.Integer(), default=22),
        sa.Column('night_end_hour', sa.Integer(), default=6),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('display_order', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_car_type_slug', 'car_types', ['slug'])
    op.create_index('idx_car_type_category', 'car_types', ['category'])
    
    # Transfer Routes
    op.create_table(
        'transfer_routes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(300), nullable=False),
        sa.Column('slug', sa.String(320), nullable=False, unique=True),
        sa.Column('origin_name', sa.String(200), nullable=False),
        sa.Column('origin_city', sa.String(100), nullable=True),
        sa.Column('origin_type', sa.String(50), default='city'),
        sa.Column('origin_coords', JSONB, nullable=True),
        sa.Column('destination_name', sa.String(200), nullable=False),
        sa.Column('destination_city', sa.String(100), nullable=True),
        sa.Column('destination_type', sa.String(50), default='city'),
        sa.Column('destination_coords', JSONB, nullable=True),
        sa.Column('distance_km', sa.Float(), nullable=True),
        sa.Column('duration_minutes', sa.Integer(), nullable=True),
        sa.Column('car_type_id', sa.Integer(), sa.ForeignKey('car_types.id'), nullable=False),
        sa.Column('fixed_price', sa.Float(), nullable=True),
        sa.Column('is_bidirectional', sa.Boolean(), default=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_popular', sa.Boolean(), default=False),
        sa.Column('display_order', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_route_slug', 'transfer_routes', ['slug'])
    op.create_index('idx_route_origin', 'transfer_routes', ['origin_name'])
    op.create_index('idx_route_dest', 'transfer_routes', ['destination_name'])
    
    # Transfer Bookings
    op.create_table(
        'transfer_bookings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('booking_number', sa.String(50), nullable=False, unique=True),
        sa.Column('route_id', sa.Integer(), sa.ForeignKey('transfer_routes.id'), nullable=True),
        sa.Column('car_type_id', sa.Integer(), sa.ForeignKey('car_types.id'), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('pickup_location', sa.String(500), nullable=False),
        sa.Column('pickup_coords', JSONB, nullable=True),
        sa.Column('dropoff_location', sa.String(500), nullable=False),
        sa.Column('dropoff_coords', JSONB, nullable=True),
        sa.Column('pickup_datetime', sa.DateTime(), nullable=False),
        sa.Column('passengers', sa.Integer(), default=1),
        sa.Column('luggage_count', sa.Integer(), default=0),
        sa.Column('is_round_trip', sa.Boolean(), default=False),
        sa.Column('return_datetime', sa.DateTime(), nullable=True),
        sa.Column('distance_km', sa.Float(), nullable=True),
        sa.Column('base_amount', sa.Float(), nullable=False),
        sa.Column('night_charge', sa.Float(), default=0),
        sa.Column('toll_charges', sa.Float(), default=0),
        sa.Column('parking_charges', sa.Float(), default=0),
        sa.Column('gst_amount', sa.Float(), default=0),
        sa.Column('total_amount', sa.Float(), nullable=False),
        sa.Column('paid_amount', sa.Float(), default=0),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('payment_status', sa.String(20), default='pending'),
        sa.Column('special_requests', sa.Text(), nullable=True),
        sa.Column('passenger_name', sa.String(200), nullable=True),
        sa.Column('passenger_phone', sa.String(20), nullable=True),
        sa.Column('passenger_email', sa.String(255), nullable=True),
        sa.Column('flight_number', sa.String(20), nullable=True),
        sa.Column('driver_name', sa.String(200), nullable=True),
        sa.Column('driver_phone', sa.String(20), nullable=True),
        sa.Column('vehicle_number', sa.String(20), nullable=True),
        sa.Column('vehicle_model', sa.String(100), nullable=True),
        sa.Column('driver_assigned_at', sa.DateTime(), nullable=True),
        sa.Column('trip_started_at', sa.DateTime(), nullable=True),
        sa.Column('trip_completed_at', sa.DateTime(), nullable=True),
        sa.Column('cancellation_reason', sa.Text(), nullable=True),
        sa.Column('refund_amount', sa.Float(), nullable=True),
        sa.Column('admin_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_transfer_status', 'transfer_bookings', ['status'])
    op.create_index('idx_transfer_pickup', 'transfer_bookings', ['pickup_datetime'])
    op.create_index('idx_transfer_user', 'transfer_bookings', ['user_id'])
    
    # =========================================================================
    # CMS MODULE TABLES
    # =========================================================================
    
    # Sliders
    op.create_table(
        'cms_sliders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(300), nullable=False),
        sa.Column('subtitle', sa.String(500), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('image_url', sa.String(500), nullable=False),
        sa.Column('mobile_image_url', sa.String(500), nullable=True),
        sa.Column('video_url', sa.String(500), nullable=True),
        sa.Column('link_url', sa.String(500), nullable=True),
        sa.Column('link_text', sa.String(100), nullable=True),
        sa.Column('link_target', sa.String(20), default='_self'),
        sa.Column('placement', sa.String(50), default='homepage'),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('display_order', sa.Integer(), default=0),
        sa.Column('tenant_id', sa.Integer(), sa.ForeignKey('tenants.id'), nullable=True),
        sa.Column('created_by_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_slider_placement', 'cms_sliders', ['placement'])
    op.create_index('idx_slider_status', 'cms_sliders', ['status'])
    
    # Offers
    op.create_table(
        'cms_offers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(300), nullable=False),
        sa.Column('slug', sa.String(320), nullable=False, unique=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('terms_conditions', sa.Text(), nullable=True),
        sa.Column('code', sa.String(50), nullable=True, unique=True),
        sa.Column('discount_type', sa.String(20), default='percentage'),
        sa.Column('discount_value', sa.Float(), default=0),
        sa.Column('max_discount', sa.Float(), nullable=True),
        sa.Column('min_order_value', sa.Float(), default=0),
        sa.Column('usage_limit', sa.Integer(), nullable=True),
        sa.Column('per_user_limit', sa.Integer(), default=1),
        sa.Column('current_usage', sa.Integer(), default=0),
        sa.Column('applicable_to', sa.String(100), nullable=True),
        sa.Column('image_url', sa.String(500), nullable=True),
        sa.Column('banner_url', sa.String(500), nullable=True),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('is_featured', sa.Boolean(), default=False),
        sa.Column('display_order', sa.Integer(), default=0),
        sa.Column('tenant_id', sa.Integer(), sa.ForeignKey('tenants.id'), nullable=True),
        sa.Column('created_by_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_offer_slug', 'cms_offers', ['slug'])
    op.create_index('idx_offer_code', 'cms_offers', ['code'])
    op.create_index('idx_offer_status', 'cms_offers', ['status'])
    
    # Blog Categories
    op.create_table(
        'cms_blog_categories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False, unique=True),
        sa.Column('slug', sa.String(120), nullable=False, unique=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('image_url', sa.String(500), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('display_order', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_blog_cat_slug', 'cms_blog_categories', ['slug'])
    
    # Blog Posts
    op.create_table(
        'cms_blog_posts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('slug', sa.String(520), nullable=False, unique=True),
        sa.Column('excerpt', sa.String(1000), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('category_id', sa.Integer(), sa.ForeignKey('cms_blog_categories.id'), nullable=True),
        sa.Column('featured_image', sa.String(500), nullable=True),
        sa.Column('thumbnail_url', sa.String(500), nullable=True),
        sa.Column('gallery', JSONB, nullable=True),
        sa.Column('tags', JSONB, nullable=True),
        sa.Column('meta_title', sa.String(200), nullable=True),
        sa.Column('meta_description', sa.String(500), nullable=True),
        sa.Column('meta_keywords', sa.String(500), nullable=True),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('is_featured', sa.Boolean(), default=False),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.Column('view_count', sa.Integer(), default=0),
        sa.Column('author_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_blog_slug', 'cms_blog_posts', ['slug'])
    op.create_index('idx_blog_status', 'cms_blog_posts', ['status'])
    op.create_index('idx_blog_category', 'cms_blog_posts', ['category_id'])
    
    # Static Pages
    op.create_table(
        'cms_static_pages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(300), nullable=False),
        sa.Column('slug', sa.String(320), nullable=False, unique=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('page_type', sa.String(50), default='content'),
        sa.Column('banner_image', sa.String(500), nullable=True),
        sa.Column('meta_title', sa.String(200), nullable=True),
        sa.Column('meta_description', sa.String(500), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('show_in_footer', sa.Boolean(), default=False),
        sa.Column('show_in_header', sa.Boolean(), default=False),
        sa.Column('display_order', sa.Integer(), default=0),
        sa.Column('tenant_id', sa.Integer(), sa.ForeignKey('tenants.id'), nullable=True),
        sa.Column('created_by_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_page_slug', 'cms_static_pages', ['slug'])
    op.create_index('idx_page_type', 'cms_static_pages', ['page_type'])
    
    # =========================================================================
    # SETTINGS MODULE TABLES
    # =========================================================================
    
    # Convenience Fees
    op.create_table(
        'convenience_fees',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('service_type', sa.String(50), nullable=False),
        sa.Column('payment_mode', sa.String(20), nullable=False),
        sa.Column('fee_type', sa.String(20), default='percentage'),
        sa.Column('percentage', sa.Float(), default=0),
        sa.Column('fixed_amount', sa.Float(), default=0),
        sa.Column('min_fee', sa.Float(), default=0),
        sa.Column('max_fee', sa.Float(), nullable=True),
        sa.Column('gst_percentage', sa.Float(), default=18.0),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('tenant_id', sa.Integer(), sa.ForeignKey('tenants.id'), nullable=True),
        sa.Column('created_by_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_fee_service_payment', 'convenience_fees', ['service_type', 'payment_mode'])
    
    # Staff Permissions
    op.create_table(
        'staff_permissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(100), nullable=False, unique=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('module', sa.String(50), nullable=False),
        sa.Column('display_order', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_permission_module', 'staff_permissions', ['module'])
    
    # Staff Roles
    op.create_table(
        'staff_roles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False, unique=True),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('permissions', JSONB, nullable=True),
        sa.Column('is_system', sa.Boolean(), default=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('tenant_id', sa.Integer(), sa.ForeignKey('tenants.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_role_tenant', 'staff_roles', ['tenant_id'])
    
    # Staff Members
    op.create_table(
        'staff_members',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False, unique=True),
        sa.Column('employee_id', sa.String(50), nullable=True, unique=True),
        sa.Column('department', sa.String(100), nullable=True),
        sa.Column('designation', sa.String(100), nullable=True),
        sa.Column('role_id', sa.Integer(), sa.ForeignKey('staff_roles.id'), nullable=False),
        sa.Column('additional_permissions', JSONB, nullable=True),
        sa.Column('restricted_permissions', JSONB, nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('can_access_admin', sa.Boolean(), default=True),
        sa.Column('ip_whitelist', JSONB, nullable=True),
        sa.Column('tenant_id', sa.Integer(), sa.ForeignKey('tenants.id'), nullable=True),
        sa.Column('created_by_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('last_login_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_staff_user', 'staff_members', ['user_id'])
    op.create_index('idx_staff_role', 'staff_members', ['role_id'])
    
    # System Settings
    op.create_table(
        'system_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(100), nullable=False),
        sa.Column('value', JSONB, nullable=True),
        sa.Column('value_type', sa.String(20), default='string'),
        sa.Column('category', sa.String(50), default='general'),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('is_public', sa.Boolean(), default=False),
        sa.Column('is_editable', sa.Boolean(), default=True),
        sa.Column('tenant_id', sa.Integer(), sa.ForeignKey('tenants.id'), nullable=True),
        sa.Column('updated_by_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_setting_key_tenant', 'system_settings', ['key', 'tenant_id'], unique=True)
    op.create_index('idx_setting_category', 'system_settings', ['category'])


def downgrade() -> None:
    # Drop Settings tables
    op.drop_table('system_settings')
    op.drop_table('staff_members')
    op.drop_table('staff_roles')
    op.drop_table('staff_permissions')
    op.drop_table('convenience_fees')
    
    # Drop CMS tables
    op.drop_table('cms_static_pages')
    op.drop_table('cms_blog_posts')
    op.drop_table('cms_blog_categories')
    op.drop_table('cms_offers')
    op.drop_table('cms_sliders')
    
    # Drop Transfer tables
    op.drop_table('transfer_bookings')
    op.drop_table('transfer_routes')
    op.drop_table('car_types')
    
    # Drop Activity tables
    op.drop_table('activity_bookings')
    op.drop_table('activity_slots')
    op.drop_table('activities')
    op.drop_table('activity_locations')
    op.drop_table('activity_categories')
    
    # Drop Visa tables
    op.drop_table('visa_applications')
    op.drop_table('visa_requirements')
    op.drop_table('visa_types')
    op.drop_table('visa_countries')
    
    # Drop Holiday tables
    op.drop_table('package_bookings')
    op.drop_table('package_enquiries')
    op.drop_table('package_images')
    op.drop_table('package_inclusions')
    op.drop_table('package_itineraries')
    op.drop_table('holiday_packages')
    op.drop_table('package_destinations')
    op.drop_table('package_themes')
