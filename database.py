import os

from sqlalchemy import (
    BigInteger,
    ForeignKeyConstraint,
    Integer,
    String,
    delete,
    select,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite+aiosqlite:///hunts.db",
)


class Base(DeclarativeBase):
    pass


class Hunt(Base):
    __tablename__ = "hunts"

    hunt_type: Mapped[str] = mapped_column(
        String(16),
        primary_key=True,
    )

    owner_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    channel_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    mention: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
    )


class HuntClass(Base):
    __tablename__ = "hunt_classes"

    hunt_type: Mapped[str] = mapped_column(
        String(16),
        primary_key=True,
    )

    owner_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    crn: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    seats_left: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    total_seats: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    message_id: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )

    __table_args__ = (
        ForeignKeyConstraint(
            ["hunt_type", "owner_id"],
            ["hunts.hunt_type", "hunts.owner_id"],
            ondelete="CASCADE",
        ),
    )


engine = create_async_engine(
    DATABASE_URL,
    echo=False,
)

Session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def initialize_database():
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


async def save_hunt(hunt_key, hunt):
    """
    Create or completely replace a hunt.
    """
    hunt_type, owner_id = hunt_key

    async with Session.begin() as session:
        existing = await session.get(
            Hunt,
            {
                "hunt_type": hunt_type,
                "owner_id": owner_id,
            },
        )

        if existing is None:
            existing = Hunt(
                hunt_type=hunt_type,
                owner_id=owner_id,
                channel_id=hunt["channel_id"],
                mention=hunt["mention"],
            )
            session.add(existing)
        else:
            existing.channel_id = hunt["channel_id"]
            existing.mention = hunt["mention"]

        # A new /begin_hunt replaces the existing CRN list.
        await session.execute(
            delete(HuntClass).where(
                HuntClass.hunt_type == hunt_type,
                HuntClass.owner_id == owner_id,
            )
        )

        for crn in hunt["crns"]:
            session.add(
                HuntClass(
                    hunt_type=hunt_type,
                    owner_id=owner_id,
                    crn=crn,
                )
            )


async def add_class(hunt_key, crn):
    hunt_type, owner_id = hunt_key

    async with Session.begin() as session:
        existing = await session.get(
            HuntClass,
            {
                "hunt_type": hunt_type,
                "owner_id": owner_id,
                "crn": crn,
            },
        )

        if existing is None:
            session.add(
                HuntClass(
                    hunt_type=hunt_type,
                    owner_id=owner_id,
                    crn=crn,
                )
            )


async def remove_class(hunt_key, crn):
    hunt_type, owner_id = hunt_key

    async with Session.begin() as session:
        await session.execute(
            delete(HuntClass).where(
                HuntClass.hunt_type == hunt_type,
                HuntClass.owner_id == owner_id,
                HuntClass.crn == crn,
            )
        )


async def delete_hunt(hunt_key):
    hunt_type, owner_id = hunt_key

    async with Session.begin() as session:
        # Explicitly delete children first so this behaves consistently
        # even if SQLite foreign-key enforcement changes.
        await session.execute(
            delete(HuntClass).where(
                HuntClass.hunt_type == hunt_type,
                HuntClass.owner_id == owner_id,
            )
        )

        await session.execute(
            delete(Hunt).where(
                Hunt.hunt_type == hunt_type,
                Hunt.owner_id == owner_id,
            )
        )


async def save_class_state(hunt_key, crn, state):
    hunt_type, owner_id = hunt_key

    async with Session.begin() as session:
        hunt_class = await session.get(
            HuntClass,
            {
                "hunt_type": hunt_type,
                "owner_id": owner_id,
                "crn": crn,
            },
        )

        if hunt_class is None:
            # This should normally not happen, but makes the function
            # resilient if the in-memory state gets ahead of the DB.
            hunt_class = HuntClass(
                hunt_type=hunt_type,
                owner_id=owner_id,
                crn=crn,
            )
            session.add(hunt_class)

        hunt_class.name = state.get("name")
        hunt_class.seats_left = state.get("left")
        hunt_class.total_seats = state.get("total")
        hunt_class.message_id = state.get("message_id")


async def load_hunts():
    hunts = {}

    async with Session() as session:
        hunt_result = await session.execute(
            select(Hunt)
        )

        persisted_hunts = hunt_result.scalars().all()

        for hunt in persisted_hunts:
            class_result = await session.execute(
                select(HuntClass)
                .where(
                    HuntClass.hunt_type == hunt.hunt_type,
                    HuntClass.owner_id == hunt.owner_id,
                )
                .order_by(HuntClass.crn)
            )

            classes = class_result.scalars().all()

            crns = []
            class_states = {}

            for course in classes:
                crns.append(course.crn)

                # A class may not have been polled yet.
                if course.name is not None:
                    class_states[course.crn] = {
                        "name": course.name,
                        "left": course.seats_left,
                        "total": course.total_seats,
                        "message_id": course.message_id,
                    }

            hunt_key = (
                hunt.hunt_type,
                hunt.owner_id,
            )

            hunts[hunt_key] = {
                "channel_id": hunt.channel_id,
                "crns": crns,
                "class_states": class_states,
                "mention": hunt.mention,
                "task": None,
            }

    return hunts


async def close_database():
    await engine.dispose()