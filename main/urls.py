from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("projects/", views.projects, name="projects"),
    path("projects/<slug:slug>/", views.project_detail, name="project_detail"),
    path("services/", views.services, name="services"),
    path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),
    path("reviews/submit/", views.submit_review, name="submit_review"),
    path("sitemap.xml", views.sitemap_view, name="sitemap"),

    # NEW — approve / reject from the notification email
    path(
        "contact-action/<uuid:token>/<str:action>/",
        views.contact_action,
        name="contact_action",
    ),
]