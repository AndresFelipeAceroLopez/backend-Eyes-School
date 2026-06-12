# Backend Standards

Siempre usar:

- Python 3.12+
- FastAPI
- SQLAlchemy 2 Async
- Pydantic v2
- Alembic
- PostgreSQL
- Redis

Arquitectura:

domain/
application/
infrastructure/
presentation/

Nunca:

- SQL en routers
- lógica en endpoints
- repositorios dentro de controllers
- DTOs mezclados con entidades

Cada tabla debe generar:

- Entity
- Repository Interface
- Repository Implementation
- Use Cases
- DTO Create
- DTO Update
- DTO Response
- Router

Coverage mínimo 85%.