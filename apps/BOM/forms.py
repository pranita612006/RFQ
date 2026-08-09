from django import forms
from django.core.exceptions import ValidationError
from .permissions import can_user_edit_record, is_record_locked
from .models import BOMHeader, BOMTransaction

class LockableFormMixin:
    """
    Mixin for Django Forms/ModelForms that dynamically disables form controls
    when the underlying record is in a locked status ("Sent for approval", "Approved").
    Allows administrative / authorized users to override and edit.
    """
    user = None

    def __init__(self, *args, user=None, instance=None, **kwargs):
        self.user = user
        super().__init__(*args, instance=instance, **kwargs)
        
        # Resolve target instance
        target_instance = instance or getattr(self, 'instance', None)
        
        if target_instance and is_record_locked(target_instance):
            if not can_user_edit_record(self.user, target_instance):
                self.disable_all_fields()

    def disable_all_fields(self):
        """
        Dynamically sets disabled=True on all form widgets for frontend rendering
        and backend POST validation enforcement.
        """
        for field_name, field in self.fields.items():
            field.disabled = True
            field.widget.attrs['disabled'] = 'disabled'
            field.widget.attrs['readonly'] = 'readonly'
            field.widget.attrs['class'] = (field.widget.attrs.get('class', '') + ' bg-light text-muted locked-field').strip()

    def clean(self):
        cleaned_data = super().clean()
        target_instance = getattr(self, 'instance', None)
        if target_instance and is_record_locked(target_instance):
            if not can_user_edit_record(self.user, target_instance):
                raise ValidationError("This record is locked ('Sent for approval' / 'Approved'). Form updates are disabled.")
        return cleaned_data


class BOMHeaderForm(LockableFormMixin, forms.ModelForm):
    """
    Form representation for BOMHeader with built-in dynamic locking safeguards.
    """
    class Meta:
        model = BOMHeader
        fields = [
            'customer_id', 
            'item_creation_id', 
            'description', 
            'description_2', 
            'search_name', 
            'uom_code', 
            'low_level_code', 
            'version_number', 
            'series', 
            'remark'
        ]
        widgets = {
            'customer_id': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'item_creation_id': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'description': forms.Textarea(attrs={'class': 'form-control form-control-sm', 'rows': 2}),
            'description_2': forms.Textarea(attrs={'class': 'form-control form-control-sm', 'rows': 2}),
            'search_name': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'uom_code': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'low_level_code': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'version_number': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'series': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'remark': forms.Textarea(attrs={'class': 'form-control form-control-sm', 'rows': 2}),
        }
