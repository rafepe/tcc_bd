from django.contrib import admin
from django.urls import path
from django.views.generic.base import RedirectView
from django.contrib.auth import views as auth_views

from . import views
from .views import *

favicon_view = RedirectView.as_view(url='/static/favicon.ico', permanent=True)

urlpatterns = [
    path('', views.index, name='index'),
    path('favicon.ico', favicon_view),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    path('importar_csv/', views.importar_csv, name='importar_csv'),

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


    # path('contrapartida_pesquisa_create/', views.contrapartida_pesquisa_create, name='contrapartida_pesquisa_create'),
    # path('buscar_pessoas/', views.buscar_pessoas, name='buscar_pessoas'),
    # path('buscar_salarios/', views.buscar_salarios, name='buscar_salarios'),
]

