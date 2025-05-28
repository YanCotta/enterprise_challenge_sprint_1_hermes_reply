"""
Database configuration and base models for Smart Maintenance SaaS.

This module defines the SQLAlchemy base class and core database components.
"""

from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase


class Base(AsyncAttrs, DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass
