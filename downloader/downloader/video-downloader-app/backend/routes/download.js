import express from 'express';
import { downloadVideo } from '../utils/pythonExecutor.js';
import db from '../config/database.js';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const router = express.Router();

router.post('/', async (req, res) => {
  try {
    const { url, title, thumbnail, platform, videoId, duration, viewCount } = req.body;

    if (!url) {
      return res.status(400).json({ error: 'Video URL is required' });
    }

    const [result] = await db.query(
      `INSERT INTO downloads (video_id, title, thumbnail, url, platform, duration, view_count, download_status)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
      [videoId || '', title || '', thumbnail || '', url, platform || 'youtube', duration || '', viewCount || '', 'pending']
    );

    const downloadId = result.insertId;

    const outputPath = path.join(__dirname, '../downloads');

    downloadVideo(url, outputPath)
      .then(async (downloadResult) => {
        await db.query(
          'UPDATE downloads SET download_status = ?, file_path = ? WHERE id = ?',
          ['completed', downloadResult.file_path || '', downloadId]
        );
      })
      .catch(async (error) => {
        await db.query(
          'UPDATE downloads SET download_status = ? WHERE id = ?',
          ['failed', downloadId]
        );
      });

    res.json({
      success: true,
      message: 'Download started',
      downloadId
    });
  } catch (error) {
    console.error('Download error:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

router.get('/status/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const [rows] = await db.query('SELECT * FROM downloads WHERE id = ?', [id]);

    if (rows.length === 0) {
      return res.status(404).json({ error: 'Download not found' });
    }

    res.json(rows[0]);
  } catch (error) {
    console.error('Status check error:', error);
    res.status(500).json({ error: error.message });
  }
});

export default router;
