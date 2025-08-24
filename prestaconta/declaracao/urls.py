from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from . import views
from .views_folder.declaracoes_menu import declaracoes_menu

urlpatterns = [
    path('', declaracoes_menu, name='declaracoes_menu'),
    path('ajax/dados-projeto/', views.ajax_dados_projeto, name='ajax_dados_projeto'),
    path('central-declaracoes/', views.central_declaracoes, name='central_declaracoes'),
    path('central/', views.central_declaracoes, name='central_declaracoes'),
    path('contrapartida_equipamento/<int:id_declaracao>/', views.declaracao_contrapartida_equipamento_view.as_view(), name='ver_declaracao_contrapartida_equipamento'),
    path('contrapartida_pesquisa/<int:id_declaracao>/', views.declaracao_contrapartida_pesquisa_view.as_view(), name='ver_declaracao_contrapartida_pesquisa'),
    path('contrapartida_rh/<int:id_declaracao>/', views.declaracao_contrapartida_rh_view.as_view(), name='ver_declaracao_contrapartida_rh'),
    path('contrapartida_so/<int:id_declaracao>/', views.declaracao_contrapartida_so_view.as_view(), name='ver_declaracao_contrapartida_so'),
    path('declaracao/<int:declaracao_id>/', views.visualizar_declaracao, name='visualizar_declaracao'),
    path('declaracao/<int:declaracao_id>/editar/', views.editar_declaracao, name='editar_declaracao'),
    path('declaracao/<int:declaracao_id>/pdf/', views.download_declaracao, name='download_declaracao'),
    path('declaracao/download/', views.download_declaracao_mes, name='download_declaracao_mes'),
    path('declaracao/gerar/', views.gerar_declaracao_contrapartida_rh, name='gerar_declaracao_contrapartida_rh'),
    path('gerar_declaracao_contrapartida_equipamento/<int:projeto_id>/<int:mes>/<int:ano>/', views.gerar_declaracao_contrapartida_equipamento, name='gerar_declaracao_contrapartida_equipamento'),
    path('gerar_declaracao_contrapartida_pesquisa/<int:projeto_id>/<int:mes>/<int:ano>/', views.gerar_declaracao_contrapartida_pesquisa, name='gerar_declaracao_contrapartida_pesquisa'),
    path('gerar_declaracao_contrapartida_rh/<int:projeto_id>/<int:mes>/<int:ano>/', views.gerar_declaracao_contrapartida_rh, name='gerar_declaracao_contrapartida_rh'),
    path('gerar_declaracao_contrapartida_so/<int:projeto_id>/<int:mes>/<int:ano>/', views.gerar_declaracao_contrapartida_so, name='gerar_declaracao_contrapartida_so'),
    path('gerar-docx-equipamento/<int:id>/', views.gerar_docx_equipamento, name='gerar_docx_equipamento'),
    path('gerar-docx-pesquisa/<int:declaracao_id>/', views.gerar_docx_pesquisa, name='gerar_docx_pesquisa'),
    path('gerar-docx-rh/<int:declaracao_id>/', views.gerar_docx_rh, name='gerar_docx_rh'),
    path('gerar-docx-so/<int:declaracao_id>/', views.gerar_docx_so, name='gerar_docx_so'),
    path('menu/', declaracoes_menu, name='declaracoes_menu'),
    path('remover_contrapartida_equipamento/<int:pk>/', views.declaracao_contrapartida_equipamento_delete.as_view(), name='remover_declaracao_contrapartida_equipamento'),
    path('remover_contrapartida_pesquisa/<int:pk>/', views.declaracao_contrapartida_pesquisa_delete.as_view(), name='remover_declaracao_contrapartida_pesquisa'),
    path('remover_contrapartida_rh/<int:pk>/', views.declaracao_contrapartida_rh_delete.as_view(), name='remover_declaracao_contrapartida_rh'),
    path('remover_contrapartida_so/<int:pk>/', views.declaracao_contrapartida_so_delete.as_view(), name='remover_declaracao_contrapartida_so'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)