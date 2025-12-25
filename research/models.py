from django.db import models
from django.contrib.auth.models import User

class ResearchSession(models.Model):
    STATUS_CHOICES = [
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    query = models.TextField()
    parent_session = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='child_sessions'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='running')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    trace_id = models.CharField(max_length=255, blank=True, null=True)
    def __str__(self):
        return self.query[:50]

class ResearchSummary(models.Model):
    session = models.OneToOneField(ResearchSession, on_delete=models.CASCADE)
    summary = models.TextField()   

class ResearchReasoning(models.Model):
    session = models.OneToOneField(ResearchSession, on_delete=models.CASCADE)
    reasoning_json = models.JSONField()
    sources_json = models.JSONField()

class LLM(models.Model):
    session = models.ForeignKey(ResearchSession, on_delete=models.CASCADE, related_name='llm_records')
    parent_session = models.ForeignKey(
        ResearchSession, on_delete=models.CASCADE, related_name='child_llm_records'
    )
    query = models.TextField()
    gptresponse = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

class UploadedDocument(models.Model):
    session = models.ForeignKey(
        ResearchSession,
        on_delete=models.CASCADE,
        related_name='documents'
    )
    file = models.FileField(upload_to='research_docs/')
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.file.name}"
class ResearchCost(models.Model):
    session = models.ForeignKey(ResearchSession, on_delete=models.CASCADE)
    input_tokens = models.IntegerField(default=0)
    output_tokens = models.IntegerField(default=0)
    total_cost = models.FloatField(default=0.0)

    

