from celery import shared_task
from django.conf.global_settings import EMAIL_HOST_USER
from django.core.mail import send_mail


@shared_task(bind=True)
def send_email(self, target_mail, mail_subject, message):
    send_mail(
        subject=mail_subject,
        message=message,
        from_email=EMAIL_HOST_USER,
        recipient_list=[target_mail],
        fail_silently=False,
        )
    return 'Done'
