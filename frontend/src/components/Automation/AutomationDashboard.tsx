/**
 * Automation Dashboard Component
 * 
- Visual rule editor
- Activity feed with confidence scores
- Override AI actions
 */

'use client';

import { useState, useEffect } from 'react';
import { Plus, Settings, Play, Pause, Trash2, Clock, CheckCircle, AlertTriangle, Zap } from 'lucide-react';

interface AutomationRule {
  id: string;
  name: string;
  description: string;
  rule_type: string;
  is_enabled: boolean;
  confidence_threshold: number;
  execution_count_today: number;
  priority: number;
  created_at: string;
}

interface AutomationExecution {
  id: string;
  rule_name: string;
  trigger_type: string;
  status: string;
  confidence_score: number;
  automation_tier: string;
  action_taken: string | null;
  started_at: string;
  completed_at: string | null;
}

export default function AutomationDashboard() {
  const [rules, setRules] = useState<AutomationRule[]>([]);
  const [executions, setExecutions] = useState<AutomationExecution[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'rules' | 'activity'>('rules');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      // SECURITY FIX: Use credentials:include instead of localStorage token
      // httpOnly cookies are sent automatically, no need to manually set Authorization
      const [rulesRes, executionsRes] = await Promise.all([
        fetch('/api/v1/automation/rules', {
          credentials: 'include' // Sends httpOnly cookies automatically
        }),
        fetch('/api/v1/automation/executions?limit=20', {
          credentials: 'include' // Sends httpOnly cookies automatically
        })
      ]);

      if (rulesRes.ok) {
        const rulesData = await rulesRes.json();
        setRules(rulesData);
      }

      if (executionsRes.ok) {
        const executionsData = await executionsRes.json();
        setExecutions(executionsData);
      }
    } catch (error) {
      console.error('Failed to load automation data:', error);
    } finally {
      setLoading(false);
    }
  };

  const toggleRule = async (ruleId: string, enabled: boolean) => {
    try {
      // SECURITY FIX: Use credentials:include instead of localStorage token
      const response = await fetch(`/api/v1/automation/rules/${ruleId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include', // Sends httpOnly cookies automatically
        body: JSON.stringify({ is_enabled: enabled }),
      });

      if (response.ok) {
        setRules(rules.map(r => r.id === ruleId ? { ...r, is_enabled: enabled } : r));
      }
    } catch (error) {
      console.error('Failed to toggle rule:', error);
    }
  };

  const deleteRule = async (ruleId: string) => {
    if (!confirm('Are you sure you want to delete this automation rule?')) return;

    try {
      // SECURITY FIX: Use credentials:include instead of localStorage token
      const response = await fetch(`/api/v1/automation/rules/${ruleId}`, {
        method: 'DELETE',
        credentials: 'include', // Sends httpOnly cookies automatically
      });

      if (response.ok) {
        setRules(rules.filter(r => r.id !== ruleId));
      }
    } catch (error) {
      console.error('Failed to delete rule:', error);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'failed':
        return <AlertTriangle className="w-4 h-4 text-red-500" />;
      case 'pending':
        return <Clock className="w-4 h-4 text-amber-500" />;
      default:
        return <Clock className="w-4 h-4 text-slate-500" />;
    }
  };

  const getTierBadge = (tier: string) => {
    switch (tier) {
      case 'full_auto':
        return <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-purple-500/20 text-purple-400">Full Auto</span>;
      case 'trusted':
        return <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-blue-500/20 text-blue-400">Trusted</span>;
      default:
        return <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-slate-500/20 text-slate-400">Draft</span>;
    }
  };

  const getConfidenceColor = (score: number) => {
    if (score >= 80) return 'text-green-400';
    if (score >= 60) return 'text-blue-400';
    if (score >= 40) return 'text-amber-400';
    return 'text-red-400';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">Automation Dashboard</h2>
          <p className="text-slate-400 mt-1">Manage AI-powered scheduling automation</p>
        </div>
        <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors text-white">
          <Plus className="w-5 h-5" />
          Create Rule
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-4 border border-slate-700/50">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-blue-500/20 flex items-center justify-center">
              <Zap className="w-5 h-5 text-blue-400" />
            </div>
            <div>
              <p className="text-2xl font-bold text-white">{rules.filter(r => r.is_enabled).length}</p>
              <p className="text-slate-400 text-sm">Active Rules</p>
            </div>
          </div>
        </div>
        <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-4 border border-slate-700/50">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-green-500/20 flex items-center justify-center">
              <CheckCircle className="w-5 h-5 text-green-400" />
            </div>
            <div>
              <p className="text-2xl font-bold text-white">{executions.filter(e => e.status === 'success').length}</p>
              <p className="text-slate-400 text-sm">Successful Today</p>
            </div>
          </div>
        </div>
        <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-4 border border-slate-700/50">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-amber-500/20 flex items-center justify-center">
              <Clock className="w-5 h-5 text-amber-400" />
            </div>
            <div>
              <p className="text-2xl font-bold text-white">{rules.reduce((sum, r) => sum + r.execution_count_today, 0)}</p>
              <p className="text-slate-400 text-sm">Total Executions</p>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-slate-700/50">
        <button
          onClick={() => setActiveTab('rules')}
          className={`px-4 py-2 text-sm font-medium transition-colors ${
            activeTab === 'rules'
              ? 'text-blue-400 border-b-2 border-blue-400'
              : 'text-slate-400 hover:text-white'
          }`}
        >
          Rules ({rules.length})
        </button>
        <button
          onClick={() => setActiveTab('activity')}
          className={`px-4 py-2 text-sm font-medium transition-colors ${
            activeTab === 'activity'
              ? 'text-blue-400 border-b-2 border-blue-400'
              : 'text-slate-400 hover:text-white'
          }`}
        >
          Activity Feed ({executions.length})
        </button>
      </div>

      {/* Rules Tab */}
      {activeTab === 'rules' && (
        <div className="space-y-3">
          {rules.length === 0 ? (
            <div className="text-center py-12 bg-slate-800/30 rounded-xl border border-slate-700/50">
              <Settings className="w-12 h-12 text-slate-500 mx-auto mb-4" />
              <h3 className="text-white font-semibold mb-2">No automation rules yet</h3>
              <p className="text-slate-400 text-sm mb-4">Create your first rule to automate scheduling tasks</p>
              <button className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors text-white text-sm">
                Browse Templates
              </button>
            </div>
          ) : (
            rules.map((rule) => (
              <div
                key={rule.id}
                className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-4 border border-slate-700/50 hover:border-slate-600/50 transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="text-white font-semibold">{rule.name}</h3>
                      <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-slate-700 text-slate-300">
                        {rule.rule_type}
                      </span>
                      {!rule.is_enabled && (
                        <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-slate-600 text-slate-400">
                          Disabled
                        </span>
                      )}
                    </div>
                    <p className="text-slate-400 text-sm mb-3">{rule.description}</p>
                    <div className="flex items-center gap-4 text-xs text-slate-500">
                      <span>Confidence: {rule.confidence_threshold}%</span>
                      <span>Priority: {rule.priority}</span>
                      <span>Executions today: {rule.execution_count_today}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => toggleRule(rule.id, !rule.is_enabled)}
                      className="p-2 hover:bg-slate-700 rounded-lg transition-colors"
                      title={rule.is_enabled ? 'Disable' : 'Enable'}
                    >
                      {rule.is_enabled ? (
                        <Pause className="w-4 h-4 text-amber-400" />
                      ) : (
                        <Play className="w-4 h-4 text-green-400" />
                      )}
                    </button>
                    <button
                      onClick={() => deleteRule(rule.id)}
                      className="p-2 hover:bg-slate-700 rounded-lg transition-colors"
                      title="Delete"
                    >
                      <Trash2 className="w-4 h-4 text-red-400" />
                    </button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Activity Tab */}
      {activeTab === 'activity' && (
        <div className="space-y-3">
          {executions.length === 0 ? (
            <div className="text-center py-12 bg-slate-800/30 rounded-xl border border-slate-700/50">
              <Clock className="w-12 h-12 text-slate-500 mx-auto mb-4" />
              <h3 className="text-white font-semibold mb-2">No activity yet</h3>
              <p className="text-slate-400 text-sm">Automation executions will appear here</p>
            </div>
          ) : (
            executions.map((execution) => (
              <div
                key={execution.id}
                className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-4 border border-slate-700/50"
              >
                <div className="flex items-start gap-4">
                  <div className="mt-0.5">
                    {getStatusIcon(execution.status)}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <h4 className="text-white font-medium">{execution.rule_name}</h4>
                      {getTierBadge(execution.automation_tier)}
                    </div>
                    <p className="text-slate-400 text-sm mb-2">
                      Trigger: {execution.trigger_type}
                    </p>
                    {execution.action_taken && (
                      <p className="text-slate-300 text-sm mb-2">
                        Action: {execution.action_taken}
                      </p>
                    )}
                    <div className="flex items-center gap-4 text-xs">
                      <span className={getConfidenceColor(execution.confidence_score)}>
                        Confidence: {execution.confidence_score}%
                      </span>
                      <span className="text-slate-500">
                        {new Date(execution.started_at).toLocaleString()}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}
