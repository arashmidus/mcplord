"""
Test Scenario definitions for MCP systems.
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class TestResult:
    """Result of a test execution."""
    
    success: bool
    output: Optional[Any] = None
    error: Optional[str] = None
    cost: float = 0.0
    execution_time: float = 0.0


@dataclass 
class TestScenario:
    """Definition of a test scenario."""
    
    name: str
    description: str
    expected_result: Any
    timeout: float = 30.0 