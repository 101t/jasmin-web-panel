from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import JsonResponse

from main.core.models import SubmitLog
from main.core.utils import paginate
from main.core.tools import require_ajax


@login_required
def submit_logs_view(request):
    collection_list = SubmitLog.objects.all().order_by("-created_at")
    collection_list = paginate(collection_list, per_page=25, page=request.GET.get("page"))
    return render(request, "web/content/submit_logs.html", dict(collection_list=collection_list))


@require_ajax
def submit_logs_view_manage(request):
    response = {}
    return JsonResponse(response)
