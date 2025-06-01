"""
Example test module demonstrating database testing patterns.

This module shows how to use fixtures for database testing.
"""

import pytest
from sqlalchemy import Column, Integer, String, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database.base import Base


# Example model for testing
class User(Base):
    """Example User model for testing database operations."""

    __tablename__ = "test_users"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.db
async def test_create_user(db_session: AsyncSession):
    """
    Test creating a user in the database.

    This test demonstrates how to use the db_session fixture for database operations.
    """
    # Create a test user
    test_user = User(username="testuser", email="test@example.com")
    db_session.add(test_user)
    await db_session.commit()

    # Query to verify the user was created
    result = await db_session.execute(select(User).where(User.username == "testuser"))
    user = result.scalar_one_or_none()

    # Assertions
    assert user is not None
    assert user.username == "testuser"
    assert user.email == "test@example.com"


@pytest.mark.unit
def test_user_creation_no_db():
    """
    A simple unit test that doesn't need the database.

    This demonstrates how to mark tests that don't require database access.
    """
    # Create a user object without saving to database
    user = User(username="unituser", email="unit@example.com")

    # Simple assertions
    assert user.username == "unituser"
    assert user.email == "unit@example.com"
