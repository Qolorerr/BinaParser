import sqlalchemy
from sqlalchemy_serializer import SerializerMixin
from src.db_session import SqlAlchemyBase


class User(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'user'
    __table_args__ = {'extend_existing': True}
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    subscription_till = sqlalchemy.Column(sqlalchemy.Integer)
