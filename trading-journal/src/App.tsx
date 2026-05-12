import React, { useState, useEffect } from 'react'
import { TrendingUp, Brain, Target, BarChart3 } from 'lucide-react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { TradingLogPage } from '@/pages/TradingLogPage'
import { ReflectionPage } from '@/pages/ReflectionPage'
import { StrategyPage } from '@/pages/StrategyPage'
import { Trade, Reflection, Strategy } from '@/types'

const STORAGE_KEY = 'trading-journal-data'

interface StoredData {
  trades: Trade[]
  reflections: Reflection[]
  strategies: Strategy[]
}

function App() {
  const [trades, setTrades] = useState<Trade[]>([])
  const [reflections, setReflections] = useState<Reflection[]>([])
  const [strategies, setStrategies] = useState<Strategy[]>([])
  const [isLoaded, setIsLoaded] = useState(false)

  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) {
      try {
        const data: StoredData = JSON.parse(stored)
        setTrades(data.trades || [])
        setReflections(data.reflections || [])
        setStrategies(data.strategies || [])
      } catch (e) {
        console.error('Failed to load data:', e)
      }
    }
    setIsLoaded(true)
  }, [])

  useEffect(() => {
    if (isLoaded) {
      const data: StoredData = { trades, reflections, strategies }
      localStorage.setItem(STORAGE_KEY, JSON.stringify(data))
    }
  }, [trades, reflections, strategies, isLoaded])

  const handleAddTrade = (trade: Trade) => {
    const existingIndex = trades.findIndex(t => t.id === trade.id)
    if (existingIndex >= 0) {
      setTrades(prev => prev.map(t => t.id === trade.id ? trade : t))
    } else {
      setTrades(prev => [trade, ...prev])
    }
  }

  const handleDeleteTrade = (id: string) => {
    setTrades(prev => prev.filter(t => t.id !== id))
  }

  const handleAddReflection = (reflection: Reflection) => {
    const existingIndex = reflections.findIndex(r => r.id === reflection.id)
    if (existingIndex >= 0) {
      setReflections(prev => prev.map(r => r.id === reflection.id ? reflection : r))
    } else {
      setReflections(prev => [reflection, ...prev])
    }
  }

  const handleDeleteReflection = (id: string) => {
    setReflections(prev => prev.filter(r => r.id !== id))
  }

  const handleAddStrategy = (strategy: Strategy) => {
    const existingIndex = strategies.findIndex(s => s.id === strategy.id)
    if (existingIndex >= 0) {
      setStrategies(prev => prev.map(s => s.id === strategy.id ? strategy : s))
    } else {
      setStrategies(prev => [strategy, ...prev])
    }
  }

  const handleDeleteStrategy = (id: string) => {
    setStrategies(prev => prev.filter(s => s.id !== id))
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      <header className="border-b bg-white/80 dark:bg-slate-900/80 backdrop-blur-md sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600">
              <BarChart3 className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold">交易日志</h1>
              <p className="text-xs text-muted-foreground">投资思想沉淀与策略提炼</p>
            </div>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-6">
        <Tabs defaultValue="trades" className="space-y-6">
          <TabsList className="grid w-full grid-cols-3 max-w-md">
            <TabsTrigger value="trades" className="gap-2">
              <TrendingUp className="h-4 w-4" />
              交易记录
            </TabsTrigger>
            <TabsTrigger value="reflections" className="gap-2">
              <Brain className="h-4 w-4" />
              投资复盘
            </TabsTrigger>
            <TabsTrigger value="strategies" className="gap-2">
              <Target className="h-4 w-4" />
              策略提炼
            </TabsTrigger>
          </TabsList>

          <TabsContent value="trades" className="animate-fade-in">
            <TradingLogPage
              trades={trades}
              onAddTrade={handleAddTrade}
              onDeleteTrade={handleDeleteTrade}
            />
          </TabsContent>

          <TabsContent value="reflections" className="animate-fade-in">
            <ReflectionPage
              reflections={reflections}
              onAddReflection={handleAddReflection}
              onDeleteReflection={handleDeleteReflection}
            />
          </TabsContent>

          <TabsContent value="strategies" className="animate-fade-in">
            <StrategyPage
              strategies={strategies}
              onAddStrategy={handleAddStrategy}
              onDeleteStrategy={handleDeleteStrategy}
            />
          </TabsContent>
        </Tabs>
      </main>

      <footer className="border-t mt-12 py-6 text-center text-sm text-muted-foreground">
        <p>数据仅保存在本地浏览器中</p>
      </footer>
    </div>
  )
}

export default App