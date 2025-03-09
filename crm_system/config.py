"""
Configuration settings for the CRM system
"""

# Database Configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'database': 'crm_db',
    'user': 'root',
    'password': 'root'
}

# Feature Flags for Optional Modules
FEATURES = {
    'sales_automation': False,
    'marketing_automation': False,
    'customer_support': False,
    'mobile_access': False
}

# Application Settings
APP_SETTINGS = {
    'window_width': 1200,
    'window_height': 800,
    'theme': 'light',
    'company_name': 'CRM System'
}

# User Roles and Permissions
ROLES = {
    'admin': ['all'],
    'manager': ['view_reports', 'assign_tasks', 'manage_contacts'],
    'employee': ['view_assigned_tasks', 'view_assigned_contacts']
}

# Logging Configuration
LOG_CONFIG = {
    'log_level': 'INFO',
    'log_file': 'crm.log',
    'max_log_size': 5242880,  # 5MB
    'backup_count': 3
}
