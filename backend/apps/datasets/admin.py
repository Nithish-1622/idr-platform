from django.contrib import admin

from .models import Dataset, DatasetVersion


class DatasetVersionInline(admin.TabularInline):
    model = DatasetVersion
    extra = 0
    readonly_fields = ("checksum_sha256", "file_size_bytes", "uploaded_at")


@admin.register(Dataset)
class DatasetAdmin(admin.ModelAdmin):
    list_display = ("name", "source", "created_at")
    search_fields = ("name", "source", "description")
    inlines = [DatasetVersionInline]
