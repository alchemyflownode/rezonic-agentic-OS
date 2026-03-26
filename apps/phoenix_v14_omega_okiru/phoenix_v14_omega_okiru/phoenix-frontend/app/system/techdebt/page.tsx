'use client';

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { AlertTriangle, BarChart } from 'lucide-react';
import { SovereignCanvas } from '@/components/SovereignCanvas';

export default function TechDebtPage() {
  const [analysis, setAnalysis] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [sce, setSce] = useState({
    verified: true,
    driftLock: '0x9c8d7e6f5a4b3c2d',
    narrative: [
      'Analyzing code complexity...',
      'Detecting code smells...',
      'Calculating technical debt...',
      'Generating report...'
    ]
  });

  const analyzeTechDebt = async () => {
    setIsAnalyzing(true);
    setAnalysis('');
    
    // Simulate analysis (replace with actual API call)
    setTimeout(() => {
      const mockAnalysis = {
        summary: {
          total_files: 42,
          total_lines: 12453,
          technical_debt_ratio: 0.18,
          estimated_days: 23
        },
        code_smells: [
          { type: "Long Method", count: 12, severity: "high" },
          { type: "Duplicate Code", count: 8, severity: "medium" },
          { type: "Complex Conditionals", count: 15, severity: "high" },
          { type: "Large Class", count: 5, severity: "medium" }
        ],
        recommendations: [
          "Refactor long methods in src/core/processor.py",
          "Extract duplicate validation logic",
          "Simplify conditional logic in auth module",
          "Break down large service classes"
        ],
        complexity_score: 68,
        maintainability_index: 72
      };
      
      setAnalysis(JSON.stringify(mockAnalysis, null, 2));
      setIsAnalyzing(false);
      
      setSce({
        verified: true,
        driftLock: '0x9c8d7e6f5a4b3c2d',
        narrative: [
          '✓ Analysis complete',
          '✓ 12 high-severity issues detected',
          '✓ Technical debt ratio: 18%',
          '✓ Recommendations generated',
          '✓ SCE verification passed'
        ]
      });
    }, 2000);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0a0a0c] via-[#050505] to-[#0a0a0c] p-8">
      <div className="fixed inset-0 pointer-events-none opacity-20">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,_#7dcfff_0%,_transparent_50%)] opacity-5" />
        <div className="absolute inset-0" style={{ backgroundImage: 'linear-gradient(to right, #7dcfff0a 1px, transparent 1px), linear-gradient(to bottom, #7dcfff0a 1px, transparent 1px)', backgroundSize: '40px 40px' }} />
      </div>

      <div className="relative z-10 max-w-6xl mx-auto">
        <motion.div
          initial={{ y: -20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          className="mb-8"
        >
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-[#7dcfff]/20 to-[#9B72CB]/20 border border-[#7dcfff]/30 flex items-center justify-center">
              <AlertTriangle className="w-6 h-6 text-[#7dcfff]" />
            </div>
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-[#c0caf5] to-[#7dcfff] bg-clip-text text-transparent">
                Tech Debt Analyzer
              </h1>
              <p className="text-[#565f89] mt-1">Identify and quantify technical debt in your codebase</p>
            </div>
          </div>
        </motion.div>

        {/* Analysis Button */}
        <div className="bg-black/30 backdrop-blur-xl border border-[#7dcfff]/10 rounded-2xl p-6 mb-6">
          <div className="flex justify-between items-center">
            <div>
              <h3 className="text-white font-medium mb-1">Code Quality Analysis</h3>
              <p className="text-xs text-[#565f89]">Scan your codebase for technical debt, code smells, and maintainability issues</p>
            </div>
            <button
              onClick={analyzeTechDebt}
              disabled={isAnalyzing}
              className="px-6 py-3 bg-gradient-to-r from-[#7dcfff]/20 to-[#9B72CB]/20 border border-[#7dcfff]/30 rounded-xl text-white font-medium hover:shadow-lg hover:shadow-[#7dcfff]/10 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {isAnalyzing ? (
                <>
                  <div className="w-4 h-4 border-2 border-[#7dcfff] border-t-transparent rounded-full animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  <BarChart className="w-4 h-4" />
                  Run Analysis
                </>
              )}
            </button>
          </div>
        </div>

        {/* Analysis Results */}
        {analysis && (
          <SovereignCanvas
            code={analysis}
            language="json"
            title="Code Quality Report"
            sce={sce}
            metadata={{
              author: 'TechDebtWorker',
              version: '2.1.0',
              created: new Date().toLocaleDateString()
            }}
          />
        )}

        {/* Empty State */}
        {!analysis && !isAnalyzing && (
          <div className="text-center py-20">
            <div className="w-24 h-24 mx-auto mb-4 rounded-full bg-gradient-to-br from-[#7dcfff]/10 to-[#9B72CB]/10 border border-[#7dcfff]/20 flex items-center justify-center">
              <BarChart className="w-12 h-12 text-[#565f89]" />
            </div>
            <p className="text-[#565f89]">Click "Run Analysis" to generate a technical debt report</p>
          </div>
        )}
      </div>
    </div>
  );
}
