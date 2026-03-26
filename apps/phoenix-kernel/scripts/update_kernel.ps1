# update_kernel.ps1
# Automatically adds hardening code to phoenix_kernel_v14c.py

param(
    [switch]$Backup,
    [switch]$Verify
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "PHOENIX KERNEL HARDENING INTEGRATION" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Set paths
$kernelPath = "phoenix_kernel_v14c.py"
$backupPath = "phoenix_kernel_v14c.py.backup"

# Step 1: Backup original file
if ($Backup -or (Test-Path $kernelPath)) {
    Copy-Item $kernelPath $backupPath -Force
    Write-Host "✅ Backup created: $backupPath" -ForegroundColor Green
}

# Step 2: Read current kernel content
$content = Get-Content $kernelPath -Raw

# Step 3: Check if already integrated
if ($content -match "HARDENING IMPORTS") {
    Write-Host "⚠️ Hardening code already present. Use -Force to overwrite." -ForegroundColor Yellow
    exit
}

# Step 4: Define hardening imports to add
$hardeningImports = @"
# ============================================================================
# HARDENING IMPORTS - ADDED BY update_kernel.ps1
# ============================================================================

# Phase 1: Critical Infrastructure
try:
    from workers.decorators import handle_errors, with_timeout, log_execution
    print("✅ Error handling decorators loaded")
except ImportError as e:
    print(f"⚠️ Error handling decorators not loaded: {e}")

try:
    from logging_config import setup_logging, get_logger
    setup_logging(log_level="INFO", log_file="logs/phoenix.log")
    logger = get_logger("kernel")
    print("✅ Structured logging configured")
except ImportError as e:
    print(f"⚠️ Structured logging not configured: {e}")

try:
    from workers.backup_worker import BackupWorker
    print("✅ Backup worker ready")
except ImportError as e:
    print(f"⚠️ Backup worker not available: {e}")

try:
    from graceful_shutdown import GracefulShutdown
    print("✅ Graceful shutdown handler ready")
except ImportError as e:
    print(f"⚠️ Graceful shutdown not available: {e}")

# Phase 2: Security & Operations
try:
    from security.key_manager import KeyManager
    print("✅ Key manager ready")
except ImportError as e:
    print(f"⚠️ Key manager not available: {e}")

try:
    from security.rate_limiter import RateLimiter, PerEndpointLimiter
    print("✅ Rate limiter ready")
except ImportError as e:
    print(f"⚠️ Rate limiter not available: {e}")

try:
    from security.input_validator import InputValidator, TradeValidator
    print("✅ Input validator ready")
except ImportError as e:
    print(f"⚠️ Input validator not available: {e}")

try:
    from monitoring.metrics import *
    print("✅ Prometheus metrics ready")
except ImportError as e:
    print(f"⚠️ Metrics not available: {e}")

# Phase 3: Exchange Integration
try:
    from exchange.router import ExchangeRouter, ExchangeType
    from exchange.binance_connector import BinanceConnector
    from exchange.constitutional_trader import ConstitutionalTrader
    from workers.exchange_worker import ExchangeWorker
    print("✅ Exchange integration ready")
except ImportError as e:
    print(f"⚠️ Exchange integration not available: {e}")

"@

# Step 5: Define hardening initialization code to add to __init__
$hardeningInit = @"

        # ============================================================================
        # HARDENING INITIALIZATION - ADDED BY update_kernel.ps1
        # ============================================================================
        
        # Initialize backup worker
        try:
            self.backup_worker = BackupWorker()
            logger.info("✅ Backup worker initialized")
        except Exception as e:
            logger.warning(f"⚠️ Backup worker init failed: {e}")
        
        # Initialize graceful shutdown
        try:
            self.graceful_shutdown = GracefulShutdown(self)
            logger.info("✅ Graceful shutdown handler initialized")
        except Exception as e:
            logger.warning(f"⚠️ Graceful shutdown init failed: {e}")
        
        # Initialize key manager for API keys
        try:
            master_password = os.getenv("REZ_MASTER_KEY")
            if master_password:
                self.key_manager = KeyManager(master_password=master_password)
                logger.info("✅ Key manager initialized")
            else:
                logger.info("⚠️ REZ_MASTER_KEY not set - API key storage disabled")
        except Exception as e:
            logger.warning(f"⚠️ Key manager init failed: {e}")
        
        # Initialize rate limiter
        try:
            self.rate_limiter = PerEndpointLimiter()
            logger.info("✅ Rate limiter initialized")
        except Exception as e:
            logger.warning(f"⚠️ Rate limiter init failed: {e}")
        
        # Initialize exchange router
        try:
            self.exchange_router = ExchangeRouter()
            binance = BinanceConnector(testnet=True)
            self.exchange_router.register_exchange("binance_testnet", binance, is_primary=True)
            logger.info("✅ Exchange router initialized with Binance testnet")
        except Exception as e:
            logger.warning(f"⚠️ Exchange router init failed: {e}")
        
        # Initialize constitutional trader
        try:
            self.constitutional_trader = ConstitutionalTrader(
                binance if 'binance' in dir() else None,
                constitution if 'constitution' in dir() else None
            )
            logger.info("✅ Constitutional trader initialized")
        except Exception as e:
            logger.warning(f"⚠️ Constitutional trader init failed: {e}")
        
"@

# Step 6: Define new endpoints to add to _setup_routes
$hardeningRoutes = @"

        @self.app.get("/metrics")
        async def metrics():
            """Prometheus metrics endpoint"""
            try:
                from monitoring.metrics import generate_latest, CONTENT_TYPE_LATEST
                from fastapi.responses import Response
                return Response(
                    content=generate_latest(),
                    media_type=CONTENT_TYPE_LATEST
                )
            except ImportError:
                return {"error": "Metrics not available"}

        @self.app.get("/security/keys")
        async def list_keys():
            """List stored API keys (requires authentication)"""
            if hasattr(self, 'key_manager'):
                return {"exchanges": self.key_manager.list_exchanges()}
            return {"error": "Key manager not initialized"}

        @self.app.post("/security/keys/binance")
        async def add_binance_keys(request: Request):
            """Add Binance API keys"""
            data = await request.json()
            if hasattr(self, 'key_manager'):
                result = self.key_manager.encrypt_api_key(
                    "binance",
                    data.get("api_key"),
                    data.get("api_secret")
                )
                return result
            return {"error": "Key manager not initialized"}

        @self.app.get("/exchange/status")
        async def exchange_status():
            """Get exchange connection status"""
            if hasattr(self, 'exchange_router'):
                health = await self.exchange_router.health_check_all()
                return {
                    "exchanges": health,
                    "active": self.exchange_router.active
                }
            return {"error": "Exchange router not initialized"}

        @self.app.post("/exchange/trade")
        async def execute_trade(request: Request):
            """Execute a trade with constitutional enforcement"""
            data = await request.json()
            
            # Validate input
            valid, error = TradeValidator.validate_order(data)
            if not valid:
                return {"error": error, "success": False}
            
            # Check rate limit
            if hasattr(self, 'rate_limiter'):
                allowed = await self.rate_limiter.check("trading", request.client.host)
                if not allowed:
                    return {"error": "Rate limit exceeded", "success": False}
            
            # Execute via constitutional trader
            if hasattr(self, 'constitutional_trader'):
                from exchange.base import Order
                order = Order(
                    symbol=data["symbol"],
                    side=data["side"],
                    order_type=data.get("type", "MARKET"),
                    quantity=data["amount"],
                    price=data.get("price")
                )
                result = await self.constitutional_trader.execute_trade(
                    order,
                    portfolio_value=data.get("portfolio_value", 10000),
                    daily_pnl=data.get("daily_pnl", 0)
                )
                return result
            
            return {"error": "Constitutional trader not initialized"}

"@

# Step 7: Find insertion points
$importSectionStart = $content.IndexOf("import sys")
$initMethodStart = $content.IndexOf("def __init__(self):")
$routesMethodStart = $content.IndexOf("def _setup_routes(self):")
$workersLoadedLine = $content.IndexOf("logger.info(f\"🐝 Ultimate swarm assembled:")

Write-Host "`n📝 Found insertion points:" -ForegroundColor Yellow
Write-Host "  Imports section at: $importSectionStart" -ForegroundColor Gray
Write-Host "  __init__ method at: $initMethodStart" -ForegroundColor Gray
Write-Host "  _setup_routes method at: $routesMethodStart" -ForegroundColor Gray

# Step 8: Build new content
Write-Host "`n🔧 Building updated kernel..." -ForegroundColor Yellow

# Find where to insert imports (after existing imports)
$importEnd = $content.IndexOf("# ============================================================================", $importSectionStart + 100)
if ($importEnd -eq -1) {
    $importEnd = $content.IndexOf("class Config:", $importSectionStart)
}

$newContent = $content.Substring(0, $importEnd) + "`n" + $hardeningImports + "`n" + $content.Substring($importEnd)

# Find where to insert init code (after workers are loaded)
$initInsert = $content.IndexOf("self.reflex = ReflexCommands(self)", $initMethodStart)
if ($initInsert -eq -1) {
    $initInsert = $content.IndexOf("self._setup_routes()", $initMethodStart)
}

$newContent = $newContent.Substring(0, $initInsert) + $hardeningInit + "`n        " + $newContent.Substring($initInsert)

# Find where to insert routes (before the final @self.app.options)
$routesInsert = $content.IndexOf("@self.app.options", $routesMethodStart)
if ($routesInsert -eq -1) {
    $routesInsert = $content.IndexOf("async def options_handler", $routesMethodStart)
}

$newContent = $newContent.Substring(0, $routesInsert) + $hardeningRoutes + "`n" + $newContent.Substring($routesInsert)

# Step 9: Save updated kernel
Write-Host "`n💾 Saving updated kernel..." -ForegroundColor Yellow
$newContent | Out-File -FilePath $kernelPath -Encoding utf8
Write-Host "✅ Kernel updated successfully!" -ForegroundColor Green

# Step 10: Verify syntax
if ($Verify) {
    Write-Host "`n🔍 Verifying syntax..." -ForegroundColor Yellow
    $result = python -m py_compile $kernelPath 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Syntax check passed!" -ForegroundColor Green
    } else {
        Write-Host "❌ Syntax error detected!" -ForegroundColor Red
        Write-Host $result -ForegroundColor Red
    }
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "UPDATE COMPLETE" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host @"

🎉 Kernel updated with hardening code!

Next steps:
  1. Test the kernel: python phoenix_kernel_v14c.py
  2. If errors occur, restore backup: Copy-Item $backupPath $kernelPath
  3. Add your Binance API keys to .env
  4. Run: REZ IT UP --live

Backup saved to: $backupPath
"@ -ForegroundColor Green