from pydantic import BaseModel, PositiveFloat
from datetime import date

class Bar(BaseModel):
    permno: int
    cusip: int
    date: date
    open: PositiveFloat
    high: PositiveFloat
    low: PositiveFloat
    close: PositiveFloat
    vol: PositiveFloat
    shares_outstanding: PositiveFloat
    daily_return: PositiveFloat
    daily_return_wo_distribution: PositiveFloat
    market_cap: PositiveFloat
    price_x_volume: PositiveFloat
    delisting_flag: bool



