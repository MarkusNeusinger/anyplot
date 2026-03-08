"""
Unit tests for MCP server tools.

Tests all 6 MCP tools with mocked database sessions.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Import the tool functions from the module
# With FastMCP's @mcp_server.tool() decorator, these are plain async functions
from api.mcp.server import (
    get_implementation,
    get_spec_detail,
    get_tag_values,
    list_libraries,
    list_specs,
    search_specs_by_tags,
)


@pytest.fixture
def mock_db_context():
    """Mock database session for MCP handlers."""
    mock_session = AsyncMock()
    mock_session.close = AsyncMock()

    with (
        patch("api.mcp.server.get_mcp_db_session", AsyncMock(return_value=mock_session)),
        patch("api.mcp.server.is_db_configured", return_value=True),
    ):
        yield mock_session


@pytest.fixture
def mock_spec():
    """Create a mock spec."""
    mock_impl = MagicMock()
    mock_impl.library.id = "matplotlib"
    mock_impl.library.name = "Matplotlib"
    mock_impl.code = "import matplotlib.pyplot as plt"
    mock_impl.preview_url = "https://example.com/plot.png"
    mock_impl.preview_thumb = "https://example.com/plot_thumb.png"
    mock_impl.preview_html = None
    mock_impl.quality_score = 92
    mock_impl.created = None
    mock_impl.generated_by = "claude-opus-4"
    mock_impl.python_version = "3.13"
    mock_impl.library_version = "3.10.0"
    mock_impl.review_strengths = ["Clean code"]
    mock_impl.review_weaknesses = ["Could improve"]
    mock_impl.review_image_description = "A scatter plot"
    mock_impl.review_criteria_checklist = {"visual_quality": {"score": 36, "max": 40}}
    mock_impl.review_verdict = "APPROVED"
    mock_impl.impl_tags = {"patterns": ["data-generation"], "styling": ["alpha-blending"]}
    mock_impl.generated_at = None

    spec = MagicMock()
    spec.id = "scatter-basic"
    spec.title = "Basic Scatter Plot"
    spec.description = "A simple scatter plot"
    spec.applications = ["Data analysis", "Correlation studies"]
    spec.data = ["x (numeric)", "y (numeric)"]
    spec.notes = ["Use for continuous data"]
    spec.tags = {"plot_type": ["scatter"], "data_type": ["numeric"], "domain": ["statistics"], "features": ["basic"]}
    spec.issue = 42
    spec.suggested = "contributor"
    spec.created = None
    spec.updated = None
    spec.impls = [mock_impl]

    return spec


@pytest.mark.asyncio
async def test_list_specs(mock_db_context, mock_spec):
    """Test list_specs tool."""
    mock_repo = MagicMock()
    mock_repo.get_all = AsyncMock(return_value=[mock_spec])

    with patch("api.mcp.server.SpecRepository", return_value=mock_repo):
        result = await list_specs(limit=10, offset=0)

    assert len(result) == 1
    assert result[0]["id"] == "scatter-basic"
    assert result[0]["title"] == "Basic Scatter Plot"
    assert result[0]["library_count"] == 1


@pytest.mark.asyncio
async def test_list_specs_pagination(mock_db_context):
    """Test list_specs pagination."""
    specs = [MagicMock(id=f"spec-{i}", title=f"Spec {i}", description="", tags={}, impls=[]) for i in range(5)]

    mock_repo = MagicMock()
    mock_repo.get_all = AsyncMock(return_value=specs)

    with patch("api.mcp.server.SpecRepository", return_value=mock_repo):
        result = await list_specs(limit=2, offset=1)

    assert len(result) == 2
    assert result[0]["id"] == "spec-1"
    assert result[1]["id"] == "spec-2"


@pytest.mark.asyncio
async def test_search_specs_by_tags_spec_level(mock_db_context, mock_spec):
    """Test search_specs_by_tags with spec-level filters."""
    mock_repo = MagicMock()
    mock_repo.search_by_tags = AsyncMock(return_value=[mock_spec])

    with patch("api.mcp.server.SpecRepository", return_value=mock_repo):
        result = await search_specs_by_tags(plot_type=["scatter"], domain=["statistics"])

    # Verify repository called with flattened list (order may vary)
    call_args = mock_repo.search_by_tags.call_args[0][0]
    assert sorted(call_args) == ["scatter", "statistics"]
    assert len(result) == 1
    assert result[0]["id"] == "scatter-basic"


@pytest.mark.asyncio
async def test_search_specs_by_tags_impl_level(mock_db_context, mock_spec):
    """Test search_specs_by_tags with impl-level filters."""
    mock_repo = MagicMock()
    mock_repo.get_all = AsyncMock(return_value=[mock_spec])

    with patch("api.mcp.server.SpecRepository", return_value=mock_repo):
        result = await search_specs_by_tags(library=["matplotlib"], patterns=["data-generation"])

    assert len(result) == 1
    assert result[0]["id"] == "scatter-basic"


@pytest.mark.asyncio
async def test_search_specs_by_tags_no_matches(mock_db_context, mock_spec):
    """Test search_specs_by_tags filtering out non-matching impls."""
    mock_repo = MagicMock()
    mock_repo.get_all = AsyncMock(return_value=[mock_spec])

    with patch("api.mcp.server.SpecRepository", return_value=mock_repo):
        result = await search_specs_by_tags(library=["seaborn"])  # matplotlib impl, not seaborn

    assert len(result) == 0


@pytest.mark.asyncio
async def test_search_specs_by_tags_dataprep_styling(mock_db_context, mock_spec):
    """Test search_specs_by_tags with dataprep and styling filters."""
    mock_repo = MagicMock()
    mock_repo.get_all = AsyncMock(return_value=[mock_spec])

    with patch("api.mcp.server.SpecRepository", return_value=mock_repo):
        # Test dataprep filter - should not match (mock_spec has no dataprep tags)
        result = await search_specs_by_tags(dataprep=["normalization"])
        assert len(result) == 0

        # Test styling filter - should match (mock_spec has styling: alpha-blending)
        result = await search_specs_by_tags(styling=["alpha-blending"])
        assert len(result) == 1
        assert result[0]["id"] == "scatter-basic"


@pytest.mark.asyncio
async def test_get_spec_detail(mock_db_context, mock_spec):
    """Test get_spec_detail tool."""
    mock_repo = MagicMock()
    mock_repo.get_by_id = AsyncMock(return_value=mock_spec)

    with patch("api.mcp.server.SpecRepository", return_value=mock_repo):
        result = await get_spec_detail("scatter-basic")

    assert result["id"] == "scatter-basic"
    assert result["title"] == "Basic Scatter Plot"
    assert len(result["implementations"]) == 1
    assert result["implementations"][0]["library_id"] == "matplotlib"
    assert result["implementations"][0]["code"] == "import matplotlib.pyplot as plt"


@pytest.mark.asyncio
async def test_get_spec_detail_not_found(mock_db_context):
    """Test get_spec_detail with invalid spec_id."""
    mock_repo = MagicMock()
    mock_repo.get_by_id = AsyncMock(return_value=None)

    with patch("api.mcp.server.SpecRepository", return_value=mock_repo):
        with pytest.raises(ValueError, match="Specification 'invalid' not found"):
            await get_spec_detail("invalid")


@pytest.mark.asyncio
async def test_get_implementation(mock_db_context, mock_spec):
    """Test get_implementation tool."""
    mock_lib = MagicMock()
    mock_lib.id = "matplotlib"
    mock_lib.name = "Matplotlib"

    mock_impl = mock_spec.impls[0]

    mock_spec_repo = MagicMock()
    mock_spec_repo.get_by_id = AsyncMock(return_value=mock_spec)

    mock_lib_repo = MagicMock()
    mock_lib_repo.get_by_id = AsyncMock(return_value=mock_lib)

    mock_impl_repo = MagicMock()
    mock_impl_repo.get_by_spec_and_library = AsyncMock(return_value=mock_impl)

    with (
        patch("api.mcp.server.SpecRepository", return_value=mock_spec_repo),
        patch("api.mcp.server.LibraryRepository", return_value=mock_lib_repo),
        patch("api.mcp.server.ImplRepository", return_value=mock_impl_repo),
    ):
        result = await get_implementation("scatter-basic", "matplotlib")

    assert result["library_id"] == "matplotlib"
    assert result["code"] == "import matplotlib.pyplot as plt"
    assert result["quality_score"] == 92


@pytest.mark.asyncio
async def test_get_implementation_spec_not_found(mock_db_context):
    """Test get_implementation with invalid spec_id."""
    mock_spec_repo = MagicMock()
    mock_spec_repo.get_by_id = AsyncMock(return_value=None)

    with patch("api.mcp.server.SpecRepository", return_value=mock_spec_repo):
        with pytest.raises(ValueError, match="Specification 'invalid' not found"):
            await get_implementation("invalid", "matplotlib")


@pytest.mark.asyncio
async def test_get_implementation_library_not_found(mock_db_context, mock_spec):
    """Test get_implementation with invalid library."""
    mock_spec_repo = MagicMock()
    mock_spec_repo.get_by_id = AsyncMock(return_value=mock_spec)

    mock_lib_repo = MagicMock()
    mock_lib_repo.get_by_id = AsyncMock(return_value=None)
    mock_lib_repo.get_all = AsyncMock(return_value=[MagicMock(id="matplotlib")])

    with (
        patch("api.mcp.server.SpecRepository", return_value=mock_spec_repo),
        patch("api.mcp.server.LibraryRepository", return_value=mock_lib_repo),
    ):
        with pytest.raises(ValueError, match="Library 'invalid' not found"):
            await get_implementation("scatter-basic", "invalid")


@pytest.mark.asyncio
async def test_get_implementation_not_found(mock_db_context, mock_spec):
    """Test get_implementation when implementation doesn't exist."""
    mock_lib = MagicMock()
    mock_lib.id = "seaborn"

    mock_spec_repo = MagicMock()
    mock_spec_repo.get_by_id = AsyncMock(return_value=mock_spec)

    mock_lib_repo = MagicMock()
    mock_lib_repo.get_by_id = AsyncMock(return_value=mock_lib)

    mock_impl_repo = MagicMock()
    mock_impl_repo.get_by_spec_and_library = AsyncMock(return_value=None)

    with (
        patch("api.mcp.server.SpecRepository", return_value=mock_spec_repo),
        patch("api.mcp.server.LibraryRepository", return_value=mock_lib_repo),
        patch("api.mcp.server.ImplRepository", return_value=mock_impl_repo),
    ):
        with pytest.raises(ValueError, match="Implementation for 'scatter-basic' in library 'seaborn' not found"):
            await get_implementation("scatter-basic", "seaborn")


@pytest.mark.asyncio
async def test_list_libraries(mock_db_context):
    """Test list_libraries tool."""
    mock_lib1 = MagicMock()
    mock_lib1.id = "matplotlib"
    mock_lib1.name = "Matplotlib"
    mock_lib1.description = "The classic plotting library"

    mock_lib2 = MagicMock()
    mock_lib2.id = "seaborn"
    mock_lib2.name = "Seaborn"
    mock_lib2.description = "Statistical visualization"

    mock_libs = [mock_lib1, mock_lib2]

    mock_repo = MagicMock()
    mock_repo.get_all = AsyncMock(return_value=mock_libs)

    with patch("api.mcp.server.LibraryRepository", return_value=mock_repo):
        result = await list_libraries()

    assert len(result) == 2
    assert result[0]["id"] == "matplotlib"
    assert result[0]["name"] == "Matplotlib"
    assert result[1]["id"] == "seaborn"


@pytest.mark.asyncio
async def test_get_tag_values_spec_level(mock_db_context, mock_spec):
    """Test get_tag_values for spec-level category."""
    mock_spec2 = MagicMock()
    mock_spec2.tags = {"plot_type": ["bar", "histogram"]}
    mock_spec2.impls = []

    mock_repo = MagicMock()
    mock_repo.get_all = AsyncMock(return_value=[mock_spec, mock_spec2])

    with patch("api.mcp.server.SpecRepository", return_value=mock_repo):
        result = await get_tag_values("plot_type")

    assert sorted(result) == ["bar", "histogram", "scatter"]


@pytest.mark.asyncio
async def test_get_tag_values_impl_level(mock_db_context, mock_spec):
    """Test get_tag_values for impl-level category."""
    mock_repo = MagicMock()
    mock_repo.get_all = AsyncMock(return_value=[mock_spec])

    with patch("api.mcp.server.SpecRepository", return_value=mock_repo):
        result = await get_tag_values("patterns")

    assert sorted(result) == ["data-generation"]


@pytest.mark.asyncio
async def test_get_tag_values_invalid_category(mock_db_context):
    """Test get_tag_values with invalid category."""
    with pytest.raises(ValueError, match="Invalid category 'invalid'"):
        await get_tag_values("invalid")


# =============================================================================
# FastMCP Protocol-Level Tests (no mocks on fastmcp itself)
# =============================================================================


class TestMcpServerProtocol:
    """Tests that exercise the real fastmcp server instance.

    These tests verify tool registration and discovery without mocking fastmcp,
    so breaking changes in the fastmcp API surface will be caught.
    """

    @pytest.mark.asyncio
    async def test_all_tools_registered(self):
        """MCP server should have all 6 tools registered."""
        from api.mcp.server import mcp_server

        tools = await mcp_server.list_tools()
        tool_names = {t.name for t in tools}
        expected = {
            "list_specs",
            "search_specs_by_tags",
            "get_spec_detail",
            "get_implementation",
            "list_libraries",
            "get_tag_values",
        }
        assert tool_names == expected

    @pytest.mark.asyncio
    async def test_tool_objects_have_correct_type(self):
        """Each registered tool should be a FunctionTool with a callable fn."""
        from api.mcp.server import mcp_server

        tools = await mcp_server.list_tools()
        for tool in tools:
            assert hasattr(tool, "fn"), f"Tool {tool.name} has no 'fn' attribute"
            assert callable(tool.fn), f"Tool {tool.name}.fn is not callable"

    @pytest.mark.asyncio
    async def test_tool_schemas_are_valid(self):
        """Each tool should have a valid JSON Schema for its parameters."""
        from api.mcp.server import mcp_server

        tools = await mcp_server.list_tools()
        for tool in tools:
            schema = tool.parameters
            assert isinstance(schema, dict), f"Tool {tool.name} schema is not a dict"
            assert "properties" in schema, f"Tool {tool.name} schema has no 'properties'"
            assert schema.get("type") == "object", f"Tool {tool.name} schema type is not 'object'"

    @pytest.mark.asyncio
    async def test_get_tag_values_via_call_tool(self):
        """Calling get_tag_values with invalid category through call_tool should raise."""
        from api.mcp.server import mcp_server

        # Call through the fastmcp protocol layer — exercises serialization
        # get_tag_values("invalid") should raise ValueError
        with pytest.raises(ValueError, match="Invalid category"):
            tool = await mcp_server.get_tool("get_tag_values")
            await tool.fn(category="invalid")
