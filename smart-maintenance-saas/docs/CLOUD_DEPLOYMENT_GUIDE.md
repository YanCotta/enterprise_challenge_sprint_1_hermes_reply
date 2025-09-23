# Cloud Deployment Guide for Smart Maintenance SaaS UI

## Overview

This guide covers deploying the optimized Streamlit UI to cloud platforms like Render, Railway, Heroku, and others.

## Quick Start - Optimized UI Only

For deploying just the UI service (connecting to a separate API deployment):

```bash
# Build optimized UI container
./build-ui.sh

# Run standalone UI
docker-compose -f docker-compose.ui.yml up -d
```

## Full Stack Deployment with Optimized UI

For deploying the complete system with optimized UI:

```bash
# Use production overrides
docker-compose -f docker-compose.yml -f docker-compose.production.yml up -d
```

## Platform-Specific Deployment

### Render (Recommended)

1. **Create Web Service**
   - Repository: Connect your GitHub repository
   - Dockerfile: `Dockerfile.ui`
   - Build Command: `docker build -f Dockerfile.ui -t ui .`
   - Start Command: (use Dockerfile CMD)

2. **Environment Variables**
   ```
   API_BASE_URL=https://your-api-service.onrender.com
   API_KEY=your_secure_api_key
   ```

3. **Resource Settings**
   - Instance Type: Starter (512MB RAM)
   - Disk Size: 1GB
   - Auto-Deploy: Enabled

### Railway

1. **Deploy from Dockerfile**
   ```bash
   railway deploy --dockerfile Dockerfile.ui
   ```

2. **Environment Variables**
   ```
   PORT=8501
   API_BASE_URL=${{api-service.RAILWAY_STATIC_URL}}
   API_KEY=${{Secrets.API_KEY}}
   ```

### Heroku

1. **heroku.yml Configuration**
   ```yaml
   build:
     web:
       dockerfile: Dockerfile.ui
   run:
     web: streamlit run ui/streamlit_app.py --server.port=$PORT --server.address=0.0.0.0
   ```

2. **Deploy**
   ```bash
   heroku create your-ui-app
   heroku stack:set container
   git push heroku main
   ```

## Environment Variables

### Required
- `API_BASE_URL`: URL of your Smart Maintenance API (e.g., `https://api.yourapp.com`)
- `API_KEY`: API key for authentication

### Optional
- `STREAMLIT_SERVER_PORT`: Port number (default: 8501)
- `STREAMLIT_SERVER_ADDRESS`: Bind address (default: 0.0.0.0)
- `STREAMLIT_BROWSER_GATHER_USAGE_STATS`: Disable analytics (default: false)

## Container Specifications

### Resource Requirements
- **Minimum**: 256MB RAM, 0.25 CPU
- **Recommended**: 512MB RAM, 0.5 CPU
- **Disk**: 1GB (container + temp files)

### Image Size
- **Optimized UI**: ~400MB (vs ~1.2GB for full stack)
- **Build Time**: ~2-3 minutes (vs ~8-10 minutes for full stack)
- **Cold Start**: ~15-30 seconds (vs ~60-90 seconds for full stack)

## Health Checks

The UI includes built-in health checks:
- **Endpoint**: `/_stcore/health`
- **Interval**: 30 seconds
- **Timeout**: 10 seconds
- **Retries**: 3

## Security Considerations

1. **API Key Management**
   - Use platform secret management (Render: Environment Groups, Railway: Secrets)
   - Never commit API keys to code
   - Rotate keys regularly

2. **CORS Configuration**
   - Ensure API allows requests from UI domain
   - Configure proper CORS headers in FastAPI

3. **HTTPS Enforcement**
   - Use platform SSL termination
   - Set `API_BASE_URL` to use HTTPS

## Monitoring and Logging

### Application Logs
```bash
# Railway
railway logs

# Render
# Check logs in dashboard

# Heroku
heroku logs --tail
```

### Health Monitoring
- Platform health checks use `/_stcore/health`
- Custom monitoring can use API connectivity
- Streamlit provides built-in performance metrics

## Troubleshooting

### Common Issues

1. **"Connection Error" to API**
   - Verify `API_BASE_URL` is correct
   - Check API service is running
   - Verify API key is valid

2. **"Module Not Found" errors**
   - Ensure all required files are copied in Dockerfile
   - Check PYTHONPATH is set correctly

3. **Memory/CPU limits**
   - UI uses minimal resources
   - Consider upgrading if consistently hitting limits

4. **Slow startup**
   - Normal for first deployment
   - Subsequent starts should be faster
   - Check platform scaling settings

### Debug Mode

For debugging, temporarily add to Dockerfile:
```dockerfile
ENV STREAMLIT_LOGGER_LEVEL=debug
```

## Performance Optimization

### Tips for Cloud Deployment
1. **Enable caching**: Platform-level caching for static assets
2. **CDN usage**: If platform supports CDN for faster loading
3. **Keep-alive**: Platform settings for connection persistence
4. **Auto-scaling**: Configure based on usage patterns

### Monitoring Performance
- Use platform metrics dashboards
- Monitor response times via health checks
- Track memory and CPU usage trends

## Cost Optimization

### Free Tier Usage
- **Render**: 750 hours/month free
- **Railway**: $5 credit/month
- **Heroku**: 550-1000 dyno hours/month

### Optimization Strategies
- Use free tier for development/staging
- Implement sleep/wake for low-traffic periods
- Monitor resource usage to right-size instances

## Scaling Considerations

The optimized UI can handle:
- **Concurrent Users**: 10-50 on starter instances
- **API Calls**: Limited by API rate limits, not UI
- **Memory Growth**: Minimal due to stateless design
- **Horizontal Scaling**: Platform-dependent load balancing

For high-traffic scenarios:
- Use platform auto-scaling features
- Implement API caching strategies
- Consider dedicated database connections for UI analytics