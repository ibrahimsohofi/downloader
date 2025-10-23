import mysql from 'mysql2';
import dotenv from 'dotenv';

dotenv.config();

// In-memory storage as fallback
let inMemoryStorage = {
  searchHistory: [],
  downloadHistory: []
};

let pool = null;
let promisePool = null;

// Try to connect to MySQL if configured
if (process.env.DB_HOST || process.env.USE_DATABASE === 'true') {
  try {
    pool = mysql.createPool({
      host: process.env.DB_HOST || 'localhost',
      user: process.env.DB_USER || 'root',
      password: process.env.DB_PASSWORD || '',
      database: process.env.DB_NAME || 'video_downloader',
      waitForConnections: true,
      connectionLimit: 10,
      queueLimit: 0
    });
    promisePool = pool.promise();
    console.log('Database connection configured');
  } catch (error) {
    console.warn('Database not configured, using in-memory storage:', error.message);
  }
}

// Wrapper that falls back to in-memory storage
const db = {
  async query(sql, params) {
    if (promisePool) {
      try {
        return await promisePool.query(sql, params);
      } catch (error) {
        console.warn('Database query failed, using in-memory storage:', error.message);
      }
    }

    // In-memory fallback
    if (sql.includes('search_history')) {
      if (sql.startsWith('INSERT')) {
        const id = inMemoryStorage.searchHistory.length + 1;
        inMemoryStorage.searchHistory.push({ id, query: params[0], platform: params[1], results_count: params[2], created_at: new Date() });
        return [[{ insertId: id }]];
      }
    } else if (sql.includes('download_history')) {
      if (sql.startsWith('INSERT')) {
        const id = inMemoryStorage.downloadHistory.length + 1;
        const record = {
          id,
          url: params[0],
          title: params[1],
          thumbnail: params[2],
          platform: params[3],
          video_id: params[4],
          status: params[5] || 'pending',
          created_at: new Date()
        };
        inMemoryStorage.downloadHistory.push(record);
        return [[{ insertId: id }]];
      } else if (sql.startsWith('SELECT')) {
        return [inMemoryStorage.downloadHistory.reverse()];
      } else if (sql.startsWith('UPDATE')) {
        const id = params[params.length - 1];
        const item = inMemoryStorage.downloadHistory.find(h => h.id === id);
        if (item) {
          if (sql.includes('status')) item.status = params[0];
          if (sql.includes('file_path')) item.file_path = params[0];
          if (sql.includes('error_message')) item.error_message = params[0];
        }
        return [[{ affectedRows: 1 }]];
      }
    }
    return [[]];
  }
};

export default db;
