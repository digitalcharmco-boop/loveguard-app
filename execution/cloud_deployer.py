#!/usr/bin/env python3
"""
LoveGuard Cloud Deployment Script
Deterministic deployment to Google Cloud Run following deploy_application directive
"""

import os
import subprocess
import json
import logging
from typing import Dict, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CloudDeployer:
    def __init__(self):
        """Initialize cloud deployer"""
        self.project_id = os.getenv('GOOGLE_CLOUD_PROJECT', 'loveguard-app')
        self.region = 'us-central1'
        self.service_name = 'loveguard-app'
        
    def deploy_to_cloud_run(
        self,
        environment: str = 'production',
        custom_domain: Optional[str] = None
    ) -> Dict:
        """
        Deploy LoveGuard to Google Cloud Run
        
        Args:
            environment: deployment environment (development, staging, production)
            custom_domain: optional custom domain
            
        Returns:
            Deployment result dictionary
        """
        
        logger.info(f"Starting deployment to Google Cloud Run - {environment}")
        
        try:
            # Step 1: Validate prerequisites
            self._validate_prerequisites()
            
            # Step 2: Build container
            build_result = self._build_container()
            if not build_result['success']:
                return build_result
            
            # Step 3: Deploy to Cloud Run
            deploy_result = self._deploy_service(environment)
            if not deploy_result['success']:
                return deploy_result
            
            # Step 4: Configure domain (if provided)
            if custom_domain:
                domain_result = self._configure_domain(custom_domain)
                deploy_result['custom_domain'] = domain_result
            
            logger.info("Deployment completed successfully")
            return deploy_result
            
        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'stage': 'deployment'
            }
    
    def _validate_prerequisites(self):
        """Validate that all prerequisites are met"""
        
        # Check if gcloud is installed and authenticated
        try:
            result = subprocess.run(['gcloud', 'auth', 'list'], 
                                  capture_output=True, text=True, check=True)
            if 'ACTIVE' not in result.stdout:
                raise Exception("No active gcloud authentication found. Run: gcloud auth login")
        except FileNotFoundError:
            raise Exception("gcloud CLI not found. Install Google Cloud SDK")
        
        # Check if Docker is available
        try:
            subprocess.run(['docker', '--version'], 
                          capture_output=True, check=True)
        except FileNotFoundError:
            logger.warning("Docker not found locally - will use Cloud Build")
        
        # Verify project exists
        try:
            result = subprocess.run(['gcloud', 'config', 'get-value', 'project'], 
                                  capture_output=True, text=True, check=True)
            current_project = result.stdout.strip()
            logger.info(f"Current project: {current_project}")
        except:
            raise Exception("No active gcloud project. Run: gcloud config set project PROJECT_ID")
    
    def _build_container(self) -> Dict:
        """Build container using Google Cloud Build"""
        
        try:
            logger.info("Building container with Cloud Build...")
            
            image_url = f"gcr.io/{self.project_id}/{self.service_name}"
            
            # Build using Cloud Build
            cmd = [
                'gcloud', 'builds', 'submit',
                '--tag', image_url,
                '.'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("Container build successful")
                return {
                    'success': True,
                    'image_url': image_url
                }
            else:
                logger.error(f"Build failed: {result.stderr}")
                return {
                    'success': False,
                    'error': result.stderr,
                    'stage': 'build'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'stage': 'build'
            }
    
    def _deploy_service(self, environment: str) -> Dict:
        """Deploy service to Cloud Run"""
        
        try:
            logger.info(f"Deploying to Cloud Run ({environment})...")
            
            image_url = f"gcr.io/{self.project_id}/{self.service_name}"
            
            # Environment-specific configurations
            configs = {
                'development': {
                    'cpu': '1',
                    'memory': '1Gi',
                    'max_instances': '2',
                    'min_instances': '0'
                },
                'staging': {
                    'cpu': '1', 
                    'memory': '1Gi',
                    'max_instances': '5',
                    'min_instances': '0'
                },
                'production': {
                    'cpu': '2',
                    'memory': '2Gi', 
                    'max_instances': '100',
                    'min_instances': '1'
                }
            }
            
            config = configs.get(environment, configs['production'])
            
            # Build deployment command
            cmd = [
                'gcloud', 'run', 'deploy', self.service_name,
                '--image', image_url,
                '--platform', 'managed',
                '--region', self.region,
                '--allow-unauthenticated',
                '--port', '8080',
                '--cpu', config['cpu'],
                '--memory', config['memory'],
                '--max-instances', config['max_instances'],
                '--min-instances', config['min_instances'],
                '--set-env-vars', f'APP_ENV={environment}',
                '--quiet'
            ]
            
            # Add environment variables if available
            env_vars = []
            if os.getenv('OPENAI_API_KEY'):
                env_vars.append(f'OPENAI_API_KEY={os.getenv("OPENAI_API_KEY")}')
            if os.getenv('STRIPE_SECRET_KEY'):
                env_vars.append(f'STRIPE_SECRET_KEY={os.getenv("STRIPE_SECRET_KEY")}')
            if os.getenv('STRIPE_PUBLISHABLE_KEY'):
                env_vars.append(f'STRIPE_PUBLISHABLE_KEY={os.getenv("STRIPE_PUBLISHABLE_KEY")}')
            
            if env_vars:
                cmd.extend(['--set-env-vars', ','.join(env_vars)])
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Extract service URL from output
                service_url = self._extract_service_url(result.stdout)
                
                logger.info(f"Deployment successful: {service_url}")
                
                return {
                    'success': True,
                    'service_url': service_url,
                    'environment': environment,
                    'resource_config': config,
                    'deployment_output': result.stdout
                }
            else:
                logger.error(f"Deployment failed: {result.stderr}")
                return {
                    'success': False,
                    'error': result.stderr,
                    'stage': 'deploy'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'stage': 'deploy'
            }
    
    def _extract_service_url(self, output: str) -> str:
        """Extract service URL from gcloud output"""
        
        for line in output.split('\n'):
            if 'https://' in line and 'run.app' in line:
                # Extract URL from line
                start = line.find('https://')
                if start != -1:
                    end = line.find(' ', start)
                    if end == -1:
                        end = len(line)
                    return line[start:end].strip()
        
        return f"https://{self.service_name}-xxxxx-uc.a.run.app"
    
    def _configure_domain(self, custom_domain: str) -> Dict:
        """Configure custom domain for Cloud Run service"""
        
        try:
            logger.info(f"Configuring custom domain: {custom_domain}")
            
            # Map domain to service
            cmd = [
                'gcloud', 'run', 'domain-mappings', 'create',
                '--domain', custom_domain,
                '--service', self.service_name,
                '--region', self.region,
                '--quiet'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'domain': custom_domain,
                    'ssl_status': 'pending'
                }
            else:
                return {
                    'success': False,
                    'error': result.stderr,
                    'domain': custom_domain
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'domain': custom_domain
            }
    
    def check_health(self, service_url: str) -> Dict:
        """Check health of deployed service"""
        
        try:
            import urllib.request
            
            # Try to access the service
            response = urllib.request.urlopen(service_url, timeout=30)
            
            if response.status == 200:
                return {
                    'healthy': True,
                    'status_code': response.status,
                    'service_url': service_url
                }
            else:
                return {
                    'healthy': False,
                    'status_code': response.status,
                    'service_url': service_url
                }
                
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e),
                'service_url': service_url
            }

def main():
    """Command line interface for deployment"""
    import sys
    
    deployer = CloudDeployer()
    
    environment = sys.argv[1] if len(sys.argv) > 1 else 'production'
    custom_domain = sys.argv[2] if len(sys.argv) > 2 else None
    
    print(f"Deploying LoveGuard to {environment} environment...")
    
    result = deployer.deploy_to_cloud_run(environment, custom_domain)
    
    if result['success']:
        print(f"SUCCESS: Deployed to {result['service_url']}")
        
        # Health check
        health = deployer.check_health(result['service_url'])
        if health['healthy']:
            print("Health check: PASSED")
        else:
            print("Health check: FAILED")
            
    else:
        print(f"FAILED: {result['error']}")
        sys.exit(1)

if __name__ == "__main__":
    main()