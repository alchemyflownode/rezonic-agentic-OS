import React, { useState } from 'react';
import { usePhoenix } from '../hooks/usePhoenix';
import { ExecutionResult } from '../types/phoenix.types';

interface DevModeWorkspaceProps {
    className?: string;
}

export const DevModeWorkspace: React.FC<DevModeWorkspaceProps> = ({ className = '' }) => {
    const [code, setCode] = useState('');
    const [result, setResult] = useState<ExecutionResult | null>(null);
    const [isExecuting, setIsExecuting] = useState(false);
    const { executeTask, loading, error, connected } = usePhoenix();

    const handleExecute = async () => {
        if (!code.trim() || !connected) return;
        
        setIsExecuting(true);
        try {
            const executionResult = await executeTask(code, 'sandbox');
            setResult(executionResult);
        } catch (err) {
            setResult({ output: `Error: ${err.message}`, duration: 0 });
        } finally {
            setIsExecuting(false);
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && e.ctrlKey) {
            e.preventDefault();
            handleExecute();
        }
    };

    return (
        <div className={`dev-workspace ${className}`}>
            <div className="workspace-header">
                <h2>Developer Workspace</h2>
                <div className="connection-status">
                    {connected ? '🟢 Connected' : '🔴 Disconnected'}
                </div>
            </div>
            
            <div className="editor-panel">
                <textarea
                    value={code}
                    onChange={(e) => setCode(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Enter code to execute..."
                    disabled={!connected || isExecuting}
                    className="code-editor"
                />
                <button
                    onClick={handleExecute}
                    disabled={!connected || !code.trim() || isExecuting}
                    className="execute-btn"
                >
                    {isExecuting ? 'Executing...' : 'Execute (Ctrl+Enter)'}
                </button>
            </div>
            
            {error && (
                <div className="error-panel">
                    <h3>Error</h3>
                    <pre>{error}</pre>
                </div>
            )}
            
            {result && (
                <div className="result-panel">
                    <h3>Result</h3>
                    {result.driftLock && (
                        <div className="drift-lock">
                            🔗 Drift Lock: {result.driftLock}
                        </div>
                    )}
                    <pre className="output">{result.output}</pre>
                    {result.duration > 0 && (
                        <div className="duration">
                            ⏱️ Execution time: {result.duration.toFixed(3)}s
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default DevModeWorkspace;
