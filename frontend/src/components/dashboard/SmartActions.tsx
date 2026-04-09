"use client";

import { useState } from "react";

export interface SmartAction {
  id: string;
  action_type: string;
  title: string;
  description: string;
  target_entity_id?: string;
  suggested_time?: string;
  confidence_score: number;
  payload?: Record<string, any>;
}

interface SmartActionsProps {
  actions: SmartAction[];
  onExecute: (action: SmartAction, overridePayload?: any) => void;
}

export function SmartActions({ actions, onExecute }: SmartActionsProps) {
  const [selectedAction, setSelectedAction] = useState<SmartAction | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  if (!actions || actions.length === 0) return null;

  const handleCardClick = (action: SmartAction) => {
    setSelectedAction(action);
    setIsModalOpen(true);
  };

  const handleConfirm = () => {
    if (selectedAction) {
      onExecute(selectedAction);
      setIsModalOpen(false);
      setSelectedAction(null);
    }
  };

  return (
    <div className="w-full py-4">
      <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3 px-1">
        AI Suggestions
      </h3>
      {/* Horizontal Swipeable Container */}
      <div className="flex overflow-x-auto space-x-4 pb-4 snap-x hide-scrollbar px-1">
        {actions.map((action) => (
          <div
            key={action.id}
            className="flex-none w-64 p-4 rounded-xl border border-gray-200 bg-white shadow-sm hover:shadow-md transition-shadow cursor-pointer snap-start"
            onClick={() => handleCardClick(action)}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold px-2 py-1 rounded-full bg-blue-100 text-blue-800">
                {action.action_type.replace('_', ' ')}
              </span>
              {action.confidence_score > 0.8 && (
                <span className="text-xs text-green-600 font-medium flex items-center">
                  <span className="w-2 h-2 rounded-full bg-green-500 mr-1 flex-shrink-0"></span>
                  High Confidence
                </span>
              )}
            </div>
            <h4 className="text-sm font-semibold text-gray-900 mb-1">{action.title}</h4>
            <p className="text-xs text-gray-600 line-clamp-2">{action.description}</p>
          </div>
        ))}
      </div>

      {/* Confirmation Modal */}
      {isModalOpen && selectedAction && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md overflow-hidden flex flex-col max-h-[90vh]">
            <div className="p-6 border-b border-gray-100">
              <h2 className="text-xl font-semibold text-gray-900">Confirm Action</h2>
              <p className="text-sm text-gray-500 mt-1">Please review the details before proceeding.</p>
            </div>
            
            <div className="p-6 overflow-y-auto">
              <div className="bg-gray-50 p-4 rounded-lg border border-gray-100">
                <h5 className="font-medium text-gray-900 mb-1">{selectedAction.title}</h5>
                <p className="text-sm text-gray-600 mb-4">{selectedAction.description}</p>
                
                {selectedAction.suggested_time && (
                  <div className="text-sm flex items-center mb-2">
                    <span className="font-semibold text-gray-700 w-24">Time:</span>
                    <span className="text-gray-900">{selectedAction.suggested_time}</span>
                  </div>
                )}
                
                {selectedAction.payload && Object.keys(selectedAction.payload).length > 0 && (
                  <div className="text-sm flex flex-col mt-3">
                    <span className="font-semibold text-gray-700 mb-1">Details:</span>
                    <pre className="text-xs bg-white p-3 rounded-md border border-gray-200 overflow-x-auto text-gray-800">
                      {JSON.stringify(selectedAction.payload, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            </div>

            <div className="p-6 border-t border-gray-100 flex items-center justify-end gap-3 bg-gray-50">
              <button
                type="button"
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                onClick={() => setIsModalOpen(false)}
              >
                Cancel
              </button>
              <button
                type="button"
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 shadow-sm transition-colors"
                onClick={handleConfirm}
              >
                Execute Action
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
