from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Count, Case, When, IntegerField, Q

from main.core.models import SubmitLog
from main.core.utils import paginate
from main.core.tools import require_post_ajax


@login_required
def submit_logs_view(request):
    # Get search and filter parameters
    search_query = request.GET.get('search', '').strip()
    status_filter = request.GET.get('status_filter', '')
    
    # Start with all logs
    submit_logs = SubmitLog.objects.all()
    
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
    })


@require_post_ajax
def submit_logs_view_manage(request):
    response = {}
    return JsonResponse(response)
