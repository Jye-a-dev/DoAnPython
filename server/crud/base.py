from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from pydantic import BaseModel
from sqlmodel import Session, SQLModel, col, func, select

ModelType = TypeVar("ModelType", bound=SQLModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Generic repository providing standardized CRUD and aggregate count operations."""

    def __init__(self, model: Type[ModelType]):
        self.model = model

    def get(self, session: Session, id: Any) -> Optional[ModelType]:
        """Fetch a single record by primary key."""
        return session.get(self.model, id)

    def get_multi(
        self, session: Session, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """Retrieve paginated records."""
        statement = select(self.model).offset(skip).limit(limit)
        return list(session.exec(statement).all())

    def count(self, session: Session) -> int:
        """Calculate total number of records."""
        statement = select(func.count()).select_from(self.model)
        result = session.exec(statement).one()
        return int(result)

    def create(self, session: Session, obj_in: CreateSchemaType) -> ModelType:
        """
        Persist a new record to the database.
        Maintains string UUID v4 or allows model default_factory to populate it.
        """
        import uuid
        obj_data = obj_in.model_dump() if hasattr(obj_in, "model_dump") else dict(obj_in)
        if obj_data.get("id") is None:
            obj_data.pop("id", None)
        db_obj = self.model(**obj_data)

        if getattr(db_obj, "id", None) is None and getattr(self.model, "__tablename__", "") != "roles":
            setattr(db_obj, "id", str(uuid.uuid4()))

        session.add(db_obj)
        session.commit()
        session.refresh(db_obj)
        return db_obj

    def update(
        self,
        session: Session,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """Update fields of an existing model instance."""
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        # Do not allow overriding primary key ID
        update_data.pop("id", None)

        for field, value in update_data.items():
            setattr(db_obj, field, value)

        session.add(db_obj)
        session.commit()
        session.refresh(db_obj)
        return db_obj

    def remove(self, session: Session, id: Any) -> Optional[ModelType]:
        """Delete a record by primary key."""
        obj = session.get(self.model, id)
        if obj:
            session.delete(obj)
            session.commit()
        return obj

