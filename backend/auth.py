"""
Legacy auth module alias for backward compatibility.
Redirects to production routes.auth module.
"""
from routes.auth import auth_bp

auth = auth_bp