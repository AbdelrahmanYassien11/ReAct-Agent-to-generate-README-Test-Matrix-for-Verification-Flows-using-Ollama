# tools.py
import sys
import os

# Adding the path of the directory containing 'tools.py' to sys.path
sys.path.append(os.path.abspath("/agent_tools"))

from .parse_spec_tool import parse_spec_tool
from .extract_test_requirements_tool import extract_test_requirements_tool
from .generate_test_scenarios_tool import generate_test_scenarios_tool
from .format_and_write_tool import format_and_write_tool


def reset_state():
    pass  # No state needed in linear pipeline


# ============================================================================
# TOOL REGISTRY
# ============================================================================
TOOL_REGISTRY = {
    "parse_spec": parse_spec_tool,
    "extract_test_requirements": extract_test_requirements_tool,
    "generate_test_scenarios": generate_test_scenarios_tool,
    "format_and_write": format_and_write_tool,
}
