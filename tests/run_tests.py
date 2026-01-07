#!/usr/bin/env python3
"""
Test runner for the FLEET vehicle management system
Runs all test suites with proper reporting and coverage
"""
import sys
import os
import subprocess
import argparse
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERROR: {description} failed with exit code {e.returncode}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False
    except FileNotFoundError:
        print(f"ERROR: Command not found. Make sure pytest is installed.")
        return False

def install_dependencies():
    """Install test dependencies"""
    print("Installing test dependencies...")
    requirements_file = Path(__file__).parent / "requirements.txt"
    
    if requirements_file.exists():
        cmd = [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)]
        return run_command(cmd, "Installing test dependencies")
    else:
        print("No requirements.txt found, skipping dependency installation")
        return True

def run_unit_tests(verbose=False):
    """Run unit tests"""
    cmd = [sys.executable, "-m", "pytest", "unit/", "-v" if verbose else "-q"]
    return run_command(cmd, "Unit Tests")

def run_property_tests(verbose=False):
    """Run property-based tests"""
    cmd = [sys.executable, "-m", "pytest", "property/", "-v" if verbose else "-q"]
    if verbose:
        cmd.extend(["--hypothesis-show-statistics"])
    return run_command(cmd, "Property-Based Tests")

def run_integration_tests(verbose=False):
    """Run integration tests"""
    cmd = [sys.executable, "-m", "pytest", "integration/", "-v" if verbose else "-q"]
    return run_command(cmd, "Integration Tests")

def run_all_tests_with_coverage(verbose=False):
    """Run all tests with coverage reporting"""
    cmd = [
        sys.executable, "-m", "pytest",
        ".",
        "--cov=../src",
        "--cov-report=html:coverage_html",
        "--cov-report=term-missing",
        "--cov-fail-under=80",
        "-v" if verbose else "-q"
    ]
    return run_command(cmd, "All Tests with Coverage")

def run_specific_test(test_path, verbose=False):
    """Run a specific test file or test function"""
    cmd = [sys.executable, "-m", "pytest", test_path, "-v" if verbose else "-q"]
    return run_command(cmd, f"Specific Test: {test_path}")

def lint_code():
    """Run code linting"""
    print("\nRunning code linting...")
    
    # Try flake8 first
    cmd = [sys.executable, "-m", "flake8", "src/", "tests/", "--max-line-length=120"]
    flake8_result = run_command(cmd, "Flake8 Linting")
    
    return flake8_result

def main():
    """Main test runner"""
    parser = argparse.ArgumentParser(description="Run FLEET system tests")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--install-deps", action="store_true", help="Install test dependencies")
    parser.add_argument("--unit", action="store_true", help="Run only unit tests")
    parser.add_argument("--property", action="store_true", help="Run only property-based tests")
    parser.add_argument("--integration", action="store_true", help="Run only integration tests")
    parser.add_argument("--coverage", action="store_true", help="Run all tests with coverage")
    parser.add_argument("--lint", action="store_true", help="Run code linting")
    parser.add_argument("--test", type=str, help="Run specific test file or function")
    parser.add_argument("--all", action="store_true", help="Run all tests and checks")
    
    args = parser.parse_args()
    
    # Change to tests directory
    os.chdir(Path(__file__).parent)
    
    success = True
    
    # Install dependencies if requested
    if args.install_deps:
        success &= install_dependencies()
    
    # Run specific test suite or all tests
    if args.test:
        success &= run_specific_test(args.test, args.verbose)
    elif args.unit:
        success &= run_unit_tests(args.verbose)
    elif args.property:
        success &= run_property_tests(args.verbose)
    elif args.integration:
        success &= run_integration_tests(args.verbose)
    elif args.coverage:
        success &= run_all_tests_with_coverage(args.verbose)
    elif args.lint:
        success &= lint_code()
    elif args.all:
        print("Running complete test suite...")
        success &= lint_code()
        success &= run_unit_tests(args.verbose)
        success &= run_property_tests(args.verbose)
        success &= run_integration_tests(args.verbose)
        success &= run_all_tests_with_coverage(args.verbose)
    else:
        # Default: run all tests
        print("Running all tests (use --help for more options)...")
        success &= run_unit_tests(args.verbose)
        success &= run_property_tests(args.verbose)
        success &= run_integration_tests(args.verbose)
    
    # Print summary
    print(f"\n{'='*60}")
    if success:
        print("✅ All tests completed successfully!")
        print("\nNext steps:")
        print("1. Review test coverage report in tests/coverage_html/index.html")
        print("2. Ensure all tests pass before deployment")
        print("3. Add more tests for new features")
    else:
        print("❌ Some tests failed!")
        print("\nPlease fix failing tests before deployment.")
    print(f"{'='*60}")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())