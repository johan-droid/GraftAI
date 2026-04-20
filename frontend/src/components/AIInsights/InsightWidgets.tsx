/**
 * AI Insight Widgets for Dashboard
 * 
- AI-suggested optimal meeting times
- Conflict predictions
- Productivity score based on calendar patterns
- Resource utilization recommendations
 */

'use client';

import { useState, useEffect } from 'react';
import { Clock, TrendingUp, AlertTriangle, Lightbulb, X, Check } from 'lucide-react';
import { enhancedApiClient } from '@/lib/api-client-enhanced';

interface Insight {
  id: string;
  type: 'optimal_time' | 'conflict_prediction' | 'productivity' | 'resource_utilization';
  title: string;
  description: string;
  confidence: number;
  actionable: boolean;
  actionText?: string;
  data?: Record<string, unknown>;
  dismissed: boolean;
}

export default function AIInsightWidgets() {
  const [insights, setInsights] = useState<Insight[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadInsights();
  }, []);

  const loadInsights = async () => {
    try {
      const data = await enhancedApiClient.get<{
        insights?: Array<{
          id?: string;
          type?: Insight['type'];
          title?: string;
          description?: string;
          confidence?: number;
          actionable?: boolean;
          action_text?: string;
          data?: Record<string, unknown>;
        }>;
      }>('/analytics/advanced/dashboard');

      const normalized = (data.insights || [])
        .filter((item) => item.title && item.description)
        .map((item, index): Insight => ({
          id: item.id || `insight-${index}`,
          type: item.type || 'productivity',
          title: item.title || 'Insight',
          description: item.description || '',
          confidence: typeof item.confidence === 'number' ? item.confidence : 0,
          actionable: Boolean(item.actionable),
          actionText: item.action_text,
          data: item.data,
          dismissed: false,
        }));

      setInsights(normalized);
    } catch (error) {
      console.error('Failed to load insights:', error);
    } finally {
      setLoading(false);
    }
  };

  const dismissInsight = (insightId: string) => {
    setInsights(insights.map(i => i.id === insightId ? { ...i, dismissed: true } : i));
  };

  const applyInsight = (insight: Insight) => {
    // Handle insight action
    console.log('Applying insight:', insight);
    // This would trigger the appropriate action based on insight type
  };

  const getIcon = (type: string) => {
    switch (type) {
      case 'optimal_time':
        return <Clock className="w-5 h-5 text-blue-400" />;
      case 'conflict_prediction':
        return <AlertTriangle className="w-5 h-5 text-amber-400" />;
      case 'productivity':
        return <TrendingUp className="w-5 h-5 text-green-400" />;
      case 'resource_utilization':
        return <Lightbulb className="w-5 h-5 text-purple-400" />;
      default:
        return <Lightbulb className="w-5 h-5 text-slate-400" />;
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 80) return 'text-green-400';
    if (confidence >= 60) return 'text-blue-400';
    if (confidence >= 40) return 'text-amber-400';
    return 'text-red-400';
  };

  const activeInsights = insights.filter(i => !i.dismissed);

  if (loading) {
    return (
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-white">AI Insights</h3>
        <div className="flex items-center justify-center h-32">
          <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
        </div>
      </div>
    );
  }

  if (activeInsights.length === 0) {
    return (
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-white">AI Insights</h3>
        <div className="bg-slate-800/30 rounded-xl p-6 border border-slate-700/50 text-center">
          <Lightbulb className="w-12 h-12 text-slate-500 mx-auto mb-3" />
          <p className="text-slate-400 text-sm">No insights available right now</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-white">AI Insights</h3>
        <span className="text-xs text-slate-400">{activeInsights.length} suggestions</span>
      </div>

      <div className="space-y-3">
        {activeInsights.map((insight) => (
          <div
            key={insight.id}
            className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-4 border border-slate-700/50 hover:border-slate-600/50 transition-colors"
          >
            <div className="flex items-start gap-3">
              <div className="mt-0.5">
                {getIcon(insight.type)}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between gap-2 mb-1">
                  <h4 className="text-white font-medium text-sm">{insight.title}</h4>
                  <button
                    type="button"
                    aria-label={`Dismiss ${insight.title}`}
                    onClick={() => dismissInsight(insight.id)}
                    className="p-1 hover:bg-slate-700 rounded transition-colors flex-shrink-0"
                  >
                    <X className="w-4 h-4 text-slate-500 hover:text-slate-300" />
                  </button>
                </div>
                <p className="text-slate-400 text-sm mb-3">{insight.description}</p>
                
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-slate-500">Confidence:</span>
                    <span className={`text-xs font-medium ${getConfidenceColor(insight.confidence)}`}>
                      {insight.confidence}%
                    </span>
                  </div>
                  
                  {insight.actionable && (
                    <button
                      type="button"
                      aria-label={insight.actionText ?? `Apply ${insight.title}`}
                      onClick={() => applyInsight(insight)}
                      className="flex items-center gap-1 px-3 py-1.5 bg-blue-600/20 hover:bg-blue-600/30 text-blue-400 rounded-lg transition-colors text-xs font-medium"
                    >
                      <Check className="w-3 h-3" />
                      <span className="ml-1">{insight.actionText ?? 'Apply'}</span>
                    </button>
                  )}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Dismissed insights toggle */}
      {insights.some(i => i.dismissed) && (
        <button
          type="button"
          aria-label="Show dismissed insights"
          onClick={() => setInsights(insights.map(i => ({ ...i, dismissed: false })))}
          className="w-full py-2 text-sm text-slate-400 hover:text-white transition-colors"
        >
          Show dismissed insights
        </button>
      )}
    </div>
  );
}
