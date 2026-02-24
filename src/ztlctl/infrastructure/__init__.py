"""Infrastructure layer — database, graph engine, filesystem.

This layer depends on stdlib and third-party libs (SQLAlchemy, NetworkX).
It must never import from domain, services, commands, or output.
The service layer bridges between domain models and infrastructure.
"""
