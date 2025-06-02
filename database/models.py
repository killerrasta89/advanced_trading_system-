from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from src.main import db
import datetime

class User(db.Model):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(64), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(128))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Exchange(db.Model):
    __tablename__ = 'exchanges'
    id = Column(Integer, primary_key=True)
    name = Column(String(64), nullable=False)
    api_key = Column(String(128))
    api_secret = Column(String(128))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    accounts = relationship("Account", back_populates="exchange")
    
    def __repr__(self):
        return f'<Exchange {self.name}>'

class Account(db.Model):
    __tablename__ = 'accounts'
    id = Column(Integer, primary_key=True)
    exchange_id = Column(Integer, ForeignKey('exchanges.id'))
    name = Column(String(64), nullable=False)
    balance_usd = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    exchange = relationship("Exchange", back_populates="accounts")
    assets = relationship("Asset", back_populates="account")
    
    def __repr__(self):
        return f'<Account {self.name}>'

class Asset(db.Model):
    __tablename__ = 'assets'
    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey('accounts.id'))
    symbol = Column(String(20), nullable=False)
    amount = Column(Float, default=0.0)
    avg_buy_price = Column(Float, default=0.0)
    current_price = Column(Float, default=0.0)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    account = relationship("Account", back_populates="assets")
    
    def __repr__(self):
        return f'<Asset {self.symbol}>'

class Strategy(db.Model):
    __tablename__ = 'strategies'
    id = Column(Integer, primary_key=True)
    name = Column(String(64), nullable=False)
    type = Column(String(64), nullable=False)
    config = Column(String(1024))
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    trades = relationship("Trade", back_populates="strategy")
    
    def __repr__(self):
        return f'<Strategy {self.name}>'

class Trade(db.Model):
    __tablename__ = 'trades'
    id = Column(Integer, primary_key=True)
    strategy_id = Column(Integer, ForeignKey('strategies.id'))
    exchange_id = Column(Integer, ForeignKey('exchanges.id'))
    symbol = Column(String(20), nullable=False)
    order_type = Column(String(20), nullable=False)
    side = Column(String(10), nullable=False)
    amount = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    status = Column(String(20), default='open')
    executed_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    strategy = relationship("Strategy", back_populates="trades")
    
    def __repr__(self):
        return f'<Trade {self.symbol} {self.side}>'

class MarketData(db.Model):
    __tablename__ = 'market_data'
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Float)
    
    def __repr__(self):
        return f'<MarketData {self.symbol} {self.timestamp}>'

class SystemLog(db.Model):
    __tablename__ = 'system_logs'
    id = Column(Integer, primary_key=True)
    level = Column(String(20), nullable=False)
    message = Column(String(512), nullable=False)
    component = Column(String(64))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    def __repr__(self):
        return f'<SystemLog {self.level} {self.component}>'
