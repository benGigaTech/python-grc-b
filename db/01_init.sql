-- init.sql

CREATE TABLE IF NOT EXISTS users (
    userid SERIAL PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    isadmin INTEGER NOT NULL DEFAULT 0,
    email TEXT,
    resettoken TEXT,
    tokenexpiration TEXT
);

CREATE TABLE IF NOT EXISTS controls (
    controlid TEXT PRIMARY KEY,
    controlname TEXT NOT NULL,
    controldescription TEXT,
    nist_sp_800_171_mapping TEXT,
    policyreviewfrequency TEXT,
    lastreviewdate TEXT,
    nextreviewdate TEXT
);

CREATE TABLE IF NOT EXISTS tasks (
    taskid SERIAL PRIMARY KEY,
    controlid TEXT NOT NULL,
    taskdescription TEXT NOT NULL,
    assignedto TEXT,
    duedate TEXT,
    status TEXT,
    confirmed INTEGER DEFAULT 0,
    reviewer TEXT,
    FOREIGN KEY (controlid) REFERENCES controls(controlid)
);

CREATE TABLE IF NOT EXISTS auditlogs (
    logid SERIAL PRIMARY KEY,
    timestamp TEXT NOT NULL,
    username TEXT NOT NULL,
    action TEXT NOT NULL,
    objecttype TEXT NOT NULL,
    objectid TEXT,
    details TEXT
); 