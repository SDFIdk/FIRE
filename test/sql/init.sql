-- Create user fire with password fire
CREATE USER fire IDENTIFIED BY fire;

-- Grant
GRANT create session TO fire;
GRANT create table TO fire;
GRANT create view TO fire;
GRANT create any trigger TO fire;
GRANT create any procedure TO fire;
GRANT create sequence TO fire;
GRANT create synonym TO fire;

GRANT UNLIMITED TABLESPACE TO fire;