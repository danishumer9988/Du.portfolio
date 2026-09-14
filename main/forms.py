from django import forms
from .models import ContactMessage, Review

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ["name", "profile_picture", "role", "company", "rating", "review_text"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Your name", "autocomplete": "name"}),
            "profile_picture": forms.ClearableFileInput(attrs={"accept": "image/*"}),
            "role": forms.TextInput(attrs={"placeholder": "e.g. Founder"}),
            "company": forms.TextInput(attrs={"placeholder": "e.g. Acme Inc."}),
            "rating": forms.HiddenInput(),
            "review_text": forms.Textarea(attrs={"placeholder": "Share your experience…", "rows": 5}),
        }

class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ["name", "email", "subject", "message", "project_type", "budget"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Your name", "autocomplete": "name"}),
            "email": forms.EmailInput(attrs={"placeholder": "you@example.com", "autocomplete": "email"}),
            "subject": forms.TextInput(attrs={"placeholder": "What can I help you build?"}),
            "message": forms.Textarea(attrs={"placeholder": "Tell me a little about the project…", "rows": 6}),
            "project_type": forms.TextInput(attrs={"placeholder": "e.g. SaaS, e-commerce, website"}),
            "budget": forms.TextInput(attrs={"placeholder": "e.g. $1,000–$3,000"}),
        }

    def clean_message(self):
        value = self.cleaned_data["message"].strip()
        if len(value) < 12:
            raise forms.ValidationError("Please provide a little more detail.")
        return value
