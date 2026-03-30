"""
Pytest configuration and fixtures for pyplots tests.
"""

import matplotlib
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from core.database.models import Base


matplotlib.use("Agg")  # Non-interactive backend for CI


# Test constants
TEST_IMAGE_URL = "https://example.com/plot.png"
TEST_HTML_URL = "https://example.com/plot.html"


@pytest.fixture
def sample_data():
    """Provide sample data for plot tests."""
    import numpy as np
    import pandas as pd

    np.random.seed(42)
    return pd.DataFrame(
        {
            "x": np.random.randn(50),
            "y": np.random.randn(50),
            "category": np.random.choice(["A", "B", "C"], 50),
            "size": np.random.uniform(10, 100, 50),
        }
    )


@pytest.fixture
def temp_output_dir(tmp_path):
    """Provide a temporary directory for plot outputs."""
    output_dir = tmp_path / "plot_outputs"
    output_dir.mkdir()
    return output_dir


# ===== Integration Test Fixtures =====


@pytest.fixture
async def test_engine():
    """Create an in-memory SQLite async engine for testing."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Cleanup
    await engine.dispose()


@pytest.fixture
async def test_session(test_engine):
    """Create a test database session."""
    async_session = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        yield session


@pytest.fixture
async def test_db_with_data(test_session):
    """Create a test database with sample data."""
    from core.database.models import Impl, Library, Spec

    # Create libraries
    matplotlib_lib = Library(
        id="matplotlib",
        name="Matplotlib",
        version="3.10.0",
        documentation_url="https://matplotlib.org",
        description="Comprehensive library for visualizations",
    )
    seaborn_lib = Library(
        id="seaborn",
        name="Seaborn",
        version="0.13.0",
        documentation_url="https://seaborn.pydata.org",
        description="Statistical data visualization",
    )
    test_session.add_all([matplotlib_lib, seaborn_lib])

    # Create specs
    scatter_spec = Spec(
        id="scatter-basic",
        title="Basic Scatter Plot",
        description="A basic scatter plot",
        applications=["data visualization", "correlation analysis"],
        data=["numeric"],
        notes=["Use for 2D data"],
        tags={"plot_type": ["scatter"], "domain": ["statistics"], "data_type": ["numeric"], "features": ["basic"]},
        issue=42,
        suggested="contributor",
    )
    bar_spec = Spec(
        id="bar-grouped",
        title="Grouped Bar Chart",
        description="A grouped bar chart",
        applications=["comparisons"],
        data=["categorical", "numeric"],
        notes=["Good for comparing categories"],
        tags={"plot_type": ["bar"], "domain": ["statistics"], "data_type": ["categorical"], "features": ["grouped"]},
        issue=43,
        suggested="contributor2",
    )
    test_session.add_all([scatter_spec, bar_spec])
    await test_session.commit()

    # Create implementations
    scatter_matplotlib = Impl(
        spec_id="scatter-basic",
        library_id="matplotlib",
        code="import matplotlib.pyplot as plt\n# scatter plot code",
        preview_url=TEST_IMAGE_URL.replace("plot", "scatter-matplotlib"),
        quality_score=92.5,
        generated_by="claude",
        python_version="3.13",
        library_version="3.10.0",
    )
    scatter_seaborn = Impl(
        spec_id="scatter-basic",
        library_id="seaborn",
        code="import seaborn as sns\n# scatter plot code",
        preview_url=TEST_IMAGE_URL.replace("plot", "scatter-seaborn"),
        quality_score=95.0,
        generated_by="claude",
        python_version="3.13",
        library_version="0.13.0",
    )
    bar_matplotlib = Impl(
        spec_id="bar-grouped",
        library_id="matplotlib",
        code="import matplotlib.pyplot as plt\n# bar chart code",
        preview_url=TEST_IMAGE_URL.replace("plot", "bar-matplotlib"),
        quality_score=88.0,
        generated_by="claude",
        python_version="3.13",
        library_version="3.10.0",
    )
    test_session.add_all([scatter_matplotlib, scatter_seaborn, bar_matplotlib])
    await test_session.commit()

    # Expire all cached objects to ensure fresh loading with relationships
    test_session.expire_all()

    yield test_session
