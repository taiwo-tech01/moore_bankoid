
from django.urls import path
from . import views

urlpatterns = [
    path('login/',views.loginView, name='client_login'),
    # path('profile/<int:profile_id>/',views.profilePage, name='client-profile-page'),
    # path("",views.cardpurchaseEndpoint),
    # path('profiles/',views.getAllprofile,),
    # path('profile/',views.getAllprofile, name='client_profie_page'),
    path("signup/",views.signUp, name='client_signup'),
    path('logout/',views.logout_page, name= 'logout'),
    path('transfer/',views.transferPage, name= 'client_transfer'),
    path('profile/',views.profilePage, name= 'client_profile'),
    path('pin/',views.pinPage, name= 'client_pin'),
    path('dashboard/',views.dashboardPage, name= 'client_dashboard'),
    path('transactions/', views.TransactionPage, name="client_transactions"),
    path('user-search/',views.searchUser, name='client_search_page')


]