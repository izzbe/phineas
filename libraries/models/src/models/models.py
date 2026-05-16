from pydantic import BaseModel, field_validator
from datetime import date, datetime
from typing import Optional

class Header(BaseModel):
    permno: int | None
    permco: int | None
    cusip: str | None
    issuernm: str | None
    securitynm: str | None
    ticker: str | None
    secinfostartdt: date | None
    secinfoenddt: date | None
    securitybegdt: date | None
    securityenddt: date | None
    securitytype: str | None
    securitysubtype: str | None
    shareclass: str | None
    primaryexch: str | None
    tradingstatusflg: str | None
    siccd: int | None
    naics: str | None
    usincflg: str | None

    @field_validator('secinfostartdt',
                     'secinfoenddt',
                     'securitybegdt',
                     'securityenddt',
                     mode='before')
    @classmethod
    def str_to_date(cls, val: str):
        if not isinstance(val, str):
            return val
        return datetime.strptime(val, "%Y-%m-%d").date()

class Bar(BaseModel):
    permno: int
    dlycaldt: date
    dlyopen: float | None
    dlyhigh: float | None
    dlylow: float | None
    dlyprc: float | None
    dlyvol: float | None
    dlyret: float | None
    dlyretx: float | None
    dlycap: float | None
    dlyprcvol: float | None
    dlydelflg: str

    @field_validator('dlycaldt',
                     mode='before')
    @classmethod
    def str_to_date(cls, val: str):
        if not isinstance(val, str):
            return val
        return datetime.strptime(val, "%Y-%m-%d").date()

    @field_validator('dlyprc',
                     mode='before')
    @classmethod
    def turn_abs(cls, val: float):
        if not isinstance(val, float):
            return val
        return abs(val)

class Adjustment(BaseModel):
    permno: int
    dlycaldt: date
    dlyshrout: float | None
    dlycumfacpr: float
    dlycumfacshr: float
    @field_validator('dlycaldt',
                     mode='before')
    @classmethod
    def str_to_date(cls, val: str):
        if not isinstance(val, str):
            return val
        return datetime.strptime(val, "%Y-%m-%d").date()

class Link(BaseModel):
    gvkey: str
    linkdt: date
    linkenddt: date | None
    linkprim: str
    linktype: str
    lpermco: int | None
    lpermno: int | None
    @field_validator('linkdt',
                     'linkenddt',
                     mode='before')
    @classmethod
    def str_to_date(cls, val: str):
        if not isinstance(val, str):
            return val
        return datetime.strptime(val, "%Y-%m-%d").date()

class FundamentalsQuarterly(BaseModel):
    # Identifiers & period
    gvkey: str
    datadate: date
    rdq: Optional[date] = None
    fyearq: Optional[int] = None
    fqtr: Optional[int] = None
    fyr: Optional[int] = None
    datacqtr: Optional[str] = None
    datafqtr: Optional[str] = None

    # Filter discriminators
    indfmt: Optional[str] = None
    consol: Optional[str] = None
    popsrc: Optional[str] = None
    datafmt: Optional[str] = None

    # Descriptive metadata
    conm: Optional[str] = None
    tic: Optional[str] = None
    cusip: Optional[str] = None
    cik: Optional[str] = None
    curcdq: Optional[str] = None
    fic: Optional[str] = None
    costat: Optional[str] = None
    exchg: Optional[int] = None

    # Adjustment factor
    ajexq: Optional[float] = None

    # Income statement
    saleq: Optional[float] = None
    revtq: Optional[float] = None
    cogsq: Optional[float] = None
    xsgaq: Optional[float] = None
    xrdq: Optional[float] = None
    xintq: Optional[float] = None
    xoprq: Optional[float] = None
    oibdpq: Optional[float] = None
    oiadpq: Optional[float] = None
    dpq: Optional[float] = None
    nopiq: Optional[float] = None
    piq: Optional[float] = None
    txtq: Optional[float] = None
    ibq: Optional[float] = None
    ibcomq: Optional[float] = None
    niq: Optional[float] = None
    xiq: Optional[float] = None
    spiq: Optional[float] = None

    # EPS
    epsfxq: Optional[float] = None
    epspxq: Optional[float] = None
    epsfiq: Optional[float] = None
    epspiq: Optional[float] = None

    # Balance sheet
    atq: Optional[float] = None
    ltq: Optional[float] = None
    seqq: Optional[float] = None
    ceqq: Optional[float] = None
    cheq: Optional[float] = None
    actq: Optional[float] = None
    lctq: Optional[float] = None
    invtq: Optional[float] = None
    rectq: Optional[float] = None
    apq: Optional[float] = None
    ppentq: Optional[float] = None
    ppegtq: Optional[float] = None
    intanq: Optional[float] = None
    gdwlq: Optional[float] = None
    dlcq: Optional[float] = None
    dlttq: Optional[float] = None
    dd1q: Optional[float] = None
    pstkq: Optional[float] = None
    txditcq: Optional[float] = None
    req: Optional[float] = None
    icaptq: Optional[float] = None
    mibq: Optional[float] = None

    # Cash flow (YTD)
    oancfy: Optional[float] = None
    capxy: Optional[float] = None
    dvy: Optional[float] = None
    sstky: Optional[float] = None
    prstkcy: Optional[float] = None
    dltisy: Optional[float] = None
    dltry: Optional[float] = None

    # Share / market data
    cshoq: Optional[float] = None
    cshprq: Optional[float] = None
    cshfdq: Optional[float] = None
    prccq: Optional[float] = None
    mkvaltq: Optional[float] = None

    @field_validator('datadate',
                     'rdq',
                     mode='before')
    @classmethod
    def str_to_date(cls, val: str):
        if not isinstance(val, str):
            return val
        return datetime.strptime(val, "%Y-%m-%d").date()