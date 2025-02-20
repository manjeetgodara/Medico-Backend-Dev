from django.db import models
from users.models import User
from datetime import datetime


class SearchResult(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="searchresult")
    search_query = models.CharField(max_length=255,db_index=True)
    results_count = models.IntegerField(default=0,db_index=True)
    #search_results = models.TextField(default="{}")
    timestamp = models.DateTimeField(auto_now_add=True,db_index=True) 


    def __str__(self):
        return f' {self.search_query} {self.results_count}'


class UserSearchHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,related_name="searchhistory")
    filters_data = models.JSONField(default=dict,db_index=True) 
    timestamp = models.DateTimeField(auto_now_add=True,db_index=True)

    def __str__(self):
        return f' search data by filter {self.user} '

    


    