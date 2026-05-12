export interface Trade {
  id: string
  date: string
  stockCode: string
  stockName: string
  type: 'buy' | 'sell'
  price: number
  quantity: number
  amount: number
  fee: number
  reason: string
  emotion: 'calm' | 'excited' | 'anxious' | 'fear' | 'greedy'
  tags: string[]
}

export interface Reflection {
  id: string
  date: string
  title: string
  content: string
  category: 'market' | 'stock' | 'strategy' | 'psychology' | 'other'
  tags: string[]
  linkedTrades?: string[]
}

export interface Strategy {
  id: string
  date: string
  title: string
  content: string
  type: 'entry' | 'exit' | 'risk' | 'position' | 'general'
  effectiveness: 1 | 2 | 3 | 4 | 5
  notes: string
  relatedReflections?: string[]
}

export type TabType = 'trades' | 'reflections' | 'strategies'