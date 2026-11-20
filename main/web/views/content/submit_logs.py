from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.db import connection
from django.db.models import Count, Case, When, F, Func, IntegerField, Q, TextField, Value
from django.core.cache import cache
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from datetime import datetime

from main.core.models import SubmitLog
from main.core.utils import paginate
from main.core.tools import require_post_ajax, staff_required
from main.core.tasks.export_submit_logs import export_submit_logs_task

# The query string names the date field to filter on; only these two may reach the ORM.
DATE_COLUMNS = ('created_at', 'status_at')
EXPORT_FORMATS = ('csv', 'xlsx')


def _date_column(value):
    return value if value in DATE_COLUMNS else 'created_at'


def _make_aware_if_needed(dt):
    if timezone.is_naive(dt):
        return timezone.make_aware(dt, timezone.get_current_timezone())
    return dt


def apply_submit_log_search(queryset, search_query):
    """Search SubmitLog safely across SQLite, MySQL, and PostgreSQL (where short_message is BYTEA)."""
    base_q = (
        Q(msgid__icontains=search_query) |
        Q(source_addr__icontains=search_query) |
        Q(destination_addr__icontains=search_query) |
        Q(uid__icontains=search_query)
    )
    if connection.vendor == 'postgresql':
        return queryset.annotate(
            short_message_text=Func(
                F('short_message'),
                Value('escape'),
                function='encode',
                output_field=TextField(),
            )
        ).filter(base_q | Q(short_message_text__icontains=search_query))
    return queryset.filter(base_q | Q(short_message__icontains=search_query))


@staff_required
def submit_logs_view(request):
    # Get search and filter parameters
    search_query = request.GET.get('search', '').strip()
    status_filter = request.GET.get('status_filter', '')
    date_column = _date_column(request.GET.get('date_column', 'created_at'))
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()

    # Start with all logs
    submit_logs = SubmitLog.objects.all()

    # Apply date range filter
    if date_column and date_from:
        try:
            date_from_obj = _make_aware_if_needed(datetime.strptime(date_from, '%Y-%m-%d'))
            submit_logs = submit_logs.filter(**{f'{date_column}__gte': date_from_obj})
        except ValueError:
            pass  # Invalid date format, skip filter

    if date_column and date_to:
        try:
            date_to_obj = _make_aware_if_needed(
                datetime.strptime(date_to, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
            )
            submit_logs = submit_logs.filter(**{f'{date_column}__lte': date_to_obj})
        except ValueError:
            pass  # Invalid date format, skip filter

    # Apply search filter
    if search_query:
        submit_logs = apply_submit_log_search(submit_logs, search_query)

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


@staff_required
@require_http_methods(["POST"])
def submit_logs_export(request):
    """Initiate async export of submit logs."""
    export_format = request.POST.get('format', 'csv').lower()
    if export_format not in EXPORT_FORMATS:
        return JsonResponse({'status': 'error', 'message': 'Invalid export format.'}, status=400)

    # Get current filters from request
    filters = {
        'search': request.POST.get('search', '').strip(),
        'status_filter': request.POST.get('status_filter', ''),
        'date_column': _date_column(request.POST.get('date_column', 'created_at')),
        'date_from': request.POST.get('date_from', '').strip(),
        'date_to': request.POST.get('date_to', '').strip(),
    }

    # Convert dates to timezone-aware ISO format for task
    if filters['date_from']:
        try:
            date_obj = _make_aware_if_needed(datetime.strptime(filters['date_from'], '%Y-%m-%d'))
            filters['date_from'] = date_obj.isoformat()
        except ValueError:
            filters['date_from'] = ''

    if filters['date_to']:
        try:
            date_obj = _make_aware_if_needed(
                datetime.strptime(filters['date_to'], '%Y-%m-%d').replace(hour=23, minute=59, second=59)
            )
            filters['date_to'] = date_obj.isoformat()
        except ValueError:
            filters['date_to'] = ''

    # Start async task bound to the requesting user
    task = export_submit_logs_task.delay(filters, export_format, owner_id=request.user.id)
    cache.set(f'export_owner_{task.id}', request.user.id, 600)

    return JsonResponse({
        'status': 'started',
        'task_id': task.id,
        'message': 'Export started. Please wait...'
    })


def _is_export_owner(request, task_id, payload=None):
    owner_id = (payload or {}).get('owner_id')
    if owner_id is None:
        owner_id = cache.get(f'export_owner_{task_id}')
    return owner_id is not None and owner_id == request.user.id


@staff_required
@require_http_methods(["GET"])
def submit_logs_export_progress(request, task_id):
    """Check the progress of an export task."""
    progress_data = cache.get(f'export_progress_{task_id}')

    if not progress_data:
        return JsonResponse({
            'status': 'not_found',
            'message': 'Task not found or expired'
        })

    if not _is_export_owner(request, task_id, progress_data):
        return JsonResponse({'status': 'forbidden', 'message': 'Access denied'}, status=403)

    safe_progress = {k: v for k, v in progress_data.items() if k != 'owner_id'}
    return JsonResponse(safe_progress)


@staff_required
@require_http_methods(["GET"])
def submit_logs_export_download(request, task_id):
    """Download the exported file."""
    file_data = cache.get(f'export_file_{task_id}')

    if not file_data:
        return HttpResponse('File not found or expired', status=404)

    if not _is_export_owner(request, task_id, file_data):
        return HttpResponse('Forbidden', status=403)

    safe_filename = ''.join(c for c in file_data['filename'] if c.isalnum() or c in ('_', '-', '.'))
    response = HttpResponse(
        file_data['content'],
        content_type=file_data['content_type']
    )
    response['Content-Disposition'] = f'attachment; filename="{safe_filename}"'

    # Clean up cache after download
    cache.delete(f'export_file_{task_id}')
    cache.delete(f'export_progress_{task_id}')
    cache.delete(f'export_owner_{task_id}')

    return response
