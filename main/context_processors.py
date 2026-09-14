from .models import AdminPreferences, SiteSettings, SocialLink


def site_context(request):
    site = SiteSettings.objects.first()
    return {
        "site": site,
        "social_links": SocialLink.objects.filter(is_active=True) if site else [],
    }


def admin_preferences(request):
    """Only query for admin pages to avoid extra DB hits on the public site."""
    if request.path.startswith("/admin/"):
        return {"admin_prefs": AdminPreferences.load()}
    return {}