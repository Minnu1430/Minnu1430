"""
Django REST Serializers for Classified Data
"""

from rest_framework import serializers
from .models import DocumentUpload, ExtractedClassified, Category, Location, SearchLog


class DocumentUploadSerializer(serializers.ModelSerializer):
    """Serializer for DocumentUpload model"""
    
    processing_time = serializers.SerializerMethodField()
    total_classifieds = serializers.SerializerMethodField()
    
    class Meta:
        model = DocumentUpload
        fields = [
            'id', 'file_name', 'file_path', 'upload_date', 'file_size',
            'total_pages', 'status', 'processing_start', 'processing_end',
            'processing_time', 'total_classifieds', 'uploaded_by'
        ]
        read_only_fields = ['id', 'upload_date', 'processing_start', 'processing_end']
    
    def get_processing_time(self, obj):
        return obj.get_processing_time()
    
    def get_total_classifieds(self, obj):
        return obj.classifieds.count()


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Category model"""
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'keywords']


class LocationSerializer(serializers.ModelSerializer):
    """Serializer for Location model"""
    
    class Meta:
        model = Location
        fields = ['id', 'area_name', 'district', 'latitude', 'longitude']


class ExtractedClassifiedSerializer(serializers.ModelSerializer):
    """Serializer for ExtractedClassified model"""
    
    category_name = serializers.CharField(source='category.name', read_only=True)
    location_name = serializers.CharField(source='location.area_name', read_only=True)
    document_name = serializers.CharField(source='document.file_name', read_only=True)
    
    class Meta:
        model = ExtractedClassified
        fields = [
            'id', 'document', 'document_name', 'title', 'description',
            'category', 'category_name', 'location', 'location_name',
            'contact_number', 'email', 'newspaper_date', 'newspaper_name',
            'page_number', 'extracted_date', 'confidence_score', 'is_duplicate'
        ]
        read_only_fields = ['id', 'extracted_date', 'is_duplicate']


class ExtractedClassifiedDetailSerializer(ExtractedClassifiedSerializer):
    """Detailed serializer with additional information"""
    
    category_obj = CategorySerializer(source='category', read_only=True)
    location_obj = LocationSerializer(source='location', read_only=True)
    document_obj = DocumentUploadSerializer(source='document', read_only=True)
    
    class Meta(ExtractedClassifiedSerializer.Meta):
        fields = ExtractedClassifiedSerializer.Meta.fields + [
            'category_obj', 'location_obj', 'document_obj', 'original_image_reference'
        ]


class SearchLogSerializer(serializers.ModelSerializer):
    """Serializer for SearchLog model"""
    
    class Meta:
        model = SearchLog
        fields = ['id', 'search_query', 'search_filters', 'results_count', 'timestamp', 'user_id']
        read_only_fields = ['id', 'timestamp']


class DashboardStatsSerializer(serializers.Serializer):
    """Serializer for dashboard statistics"""
    
    total_documents = serializers.IntegerField()
    total_classifieds = serializers.IntegerField()
    documents_by_status = serializers.DictField()
    classifieds_by_category = serializers.DictField()
    classifieds_by_location = serializers.DictField()
    recent_uploads = DocumentUploadSerializer(many=True)
    recent_classifieds = ExtractedClassifiedSerializer(many=True)
    average_confidence = serializers.FloatField()
    total_searches = serializers.IntegerField()


class BulkUploadSerializer(serializers.Serializer):
    """Serializer for bulk file uploads"""
    
    files = serializers.ListField(
        child=serializers.FileField(),
        allow_empty=False
    )


class ClassifiedSearchSerializer(serializers.Serializer):
    """Serializer for classified search parameters"""
    
    q = serializers.CharField(required=False, allow_blank=True)
    category = serializers.CharField(required=False, allow_blank=True)
    location = serializers.CharField(required=False, allow_blank=True)
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)
    sort_by = serializers.ChoiceField(
        choices=['recent', 'relevance', 'confidence'],
        default='recent'
    )
