from django import forms
from .models import Receita

class ReceitaForm(forms.ModelForm):
    class Meta:
        model = Receita
        fields = ['titulo', 'descricao', 'ingredientes', 'modo_preparo', 'tempo_preparo', 'categoria', 'nivel_dificuldade', 'foto']
        widgets = {
            'ingredientes': forms.Textarea(attrs={'rows': 5}),
            'modo_preparo': forms.Textarea(attrs={'rows': 5}),
        }
