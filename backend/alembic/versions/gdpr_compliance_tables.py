"""Add GDPR compliance tables

Revision ID: gdpr_compliance
Revises: f1a2b3c4d5e6
Create Date: 2024-12-XX

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'gdpr_compliance'
down_revision = 'f1a2b3c4d5e6'
branch_labels = None
depends_on = None


def upgrade():
    # DSR Records table
    op.create_table(
        'dsr_records',
        sa.Column('id', sa.String(100), primary_key=True),
        sa.Column('user_id', sa.String(100), sa.ForeignKey('users.id'), nullable=False, index=True),
        sa.Column('request_type', sa.String(50), nullable=False),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deadline_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('identity_verified', sa.Boolean(), default=False),
        sa.Column('identity_verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('verification_method', sa.String(50), nullable=True),
        sa.Column('request_details', postgresql.JSON(), default=dict),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('extension_reason', sa.Text(), nullable=True),
        sa.Column('processing_log', postgresql.JSON(), default=list),
        sa.Column('data_locations_processed', sa.Integer(), default=0),
        sa.Column('third_parties_notified', sa.Integer(), default=0),
        sa.Column('response_data_url', sa.String(500), nullable=True),
        sa.Column('response_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('requester_email', sa.String(255), nullable=True),
        sa.Column('requester_ip', sa.String(45), nullable=True),
        sa.Column('requester_user_agent', sa.Text(), nullable=True),
        sa.Index('ix_dsr_records_user_id', 'user_id'),
        sa.Index('ix_dsr_records_status', 'status'),
        sa.Index('ix_dsr_records_submitted_at', 'submitted_at'),
    )
    
    # DSR Audit Logs table
    op.create_table(
        'dsr_audit_logs',
        sa.Column('id', sa.String(100), primary_key=True),
        sa.Column('dsr_id', sa.String(100), sa.ForeignKey('dsr_records.id'), nullable=False, index=True),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('action_details', postgresql.JSON(), default=dict),
        sa.Column('performed_by', sa.String(100), nullable=True),
        sa.Column('performed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('data_location', sa.String(200), nullable=True),
        sa.Column('records_affected', sa.Integer(), nullable=True),
        sa.Column('gdpr_article', sa.String(10), nullable=True),
        sa.Index('ix_dsr_audit_logs_dsr_id', 'dsr_id'),
        sa.Index('ix_dsr_audit_logs_performed_at', 'performed_at'),
    )
    
    # Data Retention Schedule table
    op.create_table(
        'data_retention_schedules',
        sa.Column('id', sa.String(100), primary_key=True),
        sa.Column('data_category', sa.String(100), nullable=False, unique=True),
        sa.Column('data_types', postgresql.JSON(), default=list),
        sa.Column('retention_days', sa.Integer(), nullable=False),
        sa.Column('retention_basis', sa.String(50), nullable=False),
        sa.Column('legal_basis_details', sa.Text(), nullable=True),
        sa.Column('action_after_retention', sa.String(50), default='delete'),
        sa.Column('auto_apply', sa.Boolean(), default=True),
        sa.Column('last_applied_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    
    # Consent Records table
    op.create_table(
        'consent_records',
        sa.Column('id', sa.String(100), primary_key=True),
        sa.Column('user_id', sa.String(100), sa.ForeignKey('users.id'), nullable=False, index=True),
        sa.Column('essential', sa.Boolean(), default=True),
        sa.Column('analytics', sa.Boolean(), default=False),
        sa.Column('marketing', sa.Boolean(), default=False),
        sa.Column('ai_training', sa.Boolean(), default=False),
        sa.Column('third_party_sharing', sa.Boolean(), default=False),
        sa.Column('consent_version', sa.String(10), default='1.0'),
        sa.Column('consented_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('consent_ip', sa.String(45), nullable=True),
        sa.Column('consent_user_agent', sa.Text(), nullable=True),
        sa.Column('withdrawn_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('withdrawal_reason', sa.Text(), nullable=True),
        sa.Column('analytics_withdrawn_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('marketing_withdrawn_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ai_training_withdrawn_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('third_party_sharing_withdrawn_at', sa.DateTime(timezone=True), nullable=True),
        sa.Index('ix_consent_records_user_id', 'user_id'),
    )
    
    # Data Processing Records (RoPA) table
    op.create_table(
        'data_processing_records',
        sa.Column('id', sa.String(100), primary_key=True),
        sa.Column('activity_id', sa.String(20), nullable=False, unique=True),
        sa.Column('activity_name', sa.String(200), nullable=False),
        sa.Column('activity_description', sa.Text(), nullable=True),
        sa.Column('purposes', postgresql.JSON(), default=list),
        sa.Column('data_categories', postgresql.JSON(), default=list),
        sa.Column('data_subjects', postgresql.JSON(), default=list),
        sa.Column('internal_recipients', postgresql.JSON(), default=list),
        sa.Column('external_recipients', postgresql.JSON(), default=list),
        sa.Column('subprocessors', postgresql.JSON(), default=list),
        sa.Column('legal_basis', sa.String(50), nullable=False),
        sa.Column('legal_basis_details', sa.Text(), nullable=True),
        sa.Column('retention_period_days', sa.Integer(), nullable=True),
        sa.Column('retention_basis', sa.Text(), nullable=True),
        sa.Column('security_measures', postgresql.JSON(), default=list),
        sa.Column('encryption_applied', sa.Boolean(), default=False),
        sa.Column('pseudonymization_applied', sa.Boolean(), default=False),
        sa.Column('involves_transfers', sa.Boolean(), default=False),
        sa.Column('transfer_mechanism', sa.String(50), nullable=True),
        sa.Column('transfer_countries', postgresql.JSON(), default=list),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('reviewed_by', sa.String(100), nullable=True),
        sa.Index('ix_data_processing_records_activity_id', 'activity_id'),
        sa.Index('ix_data_processing_records_is_active', 'is_active'),
    )
    
    # Data Breach Records table
    op.create_table(
        'data_breach_records',
        sa.Column('id', sa.String(100), primary_key=True),
        sa.Column('breach_reference', sa.String(50), nullable=False, unique=True),
        sa.Column('discovered_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('reported_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('nature_of_breach', sa.Text(), nullable=False),
        sa.Column('data_categories', postgresql.JSON(), default=list),
        sa.Column('data_subjects_affected', sa.Integer(), nullable=True),
        sa.Column('approximate_subjects', sa.String(50), nullable=True),
        sa.Column('risk_level', sa.String(20), nullable=False),
        sa.Column('likely_consequences', sa.Text(), nullable=True),
        sa.Column('special_category_data', sa.Boolean(), default=False),
        sa.Column('children_affected', sa.Boolean(), default=False),
        sa.Column('containment_measures', postgresql.JSON(), default=list),
        sa.Column('remediation_actions', postgresql.JSON(), default=list),
        sa.Column('supervisory_notified', sa.Boolean(), default=False),
        sa.Column('supervisory_notified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('supervisory_authority', sa.String(100), nullable=True),
        sa.Column('data_subjects_notified', sa.Boolean(), default=False),
        sa.Column('data_subjects_notified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notification_method', sa.String(50), nullable=True),
        sa.Column('subprocessors_notified', postgresql.JSON(), default=list),
        sa.Column('status', sa.String(50), default='investigating'),
        sa.Column('closed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('dpo_consulted', sa.Boolean(), default=False),
        sa.Column('dpo_recommendations', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Index('ix_data_breach_records_breach_reference', 'breach_reference'),
        sa.Index('ix_data_breach_records_status', 'status'),
        sa.Index('ix_data_breach_records_discovered_at', 'discovered_at'),
    )


def downgrade():
    op.drop_table('data_breach_records')
    op.drop_table('data_processing_records')
    op.drop_table('consent_records')
    op.drop_table('data_retention_schedules')
    op.drop_table('dsr_audit_logs')
    op.drop_table('dsr_records')
