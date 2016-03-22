""" These classes define the ORM models to be used by sqlalchemy for the job tracker database """

from sqlalchemy import Column, Integer, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class FileType(Base):
    __tablename__ = "file_type"

    file_id = Column(Integer, primary_key=True)
    name = Column(Text)
    description = Column(Text)

class FieldType(Base):
    __tablename__ = "field_type"

    field_type_id = Column(Integer, primary_key=True)
    name = Column(Text)
    description = Column(Text)

class RuleType(Base):
    __tablename__ = "rule_type"

    rule_type_id = Column(Integer, primary_key=True)
    name = Column(Text)
    description = Column(Text)

    TYPE_DICT = None
    TYPE_LIST = ["TYPE", "EQUAL","NOT EQUAL","LESS","GREATER","LENGTH","IN_SET"]

class MultiFieldRuleType(Base):
    __tablename__ = "multi_field_rule_type"

    multi_field_rule_type_id = Column(Integer, primary_key=True)
    name = Column(Text)
    description = Column(Text)

    session = None
    TYPE_DICT = None
    TYPE_LIST = ["CAR_MATCH"]

class FileColumn(Base):
    __tablename__ = "file_columns"

    file_column_id = Column(Integer, primary_key=True)
    file_id = Column(Integer, ForeignKey("file_type.file_id"), nullable=True)
    file = relationship("FileType", uselist=False)
    field_types_id = Column(Integer, ForeignKey("field_type.field_type_id"), nullable=True)
    field_type = relationship("FieldType", uselist=False)
    name = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    required = Column(Boolean, nullable=True)
    rules = relationship("Rule", cascade = "delete, delete-orphan")

class Rule(Base):
    __tablename__ = "rule"
    rule_id = Column(Integer, primary_key=True)
    file_column_id = Column(Integer, ForeignKey("file_columns.file_column_id"), nullable=True)
    rule_type_id  = Column(Integer, ForeignKey("rule_type.rule_type_id"), nullable=True)
    rule_text_1 = Column(Text, nullable=True)
    rule_text_2 = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    rule_type = relationship("RuleType", uselist=False)
    file_column = relationship("FileColumn", uselist=False)

class MultiFieldRule(Base):
    __tablename__ = "multi_field_rule"
    multi_field_rule_id = Column(Integer, primary_key=True)
    file_id = Column(Integer, ForeignKey("file_type.file_id"), nullable=True)
    multi_field_rule_type_id  = Column(Integer, ForeignKey("multi_field_rule_type.multi_field_rule_type_id"), nullable=True)
    rule_text_1 = Column(Text, nullable=True)
    rule_text_2 = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    multi_field_rule_type = relationship("MultiFieldRuleType", uselist=False)
    file_type = relationship("FileType", uselist=False)
    
class TASLookup(Base) :
    __tablename__ = "tas_lookup"
    tas_id = Column(Integer, primary_key=True)
    allocation_transfer_agency = Column(Text, nullable=True)
    agency_identifier = Column(Text, nullable=True)
    beginning_period_of_availability = Column(Text, nullable=True)
    ending_period_of_availability = Column(Text, nullable=True)
    availability_type_code = Column(Text, nullable=True)
    main_account_code = Column(Text, nullable=True)
    sub_account_code = Column(Text, nullable=True)