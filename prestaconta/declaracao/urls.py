from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from . import views
from .views_folder.declaracoes_menu import declaracoes_menu

urlpatterns = [
    #path('ajax/dados-projeto/', views.ajax_dados_projeto, name='ajax_dados_projeto'),
    #path('central/',views.central_declaracoes, name='central_declaracoes'),
    #path('declaracoes/', declaracoes_menu, name='declaracoes_menu'),
    #path('download_declaracao_mes', views.download_declaracao_mes, name='download_declaracao_mes'),
    #path('gerar_declaracao_contrapartida_pesquisa/<int:projeto_id>/<int:mes>/<int:ano>/', gerar_declaracao_contrapartida_pesquisa, name='gerar_declaracao_pesquisa'),
    #path('gerar_declaracoes/', views.gerar_declaracoes, name='gerar_declaracoes'),
    #path('gerar/rh/<int:projeto_id>/<int:mes>/<int:ano>/', views.gerar_declaracao_rh, name='gerar_declaracao_contrapartida_rh'),
    #path('menu/', views.declaracoes_menu, name='menu'),
    #path('menutai/', views.menutai, name='menutai'),
    #path('pdf_declaracao_contrapartida_pesquisa/<int:id_declaracao>/', pdf_declaracao_contrapartida_pesquisa, name='pdf_declaracao_pesquisa'),
    #path('ver_declaracao_contrapartida_pesquisa/<int:id_declaracao>/', declaracao_contrapartida_pesquisa_view.as_view(), name='ver_declaracao_pesquisa'),
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
    path('declaracao/menu/', views.central_declaracoes, name='central_declaracoes'),
    path('declaracoes-menu/', declaracoes_menu, name='declaracoes_menu'),
    path('gerar_declaracao_contrapartida_equipamento/<int:projeto_id>/<int:mes>/<int:ano>/', views.gerar_declaracao_contrapartida_equipamento, name='gerar_declaracao_contrapartida_equipamento'),
    path('gerar_declaracao_contrapartida_pesquisa/<int:projeto_id>/<int:mes>/<int:ano>/', views.gerar_declaracao_contrapartida_pesquisa, name='gerar_declaracao_contrapartida_pesquisa'),
    path('gerar_declaracao_contrapartida_rh/<int:projeto_id>/<int:mes>/<int:ano>/', views.gerar_declaracao_contrapartida_rh, name='gerar_declaracao_contrapartida_rh'),
    path('gerar_declaracao_contrapartida_so/<int:projeto_id>/<int:mes>/<int:ano>/', views.gerar_declaracao_contrapartida_so, name='gerar_declaracao_contrapartida_so'),
    #path('gerar-declaracao/', views.central_declaracoes, name='gerar_declaracao_contrapartida_rh'),
    #path('gerar-declaracao/', views.central_declaracoes, name='gerar_declaracao_contrapartida_rh'),
    #path('gerar-declaracao/', views.gerar_declaracao_contrapartida_rh, name='gerar_declaracao'),
    path('gerar-docx/<int:declaracao_id>/', views.gerar_docx, name='gerar_docx'),
    path('menu/', declaracoes_menu, name='declaracoes_menu'),
    path('remover_contrapartida_equipamento/<int:pk>/', views.declaracao_contrapartida_equipamento_delete.as_view(), name='remover_declaracao_contrapartida_equipamento'),
    path('remover_contrapartida_pesquisa/<int:pk>/', views.declaracao_contrapartida_pesquisa_delete.as_view(), name='remover_declaracao_contrapartida_pesquisa'),
    path('remover_contrapartida_rh/<int:pk>/', views.declaracao_contrapartida_rh_delete.as_view(), name='remover_declaracao_contrapartida_rh'),
    path('remover_contrapartida_so/<int:pk>/', views.declaracao_contrapartida_so_delete.as_view(), name='remover_declaracao_contrapartida_so'),
# URL consolidada que trata tanto visualização quanto geração
###

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)