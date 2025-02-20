
from django.contrib import admin
from django.urls import path
from .views import  UserSearch, RetrieveSearchResults , DeleteSearchResult,DeleteUserSearchHistory, UserSearchfilter


urlpatterns = [
    path('allusers/<str:mlp_id>/', UserSearch, name="alluser"),
    path('searchfilter/<str:mlp_id>/',UserSearchfilter,name="search_filter"),
    path('saveSearch/<str:mlp_id>/', RetrieveSearchResults, name="search_results"),
    path('delete-saved-searches/<int:result_id>/',DeleteSearchResult, name ="delete_saved_results"),
    path('delete-search-filter/<int:search_history_id>/',DeleteUserSearchHistory,name="delete search history")
]
