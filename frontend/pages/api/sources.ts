import type { NextApiRequest, NextApiResponse } from 'next'

const BACKEND = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'POST') {
    res.status(405).json({ error: 'Method not allowed' })
    return
  }

  try {
    const upstream = await fetch(`${BACKEND}/api/ai/search_and_cite`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req.body),
    })

    const data = await upstream.json()
    if (data.sources) {
      res.status(200).json({ sources: data.sources })
    } else if (data.results) {
      res.status(200).json({ sources: data.results })
    } else {
      res.status(200).json({ sources: data.sources || data })
    }
  } catch (err: any) {
    res.status(500).json({ error: err.message || String(err) })
  }
}
