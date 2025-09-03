#this file is social/context_processors.py
from .models import VerificationRequest

def admin_stats(request):
    """
    Add admin statistics to all admin templates
    """
    if request.path.startswith('/admin-go-hideandseek/'):
        return {
            'pending_verifications_count': VerificationRequest.objects.filter(status='PENDING').count(),
        }
    return {}
