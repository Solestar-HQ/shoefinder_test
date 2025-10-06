from django.shortcuts import (
    redirect,
    reverse
)
from django.db.models import (
    F,
    DecimalField,
    Value,
    ExpressionWrapper
)
from .models import (
    Shoe,
    Brand,
    ColorOption,
    MaterialType,
    ClosureSystem,
    Foot
)
from django.core.mail import (
    send_mail
)


# check if the request comes from HTMX
def htmx(request):
    if request.headers.get('HX-Request') == 'true':
        return True


# check whether to return partial or full template. It returns partial if when it is a
# HTMX request because HTMX points where the content is going to be rendered.
def template(request):
    if htmx(request):
        return './partial.html'
    return './index.html'


def send_confirm_subscription_email(user):
    subject = "Please confirm your newsletter subscription"
    message = (
        "Confirm your subscription. Yes, subscribe me. If you received"
        "this email bymistake, simply delete it. You won't be subscribed"
        "if you don't click the confirmation link above."
    )
    sender = "support@solestar.de"
    recipient = user.email

    send_mail(
        subject,
        message,
        sender,
        recipient,
        fail_silently=False,
    )


def get_input_value(foot, step):
    input_value = None
    print(f"FOOT: ", foot)
    try:
        input_value = getattr(foot, step)
    except Exception  as e:
        print(f"Input value e: ", e)
        input_value = foot[step]
    return input_value


def get_foot(request):
    if 'foot' in request.session:
        return request.session['foot']
    else:
        try:
            if request.user.is_authenticated:
                return Foot.objects.get(user=request.user)
            else:
                raise ValueError("User is not authenticated.")
        except:
            if request.session.session_key:
                return Foot.objects.get(session_id=request.session.session_key)
            else:
                return redirect('/shoe-finder/length')
    # try to get the foot data through the user
    '''try:
        if request.user.is_authenticated:
            return Foot.objects.get(user=request.user)
        else:
            raise ValueError("User is not authenticated")
    except Exception as e:
        # try to get the foot through the session
        try:
            return Foot.objects.get(session_id=request.session.session_key)
        except:
            # there is no foot data, redirect user to the shoe finder
            return request.session['foot']'''


def get_matching_shoes(foot):
    matching_shoes = Shoe.objects.annotate(
        length_difference=ExpressionWrapper(
            F('max_foot_length')-float(foot['length'])*10,
            output_field=DecimalField()
        ),
        width_difference=ExpressionWrapper(
            F('max_foot_width')-float(foot['width'])*10,
            output_field=DecimalField()
        )
    ).filter(
        active=True,
        length_difference__lte=F('max_foot_length')-F('min_foot_length'),
        width_difference__lte=F('max_foot_width')-F('min_foot_width'),
        length_difference__gte=0,
        width_difference__gte=0
    ).order_by('model__name').distinct('model__name')
    return matching_shoes


def get_foot_session(request):
    # return foot session data in case it exists
    if 'foot' in request.session:
        return request.session['foot']

    # else create and return the new foot session
    else:
        request.session['foot'] = {
            'length': 0,
            'width': 0,
            'circumference': 0
        }
        return request.session['foot']


def save_foot(request):
    foot = request.session['foot']
    print(f"# Save foot: ", foot, foot['length'])
    '''if request.user.is_authenticated:
        try:
            Foot.objects.filter(user=request.user).update(
                length=foot['length'],
                width=foot['width'],
                circumference=foot['circumference']
            )
        except:
            Foot.objects.filter(session_id=request.session.session_key).update(
                length=foot['length'],
                width=foot['width'],
                circumference=foot['circumference']
            )
    else:'''
    if request.user.is_authenticated == False:
        if not request.session.session_key:
            request.session.create()
        Foot.objects.update_or_create(
            session_id=request.session.session_key,
            defaults=foot
        )
        '''
        # try to get the foot data through the session id and update it
        try:
           Foot.objects.filter(session_id=request.session.session_key).update(
                length=foot['length'],
                width=foot['width'],
                circumference=foot['circumference']
           )
           print(f"No session foot")
        # else create new foot object
        except Exception as e:
            print(f"# Exception - save foot: ", e)
            if not request.session.session_key:
                request.session.create()
            Foot.objects.create(
                session_id=request.session.session_key,
                length=foot['length'],
                width=foot['width'],
                circumference=foot['circumference']
            ) '''
    '''
    # try to get the foot data through the user and update it
    try:
        if request.user.is_authenticated:
            user_foot = Foot.objects.get(user=request.user)
            user_foot.length = foot['length']
            user_foot.width = foot['width']
            user_foot.circumference = foot['circumference']
            user_foot.save()
        else:
            raise ValueError("User is not authenticated.")
    except:
        # try to get the foot data through the session id and update it
        try:
            session_foot = Foot.objects.get(session_id=request.session.session_key)
            session_foot.length = foot['length']
            session_foot.width = foot['width']
            session_foot.circumference = foot['circumference']
            session_foot.save()
        # else create new foot object
        except:
            if not request.session.session_key:
                request.session.create()
            Foot.objects.create(
                session_id=request.session.session_key,
                length=foot['length'],
                width=foot['width'],
                circumference=foot['circumference']
            )
'''
