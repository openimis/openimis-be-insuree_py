from django.contrib import admin

from .models import (
    ConfirmationType,
    Education,
    FamilyType,
    Gender,
    IdentificationType,
    InsureeStatusReason,
    Profession,
    Relation,
)


@admin.register(Gender)
class GenderAdmin(admin.ModelAdmin):
    list_display = ["code", "gender", "sort_order", "alt_language"]
    list_display_links = ["code", "gender"]
    list_editable = ["sort_order"]
    search_fields = ["code", "gender", "alt_language"]
    ordering = ["sort_order", "code"]
    fields = ["code", "gender", "sort_order", "alt_language"]

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ["code"]
        return []


@admin.register(IdentificationType)
class IdentificationTypeAdmin(admin.ModelAdmin):
    list_display = ["code", "identification_type",
                    "sort_order", "alt_language"]
    list_display_links = ["code", "identification_type"]
    list_editable = ["sort_order"]
    search_fields = ["code", "identification_type", "alt_language"]
    ordering = ["sort_order", "code"]
    fields = ["code", "identification_type", "sort_order", "alt_language"]

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ["code"]
        return []


@admin.register(FamilyType)
class FamilyTypeAdmin(admin.ModelAdmin):
    list_display = ["code", "type", "sort_order", "alt_language"]
    list_display_links = ["code", "type"]
    list_editable = ["sort_order"]
    search_fields = ["code", "type", "alt_language"]
    ordering = ["sort_order", "code"]
    fields = ["code", "type", "sort_order", "alt_language"]

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ["code"]
        return []


@admin.register(ConfirmationType)
class ConfirmationTypeAdmin(admin.ModelAdmin):
    list_display = [
        "code",
        "confirmationtype",
        "sort_order",
        "is_confirmation_number_required",
        "alt_language",
    ]
    list_display_links = ["code", "confirmationtype"]
    list_editable = ["sort_order", "is_confirmation_number_required"]
    search_fields = ["code", "confirmationtype", "alt_language"]
    ordering = ["sort_order", "code"]
    fields = [
        "code",
        "confirmationtype",
        "sort_order",
        "is_confirmation_number_required",
        "alt_language",
    ]

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ["code"]
        return []


@admin.register(Profession)
class ProfessionAdmin(admin.ModelAdmin):
    list_display = ["id", "profession", "sort_order", "alt_language"]
    list_display_links = ["id", "profession"]
    list_editable = ["sort_order"]
    search_fields = ["id", "profession", "alt_language"]
    ordering = ["sort_order", "id"]
    fields = ["id", "profession", "sort_order", "alt_language"]

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ["id"]
        return []


@admin.register(Education)
class EducationAdmin(admin.ModelAdmin):
    list_display = ["id", "education", "sort_order", "alt_language"]
    list_display_links = ["id", "education"]
    list_editable = ["sort_order"]
    search_fields = ["id", "education", "alt_language"]
    ordering = ["sort_order", "id"]
    fields = ["id", "education", "sort_order", "alt_language"]

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ["id"]
        return []


@admin.register(Relation)
class RelationAdmin(admin.ModelAdmin):
    list_display = ["id", "relation", "sort_order", "alt_language"]
    list_display_links = ["id", "relation"]
    list_editable = ["sort_order"]
    search_fields = ["id", "relation", "alt_language"]
    ordering = ["sort_order", "id"]
    fields = ["id", "relation", "sort_order", "alt_language"]

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ["id"]
        return []


@admin.register(InsureeStatusReason)
class InsureeStatusReasonAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "code",
        "insuree_status_reason",
        "status_type",
        "validity_from",
        "validity_to",
    ]
    list_display_links = ["id", "code", "insuree_status_reason"]
    search_fields = ["id", "code", "insuree_status_reason"]
    list_filter = ["status_type", ("validity_to", admin.EmptyFieldListFilter)]
    ordering = ["code", "id"]
    fields = [
        "id",
        "code",
        "insuree_status_reason",
        "status_type",
        "validity_from",
        "validity_to",
    ]

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ["id"]
        return []
