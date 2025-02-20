from rest_framework import serializers
from users.models import User
from search.models import SearchResult
import json


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id','mlp_id', 'name', 'email', 'religion', 'marital_status', 'gender', 'dob', 'about', 'future_aspirations', 
                  'profile_pictures', 'family_photos', 'activity_status', 'last_seen', 'completed_post_grad', 'caste', 'height', 
                  'weight', 'salary', 'eating_habits', 'smoking_habits', 'drinking_habits', 'hobbies', 'other_hobbies', 'city']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        for field in ['hobbies', 'partner_cities_from', 'partner_caste_from', 'profile_pictures','family_photos','partner_state_from','partner_country_from','profession','other_hobbies','video']:
            if field in representation and representation[field]:
                field_str = representation[field]
                field_list = json.loads(field_str.replace("'", "\""))
                representation[field] = field_list

        if 'religion' in representation and representation['religion']:
            religion_name = instance.religion.name
            representation['religion_name'] = religion_name

        if 'marital_status' in representation and representation['marital_status']:
            marital_status_name = instance.marital_status.name
            representation['marital_status_name'] = marital_status_name        

        return representation    


class SearchResultSerializer(serializers.ModelSerializer):
    timestamp = serializers.DateTimeField()
    class Meta:
        model = SearchResult
        fields = ['id', 'user', 'search_query', 'results_count', 'timestamp']
