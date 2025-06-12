# app/api/socket_deps.py

from functools import wraps

from app.api.deps import get_client_service, get_db_session_context, get_message_service

SERVICE_GETTERS = {
    "client_service": get_client_service,
    "message_service": get_message_service,
}


def inject_services(services: list[str] = None):
    if services is None:
        services = []

    def decorator(fn):
        @wraps(fn)
        async def wrapper(sid, *args, **kwargs):
            async with get_db_session_context() as db:
                deps = {}
                for service_name in services:
                    getter = SERVICE_GETTERS.get(service_name)
                    if getter is None:
                        raise ValueError(f"Unknown service requested: {service_name}")
                    deps[service_name] = getter(db)

                return await fn(sid, *args, **kwargs, **deps)

        return wrapper

    return decorator
