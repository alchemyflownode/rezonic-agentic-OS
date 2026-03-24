# security/input_validator.py
"""Input validation and sanitization for security"""

import re
from pathlib import Path
from typing import Any, Union, List, Optional
import logging

logger = logging.getLogger("phoenix.security")

class InputValidator:
    """
    Validate and sanitize all user inputs
    Prevents injection attacks, path traversal, and dangerous commands
    """
    
    # Dangerous patterns to block
    DANGEROUS_COMMANDS = [
        r'rm\s+-rf', r'del\s+/f', r'format\s+', r'shutdown',
        r'reboot', r'mkfs', r'dd\s+', r'>\s*/dev/', r'chmod\s+777'
    ]
    
    # Forbidden path patterns
    FORBIDDEN_PATHS = [
        r'\.\./', r'\.\.\\', r'/etc/', r'/sys/', r'/proc/',
        r'C:\\Windows', r'C:\\System32', r'/root/', r'/home/\.ssh'
    ]
    
    # Allowed characters for different fields
    ALLOWED_PATTERNS = {
        'alphanumeric': r'^[a-zA-Z0-9_\-]+$',
        'symbol': r'^[A-Z]{2,10}$',
        'amount': r'^\d+(?:\.\d{1,8})?$',
        'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
        'path': None,  # Validated separately
    }
    
    @classmethod
    def validate_command(cls, command: str) -> tuple[bool, str]:
        """
        Validate shell command for dangerous patterns
        
        Returns:
            (is_valid, error_message)
        """
        if not command:
            return False, "Command cannot be empty"
        
        command_lower = command.lower()
        
        # Check for dangerous commands
        for pattern in cls.DANGEROUS_COMMANDS:
            if re.search(pattern, command_lower):
                logger.warning(f"Blocked dangerous command: {command[:100]}")
                return False, f"Dangerous command blocked: {pattern}"
        
        return True, ""
    
    @classmethod
    def validate_path(cls, path: Union[str, Path], base_dir: Optional[Path] = None) -> tuple[bool, str, Path]:
        """
        Validate file path for traversal attacks
        
        Returns:
            (is_valid, error_message, resolved_path)
        """
        try:
            if isinstance(path, str):
                path = Path(path)
            
            # Check for forbidden patterns
            path_str = str(path).lower()
            for pattern in cls.FORBIDDEN_PATHS:
                if re.search(pattern, path_str):
                    return False, f"Path contains forbidden pattern: {pattern}", path
            
            # Resolve and normalize
            resolved = path.expanduser().resolve()
            
            # If base_dir provided, ensure path is within it
            if base_dir:
                base_resolved = base_dir.expanduser().resolve()
                try:
                    resolved.relative_to(base_resolved)
                except ValueError:
                    return False, f"Path outside allowed directory: {base_dir}", resolved
            
            return True, "", resolved
            
        except Exception as e:
            return False, f"Invalid path: {e}", path
    
    @classmethod
    def validate_amount(cls, amount: Any, min_amount: float = 0.01, max_amount: float = 100000) -> tuple[bool, str, float]:
        """
        Validate trading amount
        
        Returns:
            (is_valid, error_message, amount_float)
        """
        try:
            amount_float = float(amount)
            
            if amount_float <= 0:
                return False, "Amount must be positive", amount_float
            
            if amount_float < min_amount:
                return False, f"Amount below minimum: {min_amount}", amount_float
            
            if amount_float > max_amount:
                return False, f"Amount exceeds maximum: {max_amount}", amount_float
            
            return True, "", amount_float
            
        except (ValueError, TypeError):
            return False, f"Invalid amount format: {amount}", 0
    
    @classmethod
    def validate_symbol(cls, symbol: str) -> tuple[bool, str]:
        """
        Validate trading symbol (e.g., BTC/USDT)
        
        Returns:
            (is_valid, error_message)
        """
        if not symbol:
            return False, "Symbol cannot be empty"
        
        # Standard crypto symbol pattern
        pattern = r'^[A-Z]{2,10}[/-][A-Z]{2,10}$'
        if not re.match(pattern, symbol.upper()):
            return False, f"Invalid symbol format: {symbol}"
        
        return True, ""
    
    @classmethod
    def validate_api_key(cls, api_key: str) -> tuple[bool, str]:
        """
        Validate API key format
        
        Returns:
            (is_valid, error_message)
        """
        if not api_key:
            return False, "API key cannot be empty"
        
        # Minimum length check
        if len(api_key) < 16:
            return False, "API key too short"
        
        # Alphanumeric with dashes allowed
        if not re.match(r'^[a-zA-Z0-9\-_]+$', api_key):
            return False, "API key contains invalid characters"
        
        return True, ""
    
    @classmethod
    def sanitize_input(cls, text: str, max_length: int = 10000) -> str:
        """
        Sanitize text input by removing dangerous characters
        
        Returns:
            Sanitized text
        """
        if not text:
            return ""
        
        # Truncate if too long
        if len(text) > max_length:
            text = text[:max_length]
            logger.warning(f"Input truncated to {max_length} chars")
        
        # Remove null bytes
        text = text.replace('\x00', '')
        
        # Remove control characters except newlines and tabs
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
        
        return text
    
    @classmethod
    def validate_rate_limit(cls, client_id: str, endpoint: str) -> tuple[bool, str]:
        """
        Validate client ID format for rate limiting
        
        Returns:
            (is_valid, error_message)
        """
        if not client_id:
            return False, "Client ID cannot be empty"
        
        if len(client_id) > 255:
            return False, "Client ID too long"
        
        if not re.match(r'^[a-zA-Z0-9_\-\.:]+$', client_id):
            return False, "Client ID contains invalid characters"
        
        return True, ""
    
    @classmethod
    def validate_json(cls, data: dict, required_fields: List[str]) -> tuple[bool, str]:
        """
        Validate JSON data has required fields
        
        Returns:
            (is_valid, error_message)
        """
        for field in required_fields:
            if field not in data:
                return False, f"Missing required field: {field}"
        
        return True, ""


class TradeValidator:
    """Specialized validation for trading operations"""
    
    @staticmethod
    def validate_order(order: dict) -> tuple[bool, str]:
        """
        Validate order structure
        
        Expected order:
        {
            "symbol": "BTC/USDT",
            "side": "BUY" or "SELL",
            "amount": 100.0,
            "type": "MARKET" or "LIMIT",
            "price": 50000.0 (optional for limit)
        }
        """
        # Required fields
        required = ["symbol", "side", "amount", "type"]
        valid, error = InputValidator.validate_json(order, required)
        if not valid:
            return False, error
        
        # Validate symbol
        valid, error = InputValidator.validate_symbol(order["symbol"])
        if not valid:
            return False, error
        
        # Validate side
        if order["side"] not in ["BUY", "SELL"]:
            return False, f"Invalid side: {order['side']}"
        
        # Validate amount
        valid, error, _ = InputValidator.validate_amount(order["amount"])
        if not valid:
            return False, error
        
        # Validate type
        if order["type"] not in ["MARKET", "LIMIT"]:
            return False, f"Invalid order type: {order['type']}"
        
        # Validate price for limit orders
        if order["type"] == "LIMIT":
            if "price" not in order:
                return False, "Price required for limit order"
            valid, error, _ = InputValidator.validate_amount(order["price"])
            if not valid:
                return False, f"Invalid price: {error}"
        
        return True, ""


__all__ = ['InputValidator', 'TradeValidator']