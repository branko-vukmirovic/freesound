#
# Freesound is (c) MUSIC TECHNOLOGY GROUP, UNIVERSITAT POMPEU FABRA
#
# Freesound is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# Freesound is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Authors:
#     See AUTHORS file.
#

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse

from bookmarks.forms import BookmarkForm
from bookmarks.models import *
from sounds.models import Sound
from utils.functional import combine_dicts
from utils.pagination import paginate


def bookmarks(request, username, category_id=None):

    user = get_object_or_404(User, username__iexact=username)
    is_owner = request.user.is_authenticated and user == request.user

    n_uncat = Bookmark.objects.select_related("sound").filter(user=user, category=None).count()

    if not category_id:
        category = None
        bookmarked_sounds = Bookmark.objects.select_related("sound").filter(user=user, category=None)
    else:
        category = get_object_or_404(BookmarkCategory, id=category_id, user=user)
        bookmarked_sounds = category.bookmarks.select_related("sound").all()

    bookmark_categories = BookmarkCategory.objects.filter(user=user)

    tvars = {'user': user,
             'is_owner': is_owner,
             'n_uncat': n_uncat,
             'bookmarked_sounds': bookmarked_sounds,
             'category': category,
             'bookmark_categories': bookmark_categories}
    tvars.update(paginate(request, bookmarked_sounds, 30))

    return render(request, 'bookmarks/bookmarks.html', tvars)


@login_required
def delete_bookmark_category(request, category_id):

    category = get_object_or_404(BookmarkCategory, id=category_id, user=request.user)
    msg = "Deleted bookmark category \"" + category.name + "\"."
    category.delete()
    messages.add_message(request, messages.WARNING, msg)

    next = request.GET.get("next", "")
    if next:
        return HttpResponseRedirect(next)
    else:
        return HttpResponseRedirect(reverse("bookmarks-for-user", args=[request.user.username]))


@login_required
def add_bookmark(request, sound_id):
    sound = get_object_or_404(Sound, id=sound_id)

    if request.POST:
        form = BookmarkForm(request.POST, instance=Bookmark(user=request.user, sound=sound))
        form.fields['category'].queryset = BookmarkCategory.objects.filter(user=request.user)
        if form.is_valid():
            form.save()

    if request.is_ajax():
        return HttpResponse()

    else:
        msg = "Added new bookmark for sound \"" + sound.original_filename + "\"."
        messages.add_message(request, messages.WARNING, msg)

        next = request.GET.get("next", "")
        if next:
            return HttpResponseRedirect(next)
        else:
            return HttpResponseRedirect(reverse("sound", args=[sound.user.username, sound.id]))


@login_required
def delete_bookmark(request, bookmark_id):

    bookmark = get_object_or_404(Bookmark, id=bookmark_id, user=request.user)
    msg = "Deleted bookmark for sound \"" + bookmark.sound.original_filename + "\"."
    bookmark.delete()
    messages.add_message(request, messages.WARNING, msg)

    next = request.GET.get("next", "")
    page = request.GET.get("page", "1")
    if next:
        return HttpResponseRedirect(next + "?page=" + str(page))
    else:
        return HttpResponseRedirect(reverse("bookmarks-for-user", args=[request.user.username]) + "?page=" + str(page))


@login_required
def get_form_for_sound(request, sound_id):
    sound = Sound.objects.get(id=sound_id)
    form = BookmarkForm(instance=Bookmark(name=sound.original_filename), prefix=sound.id)
    form.fields['category'].queryset = BookmarkCategory.objects.filter(user=request.user)
    categories_already_containing_sound = BookmarkCategory.objects.filter(user=request.user, bookmarks__sound=sound).distinct()
    add_bookmark_url = '/'.join(request.build_absolute_uri(reverse('add-bookmark', args=[sound_id])).split('/')[:-2]) + '/'

    tvars = {
        'bookmarks': Bookmark.objects.filter(user=request.user, sound=sound).count() != 0,
        'sound_id': sound.id,
        'form': form,
        'categories_aready_containing_sound': categories_already_containing_sound,
        'add_bookmark_url': add_bookmark_url
    }
    template = 'bookmarks/bookmark_form.html'
    return render(request, template, tvars)
