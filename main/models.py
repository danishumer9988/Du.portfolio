import uuid

from django.core.cache import cache
from django.core.validators import MaxValueValidator, MinValueValidator, URLValidator
from django.db import models
from django.template.defaultfilters import slugify


# ============================================================
# BASE
# ============================================================

class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        abstract = True


# ============================================================
# INDUSTRY
# ============================================================

class Industry(TimeStampedModel):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=110, unique=True, blank=True)
    icon = models.CharField(
        max_length=80,
        blank=True,
        help_text="Optional inline icon class/name, e.g. ✦",
    )
    description = models.TextField(blank=True)
    display_order = models.PositiveIntegerField(default=0, db_index=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["display_order", "name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


# ============================================================
# SKILL
# ============================================================

class Skill(TimeStampedModel):
    CATEGORY_CHOICES = [
        ("Frontend", "Frontend"),
        ("Backend", "Backend"),
        ("Database", "Database"),
        ("Tools & Platforms", "Tools & Platforms"),
    ]

    name = models.CharField(max_length=100)
    category = models.CharField(max_length=40, choices=CATEGORY_CHOICES, db_index=True)
    icon = models.ImageField(upload_to="skills/", blank=True, null=True)
    icon_text = models.CharField(
        max_length=16,
        blank=True,
        help_text="Optional emoji/text icon.",
    )
    skill_level = models.PositiveIntegerField(
        default=85,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
    )
    display_order = models.PositiveIntegerField(default=0, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ["category", "display_order", "name"]
        indexes = [models.Index(fields=["category", "is_active"])]
        constraints = [
            models.UniqueConstraint(
                fields=["name", "category"],
                name="unique_skill_category",
            )
        ]

    def __str__(self):
        return f"{self.category}: {self.name}"


# ============================================================
# SERVICE
# ============================================================

class Service(TimeStampedModel):
    title = models.CharField(max_length=140)
    slug = models.SlugField(max_length=160, unique=True, blank=True)
    icon = models.CharField(max_length=80, default="◈")
    short_description = models.CharField(max_length=280)
    full_description = models.TextField(blank=True)
    features = models.TextField(blank=True, help_text="One feature per line.")
    starting_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
    )
    is_active = models.BooleanField(default=True, db_index=True)
    display_order = models.PositiveIntegerField(default=0, db_index=True)

    class Meta:
        ordering = ["display_order", "title"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def feature_list(self):
        return [x.strip() for x in self.features.splitlines() if x.strip()]

    def __str__(self):
        return self.title


# ============================================================
# PROJECT
# ============================================================

class Project(TimeStampedModel):
    title = models.CharField(max_length=180)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    short_description = models.CharField(max_length=300)
    full_description = models.TextField()
    featured_image = models.ImageField(
        upload_to="projects/featured/",
        blank=True,
        null=True,
    )
    technologies = models.ManyToManyField(
        Skill,
        blank=True,
        related_name="projects",
    )
    category = models.CharField(max_length=100, db_index=True)
    industry = models.ForeignKey(
        Industry,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="projects",
    )
    client = models.CharField(max_length=180, blank=True)
    project_date = models.DateField(blank=True, null=True, db_index=True)
    live_url = models.URLField(blank=True, validators=[URLValidator()])
    github_url = models.URLField(blank=True, validators=[URLValidator()])
    features = models.TextField(blank=True, help_text="One feature per line.")
    challenges = models.TextField(blank=True)
    solutions = models.TextField(blank=True)
    results = models.TextField(blank=True)
    seo_title = models.CharField(max_length=180, blank=True)
    seo_description = models.CharField(max_length=300, blank=True)
    featured = models.BooleanField(default=False, db_index=True)
    display_order = models.PositiveIntegerField(default=0, db_index=True)

    class Meta:
        ordering = ["display_order", "-project_date", "-created_at"]
        indexes = [
            models.Index(fields=["featured", "display_order"]),
            models.Index(fields=["category", "industry"]),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def line_list(self, attr):
        return [x.strip() for x in getattr(self, attr).splitlines() if x.strip()]

    @property
    def meta_title(self):
        return self.seo_title or self.title

    @property
    def meta_description(self):
        return self.seo_description or self.short_description

    def __str__(self):
        return self.title


# ============================================================
# PROJECT IMAGE
# ============================================================

class ProjectImage(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="gallery",
    )
    image = models.ImageField(upload_to="projects/gallery/")
    alt_text = models.CharField(max_length=180, blank=True)
    caption = models.CharField(max_length=200, blank=True)
    display_order = models.PositiveIntegerField(default=0, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)

    class Meta:
        ordering = ["display_order", "id"]

    def __str__(self):
        return f"{self.project.title} — image {self.pk}"


# ============================================================
# EXPERIENCE
# ============================================================

class Experience(TimeStampedModel):
    position = models.CharField(max_length=180)
    company = models.CharField(max_length=180)
    location = models.CharField(max_length=180, blank=True)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    is_current = models.BooleanField(default=False)
    description = models.TextField(blank=True)
    responsibilities = models.TextField(
        blank=True,
        help_text="One responsibility per line.",
    )
    technologies = models.ManyToManyField(
        Skill,
        blank=True,
        related_name="experiences",
    )
    display_order = models.PositiveIntegerField(default=0, db_index=True)

    class Meta:
        ordering = ["display_order", "-start_date"]

    def responsibility_list(self):
        return [x.strip() for x in self.responsibilities.splitlines() if x.strip()]

    def __str__(self):
        return f"{self.position} — {self.company}"


# ============================================================
# REVIEW
# ============================================================

class Review(TimeStampedModel):
    name = models.CharField(max_length=150)
    profile_picture = models.ImageField(upload_to="reviews/", blank=True, null=True)
    role = models.CharField(max_length=150, blank=True)
    company = models.CharField(max_length=150, blank=True)
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    review_text = models.TextField()
    is_approved = models.BooleanField(default=False, db_index=True)
    is_featured = models.BooleanField(default=False, db_index=True)

    class Meta:
        ordering = ["-is_featured", "-created_at"]
        indexes = [
            models.Index(fields=["is_approved", "is_featured", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.rating}/5)"


# ============================================================
# CONTACT MESSAGE
# ============================================================

class ContactMessage(TimeStampedModel):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    name = models.CharField(max_length=150)
    email = models.EmailField()
    subject = models.CharField(max_length=220)
    message = models.TextField()
    project_type = models.CharField(max_length=120, blank=True)
    budget = models.CharField(max_length=100, blank=True)
    is_read = models.BooleanField(default=False, db_index=True)

    # Workflow
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        db_index=True,
    )
    token = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    rejected_at = models.DateTimeField(null=True, blank=True)
    reply_sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.name} — {self.subject} ({self.get_status_display()})"

    @property
    def is_pending(self):
        return self.status == "pending"

    @property
    def is_approved(self):
        return self.status == "approved"

    @property
    def is_rejected(self):
        return self.status == "rejected"


# ============================================================
# SOCIAL LINK
# ============================================================

class SocialLink(TimeStampedModel):
    PLATFORM_CHOICES = [
        ("GitHub", "GitHub"),
        ("LinkedIn", "LinkedIn"),
        ("X", "X / Twitter"),
        ("Instagram", "Instagram"),
        ("Facebook", "Facebook"),
        ("Fiverr", "Fiverr"),
        ("Upwork", "Upwork"),
        ("Website", "Website"),
    ]

    platform = models.CharField(max_length=40, choices=PLATFORM_CHOICES)
    label = models.CharField(max_length=80, blank=True)
    url = models.URLField()
    icon = models.CharField(max_length=30, blank=True)
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["display_order", "platform"]

    def __str__(self):
        return self.label or self.platform


# ============================================================
# SITE SETTINGS
# ============================================================

class SiteSettings(TimeStampedModel):
    site_name = models.CharField(max_length=160, default="Danish Umer")
    headline = models.CharField(max_length=220, default="Full-Stack Web Developer")
    hero_eyebrow = models.CharField(
        max_length=220,
        default="Available for freelance & contract work",
    )
    hero_intro = models.TextField(
        default="I build modern, scalable and high-performing digital experiences for ambitious businesses."
    )
    about_title = models.CharField(
        max_length=180,
        default="Engineering with product thinking.",
    )
    about_text = models.TextField(
        default="I design and build dependable digital products with a sharp focus on clarity, performance, maintainability, and user experience."
    )
    email = models.EmailField(default="hello@example.com")
    phone = models.CharField(max_length=80, blank=True)
    location = models.CharField(max_length=180, default="Pakistan")
    availability = models.CharField(
        max_length=180,
        default="Open to selected freelance & contract work",
    )
    profile_image = models.ImageField(upload_to="site/", blank=True, null=True)
    logo_text = models.CharField(max_length=80, default="DU.")
    resume_url = models.URLField(blank=True)
    footer_description = models.CharField(
        max_length=300,
        default="Full-stack engineering for ambitious ideas.",
    )
    meta_title = models.CharField(
        max_length=180,
        default="Danish Umer — Full-Stack Developer",
    )
    meta_description = models.CharField(
        max_length=300,
        default="Premium portfolio of Danish Umer, a full-stack web developer building modern digital products.",
    )
    og_image = models.ImageField(upload_to="site/", blank=True, null=True)
    canonical_url = models.URLField(blank=True)

    class Meta:
        verbose_name = "Site Settings"
        verbose_name_plural = "Site Settings"

    def __str__(self):
        return self.site_name

class AdminPreferences(models.Model):
    """Singleton — admin UI preferences."""

    # Layout
    boxed_layout = models.BooleanField(default=False)
    sticky_header = models.BooleanField(default=True)
    minimal_sidebar = models.BooleanField(default=False)
    dark_header = models.BooleanField(default=True)
    dark_sidebar = models.BooleanField(default=True)

    # Banner
    show_banner = models.BooleanField(default=False)
    banner_text = models.CharField(
        max_length=240,
        blank=True,
        default="Welcome to your portfolio CMS.",
    )

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Admin preferences"
        verbose_name_plural = "Admin preferences"

    def __str__(self):
        return "Admin preferences"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)
        cache.delete("admin_preferences")

    @classmethod
    def load(cls):
        prefs = cache.get("admin_preferences")
        if prefs is None:
            prefs, _ = cls.objects.get_or_create(pk=1)
            cache.set("admin_preferences", prefs, 300)
        return prefs