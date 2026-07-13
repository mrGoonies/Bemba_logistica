from django import forms

from .models import Answer, Question


class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ["status", "comment", "photo"]


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ["area", "text", "criterio", "order"]
        widgets = {
            "area": forms.Select(attrs={"class": "input"}),
            "text": forms.TextInput(attrs={"class": "input"}),
            "criterio": forms.Textarea(attrs={"class": "input", "rows": 3}),
            "order": forms.NumberInput(attrs={"class": "input"}),
        }
