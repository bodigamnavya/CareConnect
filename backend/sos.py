"""
Legacy SOS module alias for backward compatibility.
Redirects to production routes.sos module.
"""
from routes.sos import sos_bp

sos = sos_bp