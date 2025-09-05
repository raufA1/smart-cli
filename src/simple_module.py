"""Simple module to generate coverage data."""

def hello_world():
    """Return hello world."""
    return "Hello World!"

def calculate_sum(numbers):
    """Calculate sum of numbers."""
    if not numbers:
        return 0
    return sum(numbers)

def is_even(number):
    """Check if number is even."""
    return number % 2 == 0

class SimpleCalculator:
    """Simple calculator class."""
    
    def __init__(self):
        self.result = 0
    
    def add(self, x, y):
        """Add two numbers."""
        self.result = x + y
        return self.result
    
    def subtract(self, x, y):
        """Subtract two numbers."""
        self.result = x - y
        return self.result