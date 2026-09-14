from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group, User
from django.template.response import TemplateResponse
from django.contrib.admin import helpers
from django.http import HttpResponse
from django.utils import timezone
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from unfold.admin import ModelAdmin, TabularInline
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm

from .models import (
    AdminPreferences,
    ContactMessage,
    Experience,
    Industry,
    Project,
    ProjectImage,
    Review,
    Service,
    SiteSettings,
    Skill,
    SocialLink,
)

import csv


# ============================================================
# ADMIN BRANDING
# ============================================================

admin.site.site_header = "Danish Umer · CMS"
admin.site.site_title = "Portfolio Admin"
admin.site.index_title = "Content management"


# ============================================================
# USER & GROUP
# ============================================================

admin.site.unregister(User)
admin.site.unregister(Group)


@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm


@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    pass


# ============================================================
# PROJECT IMAGE — inline
# ============================================================

class ProjectImageInline(TabularInline):
    model = ProjectImage
    extra = 1
    fields = ("image", "preview", "alt_text", "caption", "display_order")
    readonly_fields = ("preview",)
    ordering = ("display_order",)

    def preview(self, obj):
        if obj and obj.image:
            return format_html(
                '<img src="{}" style="width:90px;height:60px;object-fit:cover;border-radius:6px;">',
                obj.image.url,
            )
        return "—"


# ============================================================
# PROJECT
# ============================================================

@admin.register(Project)
class ProjectAdmin(ModelAdmin):
    list_display = (
        "thumb", "title", "category", "industry",
        "featured", "project_date", "created_at",
    )
    list_display_links = ("title",)
    list_filter = ("featured", "category", "industry")
    search_fields = ("title", "short_description", "client", "technologies__name")
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("technologies",)
    date_hierarchy = "project_date"
    ordering = ("display_order", "-project_date")
    inlines = [ProjectImageInline]

    fieldsets = (
        ("Identity", {
            "fields": ("title", "slug", "short_description",
                       "full_description", "featured_image"),
        }),
        ("Classification", {
            "fields": ("category", "industry", "client",
                       "project_date", "technologies"),
        }),
        ("Case Study", {
            "fields": ("features", "challenges", "solutions", "results"),
        }),
        ("Links", {
            "fields": ("live_url", "github_url"),
        }),
        ("Publishing & SEO", {
            "fields": ("featured", "display_order", "seo_title", "seo_description"),
        }),
        ("System", {
            "fields": ("created_at", "updated_at"),
        }),
    )
    readonly_fields = ("created_at", "updated_at")

    @admin.display(description="")
    def thumb(self, obj):
        if obj.featured_image:
            return format_html(
                '<img src="{}" style="width:56px;height:38px;object-fit:cover;border-radius:6px;">',
                obj.featured_image.url,
            )
        return mark_safe('<span style="opacity:.4">—</span>')


# ============================================================
# SKILL
# ============================================================

@admin.register(Skill)
class SkillAdmin(ModelAdmin):
    list_display = ("name", "category", "skill_level", "is_active", "display_order")
    list_filter = ("category", "is_active")
    search_fields = ("name",)
    ordering = ("category", "display_order", "name")


# ============================================================
# SERVICE
# ============================================================

@admin.register(Service)
class ServiceAdmin(ModelAdmin):
    list_display = ("title", "starting_price", "is_active", "display_order")
    list_filter = ("is_active",)
    search_fields = ("title", "short_description")
    prepopulated_fields = {"slug": ("title",)}
    ordering = ("display_order", "title")


# ============================================================
# INDUSTRY
# ============================================================

@admin.register(Industry)
class IndustryAdmin(ModelAdmin):
    list_display = ("name", "is_active", "display_order")
    list_filter = ("is_active",)
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


# ============================================================
# EXPERIENCE
# ============================================================

@admin.register(Experience)
class ExperienceAdmin(ModelAdmin):
    list_display = ("position", "company", "start_date", "end_date",
                    "is_current", "display_order")
    list_filter = ("is_current", "company")
    search_fields = ("position", "company", "location")
    filter_horizontal = ("technologies",)
    ordering = ("display_order", "-start_date")


# ============================================================
# REVIEW
# ============================================================

@admin.register(Review)
class ReviewAdmin(ModelAdmin):
    list_display = ("thumb", "name", "rating", "role", "company",
                    "is_approved", "is_featured", "created_at")
    list_display_links = ("name",)
    list_filter = ("is_approved", "is_featured", "rating")
    search_fields = ("name", "company", "role", "review_text")
    list_editable = ("is_approved", "is_featured")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)

    @admin.display(description="")
    def thumb(self, obj):
        if obj.profile_picture:
            return format_html(
                '<img src="{}" style="width:36px;height:36px;object-fit:cover;border-radius:50%;">',
                obj.profile_picture.url,
            )
        return format_html(
            '<span style="display:inline-flex;width:36px;height:36px;'
            'border-radius:50%;background:rgba(201,255,106,.15);color:#c9ff6a;'
            'align-items:center;justify-content:center;font-weight:700;">{}</span>',
            obj.name[:1].upper() if obj.name else "?",
        )


# ============================================================
# CONTACT MESSAGE — approve/reject with confirmation page + CSV export
# ============================================================

@admin.action(description="✓ Approve & send confirmation")
def approve_contact_messages(modeladmin, request, queryset):
    from .views import _send_user_confirmation

    pending = queryset.filter(status="pending")

    if request.POST.get("confirm"):
        sent, failed = 0, 0
        for msg in pending:
            msg.status = "approved"
            msg.approved_at = timezone.now()
            msg.save(update_fields=["status", "approved_at", "updated_at"])
            try:
                _send_user_confirmation(msg)
                msg.reply_sent_at = timezone.now()
                msg.save(update_fields=["reply_sent_at"])
                sent += 1
            except Exception:
                failed += 1
        modeladmin.message_user(request, f"Approved {sent} message(s). {failed} failed.")
        return None

    context = {
        **modeladmin.admin_site.each_context(request),
        "title": "Confirm approval",
        "queryset": pending,
        "action_checkbox_name": helpers.ACTION_CHECKBOX_NAME,
        "opts": modeladmin.model._meta,
        "action_name": "approve_contact_messages",
        "action_label": "Approve & send confirmation",
    }
    return TemplateResponse(request, "admin/contact_confirm_approve.html", context)


@admin.action(description="✕ Reject selected messages")
def reject_contact_messages(modeladmin, request, queryset):
    updated = queryset.filter(status="pending").update(
        status="rejected",
        rejected_at=timezone.now(),
    )
    modeladmin.message_user(request, f"Rejected {updated} message(s).")


@admin.action(description="⇩ Export selected to CSV")
def export_contacts_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="contact_messages.csv"'
    writer = csv.writer(response)
    writer.writerow(["Name", "Email", "Subject", "Message",
                     "Project type", "Budget", "Status", "Read", "Created"])
    for obj in queryset:
        writer.writerow([
            obj.name, obj.email, obj.subject, obj.message,
            obj.project_type, obj.budget, obj.get_status_display(),
            "yes" if obj.is_read else "no",
            obj.created_at.strftime("%Y-%m-%d %H:%M"),
        ])
    return response


@admin.register(ContactMessage)
class ContactMessageAdmin(ModelAdmin):
    list_display = ("name", "email", "subject", "status",
                    "is_read", "created_at")
    list_filter = ("status", "is_read", "project_type")
    search_fields = ("name", "email", "subject", "message")
    list_editable = ("is_read",)
    readonly_fields = ("created_at", "updated_at", "token",
                       "approved_at", "rejected_at", "reply_sent_at")
    ordering = ("-created_at",)
    actions = (approve_contact_messages, reject_contact_messages, export_contacts_csv)

    fieldsets = (
        ("Sender", {"fields": ("name", "email")}),
        ("Message", {"fields": ("subject", "message", "project_type", "budget")}),
        ("Workflow", {"fields": ("status", "is_read",
                                 "approved_at", "rejected_at", "reply_sent_at")}),
        ("System", {"fields": ("token", "created_at", "updated_at")}),
    )


# ============================================================
# SOCIAL LINK
# ============================================================

@admin.register(SocialLink)
class SocialLinkAdmin(ModelAdmin):
    list_display = ("platform", "label", "url", "is_active", "display_order")
    list_filter = ("platform", "is_active")
    ordering = ("display_order", "platform")


# ============================================================
# SITE SETTINGS
# ============================================================

@admin.register(SiteSettings)
class SiteSettingsAdmin(ModelAdmin):
    fieldsets = (
        ("Brand", {
            "fields": ("site_name", "logo_text", "headline",
                       "hero_eyebrow", "hero_intro",
                       "profile_image", "resume_url"),
        }),
        ("About", {"fields": ("about_title", "about_text")}),
        ("Contact", {"fields": ("email", "phone", "location", "availability")}),
        ("SEO", {"fields": ("meta_title", "meta_description",
                            "og_image", "canonical_url")}),
        ("Footer", {"fields": ("footer_description",)}),
        ("System", {"fields": ("created_at", "updated_at")}),
    )
    readonly_fields = ("created_at", "updated_at")

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()


# ============================================================
# ADMIN PREFERENCES — the toggle switches page
# ============================================================

@admin.register(AdminPreferences)
class AdminPreferencesAdmin(ModelAdmin):
    fieldsets = (
        ("Layout", {
            "description": "Boxed layout creates a contained view with fixed width. "
                           "Sticky header keeps controls visible while scrolling.",
            "fields": ("boxed_layout", "sticky_header", "minimal_sidebar"),
        }),
        ("Theme", {
            "description": "Force dark header and sidebar for better contrast.",
            "fields": ("dark_header", "dark_sidebar"),
        }),
        ("Banner", {
            "description": "Show a message strip at the top of every admin page.",
            "fields": ("show_banner", "banner_text"),
        }),
    )

    def has_add_permission(self, request):
        return not AdminPreferences.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        from django.shortcuts import redirect
        from django.urls import reverse
        prefs = AdminPreferences.load()
        return redirect(
            reverse("admin:main_adminpreferences_change", args=[prefs.pk])
        )