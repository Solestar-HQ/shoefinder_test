from django.shortcuts import (
    get_object_or_404,
    HttpResponse,
    HttpResponseRedirect,
    redirect,
    reverse,
    render
)
from django.contrib import (
    messages
)
from django.core.paginator import (
    Paginator
)
from django.contrib.auth.decorators import (
    login_required
)
from django.contrib.auth.models import (
    User
)
from .models import (
    Shoe,
    Brand,
    Model,
    ShoeImage,
    ColorOption,
    MaterialType,
    ClosureSystem,
    Foot,
    UserProfile
)
from .utils import (
    htmx,
    template,
    get_input_value,
    get_foot,
    get_matching_shoes,
    get_foot_session,
    save_foot
)
from .filters import (
    ShoeFilter
)
from dal import (
    autocomplete
)
from .forms import (
    FootForm,
    CustomSignupForm,
    CustomUserForm,
    DeleteUserForm,
    EmailChangeForm,
    RegisterForm
)
import enum


class Step(enum.Enum):
    length = 1
    width = 2
    circumference = 3
    summary = 4


def current(step):
    if step == 'circumference':
        return 'width'
    elif step == 'summary':
        return 'circumference'
    else:
        return 'length'


def next_step(step):
    if step == 'length':
        return 'width'
    elif step == 'width':
        return 'circumference'
    elif step == 'circumference':
        return 'summary'


def prev_step(step):
    if step == 'width':
        return 'length'
    elif step == 'circumference':
        return 'width'


def landing_page(request):
    html = './landing_page.html'
    title = 'Welcome to FindYourShoe'
    context = {'template': template(request), 'title': title}
    return render(request, html, context)


def shoe_finder(request, step='length'):
    html = './shoe_finder.html'
    title = 'Find your shoe'
    foot = None

    # if user is authenticated try loading the foot data from the DB
    try:
        '''
        if request.user.is_authenticated and 'foot' not in request.session:
            foot = Foot.objects.get(user=request.user)
        else:
            raise ValueError("User is not authenticated.")'''

        if request.user.is_authenticated and step == 'length':
            try:
                foot = Foot.objects.get(user=request.user)
                request.session['foot'] = {
                    'length': float(foot.length),
                    'width': float(foot.width),
                    'circumference': float(foot.circumference)
                }
                foot = request.session['foot']
            except:
                raise ValueError("User has no foot data stored.")
        else:
            raise ValueError("User is not authenticated.")
    except Exception as e:
        print(f"# Exception as e - shoe finder: ", e)
        # else try getting the foot data from the session
        if 'foot' in request.session:
            foot = request.session['foot']
        # and if the session doesn't exist, create it
        else:
            foot = request.session['foot'] = {
                'length': 0,
                'width': 0,
                'circumference': 0
            }

    # does not allow access to shoe finder's steps if the request doesn't come via HTMX.
    if request.method == 'POST':
        measurement = float(request.POST.get(current(step)))
        if measurement > 0 and measurement < 100:
            request.session['foot'][current(step)] = measurement
            request.session.modified = True
        else:
            messages.error(
                request,
                'You need to input the values before we can provide you with matching shoes.',
                extra_tags='shoe_finder'
            )
            return redirect(f'/shoe-finder/{prev_step(step)}')

    context = {
        'template': template(request),
        'title': title,
        'foot': foot,
        'step': step,
        'step_html': f'steps/step_{step}.html',
        'step_n': Step[step].value,
        'prev_step': prev_step(step),
        'next_step': next_step(step),
        'input_value': get_input_value(foot, step)
    }

    return render(request, html, context)


def summary(request):
    html = 'summary.html'
    title = 'Summary'

    if request.method == 'POST':
        measurement = float(request.POST.get('circumference'))
        if measurement > 0 and measurement < 100:
            request.session['foot']['circumference'] = measurement
            request.session.modified = True
            save_foot(request)
            print(f"SAVE FOOT")
        else:
            return HttpResponse(status=400)

    if request.user.is_authenticated:
        return redirect('results')

    context = {
        'template': template(request),
        'title': title
    }

    return render(request, html, context)


def results(request):
    html = './results.html'
    title = 'Results'

    try:
        foot = get_foot(request)
        print(f"# Get foot results: ", foot, " and type: ", type(foot))
        results = get_matching_shoes(foot)
    except Exception as e:
        print(f"# Exception as e - results page: ", e)
        messages.error(
            request,
            'You need to input the values before we can provide you with matching shoes.',
            extra_tags='shoe_finder'
        )
        return redirect('/shoe-finder/length/')

    print(f"# results - foot: ", foot)

    """
    Todo: ShoeFilter operates on the shoes that match the user's foot in size. Improvement
    would be to move it over to the filters.py but the foot data cannot be passed. But in
    case of registered users it the foot can be retrieved from the database for a better
    performance.
    """
    shoe_filter = ShoeFilter(request.GET, queryset=results)
    paginator = Paginator(shoe_filter.qs, 12)

    context = {
        'template': template(request),
        'title': title,
        'foot': foot,
        'new_foot': new_foot(request),
        'results': paginator.get_page(request.GET.get('page')),
        'filter_groups': ['brands', 'colors', 'materials', 'closure_systems'],
        'shoe_filter': shoe_filter
    }

    return render(request, html, context)


def new_foot(request):
    try:
        foot = Foot.objects.get(user=request.user)
        if request.session.session_key:
            session_foot = Foot.objects.get(session_id=request.session.session_key)
            if session_foot.length != foot.length or session_foot.width != foot.width or session_foot.circumference != foot.circumference:
                return True
            else:
                return False
    except:
        return False


def update_foot(request):
    session_foot = Foot.objects.get(session_id=request.session.session_key)
    try:
        foot = Foot.objects.get(user=request.user)
        foot.length = session_foot.length
        foot.width = session_foot.width
        foot.circumference = session_foot.circumference
        foot.save()
        session_foot.delete()
        return redirect('results')
    except:
        pass


def filter_shoes(request, page=1):
    html = './shoes.html'

    try:
        results = get_matching_shoes(get_foot(request))
    except:
        return redirect('/shoe-finder/length/')
    shoe_filter = ShoeFilter(request.GET, queryset=results)
    paginator = Paginator(shoe_filter.qs, 12)

    context = {'results': paginator.get_page(request.GET.get('page'))}
    return (request, html, context)


def get_model_color(request, model_name, color):
    model_name = ' '.join(model_name.split('_'))
    model = Model.objects.get(name=model_name)
    color = ColorOption.objects.get(name=color)
    try:
        image = ShoeImage.objects.get(model=model, color__name=color).image
    except ShoeImage.DoesNotExist:
        image = 'shoes/empty.png'
    context = {'image_path': image, 'active': 0, 'model': model.formatted(), 'color': color.name}
    return render(request, './shoe_image.html', context)


def set_list_layout(request):
    request.session['layout'] = 'list'
    return HttpResponse(status=200)


def set_grid_layout(request):
    request.session['layout'] = 'grid'
    return HttpResponse(status=200)


def unsubscribe(request):
    title = 'Unsubscrbe from the newsletter'
    html = './account/unsubscribe.html'

    user_profile = UserProfile.objects.get(user=request.user)
    context = {
        'user_profile': user_profile
    }

    if request.method == 'POST':
        user_profile.subscribed = False
        user_profile.save()
        context['user_profile'] = user_profile
        return render(request, html, context)

    return render(request, html, context)


@login_required()
def profile(request):
    title = 'Profile'
    html = './profile.html'

    user = User.objects.get(username=request.user)
    # user_profile = UserProfile.objects.get(user=user)

    context = {
        'title': title,
        'user': user,
        # 'user_profile': user_profile,
        'template': template(request)
    }

    if request.user.is_authenticated:
        return render(request, html, context)


@login_required()
def delete_account(request):
    html = 'account/account_delete.html'
    if request.method == "POST":
        form = DeleteUserForm(request.POST)

        if form.is_valid():
            user = User.objects.get(username=request.user.username)
            logout(request)
            user.delete()
            return redirect('landing_page')

    else:
        form = DeleteUserForm()
        return render(request, html, {'form': form})


@login_required()
def change_email(request):
    html = 'account/email.html'

    if request.method =='POST':
        user = User.objects.get(username=request.user.username)
        form = EmailChangeForm(user, request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, 'Email successfully changed.')
            return render(request, html, {'form': form})
        else:
            return render(request, html, {'form': form})

    else:
        user = User.objects.get(username=request.user.username)
        form = EmailChangeForm(user)
        return render(request, html, {'form': form})


@login_required()
def change_name(request):
    html = 'account/name.html'

    if request.method == "POST":
        user = User.objects.get(username=request.user.username)
        form = CustomUserForm(data=request.POST, user=user)

        if form.is_valid():
            form.save()
            messages.success(request, 'Name successfully changed.')
            return render(request, html, {'form': form})

    else:
        form = CustomUserForm(user=request.user)
        return render(request, html, {'form': form})


class ModelAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # Don't forget to filter out results depending on the visitor !
        if not self.request.user.is_authenticated:
            return Model.objects.none()

        qs = Model.objects.all()

        if self.q:
            qs = qs.filter(brand__name__istartswith=self.q)

        return qs
