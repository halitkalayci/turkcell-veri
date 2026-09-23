-- PostgreSQL şema adları DuckDB içinde doğrudan korunur.
CREATE SCHEMA raw;
CREATE SCHEMA silver;
CREATE SCHEMA gold;
CREATE SCHEMA quarantine;
CREATE SCHEMA audit;

CREATE TABLE raw.subscribers (
  subscriber_id    BIGINT,
  msisdn           TEXT,
  plan_id          TEXT,
  status           TEXT,
  activation_date  DATE,
  city             TEXT,
  segment          TEXT
);

CREATE TABLE raw.cdr_events (
  event_id      TEXT,
  msisdn        TEXT,
  event_type    TEXT,
  event_ts      TIMESTAMP,
  duration_sec  INTEGER,
  bytes         BIGINT,
  cell_id       TEXT,
  country_code  TEXT,
  ingested_at   TIMESTAMP
);

CREATE TABLE raw.recharges (
  recharge_id   BIGINT,
  msisdn        TEXT,
  amount_try    DECIMAL(10,2),
  channel       TEXT,
  recharge_ts   TIMESTAMP
);

CREATE TABLE raw.campaigns (
  campaign_id     TEXT,
  name            TEXT,
  start_date      DATE,
  end_date        DATE,
  target_segment  TEXT
);

CREATE TABLE raw.campaign_responses (
  response_id   BIGINT,
  campaign_id   TEXT,
  msisdn        TEXT,
  responded_at  TIMESTAMP,
  accepted      BOOLEAN
);

CREATE TABLE raw.plan_changes (
  msisdn       TEXT,
  old_plan_id  TEXT,
  new_plan_id  TEXT,
  changed_at   TIMESTAMP
);

CREATE TABLE raw.plans (
  plan_id      TEXT,
  plan_name    TEXT,
  plan_family  TEXT,
  monthly_fee  DECIMAL(10,2)
);

CREATE TABLE raw.corporate_accounts (
  account_id         TEXT,
  parent_account_id  TEXT,
  account_name       TEXT,
  msisdn             TEXT
);