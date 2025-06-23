from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from . import views

urlpatterns = [
    path('gerar_declaracoes/', views.gerar_declaracoes, name='gerar_declaracoes'),
    path('menu/', views.declaracoes_menu, name='declaracoes_menu'),
    path('gerar_declaracao_contrapartida_pesquisa/<int:projeto_id>/<int:mes>/<int:ano>/', views.gerar_declaracao_contrapartida_pesquisa, name='gerar_declaracao_contrapartida_pesquisa'),
    path('contrapartida_pesquisa/<int:id_declaracao>/', views.declaracao_contrapartida_pesquisa_view.as_view(), name='ver_declaracao_contrapartida_pesquisa'),
    #path('gerar_declaracao_contrapartida_pesquisa/<int:projeto_id>/<int:mes>/<int:ano>/', gerar_declaracao_contrapartida_pesquisa, name='gerar_declaracao_pesquisa'),
    #path('ver_declaracao_contrapartida_pesquisa/<int:id_declaracao>/', declaracao_contrapartida_pesquisa_view.as_view(), name='ver_declaracao_pesquisa'),
    #path('pdf_declaracao_contrapartida_pesquisa/<int:id_declaracao>/', pdf_declaracao_contrapartida_pesquisa, name='pdf_declaracao_pesquisa'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)