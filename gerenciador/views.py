from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import FormView
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.template.loader import render_to_string
from django import forms
from .models import Receita
from django.db.models import Q, Avg, Count, Exists, OuterRef
from django.http import JsonResponse

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username'].strip()
        password = request.POST['password'].strip()
        user = authenticate(request, username=username, password=password)
        if user is None:
            alerta = 'Usuário ou senha incorreta'
            context = {
                'alerta': alerta
            }
            return render(request, 'login.html', context)
        else:
            login(request, user)
    if request.user.is_authenticated:
        return redirect('receitas')
    return render(request, 'login.html')

@login_required
def fazer_logout(request):
    logout(request)
    return redirect('login')

class CustomUserCreationForm(forms.ModelForm):
    email = forms.EmailField(required=True)
    password1 = forms.CharField(label='Senha', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirme a senha', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("As senhas não coincidem")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user

class RegisterView(FormView):
    template_name = 'register.html'
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return super().form_valid(form)

@login_required
def receitas(request):
    query = request.GET.get('q')
    categoria = request.GET.get('categoria')
    dificuldade = request.GET.get('dificuldade')
    
    # Iniciar com todas as receitas
    receitas = Receita.objects.all().order_by('-data_criacao')

    # Aplicar filtros
    if query:
        receitas = receitas.filter(
            Q(titulo__icontains=query) |
            Q(ingredientes__icontains=query)
        )

    if categoria:
        receitas = receitas.filter(categoria=categoria)

    if dificuldade:
        receitas = receitas.filter(nivel_dificuldade=dificuldade)

    categorias = Receita.objects.values_list('categoria', flat=True).distinct()
    dificuldades = Receita.NIVEL_DIFICULDADE_CHOICES

    context = {
        'receitas': receitas,
        'categorias': categorias,
        'dificuldades': dificuldades,
        'query': query,
        'categoria_selecionada': categoria,
        'dificuldade_selecionada': dificuldade,
    }
    return render(request, 'receitas.html', context)

@login_required
def editar_receita(request, pk):
    receita = get_object_or_404(Receita, pk=pk, usuario=request.user)
    if request.method == 'POST':
        receita.titulo = request.POST.get('titulo', receita.titulo)
        receita.descricao = request.POST.get('descricao', receita.descricao)
        receita.ingredientes = request.POST.get('ingredientes', receita.ingredientes)
        receita.modo_preparo = request.POST.get('modo_preparo', receita.modo_preparo)
        receita.tempo_preparo = request.POST.get('tempo_preparo', receita.tempo_preparo)
        receita.categoria = request.POST.get('categoria', receita.categoria)
        receita.nivel_dificuldade = request.POST.get('nivel_dificuldade', receita.nivel_dificuldade)
        receita.foto = request.FILES.get('foto', receita.foto)

        try:
            receita.save()
            messages.success(request, 'Receita editada com sucesso!')
            return redirect('receitas')
        except Exception as e:
            messages.error(request, f'Erro ao editar receita: {str(e)}')
    
    return render(request, "receitas/editar_receita.html", {'receita': receita})

@login_required
def adicionar_receita(request):
    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        descricao = request.POST.get('descricao')
        ingredientes = request.POST.get('ingredientes')
        modo_preparo = request.POST.get('modo_preparo')
        tempo_preparo = request.POST.get('tempo_preparo')
        categoria_id = request.POST.get('categoria')
        nivel_dificuldade = request.POST.get('nivel_dificuldade')
        foto = request.FILES.get('foto')

        try:
            receita = Receita(
                usuario=request.user,
                titulo=titulo,
                descricao=descricao,
                ingredientes=ingredientes,
                modo_preparo=modo_preparo,
                tempo_preparo=tempo_preparo,
                categoria=categoria_id,
                nivel_dificuldade=nivel_dificuldade,
                foto=foto
            )
            receita.save()
            messages.success(request, 'Receita adicionada com sucesso!')
            return redirect('receitas')
        except Exception as e:
            messages.error(request, f'Erro ao adicionar receita: {str(e)}')
    return render(request, 'receitas/adicionar_receita.html')

@login_required
def excluir_receita(request, pk):
    receita = get_object_or_404(Receita, pk=pk, usuario=request.user)
    if request.method == 'POST':
        receita.delete()
        messages.success(request, 'Receita excluída com sucesso!')
        return redirect('receitas')
    return render(request, 'receitas/confirmar_exclusao.html', {'receita': receita})

@login_required
def detalhes_receita(request, pk):
    receita = get_object_or_404(Receita, pk=pk)
    is_owner = receita.usuario == request.user
    
    context = {
        'receita': receita,
        'is_owner': is_owner,
    }
    return render(request, 'receitas/detalhes_receita.html', context)

def esqueceu_senha(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            reset_link = request.build_absolute_uri(f'/redefinir-senha/{uid}/{token}/')
            
            subject = 'Redefinição de Senha - Receitas Culinárias'
            message = render_to_string('email_redefinir_senha.html', {
                'user': user,
                'reset_link': reset_link,
            })
            from_email = settings.DEFAULT_FROM_EMAIL
            recipient_list = [email]
            
            send_mail(subject, message, from_email, recipient_list, html_message=message)
            
            messages.success(request, 'Um e-mail com instruções para redefinir sua senha foi enviado.')
            return redirect('login')
        except User.DoesNotExist:
            messages.error(request, 'Não existe uma conta associada a este e-mail.')
    
    return render(request, 'esqueceu_senha.html')

def redefinir_senha(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            nova_senha = request.POST.get('nova_senha')
            confirmar_senha = request.POST.get('confirmar_senha')
            
            if nova_senha == confirmar_senha:
                user.set_password(nova_senha)
                user.save()
                messages.success(request, 'Sua senha foi redefinida com sucesso. Você pode fazer login agora.')
                return redirect('login')
            else:
                messages.error(request, 'As senhas não coincidem.')
        
        return render(request, 'redefinir_senha.html')
    else:
        messages.error(request, 'O link de redefinição de senha é inválido ou expirou.')
        return redirect('login')

@login_required
def avaliar_receita(request, pk):
    if request.method == 'POST':
        receita = get_object_or_404(Receita, pk=pk)
        estrelas = request.POST.get('estrelas')
        comentario = request.POST.get('comentario', '')

        try:
            avaliacao = Avaliacao.objects.get(usuario=request.user, receita=receita)
            avaliacao.estrelas = estrelas
            avaliacao.comentario = comentario
            avaliacao.save()
            messages.success(request, 'Avaliação atualizada com sucesso!')
        except Avaliacao.DoesNotExist:
            Avaliacao.objects.create(
                usuario=request.user,
                receita=receita,
                estrelas=estrelas,
                comentario=comentario
            )
            messages.success(request, 'Avaliação adicionada com sucesso!')

        return redirect('detalhes_receita', pk=pk)

@login_required
def favoritar_receita(request, pk):
    receita = get_object_or_404(Receita, pk=pk)
    favorito, created = Favorito.objects.get_or_create(
        usuario=request.user,
        receita=receita
    )

    if not created:
        favorito.delete()
        is_favorito = False
    else:
        is_favorito = True

    return JsonResponse({'is_favorito': is_favorito})
