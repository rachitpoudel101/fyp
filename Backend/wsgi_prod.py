"""
WSGI production config that handles path issues
"""

import os
import sys

# Add the project directory to the Python path
# Adjust the path to point to the directory containing the inventory_man_system package
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Import the WSGI application
from inventory_man_system.wsgi import application
