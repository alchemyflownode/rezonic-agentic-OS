// frontend/src/components/EntropyField.tsx
import React, { useRef, useEffect } from 'react';

interface EntropyFieldProps {
  particles: Array<{
    x: number;
    y: number;
    vx: number;
    vy: number;
    radius: number;
    entropy: number;
  }>;
}

const EntropyField: React.FC<EntropyFieldProps> = ({ particles }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let width = canvas.offsetWidth;
    let height = canvas.offsetHeight;
    canvas.width = width * 2;
    canvas.height = height * 2;
    ctx.scale(2, 2);

    const animate = () => {
      ctx.clearRect(0, 0, width, height);
      
      // Draw connective strands (correlations)
      particles.forEach((p, i) => {
        particles.slice(i + 1).forEach(p2 => {
          const dist = Math.hypot(p.x * width - p2.x * width, 
                                   p.y * height - p2.y * height);
          if (dist < 80) {
            ctx.beginPath();
            ctx.moveTo(p.x * width, p.y * height);
            ctx.lineTo(p2.x * width, p2.y * height);
            const correlation = 0.2 * (1 - dist / 80) * 
                               (1 - (p.entropy + p2.entropy) / 2);
            ctx.strokeStyle = `rgba(0, 229, 255, ${correlation})`;
            ctx.stroke();
          }
        });
      });

      // Draw particles (interpretations)
      particles.forEach(p => {
        // Glow based on certainty
        const gradient = ctx.createRadialGradient(
          p.x * width, p.y * height, 0,
          p.x * width, p.y * height, p.radius * 3
        );
        gradient.addColorStop(0, `rgba(0, 229, 255, ${1 - p.entropy})`);
        gradient.addColorStop(1, 'rgba(0, 229, 255, 0)');
        
        ctx.beginPath();
        ctx.arc(p.x * width, p.y * height, p.radius * 3, 0, Math.PI * 2);
        ctx.fillStyle = gradient;
        ctx.fill();

        // Core
        ctx.beginPath();
        ctx.arc(p.x * width, p.y * height, p.radius * (1 - p.entropy), 0, Math.PI * 2);
        ctx.fillStyle = `rgba(255, 255, 255, ${1 - p.entropy})`;
        ctx.fill();
      });

      requestAnimationFrame(animate);
    };

    const anim = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(anim);
  }, [particles]);

  return (
    <div className="relative w-full h-64 glass-surface rounded-lg overflow-hidden">
      <canvas ref={canvasRef} className="absolute inset-0 w-full h-full" />
      <div className="absolute bottom-4 left-4 text-[10px] font-mono text-white/30">
        Entropy Field • {particles.length} interpretations
      </div>
    </div>
  );
};