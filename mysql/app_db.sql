USE drive_inventory_db;

CREATE TABLE IF NOT EXISTS files (
	id VARCHAR(255) PRIMARY KEY,
	name VARCHAR(255) NOT NULL,
	extension VARCHAR(255),
	owner VARCHAR(255) NOT NULL,
	visibility ENUM('public', 'private') NOT NULL,
	last_modified DATETIME
);

 CREATE TABLE IF NOT EXISTS public_files_history (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    extension VARCHAR(255),
    owner VARCHAR(255) NOT NULL,
    visibility ENUM('public', 'private') NOT NULL,
    last_modified DATETIME
);