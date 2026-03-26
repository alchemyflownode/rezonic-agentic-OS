"""
Fixed Constitutional Council with proper class structure
"""

import subprocess
import json
import concurrent.futures
import time
from pathlib import Path

class ConstitutionalCouncil:
    """Your Supreme Constitutional AI Council - Fixed Class Version"""
    
    def __init__(self, config_path=None):
        self.models = [
            "phi4:latest",          # Chief Justice - Deep reasoning
            "qwen2.5-coder:7b",     # Lead Architect - Coding excellence
            "deepseek-coder:latest", # Bytecode Specialist - Optimization
            "glm4:latest",          # Constitutional Scholar
            "llama3.2:latest",      # Balanced Advisor
        ]
        
        self.config = self._load_config(config_path)
        self.rulings_cache = {}
        
        print("=" * 70)
        print("âš–ï¸  SOVEREIGN CONSTITUTIONAL AI COUNCIL v1.0")
        print("=" * 70)
        print(f"Council initialized with {len(self.models)} members")
    
    def _load_config(self, config_path):
        """Load council configuration"""
        default_config = {
            "timeout": 45,
            "consensus_threshold": 0.6,
            "log_rulings": True,
            "cache_enabled": True
        }
        
        if config_path and Path(config_path).exists():
            try:
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                default_config.update(user_config)
            except Exception as e:
                pass
        
        return default_config
    
    def query_model_safe(self, model_name, prompt, timeout=None):
        """Safely query a single Ollama model with timeout."""
        if timeout is None:
            timeout = self.config["timeout"]
        
        try:
            cmd = ["ollama", "run", model_name]
            
            start_time = time.time()
            process = subprocess.run(
                cmd,
                input=prompt,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                timeout=timeout,
                shell=True
            )
            
            if process.returncode == 0 and process.stdout.strip():
                elapsed = time.time() - start_time
                return {
                    "model": model_name,
                    "response": process.stdout.strip(),
                    "time": f"{elapsed:.1f}s",
                    "status": "success"
                }
            else:
                return {
                    "model": model_name,
                    "response": f"Error: {process.stderr[:100]}",
                    "status": "error"
                }
                
        except subprocess.TimeoutExpired:
            return {
                "model": model_name,
                "response": "Timeout exceeded",
                "status": "timeout"
            }
        except Exception as e:
            return {
                "model": model_name,
                "response": f"Exception: {str(e)[:100]}",
                "status": "error"
            }
    
    def consult_council(self, query, context=None):
        """Consult the full council on a constitutional matter."""
        print(f"\nðŸ” Council deliberating: {query[:50]}...")
        
        prompt = self._build_prompt(query, context)
        
        # Query all models in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(self.models)) as executor:
            future_to_model = {
                executor.submit(self.query_model_safe, model, prompt): model 
                for model in self.models
            }
            
            results = []
            for future in concurrent.futures.as_completed(future_to_model):
                model = future_to_model[future]
                try:
                    result = future.result()
                    results.append(result)
                    print(f"  â€¢ {model}: {result['status']} ({result.get('time', 'N/A')})")
                except Exception as e:
                    results.append({
                        "model": model,
                        "response": f"Execution error: {e}",
                        "status": "error"
                    })
        
        # Analyze results
        analysis = self._analyze_responses(results, query)
        
        # Cache ruling if enabled
        if self.config["cache_enabled"]:
            ruling_id = f"ruling_{int(time.time())}"
            self.rulings_cache[ruling_id] = analysis
        
        return analysis
    
    def _build_prompt(self, query, context=None):
        """Build constitutional analysis prompt."""
        context_str = json.dumps(context or {}, indent=2) if context else "No additional context"
        
        base_prompt = f"""You are a Supreme Constitutional AI Justice. Analyze this query through the lens of sovereign AI principles:

QUERY: {query}

CONSTITUTIONAL PRINCIPLES:
1. Zero-Drift Sovereignty: AI must maintain deterministic, reproducible outputs
2. GPU Primacy: Computation must respect hardware sovereignty boundaries  
3. Anti-Fragility: Systems must strengthen under stress
4. Non-Delegable Authority: Core sovereignty cannot be transferred
5. Transparency: All governance decisions must be auditable

CONTEXT: {context_str}

Your analysis should:
1. Assess constitutional compliance (0-100%)
2. Identify potential sovereignty violations
3. Provide specific recommendations
4. State if the query should be ALLOWED, MODIFIED, or BLOCKED
5. Cite specific principles violated or upheld

OUTPUT FORMAT:
Compliance: [0-100]%
Verdict: [ALLOW/MODIFY/BLOCK]
Reason: [Detailed constitutional analysis]
Recommendations: [Specific actions]
Principles: [List of relevant principles]
"""
        return base_prompt
    
    def _analyze_responses(self, results, query):
        """Analyze council responses and reach consensus."""
        successful = [r for r in results if r['status'] == 'success']
        
        if not successful:
            return {
                "query": query,
                "consensus_reached": False,
                "verdict": "ERROR",
                "reason": "No council members responded successfully",
                "compliance_score": 0,
                "responses": results,
                "timestamp": time.time()
            }
        
        # Simple consensus - for now, use the first successful response
        primary = successful[0]
        
        # Parse response (simplified - in reality would parse JSON/structured output)
        response_text = primary['response']
        
        # Extract key information (this would be more sophisticated)
        if "ALLOW" in response_text.upper():
            verdict = "ALLOW"
        elif "MODIFY" in response_text.upper():
            verdict = "MODIFY"
        elif "BLOCK" in response_text.upper():
            verdict = "BLOCK"
        else:
            verdict = "UNKNOWN"
        
        # Simple compliance scoring
        if verdict == "ALLOW":
            compliance = 75
        elif verdict == "MODIFY":
            compliance = 50
        elif verdict == "BLOCK":
            compliance = 25
        else:
            compliance = 0
        
        return {
            "query": query,
            "consensus_reached": True,
            "primary_model": primary['model'],
            "verdict": verdict,
            "response": response_text,
            "compliance_score": compliance,
            "all_responses": results,
            "timestamp": time.time()
        }
    
    def get_members(self):
        """Get list of council members."""
        return self.models.copy()
    
    def add_member(self, model_name):
        """Add a new model to the council."""
        if model_name not in self.models:
            self.models.append(model_name)
            print(f"âœ… Added {model_name} to council")
    
    def remove_member(self, model_name):
        """Remove a model from the council."""
        if model_name in self.models:
            self.models.remove(model_name)
            print(f"âœ… Removed {model_name} from council")

# Quick test if run directly
if __name__ == "__main__":
    council = ConstitutionalCouncil()
    print(f"Council members: {council.get_members()}")
    
    # Test query
    test_result = council.consult_council(
        "Should we allow model weight modifications during runtime?"
    )
    print(f"\nTest verdict: {test_result['verdict']}")
    print(f"Compliance score: {test_result['compliance_score']}%")
