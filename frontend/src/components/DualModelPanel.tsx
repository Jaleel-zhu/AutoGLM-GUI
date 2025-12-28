import React from 'react';
import {
  Brain,
  Eye,
  Loader2,
  CheckCircle2,
  XCircle,
  ChevronDown,
  ChevronUp,
  Zap,
  Target,
  MessageSquare,
} from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import type {
  DualModelStreamEvent,
  DualModelDecisionResultEvent,
  DualModelVisionRecognitionEvent,
  DualModelActionResultEvent,
  DualModelTaskPlanEvent,
} from '../api';

interface DualModelState {
  // Decision model state
  decisionActive: boolean;
  decisionStage: string;
  decisionThinking: string;
  decisionResult: string;
  taskPlan: string[];

  // Vision model state
  visionActive: boolean;
  visionStage: string;
  visionDescription: string;
  visionAction: string;

  // Progress
  currentStep: number;
  totalSteps: number;

  // History
  decisions: DualModelDecisionResultEvent[];
  recognitions: DualModelVisionRecognitionEvent[];
  actions: DualModelActionResultEvent[];
}

interface DualModelPanelProps {
  state: DualModelState;
  isStreaming: boolean;
  className?: string;
}

export function DualModelPanel({
  state,
  isStreaming,
  className = '',
}: DualModelPanelProps) {
  const [expandedSection, setExpandedSection] = React.useState<
    'decision' | 'vision' | null
  >('decision');

  const toggleSection = (section: 'decision' | 'vision') => {
    setExpandedSection(prev => (prev === section ? null : section));
  };

  const progressPercent =
    state.totalSteps > 0
      ? Math.round((state.currentStep / state.totalSteps) * 100)
      : 0;

  return (
    <div className={`space-y-3 ${className}`}>
      {/* Progress bar */}
      {isStreaming && (
        <div className="space-y-1">
          <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
            <span>
              Step {state.currentStep} / {state.totalSteps || '?'}
            </span>
            <span>{progressPercent}%</span>
          </div>
          <Progress value={progressPercent} className="h-1.5" />
        </div>
      )}

      {/* Task Plan */}
      {state.taskPlan.length > 0 && (
        <Card className="p-3 bg-slate-50 dark:bg-slate-900/50 border-slate-200 dark:border-slate-800">
          <div className="flex items-center gap-2 mb-2">
            <Target className="w-4 h-4 text-blue-500" />
            <span className="text-xs font-medium text-slate-700 dark:text-slate-300">
              Task Plan
            </span>
          </div>
          <ul className="space-y-1">
            {state.taskPlan.map((step, idx) => (
              <li
                key={idx}
                className={`text-xs flex items-start gap-2 ${
                  idx < state.currentStep
                    ? 'text-green-600 dark:text-green-400'
                    : idx === state.currentStep
                      ? 'text-blue-600 dark:text-blue-400 font-medium'
                      : 'text-slate-500 dark:text-slate-400'
                }`}
              >
                <span className="flex-shrink-0 w-4 h-4 rounded-full border flex items-center justify-center text-[10px]">
                  {idx < state.currentStep ? (
                    <CheckCircle2 className="w-3 h-3" />
                  ) : (
                    idx + 1
                  )}
                </span>
                <span className="line-clamp-1">{step}</span>
              </li>
            ))}
          </ul>
        </Card>
      )}

      {/* Decision Model (Large Model) */}
      <Card
        className={`overflow-hidden transition-all duration-200 ${
          state.decisionActive
            ? 'border-purple-300 dark:border-purple-700 shadow-sm shadow-purple-100 dark:shadow-purple-900/20'
            : 'border-slate-200 dark:border-slate-800'
        }`}
      >
        <button
          onClick={() => toggleSection('decision')}
          className="w-full p-3 flex items-center justify-between hover:bg-slate-50 dark:hover:bg-slate-900/50 transition-colors"
        >
          <div className="flex items-center gap-2">
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center ${
                state.decisionActive
                  ? 'bg-purple-100 dark:bg-purple-900/30'
                  : 'bg-slate-100 dark:bg-slate-800'
              }`}
            >
              <Brain
                className={`w-4 h-4 ${
                  state.decisionActive
                    ? 'text-purple-600 dark:text-purple-400'
                    : 'text-slate-400'
                }`}
              />
            </div>
            <div className="text-left">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-slate-900 dark:text-slate-100">
                  Decision Model
                </span>
                <Badge
                  variant={state.decisionActive ? 'default' : 'secondary'}
                  className="text-[10px] px-1.5 py-0"
                >
                  GLM-4.7
                </Badge>
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                {state.decisionStage === 'analyzing'
                  ? 'Analyzing task...'
                  : state.decisionStage === 'deciding'
                    ? 'Making decision...'
                    : state.decisionStage === 'generating'
                      ? 'Generating content...'
                      : state.decisionActive
                        ? 'Active'
                        : 'Idle'}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {state.decisionActive && (
              <Loader2 className="w-4 h-4 text-purple-500 animate-spin" />
            )}
            {expandedSection === 'decision' ? (
              <ChevronUp className="w-4 h-4 text-slate-400" />
            ) : (
              <ChevronDown className="w-4 h-4 text-slate-400" />
            )}
          </div>
        </button>

        {expandedSection === 'decision' && (
          <div className="px-3 pb-3 space-y-2 border-t border-slate-100 dark:border-slate-800">
            {/* Current thinking */}
            {state.decisionThinking && (
              <div className="mt-2 p-2 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
                <div className="flex items-center gap-1 mb-1">
                  <MessageSquare className="w-3 h-3 text-purple-500" />
                  <span className="text-[10px] font-medium text-purple-600 dark:text-purple-400">
                    Thinking
                  </span>
                </div>
                <p className="text-xs text-purple-700 dark:text-purple-300 whitespace-pre-wrap">
                  {state.decisionThinking}
                  {state.decisionActive && (
                    <span className="inline-block w-1 h-3 ml-0.5 bg-purple-500 animate-pulse" />
                  )}
                </p>
              </div>
            )}

            {/* Latest decision */}
            {state.decisionResult && (
              <div className="mt-2 p-2 bg-slate-50 dark:bg-slate-900/50 rounded-lg">
                <div className="flex items-center gap-1 mb-1">
                  <Zap className="w-3 h-3 text-amber-500" />
                  <span className="text-[10px] font-medium text-slate-600 dark:text-slate-400">
                    Decision
                  </span>
                </div>
                <p className="text-xs text-slate-700 dark:text-slate-300">
                  {state.decisionResult}
                </p>
              </div>
            )}

            {/* Recent decisions history */}
            {state.decisions.length > 0 && (
              <details className="mt-2">
                <summary className="text-[10px] text-slate-500 cursor-pointer hover:text-slate-700 dark:hover:text-slate-300">
                  View decision history ({state.decisions.length})
                </summary>
                <div className="mt-1 space-y-1 max-h-32 overflow-y-auto">
                  {state.decisions.slice(-5).map((d, idx) => (
                    <div
                      key={idx}
                      className="text-[10px] p-1.5 bg-slate-100 dark:bg-slate-800 rounded"
                    >
                      <span className="text-purple-600 dark:text-purple-400">
                        [{d.decision.action}]
                      </span>{' '}
                      {d.decision.target}
                    </div>
                  ))}
                </div>
              </details>
            )}
          </div>
        )}
      </Card>

      {/* Vision Model (Small Model) */}
      <Card
        className={`overflow-hidden transition-all duration-200 ${
          state.visionActive
            ? 'border-green-300 dark:border-green-700 shadow-sm shadow-green-100 dark:shadow-green-900/20'
            : 'border-slate-200 dark:border-slate-800'
        }`}
      >
        <button
          onClick={() => toggleSection('vision')}
          className="w-full p-3 flex items-center justify-between hover:bg-slate-50 dark:hover:bg-slate-900/50 transition-colors"
        >
          <div className="flex items-center gap-2">
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center ${
                state.visionActive
                  ? 'bg-green-100 dark:bg-green-900/30'
                  : 'bg-slate-100 dark:bg-slate-800'
              }`}
            >
              <Eye
                className={`w-4 h-4 ${
                  state.visionActive
                    ? 'text-green-600 dark:text-green-400'
                    : 'text-slate-400'
                }`}
              />
            </div>
            <div className="text-left">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-slate-900 dark:text-slate-100">
                  Vision Model
                </span>
                <Badge
                  variant={state.visionActive ? 'success' : 'secondary'}
                  className="text-[10px] px-1.5 py-0"
                >
                  autoglm-phone
                </Badge>
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                {state.visionStage === 'capturing'
                  ? 'Capturing screen...'
                  : state.visionStage === 'recognizing'
                    ? 'Recognizing elements...'
                    : state.visionStage === 'executing'
                      ? 'Executing action...'
                      : state.visionActive
                        ? 'Active'
                        : 'Idle'}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {state.visionActive && (
              <Loader2 className="w-4 h-4 text-green-500 animate-spin" />
            )}
            {expandedSection === 'vision' ? (
              <ChevronUp className="w-4 h-4 text-slate-400" />
            ) : (
              <ChevronDown className="w-4 h-4 text-slate-400" />
            )}
          </div>
        </button>

        {expandedSection === 'vision' && (
          <div className="px-3 pb-3 space-y-2 border-t border-slate-100 dark:border-slate-800">
            {/* Screen description */}
            {state.visionDescription && (
              <div className="mt-2 p-2 bg-green-50 dark:bg-green-900/20 rounded-lg">
                <div className="flex items-center gap-1 mb-1">
                  <Eye className="w-3 h-3 text-green-500" />
                  <span className="text-[10px] font-medium text-green-600 dark:text-green-400">
                    Screen Recognition
                  </span>
                </div>
                <p className="text-xs text-green-700 dark:text-green-300 line-clamp-3">
                  {state.visionDescription}
                </p>
              </div>
            )}

            {/* Current action */}
            {state.visionAction && (
              <div className="mt-2 p-2 bg-slate-50 dark:bg-slate-900/50 rounded-lg">
                <div className="flex items-center gap-1 mb-1">
                  <Zap className="w-3 h-3 text-amber-500" />
                  <span className="text-[10px] font-medium text-slate-600 dark:text-slate-400">
                    Action
                  </span>
                </div>
                <p className="text-xs text-slate-700 dark:text-slate-300">
                  {state.visionAction}
                </p>
              </div>
            )}

            {/* Recent actions history */}
            {state.actions.length > 0 && (
              <details className="mt-2">
                <summary className="text-[10px] text-slate-500 cursor-pointer hover:text-slate-700 dark:hover:text-slate-300">
                  View action history ({state.actions.length})
                </summary>
                <div className="mt-1 space-y-1 max-h-32 overflow-y-auto">
                  {state.actions.slice(-5).map((a, idx) => (
                    <div
                      key={idx}
                      className={`text-[10px] p-1.5 rounded flex items-center gap-1 ${
                        a.success
                          ? 'bg-green-50 dark:bg-green-900/20'
                          : 'bg-red-50 dark:bg-red-900/20'
                      }`}
                    >
                      {a.success ? (
                        <CheckCircle2 className="w-3 h-3 text-green-500" />
                      ) : (
                        <XCircle className="w-3 h-3 text-red-500" />
                      )}
                      <span
                        className={
                          a.success
                            ? 'text-green-700 dark:text-green-300'
                            : 'text-red-700 dark:text-red-300'
                        }
                      >
                        [{a.action_type}] {a.target}
                      </span>
                    </div>
                  ))}
                </div>
              </details>
            )}
          </div>
        )}
      </Card>
    </div>
  );
}

// Helper hook to manage dual model state
export function useDualModelState() {
  const [state, setState] = React.useState<DualModelState>({
    decisionActive: false,
    decisionStage: 'idle',
    decisionThinking: '',
    decisionResult: '',
    taskPlan: [],
    visionActive: false,
    visionStage: 'idle',
    visionDescription: '',
    visionAction: '',
    currentStep: 0,
    totalSteps: 0,
    decisions: [],
    recognitions: [],
    actions: [],
  });

  const handleEvent = React.useCallback((event: DualModelStreamEvent) => {
    setState(prev => {
      switch (event.type) {
        case 'decision_start':
          return {
            ...prev,
            decisionActive: true,
            decisionStage: event.stage,
            visionActive: false,
          };

        case 'decision_thinking':
          return {
            ...prev,
            decisionThinking: prev.decisionThinking + event.chunk,
          };

        case 'decision_result':
          return {
            ...prev,
            decisionActive: false,
            decisionStage: 'idle',
            decisionThinking: '',
            decisionResult: `${event.decision.action}: ${event.decision.target}`,
            decisions: [...prev.decisions, event],
          };

        case 'task_plan':
          return {
            ...prev,
            taskPlan: event.plan.steps,
            totalSteps: event.plan.estimated_actions,
          };

        case 'vision_start':
          return {
            ...prev,
            visionActive: true,
            visionStage: event.stage,
            decisionActive: false,
          };

        case 'vision_recognition':
          return {
            ...prev,
            visionDescription: event.description,
            recognitions: [...prev.recognitions, event],
          };

        case 'action_start':
          return {
            ...prev,
            visionStage: 'executing',
            visionAction: `${event.action.action}: ${event.action.target}`,
          };

        case 'action_result':
          return {
            ...prev,
            visionActive: false,
            visionStage: 'idle',
            visionAction: `${event.action_type}: ${event.target} - ${event.success ? 'Success' : 'Failed'}`,
            actions: [...prev.actions, event],
          };

        case 'step_complete':
          return {
            ...prev,
            currentStep: event.step,
          };

        case 'task_complete':
          return {
            ...prev,
            decisionActive: false,
            visionActive: false,
            decisionStage: 'idle',
            visionStage: 'idle',
          };

        case 'error':
        case 'aborted':
          return {
            ...prev,
            decisionActive: false,
            visionActive: false,
            decisionStage: 'idle',
            visionStage: 'idle',
          };

        default:
          return prev;
      }
    });
  }, []);

  const reset = React.useCallback(() => {
    setState({
      decisionActive: false,
      decisionStage: 'idle',
      decisionThinking: '',
      decisionResult: '',
      taskPlan: [],
      visionActive: false,
      visionStage: 'idle',
      visionDescription: '',
      visionAction: '',
      currentStep: 0,
      totalSteps: 0,
      decisions: [],
      recognitions: [],
      actions: [],
    });
  }, []);

  return { state, handleEvent, reset };
}
