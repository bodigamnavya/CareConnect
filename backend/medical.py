"""
Legacy medical profile module alias for backward compatibility.
Redirects to production routes.profile module.
"""
from routes.profile import profile_bp

medical = profile_bp