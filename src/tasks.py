import sqlalchemy
from sqlalchemy_serializer import SerializerMixin
from src.db_session import SqlAlchemyBase


class Task(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'task'
    __table_args__ = {'extend_existing': True}
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    user_id = sqlalchemy.Column(sqlalchemy.Integer)
    name = sqlalchemy.Column(sqlalchemy.String)
    url = sqlalchemy.Column(sqlalchemy.String)
    frequency = sqlalchemy.Column(sqlalchemy.Integer)
    last_items = sqlalchemy.Column(sqlalchemy.String)
