from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from . import views

urlpatterns = [
    path('gerar_declaracoes/', views.gerar_declaracoes, name='gerar_declaracoes'),
    path('menu/', views.declaracoes_menu, name='declaracoes_menu'),
    path('gerar_declaracao_contrapartida_pesquisa/<int:projeto_id>/<int:mes>/<int:ano>/', views.gerar_declaracao_contrapartida_pesquisa, name='gerar_declaracao_contrapartida_pesquisa'),
    path('contrapartida_pesquisa/<int:id_declaracao>/', views.declaracao_contrapartida_pesquisa_view.as_view(), name='ver_declaracao_contrapartida_pesquisa'),
    path('remover_contrapartida_pesquisa/<int:pk>/', views.declaracao_contrapartida_pesquisa_delete.as_view(), name='remover_declaracao_contrapartida_pesquisa'),
    #path('gerar_declaracao_contrapartida_pesquisa/<int:projeto_id>/<int:mes>/<int:ano>/', gerar_declaracao_contrapartida_pesquisa, name='gerar_declaracao_pesquisa'),
    #path('ver_declaracao_contrapartida_pesquisa/<int:id_declaracao>/', declaracao_contrapartida_pesquisa_view.as_view(), name='ver_declaracao_pesquisa'),
    #path('pdf_declaracao_contrapartida_pesquisa/<int:id_declaracao>/', pdf_declaracao_contrapartida_pesquisa, name='pdf_declaracao_pesquisa'),
    path('gerar_declaracao_contrapartida_so/<int:projeto_id>/<int:mes>/<int:ano>/', views.gerar_declaracao_contrapartida_so, name='gerar_declaracao_contrapartida_so'),
    path('contrapartida_so/<int:id_declaracao>/', views.declaracao_contrapartida_so_view.as_view(), name='ver_declaracao_contrapartida_so'),
    path('remover_contrapartida_so/<int:pk>/', views.declaracao_contrapartida_so_delete.as_view(), name='remover_declaracao_contrapartida_so'),
    path('gerar_declaracao_contrapartida_rh/<int:projeto_id>/<int:mes>/<int:ano>/', views.gerar_declaracao_contrapartida_rh, name='gerar_declaracao_contrapartida_rh'),
    path('contrapartida_rh/<int:id_declaracao>/', views.declaracao_contrapartida_rh_view.as_view(), name='ver_declaracao_contrapartida_rh'),
    path('remover_contrapartida_rh/<int:pk>/', views.declaracao_contrapartida_rh_delete.as_view(), name='remover_declaracao_contrapartida_rh'),
    path('gerar_declaracao_contrapartida_equipamento/<int:projeto_id>/<int:mes>/<int:ano>/', views.gerar_declaracao_contrapartida_equipamento, name='gerar_declaracao_contrapartida_equipamento'),
    path('contrapartida_equipamento/<int:id_declaracao>/', views.declaracao_contrapartida_equipamento_view.as_view(), name='ver_declaracao_contrapartida_equipamento'),
    path('remover_contrapartida_equipamento/<int:pk>/', views.declaracao_contrapartida_equipamento_delete.as_view(), name='remover_declaracao_contrapartida_equipamento'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)