"""
WorkerAdapter - Universal worker initializer that handles different init signatures
"""

import logging
import inspect

logger = logging.getLogger("rezhive")

class WorkerAdapter:
    """Adapts workers with different init signatures to a common interface"""
    
    @staticmethod
    def create_worker(worker_class, hive_bus=None, worker_name=None):
        """
        Create a worker instance regardless of its __init__ signature
        
        Args:
            worker_class: The worker class to instantiate
            hive_bus: Optional hive bus instance
            worker_name: Optional name for logging
            
        Returns:
            Worker instance or None if failed
        """
        name = worker_name or getattr(worker_class, '__name__', 'unknown')
        
        # Get the signature of __init__
        try:
            sig = inspect.signature(worker_class.__init__)
            params = list(sig.parameters.keys())
            
            # Pattern 1: __init__(self, hive_bus=None) or similar
            if len(params) == 2 and params[1] == 'hive_bus':
                try:
                    return worker_class(hive_bus=hive_bus)
                except:
                    pass
            
            # Pattern 2: __init__(self, hive_bus) - positional
            if len(params) == 2:
                try:
                    return worker_class(hive_bus)
                except:
                    pass
            
            # Pattern 3: __init__(self, **kwargs)
            if 'kwargs' in str(sig) or any(p.startswith('**') for p in params):
                try:
                    return worker_class(hive_bus=hive_bus)
                except:
                    pass
            
            # Pattern 4: __init__(self) - no args
            if len(params) == 1:
                try:
                    return worker_class()
                except:
                    pass
            
            # Pattern 5: Try all patterns in sequence
            try:
                return worker_class(hive_bus=hive_bus)
            except TypeError:
                try:
                    return worker_class(hive_bus)
                except TypeError:
                    try:
                        return worker_class()
                    except TypeError:
                        pass
            
        except Exception as e:
            logger.debug(f"Error inspecting {name}: {e}")
        
        # Last resort - try without any inspection
        try:
            return worker_class(hive_bus=hive_bus)
        except:
            try:
                return worker_class()
            except:
                logger.error(f"Failed to initialize {name}: all patterns failed")
                return None