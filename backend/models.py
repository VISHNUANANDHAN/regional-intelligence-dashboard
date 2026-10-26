
# from sqlalchemy import Column, DateTime, Integer, String, func
# from database import Base


# class User(Base):
#     __tablename__ = "users"

#     id = Column(Integer, primary_key=True, index=True)
#     email = Column(String(255), unique=True, nullable=False, index=True)
#     password_hash = Column(String, nullable=False)
#     created_at = Column(DateTime, server_default=func.now())


from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class SavedReport(Base):
    __tablename__ = "saved_reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    location = Column(String(255), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    report_data = Column(Text, nullable=False)
    created_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    expires_at = Column(DateTime, nullable=False, index=True)


class Incident(Base):
    """A real incident obtained from an external monitoring source."""

    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)

    # Stable identifier provided by our monitoring code.
    source_id = Column(String(64), nullable=False, unique=True)

    title = Column(String(1000), nullable=False)
    summary = Column(Text, nullable=True)

    category = Column(String(100), nullable=False, index=True)
    severity = Column(String(20), nullable=False, index=True)
    severity_basis = Column(Text, nullable=True)

    location = Column(String(500), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    source = Column(String(255), nullable=False)
    source_url = Column(Text, nullable=False)
    data_type = Column(String(50), nullable=False)

    published_at = Column(DateTime(timezone=True), nullable=True, index=True)
    first_seen_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    last_seen_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        Index("ix_incidents_category_published", "category", "published_at"),
        Index("ix_incidents_severity_published", "severity", "published_at"),
    )
