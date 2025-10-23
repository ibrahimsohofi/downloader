CREATE DATABASE IF NOT EXISTS video_downloader;
USE video_downloader;

CREATE TABLE IF NOT EXISTS downloads (
  id INT AUTO_INCREMENT PRIMARY KEY,
  video_id VARCHAR(255) NOT NULL,
  title VARCHAR(500) NOT NULL,
  thumbnail VARCHAR(1000),
  url VARCHAR(1000) NOT NULL,
  platform VARCHAR(50) NOT NULL,
  duration VARCHAR(50),
  view_count VARCHAR(50),
  download_status VARCHAR(50) DEFAULT 'pending',
  file_path VARCHAR(1000),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_video_id (video_id),
  INDEX idx_platform (platform),
  INDEX idx_created_at (created_at)
);

CREATE TABLE IF NOT EXISTS search_history (
  id INT AUTO_INCREMENT PRIMARY KEY,
  query VARCHAR(500) NOT NULL,
  platform VARCHAR(50) NOT NULL,
  results_count INT DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_platform (platform),
  INDEX idx_created_at (created_at)
);
