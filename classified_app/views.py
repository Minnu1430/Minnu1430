"""
Django Views and API Endpoints for ClassiFind AI
"""

import logging
import os
from datetime import datetime, timedelta
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.db.models import Q, Count
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from .models import (
    DocumentUpload, ExtractedClassified, Category,
    Location, SearchLog, ProcessingLog
)
from .serializers import (
    DocumentUploadSerializer, ExtractedClassifiedSerializer,
    ExtractedClassifiedDetailSerializer, CategorySerializer,
    LocationSerializer, SearchLogSerializer, DashboardStatsSerializer
)
from .ocr_engine import ocr_engine
from .nlp_engine import nlp_engine

logger = logging.getLogger(__name__)


class DocumentUploadViewSet(viewsets.ModelViewSet):
    """ViewSet for document uploads"""
    
    queryset = DocumentUpload.objects.all()
    serializer_class = DocumentUploadSerializer
    parser_classes = (MultiPartParser, FormParser)
    
    def create(self, request, *args, **kwargs):
        """Handle document upload"""
        try:
            file_obj = request.FILES.get('file')
            if not file_obj:
                return Response(
                    {'error': 'No file provided'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create DocumentUpload record
            doc = DocumentUpload.objects.create(
                file_name=file_obj.name,
                file_path=file_obj,
                file_size=file_obj.size,
                uploaded_by=request.user.username if request.user.is_authenticated else 'admin',
                status='uploaded'
            )
            
            logger.info(f"Document uploaded: {doc.file_name} (ID: {doc.id})")
            
            # Trigger processing
            self.process_document(doc)
            
            serializer = self.get_serializer(doc)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            logger.error(f"Upload error: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def process_document(self, doc):
        """Process uploaded document for OCR and extraction"""
        try:
            doc.status = 'processing'
            doc.processing_start = datetime.now()
            doc.save()
            
            logger.info(f"Starting processing for document: {doc.file_name}")
            
            # Determine file type and process
            file_ext = os.path.splitext(doc.file_path.name)[1].lower()
            
            if file_ext == '.pdf':
                result = ocr_engine.process_pdf(doc.file_path.path)
                pages_data = result.get('pages', [])
                doc.total_pages = result.get('total_pages', 1)
            else:
                result = ocr_engine.process_image(doc.file_path.path)
                pages_data = [result] if result.get('status') == 'success' else []
                doc.total_pages = 1
            
            # Extract classifieds from each page
            for page_data in pages_data:
                self.extract_classifieds_from_page(doc, page_data)
            
            doc.status = 'completed'
            doc.processing_end = datetime.now()
            doc.save()
            
            logger.info(f"Document processing completed: {doc.file_name}")
        
        except Exception as e:
            logger.error(f"Processing error for document {doc.id}: {str(e)}")
            doc.status = 'failed'
            doc.error_message = str(e)
            doc.processing_end = datetime.now()
            doc.save()
    
    def extract_classifieds_from_page(self, doc, page_data):
        """Extract classifieds from OCR'd page text"""
        try:
            text = page_data.get('text', '')
            if not text or len(text.strip()) < 20:
                return
            
            # Split text into potential classified ads (by double newlines)
            ads = [ad.strip() for ad in text.split('\n\n') if ad.strip()]
            
            for ad_text in ads:
                # Use NLP to extract information
                extracted = nlp_engine.extract_all(ad_text)
                
                # Get or create category
                category = None
                if extracted.get('category'):
                    category, _ = Category.objects.get_or_create(
                        name=extracted['category'],
                        defaults={'description': f'Auto-classified: {extracted["category"]}'}
                    )
                
                # Get or create location
                location = None
                if extracted.get('location'):
                    location, _ = Location.objects.get_or_create(
                        area_name=extracted['location'],
                        defaults={'district': 'Hyderabad'}
                    )
                
                # Check for duplicates
                is_duplicate = False
                duplicate_of = None
                existing = ExtractedClassified.objects.filter(
                    title__iexact=extracted['title']
                ).first()
                
                if existing:
                    is_duplicate = True
                    duplicate_of = existing
                
                # Create ExtractedClassified
                contact_info = extracted.get('contact_info', {})
                phone = contact_info.get('phone_numbers', [''])[0] if contact_info.get('phone_numbers') else None
                email = contact_info.get('emails', [''])[0] if contact_info.get('emails') else None
                
                classified = ExtractedClassified.objects.create(
                    document=doc,
                    title=extracted['title'][:500],
                    description=extracted['description'],
                    category=category,
                    location=location,
                    contact_number=phone,
                    email=email,
                    newspaper_date=datetime.strptime(extracted['date'], '%d-%m-%Y').date() if extracted.get('date') else None,
                    newspaper_name=doc.file_name,
                    page_number=page_data.get('page_number', 1),
                    confidence_score=page_data.get('confidence', 0.0),
                    is_duplicate=is_duplicate,
                    duplicate_of=duplicate_of
                )
                
                logger.info(f"Created classified ad: {classified.title} (ID: {classified.id})")
        
        except Exception as e:
            logger.error(f"Extraction error for page: {str(e)}")
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get document upload statistics"""
        stats = {
            'total_documents': DocumentUpload.objects.count(),
            'documents_by_status': dict(
                DocumentUpload.objects.values('status').annotate(count=Count('id')).values_list('status', 'count')
            ),
            'total_pages_processed': sum(d.total_pages for d in DocumentUpload.objects.filter(status='completed')),
            'average_processing_time': self._calculate_avg_processing_time(),
        }
        return Response(stats)
    
    def _calculate_avg_processing_time(self):
        """Calculate average processing time in seconds"""
        docs = DocumentUpload.objects.filter(
            status='completed',
            processing_start__isnull=False,
            processing_end__isnull=False
        )
        
        if not docs:
            return 0
        
        total_time = sum((d.get_processing_time() or 0) for d in docs)
        return round(total_time / docs.count(), 2)


class ExtractedClassifiedViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for extracted classifieds"""
    
    queryset = ExtractedClassified.objects.select_related('document', 'category', 'location')
    serializer_class = ExtractedClassifiedSerializer
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ExtractedClassifiedDetailSerializer
        return ExtractedClassifiedSerializer
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Search classifieds with filters"""
        queryset = self.get_queryset()
        
        # Get search parameters
        query = request.query_params.get('q', '').strip()
        category = request.query_params.get('category', '').strip()
        location = request.query_params.get('location', '').strip()
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        
        # Apply filters
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(contact_number__icontains=query)
            )
            
            # Log search
            SearchLog.objects.create(
                search_query=query,
                results_count=queryset.count(),
                user_id=request.user.username if request.user.is_authenticated else 'anonymous'
            )
        
        if category:
            queryset = queryset.filter(category__name__iexact=category)
        
        if location:
            queryset = queryset.filter(location__area_name__iexact=location)
        
        if date_from:
            queryset = queryset.filter(newspaper_date__gte=date_from)
        
        if date_to:
            queryset = queryset.filter(newspaper_date__lte=date_to)
        
        # Exclude duplicates by default
        queryset = queryset.filter(is_duplicate=False)
        
        # Pagination
        page = request.query_params.get('page', 1)
        page_size = 20
        start = (int(page) - 1) * page_size
        end = start + page_size
        
        total_count = queryset.count()
        queryset = queryset.order_by('-newspaper_date')[start:end]
        
        serializer = self.get_serializer(queryset, many=True)
        
        return Response({
            'count': total_count,
            'page': page,
            'page_size': page_size,
            'results': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """Get classifieds grouped by category"""
        category_name = request.query_params.get('category')
        
        if category_name:
            queryset = self.get_queryset().filter(category__name__iexact=category_name)
        else:
            queryset = self.get_queryset()
        
        queryset = queryset.filter(is_duplicate=False)
        serializer = self.get_serializer(queryset, many=True)
        
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_location(self, request):
        """Get classifieds grouped by location"""
        location_name = request.query_params.get('location')
        
        if location_name:
            queryset = self.get_queryset().filter(location__area_name__iexact=location_name)
        else:
            queryset = self.get_queryset()
        
        queryset = queryset.filter(is_duplicate=False)
        serializer = self.get_serializer(queryset, many=True)
        
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get classified advertisements statistics"""
        queryset = self.get_queryset().filter(is_duplicate=False)
        
        stats = {
            'total_classifieds': queryset.count(),
            'by_category': list(
                queryset.values('category__name').annotate(count=Count('id'))
            ),
            'by_location': list(
                queryset.values('location__area_name').annotate(count=Count('id'))
            ),
            'average_confidence': queryset.aggregate(
                avg_confidence=__import__('django.db.models', fromlist=['Avg'])['Avg']('confidence_score')
            )['avg_confidence'] or 0,
            'recent_additions': list(
                queryset.order_by('-extracted_date')[:5].values('id', 'title', 'category__name', 'extracted_date')
            ),
        }
        
        return Response(stats)


class DashboardView:
    """Dashboard statistics view"""
    
    @staticmethod
    def get_dashboard_stats():
        """Compile all dashboard statistics"""
        documents = DocumentUpload.objects.all()
        classifieds = ExtractedClassified.objects.filter(is_duplicate=False)
        
        return {
            'total_documents': documents.count(),
            'total_classifieds': classifieds.count(),
            'documents_by_status': dict(
                documents.values('status').annotate(count=Count('id')).values_list('status', 'count')
            ),
            'classifieds_by_category': dict(
                classifieds.values('category__name').annotate(count=Count('id')).values_list('category__name', 'count')
            ),
            'classifieds_by_location': dict(
                classifieds.values('location__area_name').annotate(count=Count('id')).values_list('location__area_name', 'count')
            ),
            'recent_uploads': DocumentUploadSerializer(
                documents.order_by('-upload_date')[:5],
                many=True
            ).data,
            'recent_classifieds': ExtractedClassifiedSerializer(
                classifieds.order_by('-extracted_date')[:5],
                many=True
            ).data,
            'average_confidence': classifieds.aggregate(
                avg=__import__('django.db.models', fromlist=['Avg'])['Avg']('confidence_score')
            )['avg'] or 0,
            'total_searches': SearchLog.objects.count(),
        }


def dashboard(request):
    """Render dashboard HTML"""
    stats = DashboardView.get_dashboard_stats()
    return render(request, 'dashboard.html', stats)


def api_dashboard_stats(request):
    """API endpoint for dashboard stats"""
    stats = DashboardView.get_dashboard_stats()
    return JsonResponse(stats)
