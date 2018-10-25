from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import ArticleColumn
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import HttpResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from .models import ArticleColumn, ArticlePost
from .forms import ArticleColumnForm, ArticlePostForm
from django.views.decorators.http import require_POST
from pandas.io.sas.sas_constants import column_name_length_length
from anaconda_navigator.utils.py3compat import request
# Create your views here.

@login_required(login_url='/account/login/')
@csrf_exempt
def article_column(request):
    if request.method == "GET":
        columns = ArticleColumn.objects.filter(user=request.user)
        print("columns: {}".format(columns))
        column_form = ArticleColumnForm()
        return render(request, 'article/column/article_column.html', {'column': columns, 'column_form': column_form})
    
    if request.method == "POST":
        print('request.POST: {}'.format(request.POST))
        column_name = request.POST['column']
        print("column_name: {}".format(column_name))
        columns = ArticleColumn.objects.filter(user_id=request.user.id, column=column_name)
        print("columns: {}".format(columns))

        if columns:
            return HttpResponse('2')
        else:
            ArticleColumn.objects.create(user=request.user, column=column_name)
            return HttpResponse("1")

      
@login_required(login_url="/account/login")
@require_POST
@csrf_exempt
def rename_article_column(request):
    column_name = request.POST["column_name"]
    column_id = request.POST["column_id"]
    try:
        line = ArticleColumn.objects.get(id=column_id)
        line.column = column_name
        line.save()
        return HttpResponse("1")
    except:
        return HttpResponse("0")


@login_required(login_url="/account/login")
@require_POST
@csrf_exempt
def del_article_column(request):
    column_id = request.POST["column_id"]
    try:
        line = ArticleColumn.objects.get(id=column_id)
        line.delete()
        return HttpResponse("1")
    except:
        return HttpResponse("2")

@login_required(login_url='/account/login')
@csrf_exempt
def article_post(request):
    if request.method == "POST":
        article_post_form = ArticlePostForm(data=request.POST)
        if article_post_form.is_valid():
            cd = article_post_form.cleaned_data
            try:
                new_article = article_post_form.save(commit=False)
                new_article.author = request.user
                new_article.column = request.user.article_column.get(id=request.POST['column_id'])
                new_article.save()
                return HttpResponse('1')
            except:
                return HttpResponse('2')
        else:
            return HttpResponse('3')
    else:
        article_post_form = ArticlePostForm()
        article_columns = request.user.article_column.all()
        return render(request, 'article/column/article_post.html', {'article_post_form': article_post_form, \
                                                                    'article_columns': article_columns})


@login_required(login_url='/account/login')
def article_list(request):
    articles_list = ArticlePost.objects.filter(author=request.user)
    paginator = Paginator(articles_list, 2)
    page = request.GET.get('page')
    try:
        current_page = paginator.page(page)
        articles = current_page.object_list
    except PageNotAnInteger:
        current_page = paginator.page(1)
        articles = current_page.object_list
    except EmptyPage:
        current_page = paginator.page(paginator.num_pages)
        articles = current_page.object_list    
    return render(request, "article/column/article_list.html", {"articles":articles, "page":current_page})

@login_required(login_url='/account/login')
def article_detail(request, id, slug):
    article = get_object_or_404(ArticlePost, id=id, slug=slug)
    return render(request, "article/column/article_detail.html", {"article": article})


@login_required(login_url='/account/login')
@require_POST
@csrf_exempt
def del_article(request):
    article_id = request.POST['article_id']
    try:
        article = ArticlePost.objects.get(id=article_id)
        article.delete()
        return HttpResponse("1")
    except:
        return HttpResponse("2")
    
    
@login_required(login_url='/account/login')
@csrf_exempt
def redit_article(request, article_id):
    print("article_id: {}".format(id))
    if request.method == "GET":
        article_columns = request.user.article_column.all()
        article = ArticlePost.objects.get(id=article_id)
        this_article_form = ArticlePostForm(initial={"title":article.title})
        this_article_column = article.column
        return render(request, "article/column/redit_article.html", {"article": article, \
                      "article_columns": article_columns, "this_article_column": this_article_column, \
                      "this_article_form": this_article_form})
    else:
        redit_article = ArticlePost.objects.get(id=article_id)
        try:
            redit_article.column = request.user.article_column.get(id=request.POST['column_id'])
            redit_article.title = request.POST['title']
            redit_article.body = request.POST['body']
            redit_article.save()
            return HttpResponse("1")
        except:
            return HttpResponse("2")