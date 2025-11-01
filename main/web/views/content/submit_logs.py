from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.db.models import Count, Case, When, IntegerField, Q
from django.core.cache import cache
from django.views.decorators.http import require_http_methods
from datetime import datetime

from main.core.models import SubmitLog
from main.core.utils import paginate
from main.core.tools import require_post_ajax
from main.core.tasks.export_submit_logs import export_submit_logs_task


@login_required
def submit_logs_view(request):
    # Get search and filter parameters
    search_query = request.GET.get('search', '').strip()
    status_filter = request.GET.get('status_filter', '')
    date_column = request.GET.get('date_column', 'created_at')  # 'created_at' or 'status_at'
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()
    
    # Start with all logs
    submit_logs = SubmitLog.objects.all()
    
    # Apply date range filter
    if date_column and date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            submit_logs = submit_logs.filter(**{f'{date_column}__gte': date_from_obj})
        except ValueError:
            pass  # Invalid date format, skip filter
    
    if date_column and date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
            # Add 23:59:59 to include the entire day
            date_to_obj = date_to_obj.replace(hour=23, minute=59, second=59)
            submit_logs = submit_logs.filter(**{f'{date_column}__lte': date_to_obj})
        except ValueError:
            pass  # Invalid date format, skip filter
    
    # Apply search filter
    if search_query:
        submit_logs = submit_logs.filter(
            Q(msgid__icontains=search_query) |
            Q(source_addr__icontains=search_query) |
            Q(destination_addr__icontains=search_query) |
            Q(short_message__icontains=search_query) |
            Q(uid__icontains=search_query)
        )
    
    # Apply status filter
    if status_filter == 'success':
        submit_logs = submit_logs.filter(status__in=['ESME_ROK', 'ESME_RINVNUMDESTS'])
    elif status_filter == 'fail':
        submit_logs = submit_logs.filter(status='ESME_RDELIVERYFAILURE')
    elif status_filter == 'unknown':
        submit_logs = submit_logs.exclude(status__in=['ESME_ROK', 'ESME_RINVNUMDESTS', 'ESME_RDELIVERYFAILURE'])
    
    # Calculate statistics (on all logs, not filtered)
    all_logs = SubmitLog.objects.all()
    stats = all_logs.aggregate(
        total_count=Count('id'),
        success_count=Count(Case(
            When(status__in=['ESME_ROK', 'ESME_RINVNUMDESTS'], then=1),
            output_field=IntegerField()
        )),
        fail_count=Count(Case(
            When(status='ESME_RDELIVERYFAILURE', then=1),
            output_field=IntegerField()
        )),
    )
    # Calculate unknown count (all - success - fail)
    stats['unknown_count'] = stats['total_count'] - stats['success_count'] - stats['fail_count']
    
    # Order and paginate
    submit_logs = submit_logs.order_by("-created_at")
    submit_logs = paginate(submit_logs, per_page=25, page=request.GET.get("page"))
    
    return render(request, "web/content/submit_logs.html", context={
        "submit_logs": submit_logs,
        "stats": stats,
        "search_query": search_query,
        "status_filter": status_filter,
        "date_column": date_column,
        "date_from": date_from,
        "date_to": date_to,
    })


@require_post_ajax
def submit_logs_view_manage(request):
    response = {}
    return JsonResponse(response)


@login_required
@require_http_methods(["POST"])
def submit_logs_export(request):
    """Initiate async export of submit logs."""
    export_format = request.POST.get('format', 'csv')  # 'csv' or 'xlsx'
    
    # Get current filters from request
    filters = {
        'search': request.POST.get('search', '').strip(),
        'status_filter': request.POST.get('status_filter', ''),
        'date_column': request.POST.get('date_column', 'created_at'),
        'date_from': request.POST.get('date_from', '').strip(),
        'date_to': request.POST.get('date_to', '').strip(),
    }
    
    # Convert dates to ISO format for task
    if filters['date_from']:
        try:
            date_obj = datetime.strptime(filters['date_from'], '%Y-%m-%d')
            filters['date_from'] = date_obj.isoformat()
        except ValueError:
            filters['date_from'] = ''
    
    if filters['date_to']:
        try:
            date_obj = datetime.strptime(filters['date_to'], '%Y-%m-%d')
            date_obj = date_obj.replace(hour=23, minute=59, second=59)
            filters['date_to'] = date_obj.isoformat()
        except ValueError:
            filters['date_to'] = ''
    
    # Start async task
    task = export_submit_logs_task.delay(filters, export_format)
    
    return JsonResponse({
        'status': 'started',
        'task_id': task.id,
        'message': 'Export started. Please wait...'
    })


@login_required
@require_http_methods(["GET"])
def submit_logs_export_progress(request, task_id):
    """Check the progress of an export task."""
    progress_data = cache.get(f'export_progress_{task_id}')
    
    if not progress_data:
        return JsonResponse({
            'status': 'not_found',
            'message': 'Task not found or expired'
        })
    
    return JsonResponse(progress_data)


@login_required
@require_http_methods(["GET"])
def submit_logs_export_download(request, task_id):
    """Download the exported file."""
    file_data = cache.get(f'export_file_{task_id}')
    
    if not file_data:
        return HttpResponse('File not found or expired', status=404)
    
    response = HttpResponse(
        file_data['content'],
        content_type=file_data['content_type']
    )
    response['Content-Disposition'] = f'attachment; filename="{file_data["filename"]}"'
    
    # Clean up cache after download
    cache.delete(f'export_file_{task_id}')
    cache.delete(f'export_progress_{task_id}')
    
    return response
