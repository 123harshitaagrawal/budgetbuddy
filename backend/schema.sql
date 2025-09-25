CREATE TABLE IF NOT EXISTS users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(255) UNIQUE NOT NULL,
  password VARCHAR(255) NULL,
  password_hash VARCHAR(255) NULL
);

CREATE TABLE IF NOT EXISTS expenses (
  id INT AUTO_INCREMENT PRIMARY KEY,
  amount DECIMAL(10,2) NOT NULL,
  category VARCHAR(255) NOT NULL,
  date DATE NOT NULL,
  split_user_ids TEXT NULL,
  user_share DECIMAL(10,2) NOT NULL,
  user_id INT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_expenses_user_date (user_id, date),
  CONSTRAINT fk_expenses_user FOREIGN KEY (user_id) REFERENCES users(id)
);


