import React, { useState } from 'react'
import { Plus, Target, Star, Calendar, Edit2, Trash2, CheckCircle, XCircle, AlertTriangle, TrendingUp } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { Strategy } from '@/types'
import { formatDate } from '@/lib/utils'

interface StrategyPageProps {
  strategies: Strategy[]
  onAddStrategy: (strategy: Strategy) => void
  onDeleteStrategy: (id: string) => void
}

const typeConfig: Record<string, { label: string; icon: React.ElementType; color: string; bgColor: string }> = {
  entry: { label: '入场策略', icon: TrendingUp, color: 'text-green-600', bgColor: 'bg-green-100' },
  exit: { label: '出场策略', icon: TrendingUp, color: 'text-red-600', bgColor: 'bg-red-100' },
  risk: { label: '风险控制', icon: AlertTriangle, color: 'text-orange-600', bgColor: 'bg-orange-100' },
  position: { label: '仓位管理', icon: Target, color: 'text-blue-600', bgColor: 'bg-blue-100' },
  general: { label: '综合策略', icon: Target, color: 'text-purple-600', bgColor: 'bg-purple-100' },
}

const effectivenessLabels: Record<number, { label: string; color: string }> = {
  1: { label: '待验证', color: 'text-gray-500' },
  2: { label: '初步有效', color: 'text-blue-500' },
  3: { label: '基本有效', color: 'text-amber-500' },
  4: { label: '非常有效', color: 'text-green-500' },
  5: { label: '高度有效', color: 'text-emerald-500' },
}

function StarRating({ value, onChange }: { value: number; onChange?: (v: number) => void }) {
  return (
    <div className="flex items-center gap-1">
      {[1, 2, 3, 4, 5].map(star => (
        <button
          key={star}
          type="button"
          onClick={() => onChange?.(star)}
          className={`p-0.5 transition-colors ${onChange ? 'cursor-pointer hover:scale-110' : ''}`}
        >
          <Star
            className={`h-5 w-5 ${
              star <= value
                ? 'fill-amber-400 text-amber-400'
                : 'text-gray-300'
            }`}
          />
        </button>
      ))}
    </div>
  )
}

export function StrategyPage({ strategies, onAddStrategy, onDeleteStrategy }: StrategyPageProps) {
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [editingStrategy, setEditingStrategy] = useState<Strategy | null>(null)
  const [formData, setFormData] = useState({
    title: '',
    content: '',
    type: 'general' as Strategy['type'],
    effectiveness: 3 as Strategy['effectiveness'],
    notes: '',
  })

  const handleSubmit = () => {
    const strategy: Strategy = {
      id: editingStrategy?.id || Date.now().toString(),
      date: editingStrategy?.date || new Date().toISOString(),
      title: formData.title,
      content: formData.content,
      type: formData.type,
      effectiveness: formData.effectiveness,
      notes: formData.notes,
    }

    onAddStrategy(strategy)
    resetForm()
  }

  const resetForm = () => {
    setIsDialogOpen(false)
    setEditingStrategy(null)
    setFormData({
      title: '',
      content: '',
      type: 'general',
      effectiveness: 3,
      notes: '',
    })
  }

  const handleEdit = (strategy: Strategy) => {
    setEditingStrategy(strategy)
    setFormData({
      title: strategy.title,
      content: strategy.content,
      type: strategy.type,
      effectiveness: strategy.effectiveness,
      notes: strategy.notes,
    })
    setIsDialogOpen(true)
  }

  const stats = {
    totalStrategies: strategies.length,
    highEffectiveness: strategies.filter(s => s.effectiveness >= 4).length,
    entryStrategies: strategies.filter(s => s.type === 'entry').length,
    riskStrategies: strategies.filter(s => s.type === 'risk').length,
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">策略提炼</h2>
          <p className="text-muted-foreground mt-1">从交易记录和复盘中提炼交易策略</p>
        </div>
        <Button onClick={() => setIsDialogOpen(true)} className="gap-2">
          <Plus className="h-4 w-4" />
          添加策略
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-purple-100">
                <Target className="h-5 w-5 text-purple-600" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">策略总数</p>
                <p className="text-xl font-bold">{stats.totalStrategies}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-green-100">
                <CheckCircle className="h-5 w-5 text-green-600" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">高效策略</p>
                <p className="text-xl font-bold">{stats.highEffectiveness}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-blue-100">
                <TrendingUp className="h-5 w-5 text-blue-600" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">入场策略</p>
                <p className="text-xl font-bold">{stats.entryStrategies}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-orange-100">
                <AlertTriangle className="h-5 w-5 text-orange-600" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">风险策略</p>
                <p className="text-xl font-bold">{stats.riskStrategies}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="space-y-4">
        {strategies.length === 0 ? (
          <Card className="py-12">
            <CardContent className="flex flex-col items-center justify-center text-center">
              <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center mb-4">
                <Target className="h-8 w-8 text-muted-foreground" />
              </div>
              <h3 className="text-lg font-medium mb-2">暂无交易策略</h3>
              <p className="text-muted-foreground mb-4">从你的交易记录和复盘中提炼出可复用的策略</p>
              <Button onClick={() => setIsDialogOpen(true)}>
                <Plus className="h-4 w-4 mr-2" />
                添加策略
              </Button>
            </CardContent>
          </Card>
        ) : (
          strategies.map(strategy => {
            const config = typeConfig[strategy.type]
            const Icon = config.icon
            const effConfig = effectivenessLabels[strategy.effectiveness]
            return (
              <Card key={strategy.id} className="hover:shadow-md transition-shadow">
                <CardContent className="pt-6">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-4">
                      <div className={`p-3 rounded-xl ${config.bgColor}`}>
                        <Icon className={`h-6 w-6 ${config.color}`} />
                      </div>
                      <div className="space-y-2 flex-1">
                        <div className="flex items-center gap-3">
                          <h3 className="text-lg font-semibold">{strategy.title}</h3>
                          <Badge variant="secondary">{config.label}</Badge>
                        </div>
                        <p className="text-sm text-muted-foreground flex items-center gap-1">
                          <Calendar className="h-4 w-4" />
                          {formatDate(new Date(strategy.date))}
                        </p>
                        <p className="text-sm leading-relaxed">{strategy.content}</p>
                        <div className="flex items-center gap-4">
                          <div className="flex items-center gap-2">
                            <span className="text-sm text-muted-foreground">有效性:</span>
                            <StarRating value={strategy.effectiveness} />
                            <span className={`text-sm font-medium ${effConfig.color}`}>
                              {effConfig.label}
                            </span>
                          </div>
                        </div>
                        {strategy.notes && (
                          <div className="mt-2 p-3 bg-muted/50 rounded-lg">
                            <p className="text-sm text-muted-foreground">备注: {strategy.notes}</p>
                          </div>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button variant="ghost" size="icon" onClick={() => handleEdit(strategy)}>
                        <Edit2 className="h-4 w-4" />
                      </Button>
                      <Button variant="ghost" size="icon" onClick={() => onDeleteStrategy(strategy.id)}>
                        <Trash2 className="h-4 w-4 text-destructive" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )
          })
        )}
      </div>

      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>{editingStrategy ? '编辑策略' : '提炼交易策略'}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="title">策略名称</Label>
              <Input
                id="title"
                placeholder="如: 突破前高买入策略"
                value={formData.title}
                onChange={e => setFormData({ ...formData, title: e.target.value })}
              />
            </div>

            <div className="space-y-2">
              <Label>策略类型</Label>
              <Select value={formData.type} onValueChange={(v: Strategy['type']) => setFormData({ ...formData, type: v })}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="entry">入场策略</SelectItem>
                  <SelectItem value="exit">出场策略</SelectItem>
                  <SelectItem value="risk">风险控制</SelectItem>
                  <SelectItem value="position">仓位管理</SelectItem>
                  <SelectItem value="general">综合策略</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="content">策略描述</Label>
              <Textarea
                id="content"
                placeholder="详细描述这个策略的逻辑和执行条件..."
                className="min-h-[120px]"
                value={formData.content}
                onChange={e => setFormData({ ...formData, content: e.target.value })}
              />
            </div>

            <div className="space-y-2">
              <Label>有效性评估</Label>
              <StarRating
                value={formData.effectiveness}
                onChange={(v) => setFormData({ ...formData, effectiveness: v as Strategy['effectiveness'] })}
              />
              <p className="text-xs text-muted-foreground">根据实际交易结果评估策略的有效性</p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="notes">实践备注</Label>
              <Textarea
                id="notes"
                placeholder="在实际使用这个策略时的注意事项和改进建议..."
                className="min-h-[80px]"
                value={formData.notes}
                onChange={e => setFormData({ ...formData, notes: e.target.value })}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={resetForm}>取消</Button>
            <Button onClick={handleSubmit} disabled={!formData.title || !formData.content}>
              {editingStrategy ? '保存修改' : '确认添加'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}