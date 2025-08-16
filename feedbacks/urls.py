from django.urls import path
from .views import FeedbackCreateView, FeedbackListView

urlpatterns = [
    path('feedbacks/', FeedbackListView.as_view(), name='feedback-list'),  # GET by manager (with optional ?coffee_shop_id=)
    path('feedbacks/create/', FeedbackCreateView.as_view(), name='feedback-create'),  # POST by client
]
