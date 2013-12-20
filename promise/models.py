import datetime

from sqlalchemy import (
    Column,
    Integer,
    Unicode,
    DateTime,
    ForeignKey,
    func
    )

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
    relationship,
    synonym
    )

from zope.sqlalchemy import ZopeTransactionExtension

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()

class Promise(Base):
    __tablename__ = 'promise'

    promise_id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(Unicode, nullable=False)
    state = Column(Unicode, nullable=False)
    number = Column(Integer, nullable=False)
    html_url = Column(Unicode, nullable=False)
    _github_created_at = Column('github_created_at', DateTime, nullable=False)
    _github_updated_at = Column('github_updated_at', DateTime, nullable=False)
    github_user_id = Column(Integer, ForeignKey('github_user.user_id',
                                                onupdate='CASCADE',
                                                ondelete='CASCADE'),
                            nullable=False)
    last_updated = Column(DateTime, server_default=func.now())

    def _parse_datetime_string(self, date_string):
        return datetime.datetime.strptime(date_string, '%Y-%m-%dT%H:%M:%SZ')
    
    def has_update(self, date_string):
        update_at = self._parse_datetime_string(date_string)
        return update_at == self._github_updated_at
    
    def _set_github_created_at(self, date_string):
        created_at = self._parse_datetime_string(date_string)
        self._github_created_at = created_at
    
    def _get_github_created_at(self):
        return self._github_created_at

    def _set_github_updated_at(self, date_string):
        update_at = self._parse_datetime_string(date_string)
        self._github_updated_at = update_at

    def _get_github_updated_at(self):
        return self._github_updated_at

    github_created_at = synonym('_github_created_at',
                                descriptor=property(_get_github_created_at,
                                                    _set_github_created_at))

    github_updated_at = synonym('_github_updated_at',
                                descriptor=property(_get_github_updated_at,
                                                    _set_github_updated_at))

    github_user = relationship('GithubUser', uselist=False, backref='promises')
    
class GithubUser(Base):
    __tablename__ = 'github_user'

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    login = Column(Unicode, nullable=False)
    html_url = Column(Unicode, nullable=False)
    avatar_url = Column(Unicode)
    last_updated = Column(DateTime, server_default=func.now())
