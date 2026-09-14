import logging

from django.conf import settings
from django.contrib import messages
from django.core.mail import EmailMultiAlternatives
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.html import escape

from .forms import ContactForm, ReviewForm
from .models import (
    ContactMessage,
    Experience,
    Industry,
    Project,
    Review,
    Service,
    SiteSettings,
    Skill,
    SocialLink,
)

logger = logging.getLogger(__name__)


# ============================================================
# SHARED CONTEXT
# ============================================================

def common_context():
    site = SiteSettings.objects.first()
    if not site:
        site = SiteSettings.objects.create()
    return {
        "site": site,
        "social_links": SocialLink.objects.filter(is_active=True),
    }


# ============================================================
# EMAIL HELPERS — LIGHT THEME
# ============================================================

def _send_admin_notification(instance, request):
    approve_url = request.build_absolute_uri(
        reverse("contact_action", kwargs={"token": instance.token, "action": "approve"})
    )
    reject_url = request.build_absolute_uri(
        reverse("contact_action", kwargs={"token": instance.token, "action": "reject"})
    )
    admin_url = request.build_absolute_uri("/admin/main/contactmessage/")
    admin_detail_url = request.build_absolute_uri(
        f"/admin/main/contactmessage/{instance.pk}/change/"
    )

    site = SiteSettings.objects.first()
    site_name = site.site_name if site else "Portfolio"

    pending_count = ContactMessage.objects.filter(status="pending").count()
    total_count = ContactMessage.objects.count()

    subject = f"New inquiry from {instance.name} — {instance.subject}"
    preheader = f"{instance.name} · {instance.email} — {instance.message[:90]}…"

    safe_name = escape(instance.name)
    safe_email = escape(instance.email)
    safe_subject = escape(instance.subject)
    safe_message = escape(instance.message).replace("\n", "<br>")
    safe_project_type = escape(instance.project_type) if instance.project_type else "—"
    safe_budget = escape(instance.budget) if instance.budget else "—"
    submitted_at = instance.created_at.strftime("%d %b %Y · %H:%M")
    token_short = str(instance.token)[:8]

    # Gmail compose link with the sender pre-filled
    gmail_reply_url = (
        f"https://mail.google.com/mail/?view=cm"
        f"&fs=1&to={safe_email}&su=Re%3A%20{escape(instance.subject)}"
    )

    text_body = f"""New contact form submission on {site_name}

From:         {instance.name} <{instance.email}>
Subject:      {instance.subject}
Project type: {instance.project_type or '—'}
Budget:       {instance.budget or '—'}
Received:     {submitted_at}

Message:
{instance.message}

Stats: {pending_count} pending · {total_count} total

--------------------------------------------------
APPROVE — sends confirmation to {instance.email}:
{approve_url}

REJECT — no email is sent to the sender:
{reject_url}

Reply in Gmail:
{gmail_reply_url}

Open in admin:
{admin_detail_url}
--------------------------------------------------
"""

    html_body = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{safe_subject}</title>
<style>
  @media only screen and (max-width:620px) {{
    .wrap {{ width:100% !important; }}
    .px {{ padding-left:20px !important; padding-right:20px !important; }}
    .btn-cell {{ display:block !important; width:100% !important; padding:0 0 10px 0 !important; }}
    .btn {{ display:block !important; width:100% !important; box-sizing:border-box !important; }}
    .h1 {{ font-size:22px !important; }}
    .stats-cell {{ display:block !important; width:100% !important; padding:8px 0 !important; border-left:0 !important; border-top:1px solid #f0f1f4 !important; padding-left:0 !important; }}
    .stats-cell:first-child {{ border-top:0 !important; }}
    .quick-cell {{ display:block !important; width:100% !important; padding:0 0 8px 0 !important; }}
    .quick {{ display:block !important; width:100% !important; box-sizing:border-box !important; }}
  }}
</style>
</head>
<body style="margin:0;padding:0;background:#f4f5f7;color:#111827;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;">

  <div style="display:none;font-size:1px;color:#f4f5f7;line-height:1px;max-height:0;max-width:0;opacity:0;overflow:hidden;">
    {preheader}
  </div>

  <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background:#f4f5f7;padding:40px 16px;">
    <tr>
      <td align="center">

        <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="620" class="wrap" style="width:620px;max-width:620px;background:#ffffff;border:1px solid #e5e7eb;border-radius:16px;overflow:hidden;box-shadow:0 1px 2px rgba(0,0,0,.04);">

          <!-- Accent bar -->
          <tr>
            <td style="height:4px;background:linear-gradient(90deg,#84cc16,#22d3ee);"></td>
          </tr>

          <!-- Header -->
          <tr>
            <td class="px" style="padding:32px 40px 4px;">
              <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
                <tr>
                  <td>
                    <div style="display:inline-block;padding:4px 12px;background:#f0fdf4;border:1px solid #bbf7d0;border-radius:999px;font-size:11px;letter-spacing:.14em;text-transform:uppercase;font-weight:800;color:#15803d;">
                      ● New inquiry
                    </div>
                  </td>
                  <td align="right" style="font-size:12px;color:#9ca3af;font-weight:500;">
                    {submitted_at}
                  </td>
                </tr>
              </table>

              <div class="h1" style="font-size:24px;font-weight:800;letter-spacing:-.02em;line-height:1.25;color:#0f172a;margin-top:16px;">
                {safe_subject}
              </div>
            </td>
          </tr>

          <!-- Quick stats -->
          <tr>
            <td class="px" style="padding:24px 40px 0;">
              <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background:#f9fafb;border:1px solid #eef0f3;border-radius:12px;">
                <tr>
                  <td class="stats-cell" width="33%" style="padding:16px 20px;text-align:center;border-right:1px solid #eef0f3;">
                    <div style="font-size:22px;font-weight:800;letter-spacing:-.03em;color:#15803d;line-height:1;">{pending_count}</div>
                    <div style="font-size:11px;letter-spacing:.14em;text-transform:uppercase;font-weight:700;color:#6b7280;margin-top:4px;">Pending</div>
                  </td>
                  <td class="stats-cell" width="33%" style="padding:16px 20px;text-align:center;border-right:1px solid #eef0f3;">
                    <div style="font-size:22px;font-weight:800;letter-spacing:-.03em;color:#0f172a;line-height:1;">{total_count}</div>
                    <div style="font-size:11px;letter-spacing:.14em;text-transform:uppercase;font-weight:700;color:#6b7280;margin-top:4px;">Total</div>
                  </td>
                  <td class="stats-cell" width="33%" style="padding:16px 20px;text-align:center;">
                    <div style="font-size:22px;font-weight:800;letter-spacing:-.03em;color:#0ea5e9;line-height:1;">~24h</div>
                    <div style="font-size:11px;letter-spacing:.14em;text-transform:uppercase;font-weight:700;color:#6b7280;margin-top:4px;">Reply target</div>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Sender info -->
          <tr>
            <td class="px" style="padding:24px 40px 0;">
              <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background:#f9fafb;border:1px solid #eef0f3;border-radius:12px;">
                <tr>
                  <td style="padding:20px 22px;">
                    <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
                      <tr>
                        <td style="padding:5px 0;width:130px;font-size:13px;color:#6b7280;vertical-align:top;font-weight:500;">From</td>
                        <td style="padding:5px 0;font-size:14px;color:#0f172a;font-weight:600;">
                          {safe_name}
                          <a href="mailto:{safe_email}" style="color:#0ea5e9;text-decoration:none;font-weight:500;">&lt;{safe_email}&gt;</a>
                        </td>
                      </tr>
                      <tr>
                        <td style="padding:5px 0;font-size:13px;color:#6b7280;vertical-align:top;font-weight:500;">Project type</td>
                        <td style="padding:5px 0;font-size:14px;color:#0f172a;">{safe_project_type}</td>
                      </tr>
                      <tr>
                        <td style="padding:5px 0;font-size:13px;color:#6b7280;vertical-align:top;font-weight:500;">Budget</td>
                        <td style="padding:5px 0;font-size:14px;color:#0f172a;">{safe_budget}</td>
                      </tr>
                      <tr>
                        <td style="padding:5px 0;font-size:13px;color:#6b7280;vertical-align:top;font-weight:500;">Reference</td>
                        <td style="padding:5px 0;font-size:12px;color:#9ca3af;font-family:'SF Mono',Consolas,monospace;">#{token_short}</td>
                      </tr>
                    </table>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Message -->
          <tr>
            <td class="px" style="padding:28px 40px 0;">
              <div style="font-size:11px;letter-spacing:.18em;text-transform:uppercase;font-weight:800;color:#6b7280;margin-bottom:12px;">
                Message
              </div>
              <div style="padding:20px 22px;background:#f9fafb;border:1px solid #eef0f3;border-left:4px solid #84cc16;border-radius:10px;font-size:15px;line-height:1.7;color:#1f2937;">
                {safe_message}
              </div>
            </td>
          </tr>

          <!-- Primary actions -->
          <tr>
            <td class="px" style="padding:32px 40px 0;">
              <div style="font-size:11px;letter-spacing:.18em;text-transform:uppercase;font-weight:800;color:#6b7280;margin-bottom:14px;">
                Action
              </div>

              <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
                <tr>
                  <td class="btn-cell" width="50%" style="padding-right:6px;vertical-align:top;">
                    <a href="{approve_url}" class="btn" style="display:block;padding:16px 20px;background:#84cc16;color:#1a2e05;text-align:center;font-size:15px;font-weight:800;letter-spacing:-.005em;text-decoration:none;border-radius:10px;">
                      ✓ &nbsp;Approve &amp; send reply
                    </a>
                  </td>
                  <td class="btn-cell" width="50%" style="padding-left:6px;vertical-align:top;">
                    <a href="{reject_url}" class="btn" style="display:block;padding:16px 20px;background:#ffffff;color:#dc2626;text-align:center;font-size:15px;font-weight:700;letter-spacing:-.005em;text-decoration:none;border:1px solid #fecaca;border-radius:10px;">
                      ✕ &nbsp;Reject
                    </a>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Helper note -->
          <tr>
            <td class="px" style="padding:16px 40px 0;">
              <div style="font-size:13px;line-height:1.6;color:#6b7280;text-align:center;">
                <strong style="color:#0f172a;">Approve</strong> sends a confirmation to
                <span style="color:#0ea5e9;">{safe_email}</span>.<br>
                <strong style="color:#0f172a;">Reject</strong> sends nothing — the message stays in the admin.
              </div>
            </td>
          </tr>

          <!-- Divider -->
          <tr>
            <td class="px" style="padding:32px 40px 0;">
              <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
                <tr><td style="border-top:1px solid #f0f1f4;font-size:0;line-height:0;height:1px;">&nbsp;</td></tr>
              </table>
            </td>
          </tr>

          <!-- Quick actions -->
          <tr>
            <td class="px" style="padding:24px 40px 0;">
              <div style="font-size:11px;letter-spacing:.18em;text-transform:uppercase;font-weight:800;color:#6b7280;margin-bottom:12px;">
                Quick actions
              </div>

              <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
                <tr>
                  <td class="quick-cell" width="50%" style="padding-right:5px;vertical-align:top;">
                    <a href="{gmail_reply_url}" class="quick" style="display:block;padding:12px 16px;background:#f9fafb;color:#0f172a;text-align:center;font-size:13px;font-weight:600;text-decoration:none;border:1px solid #eef0f3;border-radius:10px;">
                      ✉ &nbsp;Reply in Gmail
                    </a>
                  </td>
                  <td class="quick-cell" width="50%" style="padding-left:5px;vertical-align:top;">
                    <a href="{admin_detail_url}" class="quick" style="display:block;padding:12px 16px;background:#f9fafb;color:#0f172a;text-align:center;font-size:13px;font-weight:600;text-decoration:none;border:1px solid #eef0f3;border-radius:10px;">
                      ⚙ &nbsp;Open in admin
                    </a>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td class="px" style="padding:28px 40px 0;">
              <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
                <tr>
                  <td style="padding:16px 20px;background:#f9fafb;border:1px solid #eef0f3;border-radius:10px;font-size:12px;color:#6b7280;line-height:1.55;text-align:center;">
                    Approving or rejecting from this email is a one-time action.<br>
                    Once handled, the link becomes inactive.
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Bottom footer -->
          <tr>
            <td class="px" style="padding:24px 40px;border-top:1px solid #f0f1f4;background:#fafbfc;margin-top:24px;">
              <div style="font-size:12px;color:#9ca3af;text-align:center;line-height:1.5;">
                {site_name} · Contact form notification
              </div>
            </td>
          </tr>

        </table>

      </td>
    </tr>
  </table>

</body>
</html>
"""

    email = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=None,
        to=[settings.CONTACT_RECEIVER_EMAIL],
    )
    email.attach_alternative(html_body, "text/html")
    email.send(fail_silently=False)


def _send_user_confirmation(instance):
    site = SiteSettings.objects.first()
    site_name = site.site_name if site else "Portfolio"
    site_email = site.email if site else settings.DEFAULT_FROM_EMAIL
    site_phone = site.phone if site else ""
    site_location = site.location if site else ""

    socials = SocialLink.objects.filter(is_active=True)[:5]

    subject = f"Re: {instance.subject}"
    preheader = "I've received your message and will get back to you within 24 hours."

    safe_name = escape(instance.name)
    safe_message = escape(instance.message).replace("\n", "<br>")
    safe_subject = escape(instance.subject)
    first_name = safe_name.split(" ")[0] if safe_name else "there"

    # Build a footer with contact info + socials
    footer_lines = []
    if site_location:
        footer_lines.append(f"📍 {escape(site_location)}")
    if site_phone:
        footer_lines.append(f"📞 {escape(site_phone)}")
    footer_lines.append(f"✉ <a href='mailto:{escape(site_email)}' style='color:#65a30d;text-decoration:none;'>{escape(site_email)}</a>")
    footer_text = "<br>".join(footer_lines)

    text_body = f"""Hi {instance.name},

Thanks for reaching out. I've received your message and I'll get back to you within 24 hours.

What happens next:
1. I'll review your message and project details
2. I'll reply within 24 hours with next steps
3. We can hop on a call if it's a fit

Here's what you sent me:
---
{instance.message}
---

Best regards,
{site_name}
{site_email}
"""

    html_body = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{safe_subject}</title>
<style>
  @media only screen and (max-width:620px) {{
    .wrap {{ width:100% !important; }}
    .px {{ padding-left:22px !important; padding-right:22px !important; }}
    .h1 {{ font-size:22px !important; }}
    .step-num {{ width:32px !important; height:32px !important; line-height:32px !important; font-size:13px !important; }}
    .step-cell {{ padding-left:0 !important; padding-top:12px !important; }}
    .social-link {{ display:inline-block !important; margin:4px 4px !important; }}
  }}
</style>
</head>
<body style="margin:0;padding:0;background:#f4f5f7;color:#111827;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;">

  <div style="display:none;font-size:1px;color:#f4f5f7;line-height:1px;max-height:0;max-width:0;opacity:0;overflow:hidden;">
    {preheader}
  </div>

  <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background:#f4f5f7;padding:40px 16px;">
    <tr>
      <td align="center">

        <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="600" class="wrap" style="width:600px;max-width:600px;background:#ffffff;border:1px solid #e5e7eb;border-radius:16px;overflow:hidden;box-shadow:0 1px 2px rgba(0,0,0,.04);">

          <!-- Accent bar -->
          <tr>
            <td style="height:4px;background:linear-gradient(90deg,#84cc16,#22d3ee);"></td>
          </tr>

          <!-- Checkmark + Headline -->
          <tr>
            <td class="px" style="padding:40px 40px 0;">
              <table role="presentation" cellpadding="0" cellspacing="0" border="0">
                <tr>
                  <td style="width:56px;height:56px;background:#84cc16;border-radius:50%;text-align:center;vertical-align:middle;font-size:28px;font-weight:900;color:#1a2e05;line-height:56px;">
                    ✓
                  </td>
                </tr>
              </table>

              <div class="h1" style="font-size:26px;font-weight:800;letter-spacing:-.025em;line-height:1.25;color:#0f172a;margin-top:24px;">
                I received your message.
              </div>
            </td>
          </tr>

          <!-- Body text -->
          <tr>
            <td class="px" style="padding:18px 40px 0;">
              <p style="margin:0 0 16px;font-size:16px;line-height:1.65;color:#374151;">
                Hi {first_name},
              </p>
              <p style="margin:0 0 16px;font-size:16px;line-height:1.65;color:#374151;">
                Thanks for reaching out. I've received your message and I'll get back to you <strong style="color:#0f172a;">within 24 hours</strong>.
              </p>
              <p style="margin:0;font-size:16px;line-height:1.65;color:#374151;">
                If your enquiry is time-sensitive, you can reply directly to this email.
              </p>
            </td>
          </tr>

          <!-- What happens next — timeline -->
          <tr>
            <td class="px" style="padding:32px 40px 0;">
              <div style="font-size:11px;letter-spacing:.18em;text-transform:uppercase;font-weight:800;color:#6b7280;margin-bottom:16px;">
                What happens next
              </div>

              <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background:#f9fafb;border:1px solid #eef0f3;border-radius:12px;">
                <tr>
                  <td style="padding:20px 22px;">

                    <!-- Step 1 -->
                    <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="margin-bottom:14px;">
                      <tr>
                        <td class="step-num" width="36" style="width:36px;height:36px;background:#ecfccb;border-radius:50%;text-align:center;vertical-align:middle;font-size:14px;font-weight:800;color:#3f6212;line-height:36px;">
                          1
                        </td>
                        <td class="step-cell" style="padding-left:16px;vertical-align:middle;">
                          <div style="font-size:14px;font-weight:700;color:#0f172a;letter-spacing:-.01em;">I review your message</div>
                          <div style="font-size:13px;color:#6b7280;line-height:1.5;margin-top:2px;">I'll look at your project details and figure out the best next step.</div>
                        </td>
                      </tr>
                    </table>

                    <!-- Step 2 -->
                    <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="margin-bottom:14px;">
                      <tr>
                        <td class="step-num" width="36" style="width:36px;height:36px;background:#e0f2fe;border-radius:50%;text-align:center;vertical-align:middle;font-size:14px;font-weight:800;color:#075985;line-height:36px;">
                          2
                        </td>
                        <td class="step-cell" style="padding-left:16px;vertical-align:middle;">
                          <div style="font-size:14px;font-weight:700;color:#0f172a;letter-spacing:-.01em;">I reply within 24 hours</div>
                          <div style="font-size:13px;color:#6b7280;line-height:1.5;margin-top:2px;">You'll hear back with a clear answer — timeline, scope, or a call invite.</div>
                        </td>
                      </tr>
                    </table>

                    <!-- Step 3 -->
                    <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
                      <tr>
                        <td class="step-num" width="36" style="width:36px;height:36px;background:#f3e8ff;border-radius:50%;text-align:center;vertical-align:middle;font-size:14px;font-weight:800;color:#6b21a8;line-height:36px;">
                          3
                        </td>
                        <td class="step-cell" style="padding-left:16px;vertical-align:middle;">
                          <div style="font-size:14px;font-weight:700;color:#0f172a;letter-spacing:-.01em;">We go from there</div>
                          <div style="font-size:13px;color:#6b7280;line-height:1.5;margin-top:2px;">If it's a fit, we'll set up a call and map out the work.</div>
                        </td>
                      </tr>
                    </table>

                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Divider -->
          <tr>
            <td class="px" style="padding:32px 40px 0;">
              <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
                <tr><td style="border-top:1px solid #f0f1f4;font-size:0;line-height:0;height:1px;">&nbsp;</td></tr>
              </table>
            </td>
          </tr>

          <!-- Quoted message -->
          <tr>
            <td class="px" style="padding:24px 40px 0;">
              <div style="font-size:11px;letter-spacing:.18em;text-transform:uppercase;font-weight:800;color:#6b7280;margin-bottom:12px;">
                Your message
              </div>
              <div style="padding:18px 20px;background:#f9fafb;border:1px solid #eef0f3;border-left:4px solid #84cc16;border-radius:10px;font-size:14px;line-height:1.7;color:#374151;">
                <div style="font-size:12px;color:#6b7280;margin-bottom:10px;font-weight:600;">
                  Subject: <span style="color:#0f172a;">{safe_subject}</span>
                </div>
                {safe_message}
              </div>
            </td>
          </tr>

          <!-- Reply nudge -->
          <tr>
            <td class="px" style="padding:24px 40px 0;">
              <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:10px;">
                <tr>
                  <td style="padding:16px 20px;font-size:14px;color:#166534;line-height:1.6;">
                    <strong>Need to add something?</strong><br>
                    Just reply to this email — it comes straight to me.
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Signature -->
          <tr>
            <td class="px" style="padding:32px 40px 0;">
              <p style="margin:0 0 4px;font-size:16px;line-height:1.65;color:#374151;">
                Best regards,
              </p>
              <p style="margin:0;font-size:16px;font-weight:700;color:#0f172a;letter-spacing:-.015em;">
                {site_name}
              </p>
              <p style="margin:2px 0 0;">
                <a href="mailto:{escape(site_email)}" style="color:#65a30d;text-decoration:none;font-size:14px;font-weight:500;">
                  {escape(site_email)}
                </a>
              </p>
            </td>
          </tr>

          <!-- Contact + socials footer -->
          <tr>
            <td class="px" style="padding:28px 40px 0;">
              <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background:#f9fafb;border:1px solid #eef0f3;border-radius:12px;">
                <tr>
                  <td style="padding:20px 22px;text-align:center;">

                    <div style="font-size:11px;letter-spacing:.18em;text-transform:uppercase;font-weight:800;color:#6b7280;margin-bottom:10px;">
                      Get in touch
                    </div>

                    <div style="font-size:13px;color:#374151;line-height:1.8;">
                      {footer_text}
                    </div>

                    {"".join([
                        f'<a href="{escape(s.url)}" class="social-link" style="display:inline-block;margin:10px 5px 0;padding:6px 14px;background:#ffffff;border:1px solid #e5e7eb;border-radius:999px;font-size:12px;font-weight:600;color:#374151;text-decoration:none;">{escape(s.label or s.platform)}</a>'
                        for s in socials
                    ]) if socials else ""}

                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td class="px" style="padding:28px 40px 32px;">
              <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
                <tr>
                  <td style="padding-top:20px;border-top:1px solid #f0f1f4;font-size:12px;color:#9ca3af;line-height:1.55;text-align:center;">
                    You received this email because you contacted {site_name} through the portfolio site.<br>
                    This is an automated confirmation — replies go to my inbox directly.
                  </td>
                </tr>
              </table>
            </td>
          </tr>

        </table>

      </td>
    </tr>
  </table>

</body>
</html>
"""

    email = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=None,
        to=[instance.email],
        reply_to=[settings.CONTACT_RECEIVER_EMAIL],
    )
    email.attach_alternative(html_body, "text/html")
    email.send(fail_silently=False)


# ============================================================
# HOME
# ============================================================

def home(request):
    featured_projects = list(
        Project.objects.filter(featured=True)
        .select_related("industry")
        .prefetch_related("technologies", "gallery")[:6]
    )
    if len(featured_projects) < 6:
        existing = {p.pk for p in featured_projects}
        fallback = (
            Project.objects.exclude(pk__in=existing)
            .select_related("industry")
            .prefetch_related("technologies", "gallery")
        )
        featured_projects += list(fallback[:6 - len(featured_projects)])

    ctx = common_context()
    ctx.update({
        "skills": Skill.objects.filter(is_active=True),
        "services": Service.objects.filter(is_active=True),
        "industries": Industry.objects.filter(is_active=True),
        "experiences": Experience.objects.prefetch_related("technologies"),
        "featured_projects": featured_projects[:6],
        "reviews": Review.objects.filter(is_approved=True),
        "contact_form": ContactForm(),
        "review_form": ReviewForm(),
    })
    return render(request, "home/home.html", ctx)


# ============================================================
# PROJECTS
# ============================================================

def projects(request):
    qs = Project.objects.select_related("industry").prefetch_related("technologies")

    query = request.GET.get("q", "").strip()
    category = request.GET.get("category", "").strip()
    industry = request.GET.get("industry", "").strip()
    technology = request.GET.get("technology", "").strip()
    sort = request.GET.get("sort", "featured").strip()

    if query:
        qs = qs.filter(
            Q(title__icontains=query)
            | Q(short_description__icontains=query)
            | Q(full_description__icontains=query)
        )
    if category:
        qs = qs.filter(category=category)
    if industry:
        qs = qs.filter(industry__slug=industry)
    if technology:
        qs = qs.filter(technologies__name__iexact=technology)

    sort_map = {
        "featured": ["-featured", "display_order", "-project_date"],
        "newest": ["-project_date", "-created_at"],
        "oldest": ["project_date", "created_at"],
        "az": ["title"],
    }
    qs = qs.order_by(*sort_map.get(sort, sort_map["featured"])).distinct()

    paginator = Paginator(qs, 9)
    page_obj = paginator.get_page(request.GET.get("page"))

    ctx = common_context()
    ctx.update({
        "page_obj": page_obj,
        "categories": (
            Project.objects.values_list("category", flat=True)
            .distinct()
            .order_by("category")
        ),
        "industries": Industry.objects.filter(is_active=True),
        "technologies": (
            Skill.objects.filter(is_active=True, projects__isnull=False)
            .distinct()
            .order_by("name")
        ),
        "active_filters": {
            "q": query,
            "category": category,
            "industry": industry,
            "technology": technology,
            "sort": sort,
        },
    })
    return render(request, "projects.html", ctx)


def project_detail(request, slug):
    project = get_object_or_404(
        Project.objects.select_related("industry").prefetch_related("technologies", "gallery"),
        slug=slug,
    )

    if project.industry_id:
        related = (
            Project.objects.filter(industry=project.industry)
            .exclude(pk=project.pk)
            .select_related("industry")
            .prefetch_related("technologies")[:3]
        )
    else:
        related = (
            Project.objects.exclude(pk=project.pk)
            .select_related("industry")
            .prefetch_related("technologies")[:3]
        )

    ctx = common_context()
    ctx.update({"project": project, "related_projects": related})
    return render(request, "project_detail.html", ctx)


# ============================================================
# SERVICES / ABOUT
# ============================================================

def services(request):
    ctx = common_context()
    ctx["services"] = Service.objects.filter(is_active=True)
    return render(request, "services.html", ctx)


def about(request):
    ctx = common_context()
    ctx.update({
        "skills": Skill.objects.filter(is_active=True),
        "experiences": Experience.objects.prefetch_related("technologies"),
    })
    return render(request, "about.html", ctx)


# ============================================================
# CONTACT
# ============================================================

def contact(request):
    ctx = common_context()
    is_ajax = (
        request.headers.get("X-Requested-With") == "XMLHttpRequest"
        or "application/json" in request.headers.get("Accept", "")
    )

    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            instance = form.save()

            try:
                _send_admin_notification(instance, request)
            except Exception:
                logger.exception("Admin notification email failed")

            if is_ajax:
                return JsonResponse({
                    "ok": True,
                    "message": "Thanks — your message has been sent.",
                })

            messages.success(request, "Thanks — your message has been sent.")
            return redirect(f"{reverse('contact')}#contact-form")

        if is_ajax:
            return JsonResponse({"ok": False, "errors": form.errors}, status=400)
    else:
        form = ContactForm()

    ctx["contact_form"] = form
    return render(request, "contact.html", ctx)


# ============================================================
# CONTACT — approve / reject
# ============================================================

def contact_action(request, token, action):
    if action not in ("approve", "reject"):
        raise Http404("Unknown action")

    instance = get_object_or_404(ContactMessage, token=token)
    already_handled = instance.status != "pending"

    email_sent = False
    email_error = False

    if not already_handled:
        if action == "approve":
            instance.status = "approved"
            instance.approved_at = timezone.now()
            instance.save(update_fields=["status", "approved_at", "updated_at"])

            try:
                _send_user_confirmation(instance)
                instance.reply_sent_at = timezone.now()
                instance.save(update_fields=["reply_sent_at"])
                email_sent = True
            except Exception:
                logger.exception("Confirmation email to user failed")
                email_error = True

        else:
            instance.status = "rejected"
            instance.rejected_at = timezone.now()
            instance.save(update_fields=["status", "rejected_at", "updated_at"])

    pending_count = ContactMessage.objects.filter(status="pending").count()
    approved_count = ContactMessage.objects.filter(status="approved").count()
    rejected_count = ContactMessage.objects.filter(status="rejected").count()

    return render(
        request,
        "contact_action.html",
        {
            "instance": instance,
            "action": action,
            "already_handled": already_handled,
            "email_sent": email_sent,
            "email_error": email_error,
            "pending_count": pending_count,
            "approved_count": approved_count,
            "rejected_count": rejected_count,
        },
    )


# ============================================================
# REVIEWS
# ============================================================

def submit_review(request):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "POST required."}, status=405)

    form = ReviewForm(request.POST, request.FILES)
    if form.is_valid():
        review = form.save(commit=False)
        review.is_approved = False
        review.is_featured = False
        review.save()
        return JsonResponse({
            "ok": True,
            "message": "Thank you for your review. Your review has been submitted for approval.",
        })

    return JsonResponse({"ok": False, "errors": form.errors}, status=400)


# ============================================================
# SITEMAP
# ============================================================

def sitemap_view(request):
    urls = [("home", request.build_absolute_uri(reverse("home")))]
    for p in Project.objects.all():
        urls.append((
            p.title,
            request.build_absolute_uri(reverse("project_detail", kwargs={"slug": p.slug})),
        ))

    body = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    for _, loc in urls:
        body += f"<url><loc>{loc}</loc></url>"
    body += "</urlset>"

    return HttpResponse(body, content_type="application/xml")