from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Count, Case, When, IntegerField

from main.core.models import SubmitLog
from main.core.utils import paginate
from main.core.tools import require_post_ajax


@login_required
def submit_logs_view(request):
    stats = SubmitLog.objects.aggregate(
        total_count=Count('id'),
        success_count=Count(Case(When(status="success", then=1), output_field=IntegerField())),
        fail_count=Count(Case(When(status="fail", then=1), output_field=IntegerField())),
        unknown_count=Count(Case(When(status="unknown", then=1), output_field=IntegerField())),
    )
    submit_logs = SubmitLog.objects.order_by("-created_at")

    submit_logs = paginate(submit_logs, per_page=25, page=request.GET.get("page"))
    return render(request, "web/content/submit_logs.html", context={
        "submit_logs": submit_logs,
        "stats": stats,
    })


@require_post_ajax
def submit_logs_view_manage(request):
    response = {}
    return JsonResponse(response)
