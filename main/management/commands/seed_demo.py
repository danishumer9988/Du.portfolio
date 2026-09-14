from datetime import date
from django.core.management.base import BaseCommand
from main.models import *

class Command(BaseCommand):
    help = "Seed realistic demo portfolio content."

    def handle(self, *args, **kwargs):
        site, _ = SiteSettings.objects.get_or_create(pk=1)
        SocialLink.objects.all().delete()
        socials = [
            ("GitHub", "GitHub", "https://github.com/", "GH"),
            ("LinkedIn", "LinkedIn", "https://www.linkedin.com/", "in"),
            ("X", "X", "https://x.com/", "X"),
        ]
        for i, (p,l,u,ic) in enumerate(socials):
            SocialLink.objects.create(platform=p, label=l, url=u, icon=ic, display_order=i)

        industries = ["E-commerce","Technology","Education","Finance","Agriculture","Healthcare","Real Estate","Marketing","SaaS","Retail"]
        for i, name in enumerate(industries):
            Industry.objects.get_or_create(name=name, defaults={"icon":"✦","display_order":i})

        skills = [
            ("HTML","Frontend",92),("CSS","Frontend",90),("JavaScript","Frontend",88),("React","Frontend",86),
            ("Next.js","Frontend",84),("Python","Backend",95),("Django","Backend",94),("Express.js","Backend",78),
            ("PostgreSQL","Database",88),("SQLite","Database",90),("Git","Tools & Platforms",92),
            ("GitHub","Tools & Platforms",93),("Vercel","Tools & Platforms",82),("REST APIs","Tools & Platforms",92),("Deployment","Tools & Platforms",85),
        ]
        skill_objs = {}
        for i, (name, cat, level) in enumerate(skills):
            obj, _ = Skill.objects.get_or_create(name=name, category=cat, defaults={"skill_level":level,"display_order":i,"is_active":True})
            skill_objs[name] = obj

        services = [
            ("Full-Stack Web Development","End-to-end product engineering from interface to database.","◈"),
            ("Django Development","Robust Python backends, admin systems, APIs and data workflows.","Py"),
            ("React Development","Fast, purposeful interfaces with component-driven interaction.","⚡"),
            ("Next.js Development","Production-ready web experiences with modern routing and rendering.","N"),
            ("E-commerce Development","Conversion-focused commerce systems with secure workflows.","◇"),
            ("API Development","Clean, maintainable REST APIs designed for real-world integrations.","{}"),
            ("Database Development","Relational data modeling, migrations and performance-minded queries.","DB"),
            ("Website Optimization","Performance, UX polish, accessibility and maintainability improvements.","↗"),
            ("Digital Marketing","Technical foundations for discoverability, content and conversion.","✦"),
        ]
        for i, (title, desc, icon) in enumerate(services):
            Service.objects.get_or_create(title=title, defaults={
                "slug": slugify(title), "icon":icon, "short_description":desc,
                "full_description":desc, "features":"Semantic HTML\nResponsive UI\nMaintainable architecture",
                "display_order":i, "is_active":True
            })

        projects = [
            ("JobLidar","A focused jobs discovery product with a clear search-first experience.","Technology","Job platform"),
            ("Chrono Style","A polished commerce experience built around discovery and editorial product storytelling.","Retail","E-commerce"),
            ("Al-Toheed Crop POS","A desktop-ready agriculture retail POS with inventory, receipts and operational workflows.","Agriculture","POS"),
            ("Currency Exchanger","A responsive exchange experience for fast multi-currency calculations.","Finance","Web App"),
            ("File Converter","A local-first conversion platform with streamlined file workflows.","Technology","Productivity"),
            ("Portfolio CMS","A premium personal portfolio backed by Django Admin and relational content models.","Marketing","Portfolio"),
        ]
        default_industry = Industry.objects.get(name="Technology")
        for i, (title, short, industry_name, cat) in enumerate(projects):
            ind, _ = Industry.objects.get_or_create(name=industry_name)
            p, created = Project.objects.get_or_create(title=title, defaults={
                "slug":slugify(title), "short_description":short,
                "full_description":short + " Built with a strong emphasis on performance, accessibility, and maintainable engineering.",
                "category":cat, "industry":ind, "client":"Independent / Demo",
                "project_date":date(2025, max(1,12-i), 15),
                "features":"Responsive UI\nFast interactions\nAdmin-managed content",
                "challenges":"Balancing clarity, speed, and a polished visual identity.",
                "solutions":"Kept the architecture lightweight and made content/data first-class.",
                "results":"A scalable foundation ready for real content and deployment.",
                "featured":True, "display_order":i,
            })
            p.technologies.set([skill_objs[x] for x in ["Python","Django","JavaScript","CSS","SQLite"] if x in skill_objs][:5])

        companies = [
            ("Full-Stack Developer","Independent","Remote",date(2023,1,1),None,True),
            ("Backend / Product Engineer","Selected Projects","Pakistan",date(2022,1,1),date(2022,12,31),False),
        ]
        for i, item in enumerate(companies):
            pos, company, loc, start, end, current = item
            Experience.objects.get_or_create(position=pos, company=company, defaults={
                "location":loc,"start_date":start,"end_date":end,"is_current":current,
                "description":"Building dependable products across frontend, backend, data, and deployment.",
                "responsibilities":"Translate business requirements into clean product experiences.\nDesign maintainable application architecture.\nShip tested improvements and iterate from feedback.",
                "display_order":i,
            })

        if not Review.objects.exists():
            Review.objects.create(name="Ayesha Khan", role="Founder", company="Northstar", rating=5,
                                  review_text="Clear communication, strong ownership, and a product that felt considered at every layer.",
                                  is_approved=True, is_featured=True)
            Review.objects.create(name="Hassan Raza", role="Product Lead", company="Orbit", rating=5,
                                  review_text="Thoughtful engineering with a real eye for UX and performance.", is_approved=True)

        self.stdout.write(self.style.SUCCESS("Demo portfolio content seeded."))
