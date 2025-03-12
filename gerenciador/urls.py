from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views
from .views import RegisterView

urlpatterns = [
    path('', views.login_view, name='login'),
    path('logout/', views.fazer_logout, name='logout'),
    path('register/', RegisterView.as_view(), name='register'),
    path('receitas/', views.receitas, name='receitas'),
    path('receitas/adicionar/', views.adicionar_receita, name='adicionar_receita'),
    path('esqueceu-senha/', views.esqueceu_senha, name='esqueceu_senha'),
    path('redefinir-senha/<uidb64>/<token>/', views.redefinir_senha, name='redefinir_senha'),
    path('receitas/excluir/<int:pk>/', views.excluir_receita, name='excluir_receita'),
    path('receitas/editar/<int:pk>/', views.editar_receita, name='editar_receita'),
    path('receita/<int:pk>/', views.detalhes_receita, name='detalhes_receita'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
