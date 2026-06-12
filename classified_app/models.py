"""
ClassiFind AI - Database Models
"""

from django.db import models
from django.core.validators import FileExtensionValidator
from django.utils import timezone

class DocumentUpload(models.Model):
    """Store information about uploaded classified documents"""
    
    STATUS_CHOICES = [
        ('uploaded', 'Uploaded'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    file_name = models.CharField(max_length=255)
    file_path = models.FileField(
        upload_to='uploads/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])]
    )
    upload_date = models.DateTimeField(auto_now_add=True)
    file_size = models.BigIntegerField(help_text="File size in bytes")
    total_pages = models.IntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='uploaded')
    processing_start = models.DateTimeField(null=True, blank=True)
    processing_end = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True, null=True)
    uploaded_by = models.CharField(max_length=255, default='admin')
    
    class Meta:
        db_table = 'document_upload'
        ordering = ['-upload_date']
    
    def __str__(self):
        return self.file_name
    
    def get_processing_time(self):
        """Return processing time in seconds"""
        if self.processing_start and self.processing_end:
            return (self.processing_end - self.processing_start).total_seconds()
        return None


class Category(models.Model):
    """Classification categories for classifieds"""
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    keywords = models.TextField(help_text="Comma-separated keywords for classification")
    
    class Meta:
        db_table = 'category'
        verbose_name_plural = 'Categories'
    
    def __str__(self):
        return self.name


class Location(models.Model):
    """Hyderabad locations for classified ads"""
    
    area_name = models.CharField(max_length=100, unique=True)
    district = models.CharField(max_length=100, default='Hyderabad')
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    
    class Meta:
        db_table = 'location'
    
    def __str__(self):
        return self.area_name


class ExtractedClassified(models.Model):
    """Store extracted classified advertisement data"""
    
    document = models.ForeignKey(DocumentUpload, on_delete=models.CASCADE, related_name='classifieds')
    title = models.CharField(max_length=500)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Contact Information
    contact_number = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    
    # Document Reference
    newspaper_date = models.DateField(null=True, blank=True)
    newspaper_name = models.CharField(max_length=255, default='Classified Document')
    page_number = models.IntegerField(null=True, blank=True)
    original_image_reference = models.CharField(max_length=500, blank=True)
    
    # Metadata
    extracted_date = models.DateTimeField(auto_now_add=True)
    confidence_score = models.FloatField(default=0.0, help_text="OCR confidence score 0-1")
    is_duplicate = models.BooleanField(default=False)
    duplicate_of = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL)
    
    class Meta:
        db_table = 'extracted_classified'
        ordering = ['-extracted_date']
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['category']),
            models.Index(fields=['location']),
            models.Index(fields=['newspaper_date']),
        ]
    
    def __str__(self):
        return self.title[:100]
    
    def get_short_description(self, length=100):
        return self.description[:length] + '...' if len(self.description) > length else self.description


class SearchLog(models.Model):
    """Track user searches for analytics"""
    
    search_query = models.CharField(max_length=500)
    search_filters = models.JSONField(default=dict, blank=True)
    results_count = models.IntegerField(default=0)
    timestamp = models.DateTimeField(auto_now_add=True)
    user_id = models.CharField(max_length=255, default='anonymous')
    
    class Meta:
        db_table = 'search_log'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.search_query} - {self.timestamp}"


class ProcessingLog(models.Model):
    """Track OCR and extraction processing details"""
    
    document = models.ForeignKey(DocumentUpload, on_delete=models.CASCADE)
    process_type = models.CharField(max_length=50)  # 'OCR', 'EXTRACTION', 'CLASSIFICATION'
    status = models.CharField(max_length=20)  # 'STARTED', 'COMPLETED', 'FAILED'
    details = models.JSONField(default=dict)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'processing_log'
    
    def __str__(self):
        return f"{self.document.file_name} - {self.process_type} - {self.status}"
