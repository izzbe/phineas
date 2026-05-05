CREATE EXTENSION IF NOT EXISTS timescaledb;

CREATE TABLE bars
(
    permno                 INTEGER,
    cusip                  TEXT,
    date                   DATE,
    open                   DOUBLE PRECISION,
    high                   DOUBLE PRECISION,
    low                    DOUBLE PRECISION,
    close                  DOUBLE PRECISION,
    vol                    DOUBLE PRECISION,
    shares_outstanding     DOUBLE PRECISION,
    daily_return                 DOUBLE PRECISION,
    daily_return_wo_distribution DOUBLE PRECISION,
    market_cap             DOUBLE PRECISION,
    price_x_volume         DOUBLE PRECISION,
    delisting_flag         BOOLEAN,
    data_source            TEXT        NOT NULL DEFAULT 'crsp',
    ingested_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (permno, date)
) WITH (
      timescaledb.hypertable,
      timescaledb.partition_column = 'date',
      timescaledb.orderby = 'date DESC'
      );

CREATE TABLE adjustment
(
    permno             INTEGER,
    date               DATE,
    price_adjustment   DOUBLE PRECISION,
    volume_adjustment  DOUBLE PRECISION,
    shares_outstanding DOUBLE PRECISION,
    ingested_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (permno, date)
) WITH (
      timescaledb.hypertable,
      timescaledb.partition_column = 'date',
      timescaledb.orderby = 'date DESC'
      );

CREATE TABLE header
(
    permno           INTEGER PRIMARY KEY,
    permco           INTEGER,
    cusip            TEXT,
    issuer_name      TEXT,
    security_name    TEXT,
    ticker           TEXT,
    info_valid_start DATE,
    info_valid_end   DATE,
    security_start   DATE,
    security_end     DATE,
    security_type    TEXT,
    security_subtype TEXT,
    share_class      TEXT,
    primary_exchange TEXT,
    trading_status   TEXT,
    SIC_code         INTEGER,
    naics            INTEGER,
    us_incorporation TEXT,
    ingested_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE fundamentals_quarterly
(
    -- ---------- Identifiers & period ----------
    gvkey       TEXT        NOT NULL,
    datadate    DATE        NOT NULL, -- fiscal period end
    rdq         DATE,                 -- report announcement date (nullable pre-1971)
    fyearq      SMALLINT    NOT NULL,
    fqtr        SMALLINT    NOT NULL,
    fyr         SMALLINT,             -- fiscal year-end month
    datacqtr    TEXT,                 -- e.g. '1966Q4' (calendar)
    datafqtr    TEXT,                 -- e.g. '1966Q4' (fiscal)

    -- ---------- Filter discriminators (kept for provenance) ----------
    indfmt      TEXT        NOT NULL,
    consol      TEXT        NOT NULL,
    popsrc      TEXT        NOT NULL,
    datafmt     TEXT        NOT NULL,

    -- ---------- Descriptive metadata ----------
    conm        TEXT,                 -- company name
    tic         TEXT,                 -- most-recent ticker
    cusip       TEXT,                 -- 9-char CUSIP
    cik         TEXT,                 -- for EDGAR linking
    curcdq      TEXT,                 -- reporting currency
    fic         TEXT,                 -- country of incorporation
    costat      TEXT,                 -- 'A' active / 'I' inactive
    exchg       SMALLINT,             -- exchange code

    -- ---------- Adjustment factor ----------
    ajexq       DOUBLE PRECISION,     -- cumulative adjustment factor

    -- ---------- Income statement (quarterly, "q" suffix) ----------
    saleq       DOUBLE PRECISION,     -- sales/revenue
    revtq       DOUBLE PRECISION,     -- total revenue
    cogsq       DOUBLE PRECISION,     -- cost of goods sold
    xsgaq       DOUBLE PRECISION,     -- SG&A
    xrdq        DOUBLE PRECISION,     -- R&D expense
    xintq       DOUBLE PRECISION,     -- interest expense
    xoprq       DOUBLE PRECISION,     -- total operating expenses
    oibdpq      DOUBLE PRECISION,     -- operating income before D&A (EBITDA proxy)
    oiadpq      DOUBLE PRECISION,     -- operating income after D&A (EBIT)
    dpq         DOUBLE PRECISION,     -- depreciation & amortization
    nopiq       DOUBLE PRECISION,     -- non-operating income
    piq         DOUBLE PRECISION,     -- pretax income
    txtq        DOUBLE PRECISION,     -- income taxes
    ibq         DOUBLE PRECISION,     -- income before extraordinary items
    ibcomq      DOUBLE PRECISION,     -- IB available to common
    niq         DOUBLE PRECISION,     -- net income
    xiq         DOUBLE PRECISION,     -- extraordinary items
    spiq        DOUBLE PRECISION,     -- special items

    -- ---------- EPS ----------
    epsfxq      DOUBLE PRECISION,     -- diluted EPS, excl extraordinary
    epspxq      DOUBLE PRECISION,     -- basic EPS, excl extraordinary
    epsfiq      DOUBLE PRECISION,     -- diluted EPS, incl extraordinary
    epspiq      DOUBLE PRECISION,     -- basic EPS, incl extraordinary

    -- ---------- Balance sheet (point-in-time) ----------
    atq         DOUBLE PRECISION,     -- total assets
    ltq         DOUBLE PRECISION,     -- total liabilities
    seqq        DOUBLE PRECISION,     -- stockholders' equity
    ceqq        DOUBLE PRECISION,     -- common equity
    cheq        DOUBLE PRECISION,     -- cash & equivalents
    actq        DOUBLE PRECISION,     -- current assets
    lctq        DOUBLE PRECISION,     -- current liabilities
    invtq       DOUBLE PRECISION,     -- inventories
    rectq       DOUBLE PRECISION,     -- receivables
    apq         DOUBLE PRECISION,     -- accounts payable
    ppentq      DOUBLE PRECISION,     -- net PP&E
    ppegtq      DOUBLE PRECISION,     -- gross PP&E
    intanq      DOUBLE PRECISION,     -- intangibles
    gdwlq       DOUBLE PRECISION,     -- goodwill
    dlcq        DOUBLE PRECISION,     -- short-term / current debt
    dlttq       DOUBLE PRECISION,     -- long-term debt
    dd1q        DOUBLE PRECISION,     -- LT debt due in 1 year
    pstkq       DOUBLE PRECISION,     -- preferred stock
    txditcq     DOUBLE PRECISION,     -- deferred taxes & ITC
    req         DOUBLE PRECISION,     -- retained earnings
    icaptq      DOUBLE PRECISION,     -- invested capital
    mibq        DOUBLE PRECISION,     -- minority interest

    -- ---------- Cash flow (YTD, "y" suffix — cumulative within fiscal year) ----------
    oancfy      DOUBLE PRECISION,     -- operating cash flow YTD
    capxy       DOUBLE PRECISION,     -- capex YTD
    dvy         DOUBLE PRECISION,     -- dividends paid YTD
    sstky       DOUBLE PRECISION,     -- stock issuance YTD
    prstkcy     DOUBLE PRECISION,     -- stock repurchases YTD
    dltisy      DOUBLE PRECISION,     -- LT debt issued YTD
    dltry       DOUBLE PRECISION,     -- LT debt reduction YTD

    -- ---------- Share / market data ----------
    cshoq       DOUBLE PRECISION,     -- shares outstanding (millions)
    cshprq      DOUBLE PRECISION,     -- shares for basic EPS
    cshfdq      DOUBLE PRECISION,     -- shares for diluted EPS
    prccq       DOUBLE PRECISION,     -- close price at fiscal qtr-end
    mkvaltq     DOUBLE PRECISION,     -- market value (when populated)

    -- ---------- Provenance ----------
    data_source TEXT        NOT NULL DEFAULT 'compustat',
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    PRIMARY KEY (gvkey, datadate, indfmt)
) WITH (
      timescaledb.hypertable,
      timescaledb.partition_column = 'datadate',
      timescaledb.orderby = 'datadate DESC'
      );

CREATE TABLE link
(
    gvkey           TEXT,
    link_issue_id   TEXT,
    link_start_date DATE,
    link_end_date   DATE,
    link_primary    TEXT,
    link_type       TEXT,
    permco          INTEGER,
    permno          INTEGER,
    PRIMARY KEY (gvkey, permno, link_start_date)
);


