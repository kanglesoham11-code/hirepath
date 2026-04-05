from database import AgentLog, AsyncSessionLocal
from datetime import datetime

async def log_event(
    agent: str,
    event_type: str,
    message: str,
    data: dict | None = None,
    role_id: int | None = None,
    candidate_id: int | None = None,
):
    async with AsyncSessionLocal() as session:
        entry = AgentLog(
            agent=agent,
            event_type=event_type,
            message=message,
            data=data,
            role_id=role_id,
            candidate_id=candidate_id,
        )
        session.add(entry)
        await session.commit()

    # Also push to the global SSE broadcaster if available
    try:
        from main import broadcast
        await broadcast({"agent": agent, "event": event_type, "message": message, "data": data})
    except Exception:
        pass
