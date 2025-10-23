import express from 'express';
import db from '../config/database.js';

const router = express.Router();

router.get('/downloads', async (req, res) => {
  try {
    const { limit = 20, offset = 0 } = req.query;

    const [rows] = await db.query(
      'SELECT * FROM downloads ORDER BY created_at DESC LIMIT ? OFFSET ?',
      [parseInt(limit), parseInt(offset)]
    );

    const [countResult] = await db.query('SELECT COUNT(*) as total FROM downloads');
    const total = countResult[0].total;

    res.json({
      downloads: rows,
      total,
      limit: parseInt(limit),
      offset: parseInt(offset)
    });
  } catch (error) {
    console.error('Download history error:', error);
    res.status(500).json({ error: error.message });
  }
});

router.get('/searches', async (req, res) => {
  try {
    const { limit = 20, offset = 0 } = req.query;

    const [rows] = await db.query(
      'SELECT * FROM search_history ORDER BY created_at DESC LIMIT ? OFFSET ?',
      [parseInt(limit), parseInt(offset)]
    );

    const [countResult] = await db.query('SELECT COUNT(*) as total FROM search_history');
    const total = countResult[0].total;

    res.json({
      searches: rows,
      total,
      limit: parseInt(limit),
      offset: parseInt(offset)
    });
  } catch (error) {
    console.error('Search history error:', error);
    res.status(500).json({ error: error.message });
  }
});

router.delete('/downloads/:id', async (req, res) => {
  try {
    const { id } = req.params;
    await db.query('DELETE FROM downloads WHERE id = ?', [id]);
    res.json({ success: true, message: 'Download deleted' });
  } catch (error) {
    console.error('Delete error:', error);
    res.status(500).json({ error: error.message });
  }
});

export default router;
