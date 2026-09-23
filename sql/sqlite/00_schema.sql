-- SQLite kullanımı: Bu dosyayı raw veritabanı ATTACH edildikten sonra çalıştırın.
-- Örnek: ATTACH DATABASE 'sqlite/raw.sqlite' AS raw;

CREATE TABLE raw.subscribers (
  subscriber_id    bigint,
  msisdn           text,
  plan_id          text,
  status           text,
  activation_date  date,
  city             text,
  segment          text
);

CREATE TABLE raw.cdr_events (
  event_id      text,
  msisdn        text,
  event_type    text,
  event_ts      timestamp,
  duration_sec  integer,
  bytes         bigint,
  cell_id       text,
  country_code  text,
  ingested_at   timestamp
);

CREATE TABLE raw.recharges (
  recharge_id   bigint,
  msisdn        text,
  amount_try    numeric(10,2),
  channel       text,
  recharge_ts   timestamp
);

CREATE TABLE raw.campaigns (
  campaign_id     text,
  name            text,
  start_date      date,
  end_date        date,
  target_segment  text
);

CREATE TABLE raw.campaign_responses (
  response_id   bigint,
  campaign_id   text,
  msisdn        text,
  responded_at  timestamp,
  accepted      boolean
);

CREATE TABLE raw.plan_changes (
  msisdn       text,
  old_plan_id  text,
  new_plan_id  text,
  changed_at   timestamp
);

CREATE TABLE raw.plans (
  plan_id      text,
  plan_name    text,
  plan_family  text,
  monthly_fee  numeric(10,2)
);

CREATE TABLE raw.corporate_accounts (
  account_id         text,
  parent_account_id  text,
  account_name       text,
  msisdn             text
);