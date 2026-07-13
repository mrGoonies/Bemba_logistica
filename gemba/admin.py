from django.contrib import admin

from .models import Answer, Area, Question, Walk


@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "order")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("order",)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("text", "area", "order", "is_active")
    list_editable = ("order", "is_active")
    list_filter = ("area", "is_active")
    search_fields = ("text", "criterio")
    ordering = ("area__order", "order")


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 0
    readonly_fields = ("question", "status", "comment", "photo", "created_at", "updated_at")
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Walk)
class WalkAdmin(admin.ModelAdmin):
    list_display = ("area", "date", "operator", "status", "completed_at")
    list_filter = ("area", "status")
    date_hierarchy = "date"
    readonly_fields = ("created_at", "completed_at")
    inlines = [AnswerInline]


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ("walk", "question", "status", "created_at")
    list_filter = ("status", "walk__area")
    readonly_fields = ("walk", "question", "status", "comment", "photo", "created_at", "updated_at")

    def has_add_permission(self, request):
        return False
