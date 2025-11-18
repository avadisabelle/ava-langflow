# Deployment Checklist - Agentic Flywheel v2.0.0

This guide provides a step-by-step deployment checklist for getting Agentic Flywheel v2.0.0 up and running in production.

## Prerequisites

### Required Services
- [ ] **Flowise** instance running (default: `http://localhost:3000`)
- [ ] **Langflow** instance running (default: `http://localhost:7860`)
- [ ] Python 3.8+ installed

### Optional Services (Recommended)
- [ ] **Redis** server running (for session persistence)
- [ ] **Langfuse** account (for observability and tracing)
- [ ] **PostgreSQL** database (for Flowise admin analytics)

---

## Step 1: Installation

### Option A: From PyPI (Recommended)

```bash
# Full installation with all features
pip install agentic-flywheel[full]

# Verify installation
agentic-flywheel --version
```

### Option B: From Source

```bash
# Clone repository
git clone https://github.com/jgwill/agentic-flywheel.git
cd agentic-flywheel/src/agentic_flywheel

# Install with all dependencies
pip install -e .[full]

# Verify installation
agentic-flywheel --version
```

**Checklist**:
- [ ] Installation completed without errors
- [ ] CLI command `agentic-flywheel` available
- [ ] Version shows 2.0.0 or higher

---

## Step 2: Environment Configuration

### Create Configuration File

```bash
# Copy example configuration
cp .env.example .env

# Edit with your values
nano .env  # or use your preferred editor
```

### Required Configuration

Edit `.env` and set these **required** values:

```bash
# Backend URLs
FLOWISE_BASE_URL=http://localhost:3000
LANGFLOW_BASE_URL=http://localhost:7860
```

### Optional Configuration (Recommended)

```bash
# Langfuse Observability (Recommended)
LANGFUSE_ENABLED=true
LANGFUSE_PUBLIC_KEY=pk-lf-your-public-key
LANGFUSE_SECRET_KEY=sk-lf-your-secret-key
LANGFUSE_HOST=https://cloud.langfuse.com

# Redis Persistence (Recommended)
REDIS_ENABLED=true
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_TTL_SECONDS=604800  # 7 days

# Admin Intelligence (Optional)
FLOWISE_DB_HOST=localhost
FLOWISE_DB_PORT=5432
FLOWISE_DB_NAME=flowise
FLOWISE_DB_USER=flowise_admin
FLOWISE_DB_PASSWORD=your_db_password

# Logging
LOG_LEVEL=INFO
```

**Checklist**:
- [ ] `.env` file created
- [ ] Backend URLs configured
- [ ] API keys added (if required by backends)
- [ ] Optional services configured (Redis, Langfuse)

---

## Step 3: Health Check

Run the comprehensive health check utility:

```bash
python scripts/health_check.py
```

Expected output:
```
========================================================
Environment Configuration
========================================================

✅ FLOWISE_BASE_URL
   http://localhost:3000
✅ LANGFLOW_BASE_URL
   http://localhost:7860

========================================================
Backend Status
========================================================

✅ Backend Registry
   2 backends registered
✅ Backend Health
   2/2 backends healthy

========================================================
Overall System Health
========================================================
✅ Checks Passed: 8
❌ Checks Failed: 0
⚠️  Warnings: 2

🎉 All systems fully operational!
Ready for production deployment.
```

**Checklist**:
- [ ] Health check script runs without errors
- [ ] All backends are healthy
- [ ] No critical failures
- [ ] Optional services warnings are acceptable

---

## Step 4: Start Universal MCP Server

### Start the Server

```bash
agentic-flywheel-universal
```

Expected output:
```
Agentic Flywheel Universal MCP Server v2.0.0
Loaded 18 MCP tools across 4 categories
Server ready on stdio
```

### Alternative: Background Mode

```bash
# Start in background
nohup agentic-flywheel-universal > server.log 2>&1 &

# Check logs
tail -f server.log
```

**Checklist**:
- [ ] Server starts without errors
- [ ] 18 tools loaded successfully
- [ ] Server responds to requests

---

## Step 5: Test Basic Functionality

### Test 1: Universal Query

```bash
# Run example script
python examples/basic_query.py
```

Expected: Successful responses from both Flowise and Langflow backends

### Test 2: Backend Status

Use your MCP client to call:

```json
{
  "tool": "backend_registry_status",
  "arguments": {}
}
```

Expected: JSON response showing healthy backends

### Test 3: Flow Discovery

```json
{
  "tool": "backend_list_flows",
  "arguments": {
    "backend_filter": "all"
  }
}
```

Expected: List of available flows from both backends

**Checklist**:
- [ ] Universal query works
- [ ] Backend status returns healthy
- [ ] Flow discovery returns results
- [ ] Routing selects appropriate backends

---

## Step 6: Performance Benchmark (Optional)

Run performance tests to establish baseline:

```bash
python scripts/benchmark.py
```

Review results and compare against targets:
- Universal Query: <2000ms
- Backend Selection: <200ms
- Health Check: <500ms
- Redis Operations: <50ms

**Checklist**:
- [ ] Benchmark completes successfully
- [ ] Performance meets or exceeds targets
- [ ] No timeout errors

---

## Step 7: Integration Verification

### Run Full Test Suite

```bash
# All tests
pytest tests/ -v

# Integration tests only
pytest tests/ -v -m integration

# With coverage report
pytest tests/ -v --cov=agentic_flywheel --cov-report=html
```

Expected: 100% test coverage, all tests passing

**Checklist**:
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] Test coverage ≥ 100%

---

## Step 8: Production Configuration

### Security Hardening

```bash
# Set restrictive file permissions
chmod 600 .env

# Ensure API keys are not in version control
echo ".env" >> .gitignore
```

### Monitoring Setup

1. **Langfuse Dashboard**: Configure alerts for trace failures
2. **Redis Monitoring**: Set up Redis monitoring (if using persistence)
3. **Health Checks**: Schedule periodic health check runs
4. **Logs**: Configure log aggregation (ELK, CloudWatch, etc.)

**Checklist**:
- [ ] Environment file secured
- [ ] API keys not in git
- [ ] Monitoring configured
- [ ] Logging configured
- [ ] Alerts set up

---

## Step 9: Backup & Recovery

### Configuration Backup

```bash
# Backup environment (without secrets)
cp .env.example config.backup

# Backup flow configurations
agentic-flywheel export-config > flows.backup.json
```

### Recovery Testing

```bash
# Test configuration restoration
cp .env.example .env.test
# Verify with health check
python scripts/health_check.py
```

**Checklist**:
- [ ] Configuration backed up
- [ ] Flow definitions exported
- [ ] Recovery procedure documented
- [ ] Backup restoration tested

---

## Step 10: Documentation & Training

### Team Documentation

1. **Share deployment guide**: This file
2. **Share usage guide**: `USAGE_GUIDE.md`
3. **Share examples**: `examples/` directory
4. **Share troubleshooting**: See below

### Quick Reference

```bash
# Start server
agentic-flywheel-universal

# Health check
python scripts/health_check.py

# Performance test
python scripts/benchmark.py

# View logs
tail -f server.log

# Stop server
pkill -f agentic-flywheel-universal
```

**Checklist**:
- [ ] Team trained on usage
- [ ] Documentation distributed
- [ ] Support contacts established
- [ ] Escalation path defined

---

## Production Readiness Checklist

### ✅ Must Have (Required for Production)
- [ ] Backend services running (Flowise + Langflow)
- [ ] Environment variables configured
- [ ] Health checks passing
- [ ] Universal MCP server running
- [ ] Basic queries working
- [ ] Security hardened (.env permissions)

### ⭐ Should Have (Highly Recommended)
- [ ] Redis persistence enabled
- [ ] Langfuse observability configured
- [ ] Monitoring and alerting set up
- [ ] Backup procedures documented
- [ ] Performance benchmarks run
- [ ] Integration tests passing

### 💡 Nice to Have (Optional)
- [ ] Admin intelligence configured
- [ ] Custom flows deployed
- [ ] Load balancing configured
- [ ] Auto-scaling enabled
- [ ] Disaster recovery plan
- [ ] Team training completed

---

## Troubleshooting

### Issue: Backend Connection Failed

**Symptoms**: Health check fails with connection errors

**Solutions**:
1. Verify backend services are running:
   ```bash
   curl http://localhost:3000/api/v1/health
   curl http://localhost:7860/api/v1/health
   ```
2. Check firewall rules
3. Verify `FLOWISE_BASE_URL` and `LANGFLOW_BASE_URL` in `.env`
4. Check API keys if authentication is required

### Issue: Redis Connection Failed

**Symptoms**: Warnings about Redis not available

**Solutions**:
1. Verify Redis is running:
   ```bash
   redis-cli ping
   ```
2. Check `REDIS_HOST` and `REDIS_PORT` in `.env`
3. If not needed, set `REDIS_ENABLED=false`

### Issue: Performance Below Targets

**Symptoms**: Benchmark shows slow response times

**Solutions**:
1. Check backend health and load
2. Verify network latency to backends
3. Review Redis performance (if enabled)
4. Check system resources (CPU, memory)
5. Consider backend scaling

### Issue: Tests Failing

**Symptoms**: pytest shows failures

**Solutions**:
1. Ensure all dependencies installed: `pip install -e .[full]`
2. Verify environment variables set
3. Check backend availability
4. Review test logs for specific failures

---

## Support & Resources

### Documentation
- **Usage Guide**: `USAGE_GUIDE.md`
- **Project Summary**: `FINAL_SUMMARY.md`
- **README**: `src/agentic_flywheel/README.md`
- **RISE Specs**: `rispecs/` directory

### Examples
- **Basic Usage**: `examples/basic_query.py`
- **Health Check**: `scripts/health_check.py`
- **Benchmarking**: `scripts/benchmark.py`

### Online Resources
- **Repository**: https://github.com/jgwill/agentic-flywheel
- **Issues**: https://github.com/jgwill/agentic-flywheel/issues
- **PyPI**: https://pypi.org/project/agentic-flywheel/

---

## Post-Deployment

### Week 1
- [ ] Monitor health checks daily
- [ ] Review Langfuse traces
- [ ] Check performance metrics
- [ ] Validate session persistence

### Month 1
- [ ] Analyze usage patterns
- [ ] Review admin analytics
- [ ] Optimize backend selection
- [ ] Update documentation

### Ongoing
- [ ] Monthly performance reviews
- [ ] Quarterly security audits
- [ ] Regular backup testing
- [ ] Continuous improvement

---

**Deployment Status**: ✅ Production Ready

Built with ❤️ for the AI automation community
