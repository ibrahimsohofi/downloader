import { spawn } from 'child_process';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export function executePythonScript(scriptPath, args = []) {
  return new Promise((resolve, reject) => {
    const pythonProcess = spawn('python3', [scriptPath, ...args]);

    let stdout = '';
    let stderr = '';

    pythonProcess.stdout.on('data', (data) => {
      stdout += data.toString();
    });

    pythonProcess.stderr.on('data', (data) => {
      stderr += data.toString();
    });

    pythonProcess.on('close', (code) => {
      if (code !== 0) {
        reject(new Error(`Python process exited with code ${code}: ${stderr}`));
      } else {
        try {
          const result = JSON.parse(stdout);
          resolve(result);
        } catch (error) {
          resolve(stdout);
        }
      }
    });

    pythonProcess.on('error', (error) => {
      reject(error);
    });
  });
}

export function searchYouTube(query, page = 1) {
  const scriptPath = path.join(__dirname, '../../scripts/youtube_search.py');
  return executePythonScript(scriptPath, [query, page.toString()]);
}

export function searchSoundCloud(query, page = 1) {
  const scriptPath = path.join(__dirname, '../../scripts/soundcloud_search.py');
  return executePythonScript(scriptPath, [query, page.toString()]);
}

export function downloadVideo(url, outputPath) {
  const scriptPath = path.join(__dirname, '../../scripts/download_video.py');
  return executePythonScript(scriptPath, [url, outputPath]);
}
