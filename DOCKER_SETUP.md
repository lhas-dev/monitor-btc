# 🐳 Docker Setup Guide

Quick guide to run BTC Monitor using Docker.

## Prerequisites

- Docker installed ([Get Docker](https://docs.docker.com/get-docker/))
- Docker Compose installed (usually comes with Docker Desktop)

## Quick Start (3 Steps)

### 1. Configure Telegram

Edit `config.py` and add your Telegram credentials:

```python
TELEGRAM_BOT_TOKEN = "your_bot_token"
TELEGRAM_CHAT_ID = "your_chat_id"
TELEGRAM_ENABLED = True
```

### 2. Start the Monitor

Using the management script (recommended):
```bash
./manage.sh start
```

Or using Docker Compose directly:
```bash
docker-compose up -d
```

### 3. View Logs

```bash
./manage.sh logs
```

Or:
```bash
docker-compose logs -f btc-monitor
```

## Management Commands

The `manage.sh` script provides easy commands:

```bash
./manage.sh start       # Start the monitor
./manage.sh stop        # Stop the monitor
./manage.sh restart     # Restart the monitor
./manage.sh logs        # View real-time logs
./manage.sh status      # Check status
./manage.sh test        # Test Telegram notifications
./manage.sh rebuild     # Rebuild and restart
./manage.sh clean       # Remove everything
```

## Docker Compose Commands

If you prefer using Docker Compose directly:

```bash
# Start (detached mode)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose stop

# Restart
docker-compose restart

# Remove
docker-compose down

# Rebuild
docker-compose build --no-cache
docker-compose up -d
```

## File Structure

```
monitor-btc/
├── Dockerfile              # Docker image definition
├── docker-compose.yml      # Container orchestration
├── .dockerignore          # Files to exclude from build
├── manage.sh              # Management script
├── config.py              # Configuration (mounted as volume)
├── monitor_btc.py         # Main application
└── signals_log.json       # Generated signal logs (persistent)
```

## Persistent Data

The following are mounted as volumes and persist across container restarts:

- `config.py` - Your configuration (read-only)
- `signals_log.json` - Trading signals history
- `logs/` - Application logs

## Configuration Changes

After editing `config.py`, restart the container:

```bash
./manage.sh restart
```

Or:
```bash
docker-compose restart
```

## Viewing Signals

Signals are saved to `signals_log.json` in the project directory:

```bash
# View signals
cat signals_log.json | python -m json.tool

# Or use jq for better formatting
cat signals_log.json | jq '.'
```

## Resource Limits

The default docker-compose.yml sets resource limits:

- **CPU**: 0.5 cores max, 0.25 cores reserved
- **Memory**: 512MB max, 256MB reserved

You can adjust these in `docker-compose.yml` if needed.

## Health Checks

The container includes health checks that:
- Run every 5 minutes
- Verify Binance API connectivity
- Automatically restart if unhealthy

Check health status:
```bash
docker-compose ps
```

## Troubleshooting

### Container won't start

```bash
# Check logs for errors
docker-compose logs btc-monitor

# Verify config.py has valid values
cat config.py
```

### No Telegram notifications

```bash
# Test Telegram configuration
./manage.sh test

# Or manually
docker-compose run --rm btc-monitor python test_telegram.py
```

### Container keeps restarting

```bash
# View logs to identify the issue
docker-compose logs -f btc-monitor

# Common issues:
# - Invalid Telegram credentials
# - Network connectivity problems
# - Missing config.py
```

### Update to latest version

```bash
# Pull latest code
git pull

# Rebuild container
./manage.sh rebuild
```

## Production Deployment

### Running on a Server

1. **Clone repository on server:**
   ```bash
   git clone <your-repo-url>
   cd monitor-btc
   ```

2. **Configure:**
   ```bash
   nano config.py
   # Add your Telegram credentials
   ```

3. **Start in detached mode:**
   ```bash
   docker-compose up -d
   ```

4. **Monitor logs:**
   ```bash
   docker-compose logs -f btc-monitor
   ```

### Auto-restart on System Boot

Docker Compose is configured with `restart: unless-stopped`, which means:
- Container restarts automatically if it crashes
- Container starts automatically on system boot
- Container stays stopped if you manually stop it

### Running in Background

The monitor runs in detached mode by default (`-d` flag), so it continues running even when you close your terminal.

## Advanced Configuration

### Using Environment Variables

Create a `.env` file (copy from `.env.example`):

```bash
cp .env.example .env
nano .env
```

Environment variables override values in `config.py`.

### Custom Timezone

Edit `docker-compose.yml`:

```yaml
environment:
  - TZ=America/Sao_Paulo  # Change to your timezone
```

### Log Rotation

Logs are automatically rotated:
- Max size: 10MB per file
- Max files: 3
- Older logs are automatically deleted

## Security Notes

- ⚠️ Never commit `config.py` with real credentials
- ⚠️ Use `.gitignore` to exclude sensitive files
- ⚠️ Keep your bot token private
- ⚠️ Regularly update the Docker image

## Support

For issues or questions, check the main [README.md](README.md) or create an issue.

---

**Happy Trading! 🚀**
