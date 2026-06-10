from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from ..core.database import Base
import datetime

class BotConfig(Base):
    __tablename__ = "bot_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # ← TENANT ISOLATION
    name = Column(String, nullable=False)
    strategy = Column(String, nullable=False)  # momentum, mean_reversion, grid
    config = Column(JSON, default={})  # {"symbol": "BTCUSDT", "buy_threshold": 0.02}
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_execution = Column(DateTime, nullable=True)
    total_trades = Column(Integer, default=0)
    total_pnl = Column(Float, default=0.0)
    
    user = relationship("User", back_populates="bots")