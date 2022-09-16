/*Init script for DB, it is executed on system startup*/
/*If db data is exests, script is not executed*/
/*Create tables with with different case values*/
/*then fill tables with data from csv files in ./csv_data folder*/
CREATE TABLE cases_severity(
  id SERIAL PRIMARY KEY,
  value VARCHAR(20)
);
COPY cases_severity(id, value) FROM '/docker-entrypoint-initdb.d/csv_data/cases_severity.csv' DELIMITER ',' CSV HEADER;

CREATE TABLE cases_assessed_outage(
  id SERIAL PRIMARY KEY,
  value VARCHAR(5)
);
COPY cases_assessed_outage(id, value) FROM '/docker-entrypoint-initdb.d/csv_data/cases_assessed_outage.csv' DELIMITER ',' CSV HEADER;

CREATE TABLE cases_status(
  id SERIAL PRIMARY KEY,
  value VARCHAR(25)
);
COPY cases_status(id, value) FROM '/docker-entrypoint-initdb.d/csv_data/cases_status.csv' DELIMITER ',' CSV HEADER;

CREATE TABLE cases_product_name(
  id SERIAL PRIMARY KEY,
  value VARCHAR(50)
);
COPY cases_product_name(id, value) FROM '/docker-entrypoint-initdb.d/csv_data/cases_product_name.csv' DELIMITER ',' CSV HEADER;

CREATE TABLE cases_account_name(
  id SERIAL PRIMARY KEY,
  value VARCHAR(255)
);
COPY cases_account_name(id, value) FROM '/docker-entrypoint-initdb.d/csv_data/cases_account_name.csv' DELIMITER ',' CSV HEADER;

CREATE TABLE cases_operational_customer_name(
  id SERIAL PRIMARY KEY,
  value VARCHAR(255)
);
COPY cases_operational_customer_name(id, value) FROM '/docker-entrypoint-initdb.d/csv_data/cases_operational_customer_name.csv' DELIMITER ',' CSV HEADER;

CREATE TABLE cases_product_release(
  id SERIAL PRIMARY KEY,
  value VARCHAR(100)
);
COPY cases_product_release(id, value) FROM '/docker-entrypoint-initdb.d/csv_data/cases_product_release.csv' DELIMITER ',' CSV HEADER;

CREATE TABLE cases_support_ticket_owner(
  id SERIAL PRIMARY KEY,
  value VARCHAR(100)
);
COPY cases_support_ticket_owner(id, value) FROM '/docker-entrypoint-initdb.d/csv_data/cases_support_ticket_owner.csv' DELIMITER ',' CSV HEADER;

CREATE TABLE cases_contact_name(
  id SERIAL PRIMARY KEY,
  value VARCHAR(100)
);
COPY cases_contact_name(id, value) FROM '/docker-entrypoint-initdb.d/csv_data/cases_contact_name.csv' DELIMITER ',' CSV HEADER;

CREATE TABLE cases_current_workgroup(
  id SERIAL PRIMARY KEY,
  value VARCHAR(50)
);
COPY cases_current_workgroup(id, value) FROM '/docker-entrypoint-initdb.d/csv_data/cases_current_workgroup.csv' DELIMITER ',' CSV HEADER;

/*Main case table, with foreign keys to all other tables*/
CREATE TABLE cases(
  id SERIAL PRIMARY KEY,
  support_ticket_number integer,
  severity smallint REFERENCES cases_severity(id),
  assessed_outage smallint REFERENCES cases_assessed_outage(id),
  status smallint REFERENCES cases_status(id),
  account_name smallint REFERENCES cases_account_name(id),
  operational_customer_name smallint REFERENCES cases_operational_customer_name(id),
  product_name smallint REFERENCES cases_product_name(id),
  product_release smallint REFERENCES cases_product_release(id),
  subject text,
  description text,
  technical_analysis text,
  temporary_solution text,
  solution_details text,
  support_ticket_owner smallint REFERENCES cases_support_ticket_owner(id),
  contact_name smallint REFERENCES cases_contact_name(id),
  date_time_opened timestamp,
  date_time_closed timestamp,
  current_workgroup smallint REFERENCES cases_current_workgroup(id),
  legacy_case_number VARCHAR(30),
  problem integer,
  recovery_actions text,
  summary_of_analysis text,
  root_cause_description text,
  r_d_reference text,
  target_release text
);

COPY cases(support_ticket_number, severity, assessed_outage, status, account_name, operational_customer_name, product_name, product_release, subject, description, technical_analysis, temporary_solution, solution_details, support_ticket_owner, contact_name, date_time_opened, date_time_closed, current_workgroup, legacy_case_number, problem, recovery_actions, summary_of_analysis, root_cause_description, r_d_reference, target_release) FROM '/docker-entrypoint-initdb.d/csv_data/cases.csv' DELIMITER ',' CSV HEADER;

/*Table for fulltext search vectors*/
CREATE TABLE cases_tsvector_sum(
  id integer REFERENCES cases(id),
  value tsvector
);

/*Fill table with vectors*/
INSERT INTO cases_tsvector_sum ( SELECT cases.id, to_tsvector(CAST(support_ticket_number AS text)) || to_tsvector(COALESCE(cases.subject, '')) || to_tsvector(COALESCE(cases.description, '')) || to_tsvector(COALESCE(cases.technical_analysis, '')) || to_tsvector(COALESCE(cases.temporary_solution, '')) || to_tsvector(COALESCE(cases.solution_details, '')) || to_tsvector(COALESCE(cases.recovery_actions, '')) || to_tsvector(COALESCE(cases.summary_of_analysis, '')) || to_tsvector(COALESCE(cases.root_cause_description, '')) FROM cases);

/*Create index under vectors for fast search*/
CREATE INDEX idx_gin_ts_vector_sum ON cases_tsvector_sum USING gin ("value");

/*Table with user acccounts to access the system*/
CREATE TABLE cases_engineers(
  id SERIAL PRIMARY KEY,
  login VARCHAR(50),
  password VARCHAR(50)
);
COPY cases_engineers (id, login, password) FROM '/docker-entrypoint-initdb.d/csv_data/cases_engineers.csv' DELIMITER ',' CSV HEADER;
