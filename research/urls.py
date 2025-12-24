from django.urls import path
from .views import *
urlpatterns = [
    path("research/", start_research_view, name="start-research"),
    path("research/<int:research_id>/continue/", continue_research_view, name="continue-research"),
    path("research/history/", researchhistoryview, name="research-history"),
    path("research/<int:research_id>/", researchdetailview, name="research-detail"),
]
