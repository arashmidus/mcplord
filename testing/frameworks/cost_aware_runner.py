"""
Cost-Aware Testing Framework for MCP Systems

This module implements a testing framework specifically designed for MCP-powered 
multi-agent systems that addresses the unique challenges of testing probabilistic,
cost-incurring systems.

Key features:
- Budget management and cost tracking
- Statistical success rate measurement
- Semantic validation with LLMs
- Layered testing (tool vs toolbox)
- Test prioritization and sampling
"""

import asyncio
import json
import logging
import statistics
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from pathlib import Path

import pandas as pd
from pydantic import BaseModel

from testing.frameworks.semantic_validator import SemanticValidator
from testing.frameworks.test_scenario import TestScenario, TestResult
from monitoring.metrics.testing_metrics import TestingMetrics


@dataclass
class TestConfig:
    """Configuration for a test case."""
    
    name: str
    description: str
    test_function: Callable
    category: str = "general"  # unit, component, system
    priority: int = 1  # 1=highest, 5=lowest
    estimated_cost: float = 0.1  # USD estimate
    min_success_rate: float = 0.8  # Required success rate
    sample_size: int = 10  # Number of runs for statistical testing
    timeout: float = 30.0  # Timeout per test run
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)


@dataclass
class TestRun:
    """Result of a single test execution."""
    
    test_name: str
    success: bool
    execution_time: float
    cost: float
    error: Optional[str] = None
    output: Optional[Any] = None
    timestamp: float = field(default_factory=time.time)


@dataclass
class TestSummary:
    """Summary of test execution results."""
    
    test_name: str
    total_runs: int
    successful_runs: int
    failed_runs: int
    success_rate: float
    average_execution_time: float
    total_cost: float
    min_required_rate: float
    passed_threshold: bool
    errors: List[str] = field(default_factory=list)


class CostAwareTestRunner:
    """
    Cost-aware test runner that manages budgets and measures statistical success rates.
    
    This runner addresses the unique challenges of testing MCP systems:
    - Non-deterministic behavior requiring statistical measurement
    - Real costs associated with LLM calls and API usage
    - Need for semantic validation rather than exact matching
    - Interdependent tools requiring careful test ordering
    """
    
    def __init__(
        self,
        budget_limit: float = 100.0,
        default_sample_size: int = 10,
        enable_semantic_validation: bool = True,
        results_dir: str = "test_results"
    ):
        self.budget_limit = budget_limit
        self.current_spend = 0.0
        self.default_sample_size = default_sample_size
        self.enable_semantic_validation = enable_semantic_validation
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(exist_ok=True)
        
        # Initialize components
        self.semantic_validator = SemanticValidator() if enable_semantic_validation else None
        self.metrics = TestingMetrics()
        self.logger = logging.getLogger("testing.cost_aware_runner")
        
        # Test registry and state
        self.test_registry: Dict[str, TestConfig] = {}
        self.test_results: List[TestRun] = []
        self.test_summaries: Dict[str, TestSummary] = {}
        
        # Runtime state
        self.is_running = False
        self.stop_requested = False
    
    def register_test(self, config: TestConfig) -> None:
        """Register a test case."""
        self.test_registry[config.name] = config
        self.logger.info(f"Registered test: {config.name} (priority={config.priority}, estimated_cost=${config.estimated_cost:.2f})")
    
    def register_tests_from_module(self, module) -> None:
        """Auto-register tests from a module."""
        for attr_name in dir(module):
            if attr_name.startswith("test_"):
                test_func = getattr(module, attr_name)
                if callable(test_func):
                    # Extract test metadata from function
                    config = self._extract_test_config(attr_name, test_func)
                    self.register_test(config)
    
    def _extract_test_config(self, func_name: str, func: Callable) -> TestConfig:
        """Extract test configuration from function metadata."""
        # Get metadata from function docstring or attributes
        doc = func.__doc__ or ""
        
        # Parse basic config from docstring
        config = TestConfig(
            name=func_name,
            description=doc.split('\n')[0] if doc else func_name,
            test_function=func,
            estimated_cost=getattr(func, 'estimated_cost', 0.1),
            min_success_rate=getattr(func, 'min_success_rate', 0.8),
            sample_size=getattr(func, 'sample_size', self.default_sample_size),
            category=getattr(func, 'category', 'component'),
            priority=getattr(func, 'priority', 3),
            tags=getattr(func, 'tags', [])
        )
        
        return config
    
    async def run_all_tests(
        self,
        categories: Optional[List[str]] = None,
        priorities: Optional[List[int]] = None,
        tags: Optional[List[str]] = None,
        stop_on_budget: bool = True
    ) -> Dict[str, TestSummary]:
        """
        Run all registered tests with budget and priority management.
        
        Args:
            categories: Test categories to include
            priorities: Priority levels to include
            tags: Tags to filter by
            stop_on_budget: Stop if budget is exceeded
            
        Returns:
            Dictionary of test summaries
        """
        self.logger.info(f"Starting test run with budget ${self.budget_limit:.2f}")
        self.is_running = True
        self.stop_requested = False
        
        try:
            # Filter and prioritize tests
            selected_tests = self._select_and_prioritize_tests(categories, priorities, tags)
            
            if not selected_tests:
                self.logger.warning("No tests selected for execution")
                return {}
            
            self.logger.info(f"Selected {len(selected_tests)} tests for execution")
            
            # Execute tests in priority order
            for config in selected_tests:
                if self.stop_requested:
                    self.logger.info("Test execution stopped by request")
                    break
                
                # Check budget before running test
                if stop_on_budget and self.current_spend + config.estimated_cost > self.budget_limit:
                    self.logger.warning(f"Skipping {config.name}: would exceed budget")
                    continue
                
                self.logger.info(f"Running test: {config.name}")
                summary = await self._run_single_test(config)
                self.test_summaries[config.name] = summary
                
                # Update spend tracking
                self.current_spend += summary.total_cost
                
                self.logger.info(
                    f"Test {config.name} completed: "
                    f"success_rate={summary.success_rate:.2%}, "
                    f"cost=${summary.total_cost:.2f}, "
                    f"total_spend=${self.current_spend:.2f}"
                )
            
            # Generate final report
            await self._generate_test_report()
            
            return self.test_summaries
            
        finally:
            self.is_running = False
    
    async def run_test_by_name(self, test_name: str) -> TestSummary:
        """Run a single test by name."""
        if test_name not in self.test_registry:
            raise ValueError(f"Test '{test_name}' not found in registry")
        
        config = self.test_registry[test_name]
        return await self._run_single_test(config)
    
    async def _run_single_test(self, config: TestConfig) -> TestSummary:
        """Run a single test with statistical sampling."""
        test_runs = []
        total_cost = 0.0
        errors = []
        
        start_time = time.time()
        
        for run_number in range(config.sample_size):
            if self.stop_requested:
                break
            
            try:
                run_start = time.time()
                
                # Execute the test function
                result = await self._execute_test_function(config)
                
                run_time = time.time() - run_start
                success = self._evaluate_test_result(result, config)
                cost = self._calculate_test_cost(result, config)
                
                test_run = TestRun(
                    test_name=config.name,
                    success=success,
                    execution_time=run_time,
                    cost=cost,
                    output=result,
                    timestamp=run_start
                )
                
                test_runs.append(test_run)
                total_cost += cost
                self.test_results.append(test_run)
                
                # Log progress
                if (run_number + 1) % max(1, config.sample_size // 4) == 0:
                    current_success_rate = sum(1 for r in test_runs if r.success) / len(test_runs)
                    self.logger.debug(
                        f"{config.name}: {run_number + 1}/{config.sample_size} "
                        f"runs, success_rate={current_success_rate:.2%}"
                    )
                
            except Exception as e:
                error_msg = str(e)
                errors.append(error_msg)
                
                test_run = TestRun(
                    test_name=config.name,
                    success=False,
                    execution_time=time.time() - run_start,
                    cost=0.0,
                    error=error_msg
                )
                
                test_runs.append(test_run)
                self.test_results.append(test_run)
                
                self.logger.warning(f"Test run failed: {config.name} - {error_msg}")
        
        # Calculate summary statistics
        successful_runs = sum(1 for run in test_runs if run.success)
        success_rate = successful_runs / len(test_runs) if test_runs else 0.0
        avg_time = statistics.mean([run.execution_time for run in test_runs]) if test_runs else 0.0
        
        summary = TestSummary(
            test_name=config.name,
            total_runs=len(test_runs),
            successful_runs=successful_runs,
            failed_runs=len(test_runs) - successful_runs,
            success_rate=success_rate,
            average_execution_time=avg_time,
            total_cost=total_cost,
            min_required_rate=config.min_success_rate,
            passed_threshold=success_rate >= config.min_success_rate,
            errors=list(set(errors))  # Unique errors
        )
        
        # Record metrics
        self.metrics.record_test_summary(summary)
        
        return summary
    
    async def _execute_test_function(self, config: TestConfig) -> Any:
        """Execute a test function with timeout handling."""
        try:
            if asyncio.iscoroutinefunction(config.test_function):
                result = await asyncio.wait_for(
                    config.test_function(),
                    timeout=config.timeout
                )
            else:
                # Run sync function in thread pool
                result = await asyncio.get_event_loop().run_in_executor(
                    None, config.test_function
                )
            return result
        except asyncio.TimeoutError:
            raise RuntimeError(f"Test timed out after {config.timeout} seconds")
    
    def _evaluate_test_result(self, result: Any, config: TestConfig) -> bool:
        """Evaluate if a test result indicates success."""
        # If result is a boolean, use it directly
        if isinstance(result, bool):
            return result
        
        # If result is a dict with 'success' key
        if isinstance(result, dict) and 'success' in result:
            return bool(result['success'])
        
        # If result is a TestResult object
        if hasattr(result, 'success'):
            return bool(result.success)
        
        # For other types, assume success if no exception was raised
        return result is not None
    
    def _calculate_test_cost(self, result: Any, config: TestConfig) -> float:
        """Calculate the cost of a test execution."""
        # If result contains cost information
        if isinstance(result, dict) and 'cost' in result:
            return float(result['cost'])
        
        if hasattr(result, 'cost'):
            return float(result.cost)
        
        # Use estimated cost as fallback
        return config.estimated_cost
    
    def _select_and_prioritize_tests(
        self,
        categories: Optional[List[str]] = None,
        priorities: Optional[List[int]] = None,
        tags: Optional[List[str]] = None
    ) -> List[TestConfig]:
        """Select and prioritize tests based on filters."""
        selected_tests = []
        
        for config in self.test_registry.values():
            # Apply filters
            if categories and config.category not in categories:
                continue
            
            if priorities and config.priority not in priorities:
                continue
            
            if tags and not any(tag in config.tags for tag in tags):
                continue
            
            selected_tests.append(config)
        
        # Sort by priority (lower number = higher priority)
        selected_tests.sort(key=lambda x: (x.priority, x.estimated_cost))
        
        return selected_tests
    
    async def _generate_test_report(self) -> None:
        """Generate comprehensive test report."""
        report_data = {
            'summary': {
                'total_tests': len(self.test_summaries),
                'passed_tests': sum(1 for s in self.test_summaries.values() if s.passed_threshold),
                'failed_tests': sum(1 for s in self.test_summaries.values() if not s.passed_threshold),
                'total_cost': self.current_spend,
                'budget_limit': self.budget_limit,
                'budget_utilization': self.current_spend / self.budget_limit,
            },
            'test_results': []
        }
        
        for summary in self.test_summaries.values():
            report_data['test_results'].append({
                'test_name': summary.test_name,
                'success_rate': summary.success_rate,
                'passed_threshold': summary.passed_threshold,
                'total_runs': summary.total_runs,
                'average_execution_time': summary.average_execution_time,
                'total_cost': summary.total_cost,
                'errors': summary.errors
            })
        
        # Save JSON report
        report_file = self.results_dir / f"test_report_{int(time.time())}.json"
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        # Save CSV for analysis
        if self.test_results:
            df = pd.DataFrame([
                {
                    'test_name': run.test_name,
                    'success': run.success,
                    'execution_time': run.execution_time,
                    'cost': run.cost,
                    'timestamp': run.timestamp,
                    'error': run.error or ''
                }
                for run in self.test_results
            ])
            
            csv_file = self.results_dir / f"test_data_{int(time.time())}.csv"
            df.to_csv(csv_file, index=False)
        
        self.logger.info(f"Test report saved to {report_file}")
    
    def get_budget_status(self) -> Dict[str, float]:
        """Get current budget status."""
        return {
            'budget_limit': self.budget_limit,
            'current_spend': self.current_spend,
            'remaining_budget': self.budget_limit - self.current_spend,
            'utilization_percentage': (self.current_spend / self.budget_limit) * 100
        }
    
    def get_test_statistics(self) -> Dict[str, Any]:
        """Get overall test statistics."""
        if not self.test_summaries:
            return {}
        
        success_rates = [s.success_rate for s in self.test_summaries.values()]
        costs = [s.total_cost for s in self.test_summaries.values()]
        times = [s.average_execution_time for s in self.test_summaries.values()]
        
        return {
            'total_tests': len(self.test_summaries),
            'average_success_rate': statistics.mean(success_rates),
            'median_success_rate': statistics.median(success_rates),
            'total_cost': sum(costs),
            'average_cost_per_test': statistics.mean(costs),
            'average_execution_time': statistics.mean(times),
            'tests_passed_threshold': sum(1 for s in self.test_summaries.values() if s.passed_threshold)
        }
    
    def stop_execution(self) -> None:
        """Request to stop test execution."""
        self.stop_requested = True
        self.logger.info("Test execution stop requested")


# Decorator for marking test functions with metadata
def mcp_test(
    estimated_cost: float = 0.1,
    min_success_rate: float = 0.8,
    sample_size: int = 10,
    category: str = "component",
    priority: int = 3,
    tags: Optional[List[str]] = None
):
    """
    Decorator for marking MCP test functions with metadata.
    
    Example:
        @mcp_test(estimated_cost=0.5, min_success_rate=0.9, category="system")
        async def test_agent_workflow():
            # Test implementation
            pass
    """
    def decorator(func):
        func.estimated_cost = estimated_cost
        func.min_success_rate = min_success_rate
        func.sample_size = sample_size
        func.category = category
        func.priority = priority
        func.tags = tags or []
        return func
    return decorator 