from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base

        return f"<DeParaConfig(id={self.id}, titulo='{self.titulo}')>"
