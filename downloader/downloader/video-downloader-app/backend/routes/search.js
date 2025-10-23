import express from 'express';
import { searchYouTube, searchSoundCloud } from '../utils/pythonExecutor.js';
import db from '../config/database.js';

const router = express.Router();

router.post('/youtube', async (req, res) => {
  try {
    const { query, page = 1 } = req.body;

    if (!query) {
      return res.status(400).json({ error: 'Search query is required' });
    }

    const result = await searchYouTube(query, page);

    await db.query(
      'INSERT INTO search_history (query, platform, results_count) VALUES (?, ?, ?)',
      [query, 'youtube', result.data?.items?.length || 0]
    );

    res.json(result);
  } catch (error) {
    console.error('YouTube search error:', error);
    res.status(500).json({
      error: error.message,
      data: { items: [], is_next_page: false }
    });
  }
});

router.post('/soundcloud', async (req, res) => {
  try {
    const { query, page = 1 } = req.body;

    if (!query) {
      return res.status(400).json({ error: 'Search query is required' });
    }

    const result = await searchSoundCloud(query, page);

    await db.query(
      'INSERT INTO search_history (query, platform, results_count) VALUES (?, ?, ?)',
      [query, 'soundcloud', result.data?.items?.length || 0]
    );

    res.json(result);
  } catch (error) {
    console.error('SoundCloud search error:', error);
    res.status(500).json({
      error: error.message,
      data: { items: [], is_next_page: false }
    });
  }
});

export default router;
