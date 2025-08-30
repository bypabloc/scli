#!/usr/bin/env python3
"""
Test runner for SCLI project

Executes all integration and e2e tests without unit tests.
Custom test runner that follows the project's testing philosophy.
"""

import subprocess
import sys
import argparse
from pathlib import Path
from typing import List, Optional

# Configure logger for testing environment
try:
    from src.utils.logger import info, error, success, warning, configure_for_testing
    configure_for_testing()
except ImportError:
    # Fallback if logger not available
    def info(msg, detail=None): print(f"INFO: {msg}")
    def error(msg, detail=None): print(f"ERROR: {msg}")
    def success(msg, detail=None): print(f"SUCCESS: {msg}")
    def warning(msg, detail=None): print(f"WARNING: {msg}")

# Make logger functions global
globals().update({
    'info': info,
    'error': error, 
    'success': success,
    'warning': warning
})


def run_command(cmd: List[str], description: str) -> bool:
    """
    Execute a command and return success status.
    
    Args:
        cmd: Command to execute as list of strings
        description: Description of what the command does
        
    Returns:
        True if command succeeded, False otherwise
    """
    info("🔄 Processing task", detail={"description": description})
    info("Executing command", detail={"command": ' '.join(cmd)})
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        success("Task completed successfully", detail={"description": description})
        return True
    except subprocess.CalledProcessError as e:
        error("Task failed", detail={"description": description, "exit_code": e.returncode})
        return False
    except Exception as e:
        error("Task error", detail={"description": description, "error": str(e)})
        return False


def get_test_files() -> List[str]:
    """Get all test files from integration and e2e directories."""
    integration_files = list(Path("tests/integration").glob("*.py"))
    e2e_files = list(Path("tests/e2e").glob("*.py")) 
    
    # Filter out __init__.py files
    test_files = [str(f) for f in integration_files + e2e_files 
                  if f.name != "__init__.py"]
    
    return test_files


def run_integration_tests() -> bool:
    """Run all integration tests."""
    integration_files = [str(f) for f in Path("tests/integration").glob("*.py") 
                        if f.name != "__init__.py"]
    
    if not integration_files:
        error("No integration test files found!")
        return False
        
    cmd = ["uv", "run", "pytest"] + integration_files + ["-v"]
    return run_command(cmd, "Running Integration Tests")


def run_e2e_tests() -> bool:
    """Run all e2e tests."""
    e2e_files = [str(f) for f in Path("tests/e2e").glob("*.py") 
                 if f.name != "__init__.py"]
    
    if not e2e_files:
        error("No e2e test files found!")
        return False
        
    cmd = ["uv", "run", "pytest"] + e2e_files + ["-v"]
    return run_command(cmd, "Running E2E Tests")


def run_all_tests() -> bool:
    """Run all tests (integration + e2e)."""
    test_files = get_test_files()
    
    if not test_files:
        error("No test files found!")
        return False
        
    cmd = ["uv", "run", "pytest"] + test_files + ["-v"]
    return run_command(cmd, "Running All Tests (Integration + E2E)")


def run_fast_tests() -> bool:
    """Run only fast tests (excluding slow ones)."""
    test_files = get_test_files()
    
    if not test_files:
        error("No test files found!")
        return False
        
    cmd = ["uv", "run", "pytest"] + test_files + ["-v", "-m", "not slow"]
    return run_command(cmd, "Running Fast Tests")


def run_with_coverage() -> bool:
    """Run all tests with coverage report."""
    test_files = get_test_files()
    
    if not test_files:
        error("No test files found!")
        return False
        
    cmd = ["uv", "run", "pytest"] + test_files + ["--cov=src", "--cov-report=html", "--cov-report=term"]
    return run_command(cmd, "Running Tests with Coverage")


def main():
    """Main test runner entry point."""
    parser = argparse.ArgumentParser(
        description="SCLI Test Runner - Integration + E2E tests only",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tests/run.py                    # Run all tests
  python tests/run.py --integration     # Integration tests only
  python tests/run.py --e2e             # E2E tests only  
  python tests/run.py --fast            # Exclude slow tests
  python tests/run.py --coverage        # Run with coverage
        """
    )
    
    parser.add_argument(
        "--integration", 
        action="store_true",
        help="Run only integration tests"
    )
    
    parser.add_argument(
        "--e2e",
        action="store_true", 
        help="Run only e2e tests"
    )
    
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Run only fast tests (exclude slow ones)"
    )
    
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Run tests with coverage report"
    )
    
    args = parser.parse_args()
    
    success("🚀 SCLI Test Runner")
    info("=" * 50)
    info("Testing Philosophy: Integration + E2E (NO Unit Tests)")
    info("No mocks, no isolated function tests - only real behavior")
    info("=" * 50)
    
    # Verify we're in the right directory
    if not Path("tests").exists():
        error("Must run from project root directory")
        error("Current directory should contain 'tests/' folder")
        return 1
        
    success = True
    
    if args.integration:
        success = run_integration_tests()
    elif args.e2e:
        success = run_e2e_tests()
    elif args.fast:
        success = run_fast_tests()
    elif args.coverage:
        success = run_with_coverage()
    else:
        # Run all tests by default
        success = run_all_tests()
    
    info("\n" + "=" * 50)
    if success:
        success("🎉 All tests completed successfully!")
        success("Integration tests: Components working together")
        success("E2E tests: Complete user workflows") 
        return 0
    else:
        error("💥 Some tests failed!")
        error("Check the output above for details")
        return 1


if __name__ == "__main__":
    sys.exit(main())