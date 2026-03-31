from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func, Boolean
from sqlalchemy.orm import relationship
from .base import Base

class UserTokenTable(Base):
    """
    Sovereign Token Storage for External Integrations.
    Stores encrypted OAuth2 tokens for Google, Microsoft, and Zoom.
    """
    __tablename__ = "user_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    provider = Column(String(50), nullable=False, index=True)  # google, microsoft, zoom
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text)
    expires_at = Column(DateTime(timezone=True))
    scopes = Column(Text)  # JSON-string of granted scopes
    
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Sync Positioning
    sync_token = Column(Text) # google nextSyncToken or MS odata.deltaLink
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationship back to the user
    user = relationship("UserTable", backref="tokens")
