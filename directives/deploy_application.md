# Deploy Application Directive

## Goal
Deploy LoveGuard application to Google Cloud Run with proper security, scaling, and monitoring configurations.

## Inputs
- `environment` (string): "development", "staging", or "production"
- `project_id` (string): Google Cloud Project ID
- `region` (string): Deployment region (default: us-central1)
- `custom_domain` (string, optional): Custom domain for production

## Tools/Scripts to Use
- `execution/cloud_deployer.py` - Main deployment orchestrator
- `execution/env_manager.py` - Environment variable management
- `execution/health_checker.py` - Post-deployment verification
- `deploy.bat` - Windows deployment script (existing)

## Process Flow
1. **Pre-deployment Checks**
   - Verify Google Cloud CLI authentication
   - Check required environment variables are set
   - Validate Docker configuration and connectivity
   - Ensure billing is enabled on GCP project

2. **Environment Configuration**
   - Call `execution/env_manager.py` to prepare environment variables
   - Validate API keys (OpenAI, Stripe) are present
   - Set appropriate resource limits based on environment
   - Configure logging and monitoring settings

3. **Container Build & Push**
   - Build Docker container using Cloud Build
   - Push to Google Container Registry
   - Tag with environment and timestamp
   - Verify image integrity

4. **Cloud Run Deployment**
   - Deploy to Cloud Run with proper configuration
   - Set CPU, memory, and concurrency limits
   - Configure environment variables securely
   - Enable HTTPS and proper security headers

5. **Post-deployment Verification**
   - Call `execution/health_checker.py`
   - Test critical application endpoints
   - Verify payment processing (test mode)
   - Check AI analysis functionality

6. **Domain Configuration** (if custom_domain provided)
   - Configure Cloud Run custom domain mapping
   - Set up SSL certificates via Google-managed certs
   - Update DNS settings (manual step, provide instructions)

## Expected Outputs
```json
{
  "deployment_status": "succeeded|failed",
  "service_url": "https://loveguard-app-xxxxx-uc.a.run.app",
  "custom_url": "https://app.loveguard.com",
  "health_check_results": {
    "app_status": "healthy|unhealthy",
    "ai_analysis": "working|failed", 
    "payment_processing": "working|failed"
  },
  "resource_usage": {
    "cpu": "1 vCPU",
    "memory": "1Gi",
    "max_instances": "10"
  }
}
```

## Environment-Specific Configurations

### Development
- 1 vCPU, 1Gi memory
- Max 2 instances
- Allow unauthenticated access
- Verbose logging enabled

### Staging  
- 1 vCPU, 1Gi memory
- Max 5 instances
- Require authentication
- Standard logging

### Production
- 2 vCPU, 2Gi memory
- Max 100 instances
- Allow unauthenticated (public app)
- Error-only logging
- Enable monitoring and alerting

## Edge Cases
- **Build Failures**: Check Dockerfile syntax, dependencies, resource limits
- **Authentication Issues**: Verify service account permissions, API enablement
- **Resource Quotas**: Handle quota exceeded errors, request increases
- **Regional Outages**: Have backup regions ready for critical deployments
- **DNS Propagation**: Custom domains may take 24-48 hours to propagate
- **Cold Starts**: Configure min instances for production to reduce latency

## Success Criteria
- Deployment completes within 10 minutes
- Application responds to health checks within 30 seconds
- All critical features verified working
- HTTPS properly configured and enforced
- Resource usage within expected bounds

## Error Handling
- Build failures → check logs, fix issues, retry
- Deployment timeouts → increase timeout, check resource availability  
- Health check failures → rollback to previous version
- Authentication errors → verify service account setup
- Quota exceeded → request quota increase, deploy to different region

## Security Requirements
- All traffic over HTTPS only
- Environment variables encrypted at rest
- No secrets in container images
- Proper IAM roles and permissions
- Security headers configured (HSTS, CSP, etc.)

## Resource Limits
- CPU: 1-4 vCPU depending on environment
- Memory: 1-4Gi depending on environment
- Request timeout: 60 seconds maximum
- Concurrent requests: 1000 per instance
- Storage: Stateless, no persistent volumes

## Monitoring & Alerting
- Enable Cloud Run monitoring
- Set up uptime checks every 5 minutes
- Alert on error rates >5%
- Monitor response times >2 seconds
- Track container restarts and failures

## Cost Optimization
- Use minimum instances = 0 for development
- Set appropriate CPU and memory limits
- Enable request-based pricing
- Monitor and optimize cold start times
- Use Cloud Run's automatic scaling

## Rollback Procedures
- Keep previous 5 revisions for quick rollback
- Automated rollback on health check failures
- Manual rollback commands documented
- Database migration rollback procedures
- Communication plan for user notifications

## Updates Needed
- When Google Cloud Run features change
- If new regions become available
- When security requirements are updated
- If resource needs change with user growth