'use client'

import { useEffect, useState } from 'react'

const steps = [
  'Initializing Kernel...',
  'Loading Workers...',
  'Mounting Memory...',
  'Establishing SCE Protocol...',
  'Boot Complete.',
]

interface BootSequencerProps {
  onComplete: () => void
}

export const BootSequencer = ({ onComplete }: BootSequencerProps) => {
  const [currentStep, setCurrentStep] = useState(0)

  useEffect(() => {
    if (currentStep < steps.length - 1) {
      const timer = setTimeout(() => setCurrentStep(currentStep + 1), 800)
      return () => clearTimeout(timer)
    } else {
      setTimeout(onComplete, 500)
    }
  }, [currentStep, onComplete])

  return (
    <div className="fixed inset-0 bg-black flex items-center justify-center">
      <div className="w-96 space-y-4 font-mono">
        {steps.slice(0, currentStep + 1).map((step, i) => (
          <div key={i} className="text-green-400">
            {i === currentStep ? '> ' : '✓ '}{step}
          </div>
        ))}
      </div>
    </div>
  )
}