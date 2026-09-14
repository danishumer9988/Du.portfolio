from django.utils import timezone

from .models import ContactMessage, Project, Review


def dashboard_callback(request, context):
    today = timezone.now().date()

    pending_contacts = ContactMessage.objects.filter(status="pending").count()
    unread_contacts = ContactMessage.objects.filter(is_read=False).count()
    pending_reviews = Review.objects.filter(is_approved=False).count()
    total_projects = Project.objects.count()
    new_today = ContactMessage.objects.filter(created_at__date=today).count()

    recent_contacts = (
        ContactMessage.objects
        .order_by("-created_at")[:5]
    )

    context.update({
        "pending_contacts": pending_contacts,
        "unread_contacts": unread_contacts,
        "pending_reviews": pending_reviews,
        "total_projects": total_projects,
        "new_today": new_today,
        "recent_contacts": recent_contacts,
    })
    return context