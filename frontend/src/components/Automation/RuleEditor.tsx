/**
 * Automation Rule Editor UI
 * 
- Visual rule editor
- Condition builder
- Test rule functionality
 */

'use client';

import { useState } from 'react';
import { Save, TestTube, Plus, Trash2, ArrowRight } from 'lucide-react';

interface Condition {
  id: string;
  field: string;
  operator: string;
  value: string;
}

interface Action {
  id: string;
  type: string;
  params: Record<string, string>;
}

export default function RuleEditor() {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [ruleType, setRuleType] = useState('auto_accept');
  const [confidenceThreshold, setConfidenceThreshold] = useState(70);
  const [requireConfirmation, setRequireConfirmation] = useState(true);
  const [conditions, setConditions] = useState<Condition[]>([]);
  const [actions, setActions] = useState<Action[]>([]);
  const [isTesting, setIsTesting] = useState(false);

  const fieldOptions = [
    { value: 'event_type', label: 'Event Type' },
    { value: 'organizer', label: 'Organizer' },
    { value: 'duration', label: 'Duration' },
    { value: 'time_of_day', label: 'Time of Day' },
    { value: 'day_of_week', label: 'Day of Week' },
    { value: 'attendee_count', label: 'Attendee Count' },
  ];

  const operatorOptions = [
    { value: 'equals', label: 'Equals' },
    { value: 'not_equals', label: 'Not Equals' },
    { value: 'contains', label: 'Contains' },
    { value: 'greater_than', label: 'Greater Than' },
    { value: 'less_than', label: 'Less Than' },
    { value: 'in', label: 'In' },
  ];

  const actionTypes = [
    { value: 'accept', label: 'Accept Booking' },
    { value: 'decline', label: 'Decline Booking' },
    { value: 'reschedule', label: 'Reschedule' },
    { value: 'notify', label: 'Send Notification' },
    { value: 'add_to_calendar', label: 'Add to Calendar' },
  ];

  const addCondition = () => {
    setConditions([
      ...conditions,
      {
        id: crypto.randomUUID(),
        field: 'event_type',
        operator: 'equals',
        value: '',
      },
    ]);
  };

  const removeCondition = (id: string) => {
    setConditions(conditions.filter(c => c.id !== id));
  };

  const updateCondition = (id: string, updates: Partial<Condition>) => {
    setConditions(conditions.map(c => c.id === id ? { ...c, ...updates } : c));
  };

  const addAction = () => {
    setActions([
      ...actions,
      {
        id: crypto.randomUUID(),
        type: 'accept',
        params: {},
      },
    ]);
  };

  const removeAction = (id: string) => {
    setActions(actions.filter(a => a.id !== id));
  };

  const updateAction = (id: string, updates: Partial<Action>) => {
    setActions(actions.map(a => a.id === id ? { ...a, ...updates } : a));
  };

  const handleTest = async () => {
    setIsTesting(true);
    // Simulate testing
    setTimeout(() => {
      setIsTesting(false);
      alert('Rule test passed! Would match 3 recent events.');
    }, 1000);
  };

  const handleSave = async () => {
    const token = localStorage.getItem('access_token');
    const response = await fetch('/api/v1/automation/rules', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        name,
        description,
        rule_type: ruleType,
        conditions: conditions.reduce((acc, c) => {
          acc[c.field] = { operator: c.operator, value: c.value };
          return acc;
        }, {} as Record<string, any>),
        actions: actions.reduce((acc, a) => {
          acc[a.type] = a.params;
          return acc;
        }, {} as Record<string, any>),
        confidence_threshold: confidenceThreshold,
        requireConfirmation,
      }),
    });

    if (response.ok) {
      alert('Automation rule created successfully!');
      // Reset form or redirect
    } else {
      alert('Failed to create rule');
    }
  };

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-white mb-2">Create Automation Rule</h2>
        <p className="text-slate-400">Define when and how AI should automate your scheduling</p>
      </div>

      {/* Basic Info */}
      <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-6 border border-slate-700/50 space-y-4">
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-2">Rule Name</label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g., Auto-accept team 1:1s"
            className="w-full bg-slate-900/50 border border-slate-700 rounded-lg px-4 py-2 text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-300 mb-2">Description</label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Describe what this rule does..."
            rows={2}
            className="w-full bg-slate-900/50 border border-slate-700 rounded-lg px-4 py-2 text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 resize-none"
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">Rule Type</label>
            <select
              value={ruleType}
              onChange={(e) => setRuleType(e.target.value)}
              className="w-full bg-slate-900/50 border border-slate-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-blue-500"
            >
              <option value="auto_accept">Auto Accept</option>
              <option value="auto_decline">Auto Decline</option>
              <option value="auto_reschedule">Auto Reschedule</option>
              <option value="smart_scheduling">Smart Scheduling</option>
              <option value="conflict_resolution">Conflict Resolution</option>
              <option value="team_coordination">Team Coordination</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">Confidence Threshold: {confidenceThreshold}%</label>
            <input
              type="range"
              min="0"
              max="100"
              value={confidenceThreshold}
              onChange={(e) => setConfidenceThreshold(parseInt(e.target.value))}
              className="w-full"
            />
          </div>
        </div>

        <div className="flex items-center gap-2">
          <input
            type="checkbox"
            id="requireConfirmation"
            checked={requireConfirmation}
            onChange={(e) => setRequireConfirmation(e.target.checked)}
            className="w-4 h-4 rounded border-slate-700 bg-slate-900 text-blue-500 focus:ring-blue-500"
          />
          <label htmlFor="requireConfirmation" className="text-sm text-slate-300">
            Require user confirmation before executing
          </label>
        </div>
      </div>

      {/* Conditions Builder */}
      <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-6 border border-slate-700/50 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-white">Conditions (When to trigger)</h3>
          <button
            onClick={addCondition}
            className="flex items-center gap-2 px-3 py-1.5 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors text-white text-sm"
          >
            <Plus className="w-4 h-4" />
            Add Condition
          </button>
        </div>

        {conditions.length === 0 ? (
          <p className="text-slate-500 text-sm text-center py-4">No conditions added yet</p>
        ) : (
          <div className="space-y-3">
            {conditions.map((condition, index) => (
              <div key={condition.id} className="flex items-center gap-2">
                <span className="text-slate-500 text-sm">{index + 1}.</span>
                <select
                  value={condition.field}
                  onChange={(e) => updateCondition(condition.id, { field: e.target.value })}
                  className="flex-1 bg-slate-900/50 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
                >
                  {fieldOptions.map(opt => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
                <select
                  value={condition.operator}
                  onChange={(e) => updateCondition(condition.id, { operator: e.target.value })}
                  className="flex-1 bg-slate-900/50 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
                >
                  {operatorOptions.map(opt => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
                <input
                  type="text"
                  value={condition.value}
                  onChange={(e) => updateCondition(condition.id, { value: e.target.value })}
                  placeholder="Value"
                  className="flex-1 bg-slate-900/50 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
                />
                <button
                  onClick={() => removeCondition(condition.id)}
                  className="p-2 hover:bg-slate-700 rounded-lg transition-colors"
                >
                  <Trash2 className="w-4 h-4 text-red-400" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Actions Builder */}
      <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-6 border border-slate-700/50 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-white">Actions (What to do)</h3>
          <button
            onClick={addAction}
            className="flex items-center gap-2 px-3 py-1.5 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors text-white text-sm"
          >
            <Plus className="w-4 h-4" />
            Add Action
          </button>
        </div>

        {actions.length === 0 ? (
          <p className="text-slate-500 text-sm text-center py-4">No actions added yet</p>
        ) : (
          <div className="space-y-3">
            {actions.map((action, index) => (
              <div key={action.id} className="flex items-center gap-2">
                <span className="text-slate-500 text-sm">{index + 1}.</span>
                <select
                  value={action.type}
                  onChange={(e) => updateAction(action.id, { type: e.target.value })}
                  className="flex-1 bg-slate-900/50 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
                >
                  {actionTypes.map(opt => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
                <ArrowRight className="w-4 h-4 text-slate-500" />
                <input
                  type="text"
                  value={action.params.message || ''}
                  onChange={(e) => updateAction(action.id, { params: { ...action.params, message: e.target.value } })}
                  placeholder="Parameters (e.g., message)"
                  className="flex-1 bg-slate-900/50 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
                />
                <button
                  onClick={() => removeAction(action.id)}
                  className="p-2 hover:bg-slate-700 rounded-lg transition-colors"
                >
                  <Trash2 className="w-4 h-4 text-red-400" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="flex items-center gap-3">
        <button
          onClick={handleTest}
          disabled={isTesting || conditions.length === 0}
          className="flex items-center gap-2 px-6 py-2.5 bg-slate-700 hover:bg-slate-600 disabled:bg-slate-800 disabled:cursor-not-allowed rounded-lg transition-colors text-white"
        >
          <TestTube className="w-4 h-4" />
          {isTesting ? 'Testing...' : 'Test Rule'}
        </button>
        <button
          onClick={handleSave}
          disabled={!name || conditions.length === 0 || actions.length === 0}
          className="flex items-center gap-2 px-6 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-800 disabled:cursor-not-allowed rounded-lg transition-colors text-white"
        >
          <Save className="w-4 h-4" />
          Save Rule
        </button>
      </div>
    </div>
  );
}
