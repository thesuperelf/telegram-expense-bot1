from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine


_engine: AsyncEngine | None = None
_session_maker: async_sessionmaker[AsyncSession] | None = None


def init_engine(database_url: str) -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    global _engine, _session_maker

    if _engine is None:
        _engine = create_async_engine(database_url, echo=False)
        _session_maker = async_sessionmaker(
            bind=_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    return _engine, _session_maker


def get_engine() -> AsyncEngine:
    if _engine is None:
        raise RuntimeError("Движок БД не инициализирован. Сначала вызовите init_engine().")
    return _engine


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    if _session_maker is None:
        raise RuntimeError("Session maker не инициализирован. Сначала вызовите init_engine().")
    return _session_maker
