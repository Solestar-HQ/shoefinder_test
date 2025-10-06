from django.db import (
    models
)
from django.contrib.auth.models import (
    User,
    AbstractUser
)
from django.utils.translation import (
    gettext_lazy as _
)
from PIL import (
    Image
)

import os, json, math
from django.conf import (
    settings
)
from django.core.files.storage import FileSystemStorage


ANGLE_CHOCIES = (
    ('1', 'front'),
    ('2', 'macro'),
    ('3', 'degree45'),
    ('4', 'back'),
    ('5', 'top'),
    ('6', 'macro')
)


class UserProfile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    subscribed = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.user}'


class ColorOption(models.Model):
    name = models.CharField(max_length=64)

    def __str__(self):
        return self.name

    def formatted(self):
        return '_'.join(self.name.split(' '))

    def to_lower(self):
        return self.name.lower()


class MaterialType(models.Model):
    name = models.CharField(max_length=64)

    def __str__(self):
        return str(self.name)

    class Meta:
        ordering = ['name']


class ClosureSystem(models.Model):
    name = models.CharField(max_length=64)

    def __str__(self):
        return str(self.name)

    class Meta:
        ordering = ['name']


class Size(models.Model):
    number =  models.DecimalField(max_digits=3, decimal_places=1)

    def __str__(self):
        return str(self.number)

    class Meta:
        ordering = ['number']


class Brand(models.Model):
    name = models.CharField(max_length=64)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class AffiliateSite(models.Model):
    name = models.CharField(max_length=128)
    logo = models.FileField(upload_to='logos/')


class AffiliateLink(models.Model):
    site = models.ForeignKey('AffiliateSite', on_delete=models.SET_NULL, null=True, blank=True)
    link = models.CharField(max_length=1024)



class Model(models.Model):
    brand = models.ForeignKey('Brand', on_delete=models.CASCADE)
    name = models.CharField(max_length=64, verbose_name='Model')
    colors = models.ManyToManyField('findyourshoe.ColorOption', related_name='color_options', blank=True)
    materials = models.ManyToManyField('findyourshoe.MaterialType', related_name='material_types', blank=True, verbose_name='Materials')
    closure_system = models.ManyToManyField('findyourshoe.ClosureSystem', related_name='closure_systems', blank=True)
    # affiliated = models.ForeignKey('AffiliateLink', on_delete=models.SET_NULL, null=True, blank=True)
    # prices = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    def __str__(self):
      return self.name

    def images(self):
        return ShoeImage.objects.get(brand=self.brand, model=self.name).values('image')

    def formatted(self):
        return '_'.join(self.name.split(' '))

    def target_id(self):
        return f'#{self.pk}-{self.name}-img'

    def image(self):
        color = self.colors.first()
        image = ShoeImage.objects.get(model=self.pk, color=color).image
        return image

    def generate_affiliate_link(self):
        return f'https://www.bike24.com/search-result?searchTerm={self.brand}+{self.name}'

    class Meta:
        ordering = ['brand__name']


def upload_to_and_rename(instance, filename):
    brand = '_'.join(instance.brand.name.split(' ')).lower()
    model = '_'.join(instance.model.name.split(' ')).lower()
    color = '_'.join(instance.color.name.split(' ')).lower()
    angle = instance.angle

    upload_to = f'shoes/{str(instance.brand).lower()}/'
    ext = filename.split('.')[-1]

    filename = f'{brand}_{model}_{color}_{angle}.png'
    return os.path.join(upload_to, filename)


class ShoeImage(models.Model):
    brand = models.ForeignKey('Brand', on_delete=models.SET_NULL, null=True)
    model = models.ForeignKey('Model', on_delete=models.SET_NULL, null=True)
    color = models.ForeignKey('ColorOption', on_delete=models.CASCADE)
    angle = models.CharField(max_length=32, choices=ANGLE_CHOCIES)
    image = models.ImageField(upload_to=upload_to_and_rename)

    def __str__(self):
        return str(self.model) + ' ' + str(self.color)

    def get_image_url(self):
        return str(self.image)

    def get_color(self):
        return str(self.color)


class Shoe(models.Model):
    model = models.ForeignKey('Model', on_delete=models.SET_NULL, null=True)
    size =  models.ForeignKey('Size', on_delete=models.SET_NULL, null=True)
    length = models.DecimalField(max_digits=3, decimal_places=1)
    width = models.DecimalField(max_digits=3, decimal_places=1)
    circumference = models.DecimalField(max_digits=3, decimal_places=1)
    min_foot_length = models.DecimalField(max_digits=4, decimal_places=1)
    max_foot_length = models.DecimalField(max_digits=4, decimal_places=1)
    min_foot_width = models.DecimalField(max_digits=4, decimal_places=1)
    max_foot_width = models.DecimalField(max_digits=4, decimal_places=1)
    weight = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    material_thickness_outer = models.DecimalField(max_digits=2, decimal_places=1, null=True, blank=True)
    material_thickness_inner = models.DecimalField(max_digits=2, decimal_places=1, null=True, blank=True)
    width_wt = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    added = models.DateTimeField(auto_now_add=True, verbose_name='Date Added')
    added_by = models.CharField(max_length=32, blank=True)
    remeasure = models.BooleanField(default=False, blank=True, verbose_name='Set to remeasured')
    active  = models.BooleanField(default=True, blank=True)

    def __str__(self):
        return f'{self.model.brand} | {self.model} | {self.size}'

    def calc_width_wt(self):
        if self.material_thickness_outer is not None and self.  material_thickness_inner is not None:
            self.width_wt = self.width - self.material_thickness_inner - self.material_thickness_outer

    def target_id(self):
        return f'{self.pk}-{self.model.name}-target'

    def save(self, *args, **kwargs):
        self.width_wt = self.width
        self.calc_width_wt()
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['model__name']


class FootManager(models.Manager):
    def matching_shoes(self, foot, filters=None, page=1):
        range_length = [1.5, 2.0]
        range_width = [0.3, 0.4]
        shoes = Shoe.objects.filter(
            active=True,
            length__range=(
                float(foot.length) - range_length[0],
                float(foot.length) + range_length[1]
            ),
            width_wt__range=(
                float(foot.width) - range_width[0],
                float(foot.width) + range_width[1]
            )
        )
        matching_shoes = list()
        for shoe in shoes:
             matching_shoes.append(shoe.as_json())
        return matching_shoes


class Foot(models.Model):
    session_id = models.CharField(max_length=32, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.SET(None), null=True, blank=True)
    length = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    width = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    circumference = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    # objects = models.Manager()
    # get = FootManager()

    def __str__(self):
        return f'{self.user}, {self.length}, {self.width}, {self.circumference}'

    def as_json(self):
        return dict(
            length=self.length,
            width=self.width,
            circumference=self.circumference
        )


class BulkImport(models.Model):
    file = models.FileField(storage=FileSystemStorage(settings.IMPORTS_DIR))

    def __str__(self):
        return f'self.file'

    def save(self, commit=False, *args, **kwargs):
        file = self.file
        reader = json.loads(file.read())
        for row in reader:
            if 'Brand' in row and row['Brand'] != 'null':
                print(
                    '''
                    Adding...
                    '''
                )
                print(f'Shoe: ', row)
                _brand, brand = Brand.objects.get_or_create(
                    name=row['Brand'],
                )
                _size, size = Size.objects.get_or_create(
                    number=float(row['Size']),
                 )
                _model, model = Model.objects.get_or_create(
                    brand=Brand.objects.get(name=row['Brand']),
                    name=row['Model'],
                )
                if 'Colors' in row and len(row['Colors']) > 0:
                    for color in row['Colors']:
                        _model.colors.add(
                            ColorOption.objects.get(name=color)
                        )
                if 'Material Types' in row and len(row['Material Types']) > 0:
                    for material_type in row['Material Types']:
                        _model.materials.add(
                            MaterialType.objects.get(name=material_type)
                        )
                if 'Closure System' in row and len(row['Closure System']) > 0:
                    for closure_system in row['Closure System']:
                        _model.closure_system.add(
                            ClosureSystem.objects.get(name=closure_system)
                        )
                _shoe, shoe = Shoe.objects.get_or_create(
                    # brand=Brand.objects.get(name=row['Brand']),
                    model=Model.objects.get(name=row['Model']),
                    size=Size.objects.get(number=row['Size']),
                    length=float(row['Length']),
                    width=float(row['Width']),
                    circumference=float(row['Circumference']),
                    min_foot_length=round(float(row['Min Foot Length']), 1),
                    max_foot_length=round(float(row['Max Foot Length']), 1),
                    min_foot_width=round(float(row['Min Foot Width']), 1),
                    max_foot_width=round(float(row['Max Foot Width']), 1),
                    weight=float(row['Weight']),
                    added_by='admin',
                )
        return super(BulkImport, self).save(*args, **kwargs)
