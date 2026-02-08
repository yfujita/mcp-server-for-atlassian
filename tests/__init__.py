"""
Test suite for MCP Server for Atlassian.

This package contains all unit and integration tests for the project.
Tests are organized by module:

- test_auth/: Authentication strategy tests
- test_confluence/: Confluence client and converter tests
- test_tools/: MCP tool implementation tests

Running tests:
    pytest                    # Run all tests
    pytest tests/test_auth/   # Run auth tests only
    pytest -v                 # Verbose output
    pytest --cov=src          # With coverage report

Test conventions:
    - Use async test functions for async code
    - Mock external API calls
    - Use fixtures for common setup
    - Aim for 80%+ code coverage
"""
