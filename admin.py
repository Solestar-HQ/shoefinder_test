from django.contrib import admin
from .models import(
    UserProfile,
    Foot, 
    Brand, 
    Model, 
    Size, 
    ColorOption, 
    MaterialType, 
    ClosureSystem, 
    Shoe, 
    ShoeImage,
    BulkImport,
    AffiliateSite,
    AffiliateLink
)
from .forms import (
    BulkInput,
    ShoeImageForm,
    ShoeForm
)
from dal import autocomplete

class ShoeColorAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = ColorOption.objects.all()
        
        print(f"QUERY: ", self.q)
        
        return qs


class BulkAdmin(admin.ModelAdmin):
    list_display = ('file',)
    form = BulkInput
  
  
class ModelAdmin(admin.ModelAdmin):
    list_display = (
        'brand',
        'name'
    )
    list_filter = (
        'brand',
    )
    
    
class ShoeImageAdmin(admin.ModelAdmin):
    form = ShoeImageForm
    list_display = (
        'brand',
        'model',
        'color',
        'angle',
        'image'
    )
  

class ShoeAdmin(admin.ModelAdmin):
    form = ShoeForm
    list_display = (
        'brand',
        'model',
        'size',
        'length',
        'width',
        'min_foot_length',
        'max_foot_length',
        'min_foot_width',
        'max_foot_width',
        'circumference',
        'weight',
        'material_thickness_inner',
        'material_thickness_outer',
        'added',
        'added_by',
        'remeasure',
    )
    list_filter = (
        'model__brand',
        'model',
        'added',
        'added_by',
        'remeasure',
    )
    
    class Media: 
        css = {
            'all': ('css/admin')
        }
    
    def brand(self, obj):
        return obj.model.brand

  
admin.site.register(UserProfile)
admin.site.register(BulkImport, BulkAdmin)
admin.site.register(Foot)
admin.site.register(Brand)
admin.site.register(Model, ModelAdmin)
admin.site.register(Size)
admin.site.register(ColorOption)
admin.site.register(MaterialType)
admin.site.register(ClosureSystem)
admin.site.register(Shoe, ShoeAdmin)
admin.site.register(ShoeImage, ShoeImageAdmin)
admin.site.register(AffiliateSite)
admin.site.register(AffiliateLink)
