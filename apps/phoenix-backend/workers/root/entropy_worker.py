import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
# backend/workers/entropy_worker.py
import numpy as np
from scipy.stats import entropy

class EntropyWorker:
    """
    Measures and visualizes decision uncertainty
    Inspired by your SYNTH/APEX layers
    """
    
    def calculate_intent_entropy(self, intent_distribution):
        """Shannon entropy of intent probabilities"""
        probs = list(intent_distribution.values())
        return entropy(probs, base=2)  # bits of uncertainty
    
    def calculate_kl_divergence(self, p_distribution, q_distribution):
        """
        Kullback-Leibler divergence - measures drift
        D_KL(P || Q) = Î£ P(x) log(P(x)/Q(x))
        """
        divergence = 0
        for key in p_distribution:
            p = p_distribution[key]
            q = q_distribution.get(key, 1e-10)  # avoid log(0)
            divergence += p * np.log2(p / q)
        return divergence
    
    def generate_entropy_field(self, intent_space):
        """
        Generate particle field data for visualization
        Matches your SynthLayer's particle system
        """
        particles = []
        for i in range(40):  # Your 40 particles
            # Position in 2D intent space
            x = np.random.random()
            y = np.random.random()
            
            # Probability velocity
            vx = (np.random.random() - 0.5) * 0.01
            vy = (np.random.random() - 0.5) * 0.01
            
            # Uncertainty radius
            local_entropy = self.sample_entropy_at(x, y, intent_space)
            radius = 2 + 3 * (1 - local_entropy)  # More certain = larger
            
            particles.append({
                'x': x, 'y': y,
                'vx': vx, 'vy': vy,
                'radius': radius,
                'entropy': local_entropy
            })
        
        return particles
    
    def detect_drift(self, initial_intent, current_output):
        """Drift = KL divergence from intent to output"""
        intent_dist = self.extract_probabilities(initial_intent)
        output_dist = self.extract_probabilities(current_output)
        
        drift_score = self.calculate_kl_divergence(intent_dist, output_dist)
        
        return {
            'drift_score': drift_score,
            'drift_level': 'high' if drift_score > 0.5 else 'medium' if drift_score > 0.2 else 'low',
            'divergent_dimensions': self.identify_divergent_dimensions(intent_dist, output_dist)
        }

    async def process(self, task: str, memory_bus=None):
        """Process task – auto-generated stub"""
        return {"content": f"Processed: {task[:50]}", "worker": self.name}
    
    async def health_check(self):
        """Return worker health status"""
        return {"worker": self.name, "status": "healthy", "timestamp": __import__('time').time()}

