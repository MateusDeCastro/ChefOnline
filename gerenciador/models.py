from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User
from django.db.models import Avg

# Create your models here.

class Receita(models.Model):
    NIVEL_DIFICULDADE_CHOICES = [
        ('F', 'Fácil'),
        ('M', 'Médio'),
        ('D', 'Difícil'),
    ]
    
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    titulo = models.CharField(max_length=200)
    descricao = models.TextField()
    ingredientes = models.TextField()
    modo_preparo = models.TextField()
    tempo_preparo = models.PositiveIntegerField(help_text="Tempo de preparo em minutos")
    categoria = models.CharField(max_length=100)  # Novo campo de texto para categoria
    nivel_dificuldade = models.CharField(max_length=1, choices=NIVEL_DIFICULDADE_CHOICES)
    foto = models.ImageField(upload_to='receitas/', blank=True, null=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
 
    def __str__(self):
        return self.titulo

    class Meta:
        ordering = ['-data_criacao']