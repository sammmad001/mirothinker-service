import React, { useState } from 'react'
import { Plus, TrendingUp, TrendingDown, Calendar, DollarSign, Tag, MessageSquare, Edit2, Trash2 } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { Trade } from '@/types'
import { formatDate, formatCurrency } from '@/lib/utils'

interface TradingLogPageProps {
  trades: Trade[]
  onAddTrade: (trade: Trade) => void
  onDeleteTrade: (id: string) => void
}

const emotionLabels: Record<string, { label: string; color: string }> = {
  calm: { label: '平静', color: 'bg-slate-100 text-slate-700' },
  excited: { label: '兴奋', color: 'bg-amber-100 text-amber-700' },
  anxious: { label: '焦虑', color: 'bg-orange-100 text-orange-700' },
  fear: { label: '恐惧', color: 'bg-red-100 text-red-700' },
  greedy: { label: '贪婪', color: 'bg-purple-100 text-purple-700' },
}

export function TradingLogPage({ trades, onAddTrade, onDeleteTrade }: TradingLogPageProps) {
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [editingTrade, setEditingTrade] = useState<Trade | null>(null)
  const [formData, setFormData] = useState({
    stockCode: '',
    stockName: '',
    type: 'buy' as 'buy' | 'sell',
    price: '',
    quantity: '',
    reason: '',
    emotion: 'calm' as Trade['emotion'],
    tags: '',
  })

  const handleSubmit = () => {
    const price = parseFloat(formData.price)
    const quantity = parseInt(formData.quantity)
    const amount = price * quantity
    const fee = amount * 0.0003

    const trade: Trade = {
      id: editingTrade?.id || Date.now().toString(),
      date: editingTrade?.date || new Date().toISOString(),
      stockCode: formData.stockCode,
      stockName: formData.stockName,
      type: formData.type,
      price,
      quantity,
      amount,
      fee,
      reason: formData.reason,
      emotion: formData.emotion,
      tags: formData.tags.split(',').map(t => t.trim()).filter(Boolean),
    }

    onAddTrade(trade)
    resetForm()
  }

  const resetForm = () => {
    setIsDialogOpen(false)
    setEditingTrade(null)
    setFormData({
      stockCode: '',
      stockName: '',
      type: 'buy',
      price: '',
      quantity: '',
      reason: '',
      emotion: 'calm',
      tags: '',
    })
  }

  const handleEdit = (trade: Trade) => {
    setEditingTrade(trade)
    setFormData({
      stockCode: trade.stockCode,
      stockName: trade.stockName,
      type: trade.type,
      price: trade.price.toString(),
      quantity: trade.quantity.toString(),
      reason: trade.reason,
      emotion: trade.emotion,
      tags: trade.tags.join(', '),
    })
    setIsDialogOpen(true)
  }

  const stats = {
    totalTrades: trades.length,
    buyTrades: trades.filter(t => t.type === 'buy').length,
    sellTrades: trades.filter(t => t.type === 'sell').length,
    totalAmount: trades.reduce((sum, t) => sum + t.amount, 0),
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">交易记录</h2>
          <p className="text-muted-foreground mt-1">记录每一笔交易，追踪买卖逻辑</p>
        </div>
        <Button onClick={() => setIsDialogOpen(true)} className="gap-2">
          <Plus className="h-4 w-4" />
          记录交易
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-blue-100">
                <TrendingUp className="h-5 w-5 text-blue-600" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">买入</p>
                <p className="text-xl font-bold">{stats.buyTrades}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-red-100">
                <TrendingDown className="h-5 w-5 text-red-600" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">卖出</p>
                <p className="text-xl font-bold">{stats.sellTrades}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-purple-100">
                <DollarSign className="h-5 w-5 text-purple-600" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">总交易额</p>
                <p className="text-xl font-bold">{formatCurrency(stats.totalAmount)}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-green-100">
                <Calendar className="h-5 w-5 text-green-600" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">记录总数</p>
                <p className="text-xl font-bold">{stats.totalTrades}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="space-y-4">
        {trades.length === 0 ? (
          <Card className="py-12">
            <CardContent className="flex flex-col items-center justify-center text-center">
              <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center mb-4">
                <TrendingUp className="h-8 w-8 text-muted-foreground" />
              </div>
              <h3 className="text-lg font-medium mb-2">暂无交易记录</h3>
              <p className="text-muted-foreground mb-4">开始记录你的第一笔交易吧</p>
              <Button onClick={() => setIsDialogOpen(true)}>
                <Plus className="h-4 w-4 mr-2" />
                记录交易
              </Button>
            </CardContent>
          </Card>
        ) : (
          trades.map(trade => (
            <Card key={trade.id} className="hover:shadow-md transition-shadow">
              <CardContent className="pt-6">
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-4">
                    <div className={`p-3 rounded-xl ${trade.type === 'buy' ? 'bg-green-100' : 'bg-red-100'}`}>
                      {trade.type === 'buy' ? (
                        <TrendingUp className={`h-6 w-6 ${trade.type === 'buy' ? 'text-green-600' : 'text-red-600'}`} />
                      ) : (
                        <TrendingDown className={`h-6 w-6 text-red-600`} />
                      )}
                    </div>
                    <div className="space-y-1">
                      <div className="flex items-center gap-3">
                        <h3 className="text-lg font-semibold">{trade.stockName}</h3>
                        <Badge variant={trade.type === 'buy' ? 'buy' : 'sell'}>
                          {trade.type === 'buy' ? '买入' : '卖出'}
                        </Badge>
                        <span className="text-sm text-muted-foreground font-mono">{trade.stockCode}</span>
                      </div>
                      <div className="flex items-center gap-4 text-sm text-muted-foreground">
                        <span className="flex items-center gap-1">
                          <Calendar className="h-4 w-4" />
                          {formatDate(new Date(trade.date))}
                        </span>
                        <span className="flex items-center gap-1">
                          <DollarSign className="h-4 w-4" />
                          {formatCurrency(trade.price)} x {trade.quantity} = {formatCurrency(trade.amount)}
                        </span>
                      </div>
                      {trade.reason && (
                        <p className="text-sm mt-2 flex items-start gap-2">
                          <MessageSquare className="h-4 w-4 mt-0.5 flex-shrink-0 text-muted-foreground" />
                          {trade.reason}
                        </p>
                      )}
                      <div className="flex items-center gap-2 mt-2">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${emotionLabels[trade.emotion]?.color}`}>
                          {emotionLabels[trade.emotion]?.label}
                        </span>
                        {trade.tags.map(tag => (
                          <Badge key={tag} variant="secondary" className="text-xs">
                            <Tag className="h-3 w-3 mr-1" />
                            {tag}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button variant="ghost" size="icon" onClick={() => handleEdit(trade)}>
                      <Edit2 className="h-4 w-4" />
                    </Button>
                    <Button variant="ghost" size="icon" onClick={() => onDeleteTrade(trade.id)}>
                      <Trash2 className="h-4 w-4 text-destructive" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>

      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>{editingTrade ? '编辑交易' : '记录交易'}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="stockCode">股票代码</Label>
                <Input
                  id="stockCode"
                  placeholder="如: 600519"
                  value={formData.stockCode}
                  onChange={e => setFormData({ ...formData, stockCode: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="stockName">股票名称</Label>
                <Input
                  id="stockName"
                  placeholder="如: 贵州茅台"
                  value={formData.stockName}
                  onChange={e => setFormData({ ...formData, stockName: e.target.value })}
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>交易类型</Label>
                <Select value={formData.type} onValueChange={(v: 'buy' | 'sell') => setFormData({ ...formData, type: v })}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="buy">买入</SelectItem>
                    <SelectItem value="sell">卖出</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>交易情绪</Label>
                <Select value={formData.emotion} onValueChange={(v: Trade['emotion']) => setFormData({ ...formData, emotion: v })}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="calm">平静</SelectItem>
                    <SelectItem value="excited">兴奋</SelectItem>
                    <SelectItem value="anxious">焦虑</SelectItem>
                    <SelectItem value="fear">恐惧</SelectItem>
                    <SelectItem value="greedy">贪婪</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="price">成交价格</Label>
                <Input
                  id="price"
                  type="number"
                  step="0.01"
                  placeholder="0.00"
                  value={formData.price}
                  onChange={e => setFormData({ ...formData, price: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="quantity">成交数量</Label>
                <Input
                  id="quantity"
                  type="number"
                  placeholder="100"
                  value={formData.quantity}
                  onChange={e => setFormData({ ...formData, quantity: e.target.value })}
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="reason">交易逻辑</Label>
              <Textarea
                id="reason"
                placeholder="为什么买/卖？这笔交易的依据是什么？"
                value={formData.reason}
                onChange={e => setFormData({ ...formData, reason: e.target.value })}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="tags">标签</Label>
              <Input
                id="tags"
                placeholder="用逗号分隔，如: 价值投资, 抄底"
                value={formData.tags}
                onChange={e => setFormData({ ...formData, tags: e.target.value })}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={resetForm}>取消</Button>
            <Button onClick={handleSubmit} disabled={!formData.stockCode || !formData.price || !formData.quantity}>
              {editingTrade ? '保存修改' : '确认记录'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}