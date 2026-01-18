-- Add readings table
CREATE TABLE IF NOT EXISTS readings (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	sensor_id INTEGER NOT NULL,
	value REAL NOT NULL,
	timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
	FOREIGN KEY (sensor_id) REFERENCES sensors(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_readings_sensor_id ON readings(sensor_id);
CREATE INDEX IF NOT EXISTS idx_readings_timestamp ON readings(timestamp);
