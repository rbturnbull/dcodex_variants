from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('<str:witness_slug>/<int:location_id>/', views.location_for_witness, name='location_for_witness'),
    path('attestations/', views.attestations, name='attestations'),
    path('set_attestation/', views.set_attestation, name='set_attestation'),
    path('remove_attestation/', views.remove_attestation, name='remove_attestation'),
    path('set_contra/', views.set_contra, name='set_contra'),
    path('remove_contra/', views.remove_contra, name='remove_contra'),
    #path('get_attestation/', views.get_attestation, name='get_attestation'),
]