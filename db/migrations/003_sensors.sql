-- Add sensors table
CREATE TABLE IF NOT EXISTS sensors (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	machine_id INTEGER NOT NULL,
	name TEXT NOT NULL,
	unit TEXT NOT NULL,
	min_threshold REAL,
	max_threshold REAL,
	created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
	FOREIGN KEY (machine_id) REFERENCES machines(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_sensors_machine_id ON sensors(machine_id);
