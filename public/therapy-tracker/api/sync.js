// Vercel Serverless Function for therapy data sync using Blob storage
import { put, list } from '@vercel/blob';

const DATA_KEY = 'therapy-tracker-data.json';

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }
  
  try {
    if (req.method === 'GET') {
      // Find and load data from Blob
      try {
        const { blobs } = await list();
        const dataBlob = blobs.find(b => b.pathname === DATA_KEY);
        
        if (dataBlob) {
          const response = await fetch(dataBlob.url);
          if (response.ok) {
            const data = await response.json();
            return res.status(200).json({ data });
          }
        }
      } catch (e) {
        console.error('Load error:', e);
      }
      return res.status(200).json({ data: {} });
      
    } else if (req.method === 'POST') {
      // Save data to Blob
      const { data } = req.body;
      if (!data) {
        return res.status(400).json({ error: 'No data provided' });
      }
      
      await put(DATA_KEY, JSON.stringify(data), {
        access: 'public',
        addRandomSuffix: false,
      });
      
      return res.status(200).json({ success: true });
    }
    
    return res.status(405).json({ error: 'Method not allowed' });
    
  } catch (error) {
    console.error('Sync error:', error);
    return res.status(500).json({ error: 'Server error', details: error.message });
  }
}
