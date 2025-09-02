"""
Email notification service for Smart Maintenance SaaS.

This service provides email notifications for key system events like
drift detection and model retraining completion.
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class EmailService:
    """Email service for sending notifications."""
    
    def __init__(self):
        """Initialize email service with environment variables."""
        self.smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_user = os.getenv('SMTP_USER')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        self.from_email = os.getenv('FROM_EMAIL', self.smtp_user)
        self.enabled = os.getenv('EMAIL_NOTIFICATIONS_ENABLED', 'false').lower() == 'true'
        
        # Add email_enabled attribute for compatibility
        self.email_enabled = bool(self.smtp_host and self.smtp_user)
        
        if not self.smtp_user or not self.smtp_password:
            logger.warning("Email credentials not configured. Notifications will be logged only.")
            self.enabled = False
    
    def send_email(self, to: str, subject: str, body: str, html_body: Optional[str] = None) -> bool:
        """
        Send an email notification.
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Plain text email body
            html_body: Optional HTML email body
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        if not self.enabled:
            logger.info(f"Email notification (disabled): To={to}, Subject={subject}, Body={body}")
            return True
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.from_email
            msg['To'] = to
            msg['Subject'] = subject
            
            # Add plain text part
            text_part = MIMEText(body, 'plain')
            msg.attach(text_part)
            
            # Add HTML part if provided
            if html_body:
                html_part = MIMEText(html_body, 'html')
                msg.attach(html_part)
            
            # Connect to server and send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to}: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to}: {e}")
            return False
    
    def send_drift_alert(self, model_name: str, drift_score: float, threshold: float, 
                        timestamp: str, correlation_id: str, recipient: Optional[str] = None) -> bool:
        """
        Send a drift detection alert.
        
        Args:
            model_name: Name of the model experiencing drift
            drift_score: The drift score detected
            threshold: The threshold that was exceeded
            timestamp: When the drift was detected
            correlation_id: Correlation ID for tracing
            recipient: Email address to notify (uses DRIFT_ALERT_EMAIL if not provided)
            
        Returns:
            bool: True if email was sent successfully
        """
        if not recipient:
            recipient = os.getenv('DRIFT_ALERT_EMAIL')
            if not recipient:
                logger.warning("No recipient specified and DRIFT_ALERT_EMAIL not configured")
                return False
        
        subject = f"🚨 Model Drift Detected: {model_name}"
        
        body = f"""
Model Drift Alert

Model: {model_name}
Drift Score: {drift_score:.4f}
Threshold: {threshold:.4f}
Timestamp: {timestamp}
Correlation ID: {correlation_id}

The model is experiencing significant drift and may need retraining.
Please review the model performance and consider triggering a retraining process.

Smart Maintenance SaaS System
        """.strip()
        
        html_body = f"""
        <html>
        <body>
        <h2>🚨 Model Drift Alert</h2>
        <p><strong>Model:</strong> {model_name}</p>
        <p><strong>Drift Score:</strong> {drift_score:.4f}</p>
        <p><strong>Threshold:</strong> {threshold:.4f}</p>
        <p><strong>Timestamp:</strong> {timestamp}</p>
        <p><strong>Correlation ID:</strong> {correlation_id}</p>
        
        <p>The model is experiencing significant drift and may need retraining.</p>
        <p>Please review the model performance and consider triggering a retraining process.</p>
        
        <hr>
        <p><em>Smart Maintenance SaaS System</em></p>
        </body>
        </html>
        """
        
        return self.send_email(recipient, subject, body, html_body)
    
    def send_retrain_success(self, model_name: str, new_version: str, 
                            correlation_id: str, metrics: Optional[dict] = None, 
                            recipient: Optional[str] = None) -> bool:
        """
        Send a model retraining success notification.
        
        Args:
            model_name: Name of the retrained model
            new_version: Version of the new model
            correlation_id: Correlation ID for tracing
            metrics: Optional dictionary of model metrics
            recipient: Email address to notify (uses RETRAIN_SUCCESS_EMAIL if not provided)
            
        Returns:
            bool: True if email was sent successfully
        """
        if not recipient:
            recipient = os.getenv('RETRAIN_SUCCESS_EMAIL')
            if not recipient:
                logger.warning("No recipient specified and RETRAIN_SUCCESS_EMAIL not configured")
                return False
        
        subject = f"✅ Model Retrained Successfully: {model_name}"
        
        metrics_text = ""
        if metrics:
            metrics_text = "\n".join([f"{key}: {value}" for key, value in metrics.items()])
            metrics_text = f"\nModel Metrics:\n{metrics_text}"
        
        body = f"""
Model Retraining Complete

Model: {model_name}
New Version: {new_version}
Timestamp: {self._get_timestamp()}
Correlation ID: {correlation_id}{metrics_text}

The model has been successfully retrained and is ready for validation.
Please review the new model performance before promoting to production.

Smart Maintenance SaaS System
        """.strip()
        
        metrics_html = ""
        if metrics:
            metrics_rows = "".join([f"<tr><td>{key}</td><td>{value}</td></tr>" for key, value in metrics.items()])
            metrics_html = f"""
            <h3>Model Metrics</h3>
            <table border="1" style="border-collapse: collapse;">
            {metrics_rows}
            </table>
            """
        
        html_body = f"""
        <html>
        <body>
        <h2>✅ Model Retraining Complete</h2>
        <p><strong>Model:</strong> {model_name}</p>
        <p><strong>New Version:</strong> {new_version}</p>
        <p><strong>Timestamp:</strong> {self._get_timestamp()}</p>
        <p><strong>Correlation ID:</strong> {correlation_id}</p>
        
        {metrics_html}
        
        <p>The model has been successfully retrained and is ready for validation.</p>
        <p>Please review the new model performance before promoting to production.</p>
        
        <hr>
        <p><em>Smart Maintenance SaaS System</em></p>
        </body>
        </html>
        """
        
        return self.send_email(recipient, subject, body, html_body)
    
    def _get_timestamp(self) -> str:
        """Get current timestamp as string."""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")


# Global email service instance
email_service = EmailService()


def send_email(to: str, subject: str, body: str, html_body: Optional[str] = None) -> bool:
    """
    Convenience function to send email using the global email service.
    
    Args:
        to: Recipient email address
        subject: Email subject
        body: Plain text email body
        html_body: Optional HTML email body
        
    Returns:
        bool: True if email was sent successfully
    """
    return email_service.send_email(to, subject, body, html_body)