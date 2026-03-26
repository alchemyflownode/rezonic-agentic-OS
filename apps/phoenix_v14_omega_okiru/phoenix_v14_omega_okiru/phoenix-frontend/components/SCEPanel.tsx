import React, { useState, useEffect } from 'react';
import { usePhoenix } from '../hooks/usePhoenix';
import { Blueprint } from '../types/phoenix.types';

interface SCEPanelProps {
    className?: string;
}

export const SCEPanel: React.FC<SCEPanelProps> = ({ className = '' }) => {
    const [blueprints, setBlueprints] = useState<string[]>([]);
    const [selectedBlueprint, setSelectedBlueprint] = useState<string | null>(null);
    const [verificationResult, setVerificationResult] = useState<any>(null);
    const [stats, setStats] = useState<any>(null);
    
    const { service, loading, connected } = usePhoenix();

    useEffect(() => {
        if (connected) {
            loadBlueprints();
            loadStats();
        }
    }, [connected]);

    const loadBlueprints = async () => {
        try {
            const data = await service.getBlueprints();
            setBlueprints(data.blueprints);
        } catch (err) {
            console.error('Failed to load blueprints:', err);
        }
    };

    const loadStats = async () => {
        try {
            const status = await service.getSCEStatus();
            setStats(status);
        } catch (err) {
            console.error('Failed to load SCE stats:', err);
        }
    };

    const handleVerify = async (driftLock: string) => {
        try {
            const result = await service.verifyBlueprint(driftLock);
            setVerificationResult(result);
            setSelectedBlueprint(driftLock);
        } catch (err) {
            console.error('Verification failed:', err);
        }
    };

    return (
        <div className={`sce-panel ${className}`}>
            <div className="panel-header">
                <h2>SCE Protocol</h2>
                <div className="connection-status">
                    {connected ? '🟢 Connected' : '🔴 Disconnected'}
                </div>
            </div>
            
            {stats && (
                <div className="stats-panel">
                    <h3>Statistics</h3>
                    <div className="stat-grid">
                        <div className="stat">
                            <label>Version</label>
                            <span>{stats.version}</span>
                        </div>
                        <div className="stat">
                            <label>Blueprints</label>
                            <span>{stats.blueprints}</span>
                        </div>
                        <div className="stat">
                            <label>Drift Chain</label>
                            <span>{stats.drift_chain?.length || 0}</span>
                        </div>
                    </div>
                </div>
            )}
            
            <div className="blueprints-panel">
                <h3>Recent Blueprints</h3>
                <div className="blueprint-list">
                    {blueprints.slice(0, 10).map((lock) => (
                        <div
                            key={lock}
                            className={`blueprint-item ${selectedBlueprint === lock ? 'selected' : ''}`}
                            onClick={() => handleVerify(lock)}
                        >
                            <span className="lock">{lock.substring(0, 16)}...</span>
                            <button className="verify-btn">Verify</button>
                        </div>
                    ))}
                </div>
            </div>
            
            {verificationResult && (
                <div className="verification-panel">
                    <h3>Verification Result</h3>
                    <pre>{JSON.stringify(verificationResult, null, 2)}</pre>
                </div>
            )}
        </div>
    );
};

export default SCEPanel;
