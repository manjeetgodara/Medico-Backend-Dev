from django.contrib import admin
from search.models import SearchResult , UserSearchHistory

# Register your models here.
admin.site.register(SearchResult)
admin.site.register(UserSearchHistory)
