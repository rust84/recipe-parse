"""
Sample test file
"""

def test_main_function():
    """Test the main function exists"""
    from main import main
    # Test that main function can be called without errors
    try:
        main()
        assert True
    except Exception as e:
        assert False, f"main() raised an exception: {e}"
