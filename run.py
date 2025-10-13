#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'asase_project.settings')
    
    from django.core.management import execute_from_command_line
    
    execute_from_command_line(['manage.py', 'runserver', '0.0.0.0:5000'])
