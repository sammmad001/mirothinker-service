import React, { useState } from 'react'
import { Plus, Brain, Calendar, Tag, Edit2, Trash2, BookOpen, TrendingUp, Users, Lightbulb } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { Reflection } from '@/types'
import { formatDate } from '@/lib/utils'

interface ReflectionPageProps {
  reflections: Reflection[]
  onAddReflection: (reflection: Reflection) => void
  onDeleteReflection: (id: string) => void
}

const categoryConfig: Record<string, { label: string; icon: React.ElementType; color: string; bgColor: string }> = {
  market: { label: '市场分析', icon: TrendingUp, color: 'text-blue-600', bgColor: 'bg-blue-100' },
  stock: { label: '个股研究', icon: Users, color: 'text-purple-600', bgColor: 'bg-purple-100' },
  strategy: { label: '策略思考', icon: Lightbulb, color: 'text-amber-600', bgColor: 'bg-amber-100' },
  psychology: { label: '投资心理', icon: Brain, color: 'text-pink-600', bgColor: 'bg-pink-100' },
  other: { label: '其他思考', icon: BookOpen, color: 'text-gray-600', bgColor: 'bg-gray-100' },
}

export function ReflectionPage({ reflections, onAddReflection, onDeleteReflection }: ReflectionPageProps) {
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [editingReflection, setEditingReflection] = useState<Reflection | null>(null)
  const [formData, setFormData] = useState({
    title: '',
    content: '',
    category: 'other' as Reflection['category'],
    tags: '',
  })

  const handleSubmit = () => {
    const reflection: Reflection = {
      id: editingReflection?.id || Date.now().toString(),
      date: editingReflection?.date || new Date().toISOString(),
      title: formData.title,
      content: formData.content,
      category: formData.category,
      tags: formData.tags.split(',').map(t => t.trim()).filter(Boolean),
    }

    onAddReflection(reflection)
    resetForm()
  }

  const resetForm = () => {
    setIsDialogOpen(false)
    setEditingReflection(null)
    setFormData({
      title: '',
      content: '',
      category: 'other',
      tags: '',
    })
  }

  const handleEdit = (reflection: Reflection) => {
    setEditingReflection(reflection)
    setFormData({
      title: reflection.title,
      content: reflection.content,
      category: reflection.category,
      tags: reflection.tags.join(', '),
    })
    setIsDialogOpen(true)
  }

  const stats = {
    totalReflections: reflections.length,
    marketReflections: reflections.filter(r => r.category === 'market').length,
    strategyReflections: reflections.filter(r => r.category === 'strategy').length,
    psychologyReflections: reflections.filter(r => r.category === 'psychology').length,
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">投资复盘</h2>
          <p className="text-muted-foreground mt-1">记录你的市场观察、个股分析和投资思考</p>
        </div>
        <Button onClick={() => setIsDialogOpen(true)} className="gap-2">
          <Plus className="h-4 w-4" />
          写下思考
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-indigo-100">
                <BookOpen className="h-5 w-5 text-indigo-600" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">思考总数</p>
                <p className="text-xl font-bold">{stats.totalReflections}</p>
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
                <p className="text-sm text-muted-foreground">市场分析</p>
                <p className="text-xl font-bold">{stats.marketReflections}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-amber-100">
                <Lightbulb className="h-5 w-5 text-amber-600" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">策略思考</p>
                <p className="text-xl font-bold">{stats.strategyReflections}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-pink-100">
                <Brain className="h-5 w-5 text-pink-600" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">投资心理</p>
                <p className="text-xl font-bold">{stats.psychologyReflections}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="space-y-4">
        {reflections.length === 0 ? (
          <Card className="py-12">
            <CardContent className="flex flex-col items-center justify-center text-center">
              <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center mb-4">
                <Brain className="h-8 w-8 text-muted-foreground" />
              </div>
              <h3 className="text-lg font-medium mb-2">暂无投资思考</h3>
              <p className="text-muted-foreground mb-4">记录你对市场的观察和投资逻辑的思考</p>
              <Button onClick={() => setIsDialogOpen(true)}>
                <Plus className="h-4 w-4 mr-2" />
                写下思考
              </Button>
            </CardContent>
          </Card>
        ) : (
          reflections.map(reflection => {
            const config = categoryConfig[reflection.category]
            const Icon = config.icon
            return (
              <Card key={reflection.id} className="hover:shadow-md transition-shadow">
                <CardContent className="pt-6">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-4">
                      <div className={`p-3 rounded-xl ${config.bgColor}`}>
                        <Icon className={`h-6 w-6 ${config.color}`} />
                      </div>
                      <div className="space-y-2 flex-1">
                        <div className="flex items-center gap-3">
                          <h3 className="text-lg font-semibold">{reflection.title}</h3>
                          <Badge variant="secondary">{config.label}</Badge>
                        </div>
                        <p className="text-sm text-muted-foreground flex items-center gap-1">
                          <Calendar className="h-4 w-4" />
                          {formatDate(new Date(reflection.date))}
                        </p>
                        <p className="text-sm leading-relaxed">{reflection.content}</p>
                        {reflection.tags.length > 0 && (
                          <div className="flex items-center gap-2 flex-wrap">
                            {reflection.tags.map(tag => (
                              <Badge key={tag} variant="outline" className="text-xs">
                                <Tag className="h-3 w-3 mr-1" />
                                {tag}
                              </Badge>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button variant="ghost" size="icon" onClick={() => handleEdit(reflection)}>
                        <Edit2 className="h-4 w-4" />
                      </Button>
                      <Button variant="ghost" size="icon" onClick={() => onDeleteReflection(reflection.id)}>
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
            <DialogTitle>{editingReflection ? '编辑思考' : '写下你的思考'}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="title">标题</Label>
              <Input
                id="title"
                placeholder="如: 对当前市场走势的观察"
                value={formData.title}
                onChange={e => setFormData({ ...formData, title: e.target.value })}
              />
            </div>

            <div className="space-y-2">
              <Label>分类</Label>
              <Select value={formData.category} onValueChange={(v: Reflection['category']) => setFormData({ ...formData, category: v })}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="market">市场分析</SelectItem>
                  <SelectItem value="stock">个股研究</SelectItem>
                  <SelectItem value="strategy">策略思考</SelectItem>
                  <SelectItem value="psychology">投资心理</SelectItem>
                  <SelectItem value="other">其他思考</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="content">内容</Label>
              <Textarea
                id="content"
                placeholder="详细记录你的思考、分析和洞察..."
                className="min-h-[150px]"
                value={formData.content}
                onChange={e => setFormData({ ...formData, content: e.target.value })}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="tags">标签</Label>
              <Input
                id="tags"
                placeholder="用逗号分隔，如: 趋势, 科技股"
                value={formData.tags}
                onChange={e => setFormData({ ...formData, tags: e.target.value })}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={resetForm}>取消</Button>
            <Button onClick={handleSubmit} disabled={!formData.title || !formData.content}>
              {editingReflection ? '保存修改' : '确认提交'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}