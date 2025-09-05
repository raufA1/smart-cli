"""Simple test to generate coverage for Codecov."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from simple_module import hello_world, calculate_sum, is_even, SimpleCalculator

def test_hello_world():
    """Test hello world function."""
    result = hello_world()
    assert result == "Hello World!"

def test_calculate_sum():
    """Test calculate sum function."""
    assert calculate_sum([1, 2, 3]) == 6
    assert calculate_sum([]) == 0
    assert calculate_sum([10]) == 10
    assert calculate_sum([-1, 1]) == 0

def test_is_even():
    """Test is even function."""
    assert is_even(2) == True
    assert is_even(3) == False
    assert is_even(0) == True
    assert is_even(-2) == True
    assert is_even(-3) == False

def test_simple_calculator():
    """Test SimpleCalculator class."""
    calc = SimpleCalculator()
    assert calc.result == 0
    
    # Test addition
    result = calc.add(5, 3)
    assert result == 8
    assert calc.result == 8
    
    # Test subtraction
    result = calc.subtract(10, 4)
    assert result == 6
    assert calc.result == 6

def test_python_version():
    """Test Python version."""
    assert sys.version_info >= (3, 9)

def test_basic_imports():
    """Test basic imports work."""
    assert os is not None
    assert sys is not None