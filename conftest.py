"""
Main pytest configuration file for Hiker's Voice test suite.
Provides common fixtures and settings for all test types.
"""

import sys
import os
import logging
from math import trunc
from pathlib import Path
import pytest

# Add project roots to Python path
PROJECT_ROOT = Path(__file__).parent.parent
BACKEND_ROOT = PROJECT_ROOT / "backend"
TESTS_ROOT = PROJECT_ROOT / "tests"

sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(BACKEND_ROOT))
sys.path.insert(0, str(TESTS_ROOT))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def backend_url() -> str:
    """Return the backend URL."""
    return os.getenv("BACKEND_URL", "http://localhost:8000")


@pytest.fixture(scope="session")
def frontend_url() -> str:
    """Return the frontend URL."""
    return os.getenv("FRONTEND_URL", "http://localhost:3000")


@pytest.fixture(scope="function", autouse=True)
def log_test_info(request):
    """Log critical test failures only."""
    yield
    # Log only if test failed
    if hasattr(request.node, 'rep_call') and request.node.rep_call.failed:
        logger.error(f"Test failed: {request.node.name}")


def pytest_configure(config):
    """Configure pytest with custom markers."""
    # Register only used markers
    config.addinivalue_line(
        "markers", "critical: mark test as critical for the application"
    )
    config.addinivalue_line(
        "markers", "pages: mark test as end-to-end test"
    )


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--env",
        action="store",
        default="local",
        help="Environment to run tests against (local, staging, prod)"
    )
    parser.addoption(
        "--headless",
        action="store_true",
        default=True,
        help="Run browser tests in headless mode (no GUI)"
    )
    parser.addoption(
        "--slow-mo",
        action="store",
        default="100",
        help="Slow down browser actions by specified milliseconds"
    )


@pytest.fixture(scope="session")
def config_for_tests(request) -> dict:
    """Provide test configuration based on command line options."""
    return {
        "env": request.config.getoption("--env"),
        "headless": request.config.getoption("--headless"),
        "slow_mo": int(request.config.getoption("--slow-mo")),
    }


# Hook for better test reporting
def pytest_runtest_makereport(item, call):
    """Add test outcome to the test node for access in fixtures."""
    if call.when == 'call':
        setattr(item, 'rep_call', call)
