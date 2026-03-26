export interface ConstitutionalResult {
  originalResponse: string;
  critique: {
    passed: boolean;
    violations: string[];
    score: number;
    suggestions: string[];
  };
  revisedResponse: string;
  finalResponse: string;
  driftLock: string;
}

class ConstitutionalAIService {
  private principles = [
    { id: 'p1', name: 'Data Sovereignty', rule: 'Always cite the source of market data (BINANCE, Kernel API)', weight: 10 },
    { id: 'p2', name: 'No Financial Advice', rule: 'Never provide financial advice. Trading involves risk.', weight: 10 },
    { id: 'p3', name: 'Risk Disclosure', rule: 'Include risk warnings for volatile markets (>2% change)', weight: 8 },
    { id: 'p4', name: 'Transparency', rule: 'Explain reasoning behind market analysis with specific data points', weight: 7 },
    { id: 'p5', name: 'Objectivity', rule: 'Use neutral, data-driven terminology. Avoid hype language.', weight: 9 }
  ];

  private async checkPrincipleViolation(response: string, principle: string): Promise<boolean> {
    const patterns: Record<string, RegExp[]> = {
      'Data Sovereignty': [/source/i, /from\s+\w+/i],
      'No Financial Advice': [/\bbuy\b.*\bnow\b/i, /\bsell\b.*\ball\b/i, /\binvest\b.*\ball\b/i],
      'Risk Disclosure': [/\brisk\b/i, /\bvolatile\b/i, /\bwarning\b/i],
      'Transparency': [/\bbecause\b/i, /\bdata shows\b/i, /\bindicators?\b/i],
      'Objectivity': [/\bmoon\b/i, /\blambo\b/i, /\bto\s*the\s*moon\b/i, /\b100x\b/i, /\bpump\b/i, /\bdump\b/i]
    };
    
    const principlePatterns = patterns[principle] || [];
    const hasPattern = principlePatterns.some(pattern => pattern.test(response));
    const hasNegative = response.toLowerCase().includes('not') || response.toLowerCase().includes('avoid');
    
    return hasPattern && !hasNegative;
  }

  async critiqueResponse(response: string): Promise<{ passed: boolean; violations: string[]; score: number; suggestions: string[] }> {
    const violations: string[] = [];
    const suggestions: string[] = [];
    let score = 100;

    for (const principle of this.principles) {
      const isViolated = await this.checkPrincipleViolation(response, principle.name);
      if (isViolated) {
        violations.push('Violates ' + principle.name + ': ' + principle.rule);
        score -= principle.weight;
        suggestions.push('Consider: ' + principle.rule);
      }
    }

    return {
      passed: violations.length === 0,
      violations,
      score: Math.max(0, score),
      suggestions
    };
  }

  async reviseResponse(original: string, critique: any): Promise<string> {
    let revised = original;
    
    // Add risk disclaimer if missing
    if (critique.violations.some((v: string) => v.includes('Risk Disclosure'))) {
      revised = '⚠️ Risk Warning: Trading involves significant risk. Past performance does not guarantee future results.\n\n' + revised;
    }
    
    // Add source citation if missing
    if (critique.violations.some((v: string) => v.includes('Data Sovereignty'))) {
      revised = revised + '\n\n📊 Source: BINANCE Market Data via Phoenix Kernel';
    }
    
    // Remove hype language
    if (critique.violations.some((v: string) => v.includes('Objectivity'))) {
      revised = revised
        .replace(/\bmoon\b/gi, 'significant upward movement')
        .replace(/\blambo\b/gi, 'high growth potential')
        .replace(/\bto the moon\b/gi, 'strong upward trend')
        .replace(/\bpump\b/gi, 'upward pressure')
        .replace(/\bdump\b/gi, 'downward pressure');
    }
    
    // Add explanation if missing transparency
    if (critique.violations.some((v: string) => v.includes('Transparency'))) {
      revised = 'Analysis based on 24h price movement and volume data.\n\n' + revised;
    }
    
    return revised;
  }

  async processConstitutionalResponse(
    originalResponse: string,
    driftLock?: string
  ): Promise<ConstitutionalResult> {
    const critique = await this.critiqueResponse(originalResponse);
    let revisedResponse = originalResponse;
    
    if (!critique.passed) {
      revisedResponse = await this.reviseResponse(originalResponse, critique);
      const recritique = await this.critiqueResponse(revisedResponse);
      if (!recritique.passed) {
        revisedResponse = await this.reviseResponse(revisedResponse, recritique);
      }
    }

    return {
      originalResponse,
      critique,
      revisedResponse,
      finalResponse: revisedResponse,
      driftLock: driftLock || 'constitutional_' + Date.now()
    };
  }

  async analyzeMarketWithConstitution(marketData: any, userQuery: string): Promise<string> {
    // Generate initial analysis based on market data
    let analysis = '';
    
    if (userQuery.toLowerCase().includes('price') || userQuery.toLowerCase().includes('market')) {
      const change = Math.abs(marketData.change);
      const direction = marketData.change >= 0 ? 'upward' : 'downward';
      const volatility = change > 5 ? '⚠️ HIGH VOLATILITY ⚠️ ' : change > 2 ? '🔸 Moderate volatility: ' : '📊 Stable movement: ';
      
      analysis = volatility + marketData.symbol + ' is showing ' + direction + ' movement of ' + Math.abs(marketData.change) + '% in the last 24h.\n\n';
      analysis += 'Current price: ' + marketData.price.toLocaleString() + '\n';
      analysis += '24h Volume: ' + marketData.volume + '\n\n';
      
      if (change > 5) {
        analysis += '⚠️ EXTREME VOLATILITY DETECTED: Trading during high volatility periods carries significant risk. Consider reducing position sizes and setting tight stop-losses.\n\n';
      } else if (change > 2) {
        analysis += 'Note: Moderate volatility detected. Standard risk management practices recommended.\n\n';
      }
    } else {
      analysis = 'Based on current market data for ' + marketData.symbol + ', I can provide analysis. What specific information would you like to know about price trends, volume, or market conditions?';
    }
    
    // Apply constitutional filtering
    const constitutionalOutput = await this.processConstitutionalResponse(
      analysis,
      marketData.drift_lock
    );
    
    // Add constitutional badge
    let badge = '';
    if (constitutionalOutput.critique.score >= 90) {
      badge = '🏛️ [CONSTITUTIONAL] ✓ PASSED\n';
    } else if (constitutionalOutput.critique.score >= 70) {
      badge = '⚖️ [CONSTITUTIONAL] ⚠ MODIFIED\n';
    } else {
      badge = '🔴 [CONSTITUTIONAL] ✗ REVIEW NEEDED\n';
    }
    
    return badge + constitutionalOutput.finalResponse + '\n\n📜 Score: ' + constitutionalOutput.critique.score + '/100 | Lock: ' + constitutionalOutput.driftLock.slice(0, 8);
  }
}

export const constitutionalAI = new ConstitutionalAIService();
