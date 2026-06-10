from typing import Dict, List
from sqlalchemy.orm import Session
from ..models.bot import BotConfig
from ..models.user import User
import asyncio
import logging

logger = logging.getLogger(__name__)

class BotEngineManager:
    def __init__(self, db: Session):
        self.db = db
        self.running_bots: Dict[int, asyncio.Task] = {}
    
    async def start_bot(self, bot: BotConfig, user: User) -> bool:
        if bot.id in self.running_bots:
            return False
        
        task = asyncio.create_task(self._execution_loop(bot, user))
        self.running_bots[bot.id] = task
        
        bot.is_active = True
        self.db.commit()
        logger.info(f"Bot {bot.id} started for user {user.id}")
        return True
    
    async def stop_bot(self, bot_id: int, user_id: int) -> bool:
        if bot_id not in self.running_bots:
            return False
        
        self.running_bots[bot_id].cancel()
        del self.running_bots[bot_id]
        
        bot = self.db.query(BotConfig).filter(
            BotConfig.id == bot_id,
            BotConfig.user_id == user_id
        ).first()
        if bot:
            bot.is_active = False
            self.db.commit()
        
        logger.info(f"Bot {bot_id} stopped")
        return True
    
    async def _execution_loop(self, bot: BotConfig, user: User):
        config = bot.config or {}
        interval = config.get("interval_seconds", 60)
        
        while True:
            try:
                await asyncio.sleep(interval)
                
                if not bot.is_active:
                    break
                
                # Execute strategy logic here
                logger.info(f"Bot {bot.id} executing {bot.strategy} strategy")
                
                bot.last_execution = asyncio.get_event_loop().time()
                self.db.commit()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Bot {bot.id} error: {e}")
    
    async def shutdown_all(self):
        for task in self.running_bots.values():
            task.cancel()
        await asyncio.gather(*self.running_bots.values(), return_exceptions=True)
        self.running_bots.clear()