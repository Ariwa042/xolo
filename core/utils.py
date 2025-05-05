from django.core.mail import get_connection, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

def send_email_with_smtp(template_type, subject, recipient_email, context, template_path):
    smtp_settings = settings.EMAIL_BACKENDS.get(template_type.upper())

    if smtp_settings:
        # Create a custom connection using the selected SMTP server
        connection = get_connection(
            host=smtp_settings['EMAIL_HOST'],
            port=smtp_settings['EMAIL_PORT'],
            username=smtp_settings['EMAIL_HOST_USER'],
            password=smtp_settings['EMAIL_HOST_PASSWORD'],
            use_tls=smtp_settings['EMAIL_USE_TLS'],
        )

        html_content = render_to_string(template_path, context)
        text_content = strip_tags(html_content)

        email = EmailMultiAlternatives(
            subject, text_content, smtp_settings['EMAIL_HOST_USER'], [recipient_email], connection=connection
        )
        email.attach_alternative(html_content, "text/html")
        try:
            email.send(fail_silently=False)
            logger.info(f"Email successfully sent to {recipient_email} using {template_type} SMTP.")
        except Exception as e:
            logger.error(f"Failed to send email to {recipient_email} using {template_type} SMTP: {e}", exc_info=True)
    else:
        logger.error(f"No SMTP settings found for template type: {template_type}")
