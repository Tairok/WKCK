from pathlib import Path

from django.conf import settings
from django.http import FileResponse, HttpResponse

SPA_INDEX = Path(settings.BASE_DIR) / "frontend_dist" / "index.html"


def spa_shell(request):
    if not SPA_INDEX.exists():
        return HttpResponse(
            "Frontend is not built. Run `npm run build` in the frontend folder.",
            status=503,
            content_type="text/plain; charset=utf-8",
        )
    return FileResponse(SPA_INDEX.open("rb"), content_type="text/html; charset=utf-8")
