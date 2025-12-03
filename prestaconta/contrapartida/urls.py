from . import views
from .views import *
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.http import HttpResponse
from django.urls import path, include
from django.views.generic.base import RedirectView
from django.contrib import admin

def robots_txt(request):
    lines = [
        "User-agent: *",
        "Disallow: /",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")

urlpatterns = [
    path('', views.index, name='index'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    path("robots.txt", robots_txt),

    path('importar_csv/', views.importar_csv, name='importar_csv'),
    path('download_database/', views.download_database, name='download_database'),

    path("projeto_create/", views.projeto_create.as_view(), name='projeto_create'),
    path('projeto_menu/', views.projeto_menu.as_view(), name='projeto_menu'),
    path("projeto_update/<int:pk>/", views.projeto_update.as_view(), name='projeto_update'),
    path('projeto_delete/<int:pk>/', views.projeto_delete.as_view(), name='projeto_delete'),

    path("equipamento_create/", views.equipamento_create.as_view(), name='equipamento_create'),
    path('equipamento_menu/', views.equipamento_menu.as_view(), name='equipamento_menu'),
    path("equipamento_update/<int:pk>/", views.equipamento_update.as_view(), name='equipamento_update'),
    path('equipamento_delete/<int:pk>/', views.equipamento_delete.as_view(), name='equipamento_delete'),

    path("pessoa_create/", views.pessoa_create.as_view(), name='pessoa_create'),
    path('pessoa_menu/', views.pessoa_menu.as_view(), name='pessoa_menu'),
    path("pessoa_update/<int:pk>/", views.pessoa_update.as_view(), name='pessoa_update'),
    path('pessoa_delete/<int:pk>/', views.pessoa_delete.as_view(), name='pessoa_delete'),

    path("salario_create/", views.salario_create.as_view(), name='salario_create'),
    path('salario_menu/', views.salario_menu.as_view(), name='salario_menu'),
    path("salario_update/<int:pk>/", views.salario_update.as_view(), name='salario_update'),
    path('salario_delete/<int:pk>/', views.salario_delete.as_view(), name='salario_delete'),

    path("projetos_semestre/", projetos_semestre.as_view(), name="projetos_semestre"),

    path("contrapartida_pesquisa_create/", views.contrapartida_pesquisa_create.as_view(), name='contrapartida_pesquisa_create'),
    path('contrapartida_pesquisa_menu/', views.contrapartida_pesquisa_menu.as_view(), name='contrapartida_pesquisa_menu'),
    path("contrapartida_pesquisa_update/<int:pk>/", views.contrapartida_pesquisa_update.as_view(), name='contrapartida_pesquisa_update'),
    path('contrapartida_pesquisa_delete/<int:pk>/', views.contrapartida_pesquisa_delete.as_view(), name='contrapartida_pesquisa_delete'),
    path('contrapartida_pesquisa_criar_multiplos/',views.contrapartida_pesquisa_criar_multiplos,name='contrapartida_pesquisa_criar_multiplos'),
    path('api/horas-disponiveis/',views.obter_horas_disponiveis, name='obter_horas_disponiveis'),
    #path('api/obter-salarios-por-projeto/', views.obter_salarios_por_projeto, name='obter_salarios_por_projeto'),



    path("contrapartida_equipamento_create/", views.contrapartida_equipamento_create.as_view(), name='contrapartida_equipamento_create'),    
    path('contrapartida_equipamento_menu/', views.contrapartida_equipamento_menu.as_view(), name='contrapartida_equipamento_menu'),
    path("contrapartida_equipamento_update/<int:pk>/", views.contrapartida_equipamento_update.as_view(), name='contrapartida_equipamento_update'),
    path('contrapartida_equipamento_delete/<int:pk>/', views.contrapartida_equipamento_delete.as_view(), name='contrapartida_equipamento_delete'),
    path('contrapartida_equipamento_criar_multiplos/',views.contrapartida_equipamento_criar_multiplos,name='contrapartida_equipamento_criar_multiplos'),

    path('contrapartida_so_menu/', views.contrapartida_so_menu.as_view(), name='contrapartida_so_menu'),
    path('contrapartida_so_menu_new/', views.contrapartida_so_menu_new.as_view(), name='contrapartida_so_menu_new'),
    path('contrapartida_so_projeto/<int:id_projeto>', views.contrapartida_so_proj.as_view(),name='contrapartida_so_projeto'),
    path("contrapartida_so_create/<int:id_projeto>", views.contrapartida_so_create.as_view(), name='contrapartida_so_create'),
    path("contrapartida_so_update/<int:pk>/", views.contrapartida_so_update.as_view(), name='contrapartida_so_update'),
    path('contrapartida_so_delete/<int:pk>/', views.contrapartida_so_delete.as_view(), name='contrapartida_so_delete'),
    path('contrapartida_so_criar_multiplos/',views.contrapartida_so_criar_multiplos,name='contrapartida_so_criar_multiplos'),

    path("contrapartida_rh_create/", views.contrapartida_rh_create.as_view(), name='contrapartida_rh_create'),
    path('contrapartida_rh_menu/', views.contrapartida_rh_menu.as_view(), name='contrapartida_rh_menu'),
    path("contrapartida_rh_update/<int:pk>/", views.contrapartida_rh_update.as_view(), name='contrapartida_rh_update'),
    path('contrapartida_rh_delete/<int:pk>/', views.contrapartida_rh_delete.as_view(), name='contrapartida_rh_delete'),
    path('contrapartida_rh_criar_multiplos/',views.contrapartida_rh_criar_multiplos,name='contrapartida_rh_criar_multiplos'),

    path("contrapartida_realizada_list/", views.contrapartida_realizada_list.as_view(), name='contrapartida_realizada_list'),
    path('contrapartida_realizada_detalhes/<int:projeto_id>/', contrapartida_realizada_detalhes, name='contrapartida_realizada_detalhes'),
    path("contrapartida_realizada_geral/", contrapartida_realizada_geral, name='contrapartida_realizada_geral'),
    path('upload/', views.upload_contracheque, name='upload_contracheque'),
    
    path('verifica_contracheque/', verifica_contracheque, name='verifica_contracheque'),
    path('declaracao/', include('declaracao.urls')),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

